# Python Log Shipper

A security-event parser and forwarding agent, built as a Python port of the
Bash `ssh_login_monitor.sh` detection script (Stage 0/Block A), extended with
structured output and network forwarding.

## What it does

Parses `/var/log/auth.log` for three categories of security-relevant events:

| Category | Detects | Example trigger |
| --- | --- | --- |
| SSH probing | invalid usernames, failed password attempts | a login attempt for a username that doesn't exist |
| Account changes | account creation, group membership changes | `useradd`, `usermod -aG` |
| Sudo escalation | failed sudo authentication | a wrong sudo password |

Each match is normalized into a single JSON object with four fields:
`timestamp`, `hostname`, `event_type`, `target_user`, `src_ip` (or `"local"`
for events with no network origin, such as account changes).

## Output

- **Local file:** every run appends matched events as JSON Lines to
  `/var/log/nyagaka/events.jsonl` — one JSON object per line, the format
  Wazuh's agent will ingest directly via a `<localfile>` entry from Week 6
  onward.
- **Network push (optional):** each event is also POSTed to a central
  receiver (`receiver.py`, in this repo's `receiver/` folder) running on
  SIEM01. This stands in for the real Wazuh manager until it's installed, so
  the forwarding path is built and proven ahead of time rather than
  discovered to be broken once the SIEM exists.

## Deployment

Runs identically on WEB01 and SRV01. Requires `python3-requests`:

```bash
sudo apt install -y python3-requests
```

Set `PUSH_URL` in `log_shipper.py` to the receiver's address (currently
SIEM01's private IP, port 5000) and `PUSH_ENABLED = True`/`False` to toggle
network forwarding without touching the local-file logic.

Run manually with `sudo python3 log_shipper.py`, or on the same 15-minute
cron cadence as the original Bash monitor.

## Design notes

- Parses the **whole log file each run**, not a live tail — needed for
  totals that are directly comparable to the Bash script's counts, not just
  "whatever happened since the script last checked."
- Anchors SSH patterns to `sshd[<pid>]:` specifically, not just matching
  keywords anywhere in the line — avoids counting `sudo`'s own audit-trail
  entries, which can contain the same search words for an unrelated reason
  (see `mistakes-and-findings.md`, finding 13).
- The push step is deliberately best-effort: a network failure to the
  receiver is logged as a failed send count, never raised as an exception
  that would stop the local file from being written.

See the repo's [`mistakes-and-findings.md`](../docs/mistakes-and-findings.md)
for the real bugs hit building this (a silent vim-edit regression, a stale
firewall rule from Block A that blocked the receiver's port, and the
sudo/self-matching bug above).
