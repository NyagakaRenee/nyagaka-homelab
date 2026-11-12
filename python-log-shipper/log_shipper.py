#!/usr/bin/env python3
"""
log_shipper.py — Week 4 added account-creation and sudo-escalation detection
and JSON Lines output. Week 5 adds an optional push to a central receiver
(a stand-in for the Wazuh manager, which doesn't exist until Week 6) so the
forwarding path exists and is proven ahead of the real SIEM install.
"""
import re
import json
import requests
from pathlib import Path

LOGFILE = "/var/log/auth.log"
OUTDIR = Path("/var/log/nyagaka")
JSON_OUTPUT = OUTDIR / "events.jsonl"
THRESHOLD = 20

PUSH_URL = "http://10.0.0.236:5000/events"
PUSH_ENABLED = True

PREFIX_RE = re.compile(
    r"^(?P<timestamp>\S+)\s+(?P<hostname>\S+)\s+"
    r"(?P<process>\w+)(?:\[(?P<pid>\d+)\])?:\s*(?P<message>.*)$"
)

SSH_PATTERNS = [
    ("failed_invalid_user", re.compile(r"Failed password for invalid user (?P<user>\S+) from (?P<ip>\S+)")),
    ("failed_password",     re.compile(r"Failed password for (?P<user>\S+) from (?P<ip>\S+)")),
    ("invalid_user",        re.compile(r"Invalid user (?P<user>\S+) from (?P<ip>\S+)")),
]
ACCOUNT_PATTERNS = [
    ("account_created",  re.compile(r"new user: name=(?P<user>[^,]+)")),
    ("account_modified", re.compile(r"add '(?P<user>[^']+)' to group '(?P<group>[^']+)'")),
]
SUDO_PATTERNS = [
    ("sudo_auth_failure", re.compile(r"authentication failure;.*\buser=(?P<user>\S+)")),
]

def parse_log(logfile):
    events = []
    with open(logfile, "r") as f:
        for line in f:
            m = PREFIX_RE.search(line)
            if not m:
                continue
            process, message = m.group("process"), m.group("message")

            if process == "sshd":
                patterns, has_ip = SSH_PATTERNS, True
            elif process in ("useradd", "usermod"):
                patterns, has_ip = ACCOUNT_PATTERNS, False
            elif process == "sudo":
                patterns, has_ip = SUDO_PATTERNS, False
            else:
                continue

            for event_type, pattern in patterns:
                em = pattern.search(message)
                if em:
                    events.append({
                        "timestamp": m.group("timestamp"),
                        "hostname": m.group("hostname"),
                        "event_type": event_type,
                        "target_user": em.groupdict().get("user"),
                        "src_ip": em.groupdict().get("ip") if has_ip else "local",
                    })
                    break
    return events

def push_events(events):
    """Best-effort push to the central receiver. Never crash the script over
    a network issue — the local JSON Lines file is always the source of truth."""
    sent, failed = 0, 0
    for e in events:
        try:
            resp = requests.post(PUSH_URL, json=e, timeout=3)
            if resp.status_code == 200:
                sent += 1
            else:
                failed += 1
        except requests.exceptions.RequestException:
            failed += 1
    return sent, failed

def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    events = parse_log(LOGFILE)

    with open(JSON_OUTPUT, "a") as out:
        for e in events:
            out.write(json.dumps(e) + "\n")

    ssh_fails = sum(1 for e in events if e["event_type"] in ("failed_invalid_user", "failed_password", "invalid_user"))
    print(f"Done. {len(events)} total events written to {JSON_OUTPUT}")
    print(f"  SSH failures: {ssh_fails}")
    print(f"  Account changes: {sum(1 for e in events if e['event_type'].startswith('account'))}")
    print(f"  Sudo failures: {sum(1 for e in events if e['event_type'] == 'sudo_auth_failure')}")
    if ssh_fails > THRESHOLD:
        print("ALERT: High volume of SSH failures, possible brute-force activity!")

    if PUSH_ENABLED and events:
        sent, failed = push_events(events)
        print(f"Pushed to receiver: {sent} sent, {failed} failed")

if __name__ == "__main__":
    main()
