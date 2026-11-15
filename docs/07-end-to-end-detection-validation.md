# Week 13 — End-to-End Detection Validation

## Overview

Every piece of Block C/D has been verified individually across Weeks 7–12:
SSH detection, brute-force correlation, the WAF, FIM, AD. Week 13 proves the
**whole pipeline** end-to-end with two deliberate, precisely-timed tests —
agent sees it → Wazuh rule fires → alert lands — and surfaces two real
operational bugs that individual-component testing had never caught.

## Test 1: SSH brute-force against SRV01

6 real authentication failures sent through the SSH jump
(`ssh -J web wronguser@10.0.1.112`), landing on SRV01's actual sshd.

**First result: total pipeline failure, for a real reason.** Wazuh's
built-in SSHD ruleset caught it immediately (rule `5710`, 6/6), but the
**custom** Week 9 rules (`100005`/`100006`/`100011`) caught **zero**. Root
cause, confirmed directly rather than assumed:

- `log_shipper.py` (the custom JSON pipeline these rules depend on) had
  never been added to any schedule. Its last real event was 4 days old
  (Nov 11) — it had only ever been run manually during Week 3-5 testing.
- Root's crontab had the *original Stage 0 Bash monitor*
  (`ssh_login_monitor.sh`) scheduled every 15 minutes — and duplicated,
  identically, by mistake — which explains why log activity still looked
  "alive." The Python/JSON pipeline was a separate, silent gap underneath
  it the whole time.

**Fix (Finding 23):** removed the duplicate cron line, added a proper
schedule for `log_shipper.py`. The script originally re-read the entire
`auth.log` from byte 0 on every invocation — scheduling it as-is would have
appended duplicate copies of every historical event on every run. Added
byte-offset + inode tracking (a small state file) so each run only
processes genuinely new lines, verified by running it manually right after
initializing state and confirming `0 total events written`.

**Second result, same test, after scheduling: still zero on custom rules.**
Root cause (Finding 24, and genuinely my own mistake): the rewritten
script used the JSON key `"event_type"` — but Finding 18 (Week 9) already
established that this exact key collides with Wazuh's built-in Suricata
ruleset (rule `86600`), which silently claims the event before any custom
rule evaluates it. I reintroduced a bug that had already been fixed, by not
cross-checking the new code against the existing fix. Caught the same way
Finding 18 originally was: feeding a real captured event into
`wazuh-logtest` and watching rule `86600` claim it. Corrected the key to
`nyagaka_event_type` throughout.

**Final clean run:** 6 fresh real attempts → rule `100006` fired 5/5 on the
individual events, and rule `100011` (the brute-force correlation rule)
fired for real:
“description”:”Nyagaka: Possible SSH brute-force - 5+ failed logins from
10.0.0.157 within 10 seconds.”

Worth noting honestly: the 5 correlated events' own embedded `timestamp`
fields span about 23 seconds — wider than the rule's configured 10-second
window. Not a bug: Wazuh's `frequency`/`timeframe` counts by when
**analysisd actually processes** each match (all 6 arrived in one batch
when the per-minute cron job ran), not by the JSON payload's `timestamp`
field. The correlation window is about real alert-processing time, not log
content time.

**Detection latency:** bounded by the shipper's 1-minute cron interval —
not a clean single-test number, since this test was run multiple times
while debugging the two issues above. Reported honestly as "within one
cron cycle" rather than a false-precision figure.

## Test 2: SQL injection against WEB01

Fresh, precisely-timed test: `GET /?id=1' OR '1'='1` (URL-encoded) sent at
`13:01:58 UTC`.

- **Blocking:** instant — `403 Forbidden`, ModSecurity rule `942100`
  (libinjection SQLi match) + `949110` (anomaly score 8) fired inline.
- **SIEM alert:** rule `100012` logged at `13:02:13.953 UTC` — confirmed by
  matching the real `client_ip` (`196.207.135.31`) and query string in the
  alert body, not just a nearby timestamp.
- **Real detection latency: ~16 seconds**, end-to-end from request to
  SIEM alert (the block itself was instant; this is how long the
  audit-log → Filebeat → Wazuh → rule-match chain took).

## A genuine false-positive check (and a real true positive instead)

While searching for this test's alert, found a different `100012` hit from
real, unrelated internet traffic: `client_ip: 64.225.54.158`, requesting
`/.git/config` — classic opportunistic scanning for exposed git
repositories. Not a false positive at all — a real external probe,
legitimately blocked and alerted on by the same rule. Worth keeping in the
case study as evidence the WAF is doing real work against real internet
background noise, not just our own test payloads.

## Numbers for the case study

| Test | Attempts | Custom rules fired | Detection latency | False positives |
|---|---|---|---|---|
| SSH brute-force (SRV01) | 6 real | `100006` ×5, `100011` ×1 | within 1 cron cycle (not cleanly isolated — see note above) | 0 |
| SQLi (WEB01) | 1 real | `100012`, `100014` | ~16 seconds | 0 (plus 1 genuine true positive against real external scanning) |

## Next

Write the full case study (Situation → Problem → Investigation → What I
got wrong → Broken detection and fix → Results → Lessons), pulling from
this doc and the project's full findings log.
