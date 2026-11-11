#!/usr/bin/env python3
"""
log_shipper.py — Week 4: adds account-creation and sudo-escalation detection,
and writes normalized events as JSON Lines (one JSON object per line) instead
of plain text — the format Wazuh's agent will ingest from Week 7 onward.
"""
import re
import json
from pathlib import Path

LOGFILE = "/var/log/auth.log"
OUTDIR = Path("/var/log/nyagaka")
JSON_OUTPUT = OUTDIR / "events.jsonl"
THRESHOLD = 20

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

if __name__ == "__main__":
    main()
