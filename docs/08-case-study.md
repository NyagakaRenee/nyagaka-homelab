# Nyagaka Enterprises — Stage 1 Case Study
### Migrating, Instrumenting, and Defending a Hybrid Cloud/On-Prem Network

**Author:** Renee Nyagaka Machini
**Repo:** [NyagakaRenee/nyagaka-homelab](https://github.com/NyagakaRenee/nyagaka-homelab)
**Period:** October – November 2026

> Nyagaka Enterprises is a simulated company built for this project. No real
> organization, customer data, or production system is involved — this is a
> self-directed home lab, documented honestly, including every real mistake
> made along the way.

---

## Situation

Nyagaka Enterprises started as a small, entirely local network built in
VirtualBox during Stage 0 — three VMs (a core server, a web server, a
Windows workstation) on a single laptop, with basic hardening (SSH keys,
UFW, Fail2ban, a monitoring script) but no central visibility, no WAF, and
no identity infrastructure. The laptop was also starting to buckle under
the load of running three VMs plus a planned SIEM.

The brief I set for myself going into Stage 1: migrate the load-bearing
infrastructure to the cloud, build real detection and response capability
on top of it, and do it as a genuine build-and-debug exercise rather than a
follow-the-tutorial lab — including documenting every real failure, not
just the final working state.

## Problem

Four concrete problems needed solving, in order:

1. **Capacity** — the local lab couldn't keep growing on one laptop.
2. **Visibility** — three hardened servers with no central log aggregation
   means nobody is actually watching them; hardening without detection is
   half a security posture.
3. **Exposure** — a public-facing web server with no application-layer
   defense is one unpatched dependency away from compromise.
4. **Identity** — none of this had any centralized identity/access
   management; every account was local to its own box.

## Investigation

### Block A — Migrating to Oracle Cloud (OCI)

Moved the three-tier lab (`SRV01` admin/bastion, `WEB01` public web +
WAF, `SIEM01` manager) onto OCI's Always Free tier, deliberately as a
**lift-and-shift**, not a cloud-architecture deep dive — the goal was to
stop the laptop struggling, not to relearn networking from scratch.

- Checked real Always Free limits in-console rather than trusting stale
  documentation (OCI's own limits were reported to have changed mid-2026).
- Built the network with console wizard defaults, launched all three
  servers, re-applied the hardening already built in Stage 0 (UFW,
  Fail2ban, SSH key-only auth, PAM password policy).
- SSH access locked to a single known IP with a documented recovery path
  via OCI's browser-based console connection (a separate RSA key, since the
  console tool rejected the normal Ed25519 key).
- Real baseline captured before and after migration
  (`docs/before-after.md`): port `111`/`rpcbind` closed on all three
  servers post-hardening; zero real failed SSH attempts reaching the
  public servers; the one failed attempt recorded on SRV01 was a
  deliberate self-test, not an intrusion attempt.

### Block B — Security Automation in Python

Ported the original Bash SSH-monitoring script to Python (`log_shipper.py`),
normalizing events to JSON Lines (`timestamp`, `src_ip`, `target_user`,
`event_type`) ahead of the real SIEM install — deliberately built one
week before Wazuh existed, so the forwarding path and schema were already
proven when the manager came online in Block C.

- Expanded detection coverage beyond SSH failures to account creation
  (`useradd`/`usermod`) and `sudo` authentication failures.
- Built a lightweight Flask receiver on SIEM01 as a stand-in central
  collector before the real Wazuh manager existed, to prove the forwarding
  path end-to-end ahead of time.
- Cross-checked the Python parser against the original Bash script on real
  `auth.log` data — exact match, building confidence in the port before
  extending it.

### Block C — SIEM, WAF, and Custom Detection Engineering

- Installed Wazuh 4.14 (manager/indexer/dashboard) on SIEM01, enrolled
  SRV01 and WEB01 as agents, and wired the custom JSON log into Wazuh via
  a `<localfile>` block.
- Built a real reverse-proxy WAF on WEB01: Nginx + ModSecurity v3 (compiled
  from source for ARM64) + OWASP Core Rule Set v4.30.0. Verified in
  `DetectionOnly` mode first (confirmed SQLi detection logged but not
  blocked), then switched to active blocking at paranoia level 1 —
  confirmed a real SQLi payload → `403`, a legitimate request → `200`.
- Wrote custom Wazuh rules: individual SSH-failure detection, a
  brute-force correlation rule (5+ failures from one source within 10
  seconds), account-change detection, and ModSecurity audit-log ingestion
  with a dedicated WAF-block detection rule.
- Added real-time File Integrity Monitoring on two security-critical files
  (`sshd_config`, `fail2ban/jail.local`), verified with a live edit and a
  genuine alert within seconds.
- Mapped the custom rules and FIM to two sections of the Kenya Data
  Protection Act (2019) — Section 41 (data protection by design/default)
  and Section 43 (72-hour breach notification) — independently verified
  against the Act's actual published text, not assumed from a guessed
  section title.

### Block D — Identity: Active Directory

- Promoted a fresh Windows Server 2025 Server Core VM to a new AD forest
  (`nyagaka.internal`), chosen as a real IANA-reserved private-use TLD
  rather than an unowned public-style name.
- Built Organizational Units (`Nyagaka-Production`, `Nyagaka-Admin`), a
  test user, and a domain-level password/lockout policy — deliberately
  configured at the domain root rather than an OU, since account
  policy specifically only applies from that scope.
- Proved enforcement with a real deliberate 5-attempt lockout test, not
  just a configuration read: `BadLogonCount: 5`, `LockedOut: True`,
  cleared afterward with `Unlock-ADAccount`.

### Hardening and full-stack validation

- Nginx hardening on WEB01: closed two real information-disclosure leaks
  (`server_tokens`, the default error-page footer both advertising the
  exact Nginx version and OS) and confirmed `autoindex` was genuinely off
  with a real test request, not just an absent config line. Re-tested the
  WAF afterward to confirm no regression.
- A full end-to-end validation pass: a real SSH brute-force burst and a
  real SQL injection attempt, tracing each one from the raw log event all
  the way to a SIEM alert.

## What I Got Wrong

Documented honestly rather than smoothed over — the project's
`mistakes-and-findings.md` log runs to 24 entries. The most instructive:

- **A layered-firewall blind spot (Finding 6):** UFW showed the right
  rules, but a legacy `iptables` `REJECT` rule sitting above UFW's own
  chain was silently blocking traffic anyway. Looked like a UFW
  misconfiguration; was actually two firewalls disagreeing.
- **A leaked private key in git history (Finding 9):** found by manually
  auditing the repo's own commit history, not a scanner. Fixed by
  rewriting history into a clean bundle and rotating to a fresh
  repo-scoped deploy key — treated as a real incident, not patched
  quietly.
- **A custom field name colliding with a built-in ruleset (Finding 18):**
  a JSON field named `event_type` was silently claimed by Wazuh's
  built-in Suricata rule before any custom rule could see it — zero
  errors anywhere to flag it. Found only by feeding a real event directly
  into `wazuh-logtest`.
- **A correlation rule built on the wrong kind of field (Finding 19):**
  `<same_source_ip/>` only ever matches Wazuh's *static* `srcip` field,
  which a generic JSON decoder never populates. The fix,
  `<same_field>src_ip</same_field>`, looks like a one-character detail
  but reflects a real architectural distinction in how Wazuh's rule
  engine treats static versus dynamic fields.
- **A detection pipeline that worked perfectly by hand and not at all on
  its own (Findings 23 & 24):** running a real end-to-end test during
  final validation showed the project's own custom rules catching
  nothing, while Wazuh's built-in ruleset caught everything. Root cause:
  the Python log shipper had never actually been scheduled anywhere — it
  only ever ran when triggered manually during earlier testing. Fixing
  that (adding a cron schedule with proper offset tracking to avoid
  duplicate reprocessing) exposed a second issue: the fix itself
  accidentally reintroduced the Finding 18 field-collision bug, caught
  again via `wazuh-logtest` before being written down as resolved.

## Broken Detections and Fixes

The table below is a condensed index — the full diagnostic detail for each
lives in `docs/mistakes-and-findings.md`.

| # | Broken detection | Real root cause | Fix |
|---|---|---|---|
| 13 | Detection script flagged itself | Script's own sudo audit-trail entries matched its own pattern | Excluded the script's own log lines from the match |
| 16 | Events never reached the alerts/archives index | Needed **both** `ossec.conf`'s `logall`/`logall_json` **and** Filebeat's separate `archives.enabled` | Enabled both, confirmed via Discover view |
| 18 | Custom rules caught zero events | Field name `event_type` silently claimed by built-in Suricata rule 86600 | Renamed to `nyagaka_event_type` |
| 19 | Brute-force correlation never fired | `<same_source_ip/>` only checks a static field a JSON decoder never populates | `<same_field>src_ip</same_field>` instead |
| 23 | Custom rules caught nothing in a live end-to-end test | `log_shipper.py` was never scheduled — only ever run manually | Added a cron schedule with byte-offset tracking to prevent duplicate reprocessing |
| 24 | Same symptom, immediately after fixing #23 | The fix itself reused the `event_type` key, reintroducing Finding 18 | Corrected to `nyagaka_event_type`, re-verified live |

## Results

**Infrastructure**
- Three-tier network fully migrated off a single laptop onto OCI's Always
  Free tier, within the real (and, mid-project, revised-downward) resource
  limits.
- A real identity backbone (AD forest, OUs, enforced account policy) added
  where none existed before.

**Detection, measured, not claimed**

| Test | Real attempts | Custom rules fired | Detection latency | False positives |
|---|---|---|---|---|
| SSH brute-force (SRV01) | 6 | `100006` ×5, `100011` ×1 (correlation) | within one scheduler cycle | 0 |
| SQL injection (WEB01) | 1 | `100012`, `100014` | ~16 seconds, request to SIEM alert | 0 — plus one genuine true positive against real, unrelated internet scanning traffic (`/.git/config` probe) caught by the same rule |
| File integrity (WEB01) | 1 real edit | built-in rule 550 | seconds | 0 |

**Compliance**
- Two sections of the Kenya Data Protection Act (2019) mapped to specific,
  live technical controls, independently verified against the Act's own
  published text rather than assumed.

## Lessons

1. **A component that works in isolation is not a pipeline.** Every piece
   of this stack passed its own individual test at some point; the
   end-to-end validation in Week 13 still found two real gaps that
   component-level testing had never surfaced.
2. **Silence is not success.** More than once — a `New-ADUser` typo, a
   scheduled job that was never actually scheduled — the absence of a
   visible error was mistaken for a working state. Every account-creation
   and detection-pipeline claim in this project now gets checked directly
   against real output before being accepted.
3. **A previously-fixed bug can come back the moment related code gets
   touched again**, if the rewrite isn't checked against what the original
   fix actually required (Finding 24 reintroducing Finding 18).
4. **Verify claims against raw evidence, not against how confident the
   claim sounds** — true whether the claim comes from a teammate, a
   second AI consulted for a second opinion, or your own assumption about
   what "should" be happening. `wazuh-logtest`, real curl output, and real
   `alerts.json` entries settled every real dispute in this project; no
   finding was written down from a description alone.
5. **Honest debugging is the actual portfolio value.** The clean final
   state of this network is far less informative, to someone evaluating
   this work, than the real path of failures and root-causes that got it
   there.
