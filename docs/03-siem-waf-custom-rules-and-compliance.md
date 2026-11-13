# Week 9 — Custom Detection Rules, FIM & Compliance Matrix

## Overview

Week 9 adds custom Wazuh detection logic on top of the SIEM/WAF pipeline built in
Weeks 6–8, plus real-time File Integrity Monitoring (FIM) on two security-critical
config files, and maps each control to a specific section of the **Kenya Data
Protection Act, 2019** (Act No. 24 of 2019).

All rules below were written on the manager (`/var/ossec/etc/rules/local_rules.xml`
on SIEM01) and verified with real, triggered traffic — not assumed or synthetic
data. See `docs/mistakes-and-findings.md` (findings 18–19) for the debugging story
behind two of these: a field-name collision with Wazuh's built-in Suricata
ruleset, and a static-vs-dynamic-field correlation bug.

## Custom Rules

| Rule ID | Level | Trigger | Description |
|---|---|---|---|
| 100005 | 3 | Base ingestion | Any custom Python-detected event reaching Wazuh from `events.jsonl` |
| 100006 | 5 | SSH auth failure | Invalid user / failed password / failed invalid user, per event |
| 100011 | 10 | Correlation | 5+ rule-100006 matches from the same source IP within 10 seconds (brute-force) |
| 100013 | 8 | Account change | Account created or modified |
| 100014 | 3 | Base ingestion | Any ModSecurity audit event reaching Wazuh from `modsec_audit.log` |
| 100012 | 10 | WAF block | ModSecurity returned HTTP 403 (request blocked) |
| (built-in) 550 | 7 | FIM | Real-time integrity checksum change on a monitored file |

The full deployed rule file is at `docs/local_rules.xml` in this repo (copied from
`/var/ossec/etc/rules/local_rules.xml` on SIEM01).

## File Integrity Monitoring (FIM)

Real-time `<syscheck>` monitoring was added on WEB01 for two files that are
high-value targets for tampering:

- `/etc/ssh/sshd_config` — SSH daemon configuration (e.g. silently re-enabling
  password auth or root login would be a serious, hard-to-notice compromise)
- `/etc/fail2ban/jail.local` — intrusion-prevention configuration (an attacker
  disabling or weakening this would remove a key defense silently)

This is in addition to Wazuh's default 12-hour scheduled scan of `/etc` —
the custom entries give **real-time** (`realtime="yes"`), **full-detail**
(`check_all="yes"`) monitoring specifically on these two files, rather than
relying on the broad, infrequent default scan to eventually notice a change.

Verified: appending a single test comment line to each file produced a
real-time FIM alert (Wazuh's built-in rule 550, "Integrity checksum changed")
within seconds, with full before/after size, mtime, md5, sha1 and sha256 values.

## Compliance Mapping — Kenya Data Protection Act, 2019

Section numbers below were checked directly against the Act's text as hosted
by the Office of the Data Protection Commissioner (ODPC), not assumed. An
earlier working note in this project's tracker had guessed "Section 41,
Security Safeguards" — the section number was right but the subtitle was
wrong; the real heading is below.

### Section 41 — Data Protection by Design or by Default

> Requires a data controller/processor to adopt "appropriate technical and
> organisational measures" to apply data protection principles effectively,
> at the time processing means are determined *and* during processing itself,
> including measures to "establish and maintain appropriate safeguards against
> the identified risks" (s. 41(4)).

| Control | How it satisfies Section 41 |
|---|---|
| Rule 100006 / 100011 (SSH brute-force detection) | Identifies and alerts on a reasonably foreseeable risk (credential-stuffing / brute-force login attempts) in real time |
| Rule 100012 (WAF block alerting) | Confirms the technical safeguard (ModSecurity + OWASP CRS) is actively blocking SQLi and other attacks, and surfaces each block as a monitored event rather than a silent log line |
| Rule 100013 (account change detection) | Flags unexpected privilege/account changes, a key risk vector for insider or post-compromise activity |
| FIM on `sshd_config` / `jail.local` | Verifies that the safeguards themselves (SSH hardening, intrusion prevention) have not been tampered with — directly matches s. 41(4)(e)'s requirement to "verify that the safeguards are effectively implemented" |

### Section 43 — Notification and Communication of Breach

> Where personal data is accessed or acquired by an unauthorised person and
> there is a real risk of harm, the controller must notify the Data
> Commissioner "without delay, within seventy-two hours of becoming aware of
> such breach" (s. 43(1)(a)).

| Control | How it satisfies Section 43 |
|---|---|
| All rules above (100006, 100011, 100012, 100013, FIM/550) | These are the detection mechanisms that establish the moment of "becoming aware" of a potential breach — the starting point of the 72-hour notification clock. Without real-time detection, this legal clock could start late (or never), through no intentional fault but simply through not knowing an incident occurred. |

**Honest scope note:** these controls detect and alert on security events; they
do not themselves perform breach notification to the ODPC. That remains a
human/process responsibility. What this project demonstrates is the
*technical visibility* that Section 41 and Section 43 both presuppose a
controller must have in order to meet their legal obligations at all.

## Testing Methodology Note

Every rule above was verified against **real triggered traffic**, not
synthetic or assumed data — e.g., `wazuh-logtest` alone was insufficient for
location-based rules (it does not simulate a real logcollector `<location>`),
so final verification for those rules always went through the live pipeline
(real SSH attempts, real curl-based SQLi probes, real file edits) and a
direct check of `/var/ossec/logs/alerts/alerts.json` on the manager.
