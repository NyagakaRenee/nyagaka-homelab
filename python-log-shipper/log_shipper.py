#!/usr/bin/env python3
"""
log_shipper.py — Python port of ssh_login_monitor.sh (Nyagaka homelab, Block B Week 3).
Parses the whole auth.log, same as the bash version, so the totals are directly
comparable. Anchored to sshd[pid]: to exclude sudo audit lines (finding 13).
"""
import re
from pathlib import Path
from datetime import datetime, timezone

LOGFILE = "/var/log/auth.log"
OUTDIR = Path("/var/log/nyagaka")
OUTPUT = OUTDIR / "ssh_alerts_python.log"
THRESHOLD = 20

# Only lines that start sshd[pid]: — excludes sudo lines entirely, same fix as finding 13.
PREFIX_RE = re.compile(r"sshd\[(?P<pid>\d+)\]:\s*(?P<message>.*)")

# Tried in order, most specific first. Real sshd lines come in these shapes:
#   "Failed password for invalid user bob from 10.0.0.5 port 54321 ssh2"
#   "Failed password for root from 10.0.0.5 port 54321 ssh2"
#   "Invalid user bob from 10.0.0.5 port 54321"
# "Connection closed by invalid user ... [preauth]" is deliberately NOT matched here —
# it's the same attempt logged a second time, and counting it would double the total.
EVENT_PATTERNS = [
            ("failed_invalid_user", re.compile(r"Failed password for invalid user (?P<user>\S+) from (?P<ip>\S+)")),
            ("failed_password",     re.compile(r"Failed password for (?P<user>\S+) from (?P<ip>\S+)")),
            ("invalid_user",        re.compile(r"Invalid user (?P<user>\S+) from (?P<ip>\S+)")),
]

def parse_log(logfile):
    events = []
    with open(logfile, "r") as f:
        for line in f:
            prefix_match = PREFIX_RE.search(line)
            if not prefix_match:
                continue  # not an sshd line at all (e.g. a sudo entry)
            message = prefix_match.group("message")
 

            for event_type, pattern in EVENT_PATTERNS:
                m = pattern.search(message)
                if m:
                    events.append({
                        "pid": prefix_match.group("pid"),
                        "event_type": event_type,
                        "target_user": m.group("user"),
                        "src_ip": m.group("ip"),
                        })
                    break  # stop at the first pattern that matches this line
    return events

def count_by_source(events):
    """Dict of src_ip -> count. This is the per-IP breakdown Week 9's brute-force rule (5+ failures from one IP) will eventually need."""
    counts = {}
    for e in events:
        counts[e["src_ip"]] = counts.get(e["src_ip"], 0) + 1
    return counts

def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    events = parse_log(LOGFILE)
    fail_count = len(events)
    by_source = count_by_source(events)

    with open(OUTPUT, "a") as out:
        out.write(f"=== SSH Login Check (python): {datetime.now(timezone.utc)} ===\n")
        for e in events[-10:]:
            out.write(f"{e['event_type']}: {e['target_user']} from {e['src_ip']}\n")
            out.write(f"Total failed/invalid attempts logged: {fail_count}\n")
        for ip, count in by_source.items():
            out.write(f"  from {ip}: {count}\n")
        if fail_count > THRESHOLD:
            out.write("ALERT: High volume of failed attempts, possible brute-force activity!\n")
    
    print(f"Done. Total: {fail_count}. See {OUTPUT}")

if __name__ == "__main__":
    main()
