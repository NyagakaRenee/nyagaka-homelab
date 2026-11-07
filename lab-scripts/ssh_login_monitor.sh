#!/bin/bash
# Counts failed SSH logins and flags a possible brute-force pattern.
# Runs as root from cron (needs to read auth.log). Absolute paths only:
# under cron/sudo, $HOME is /root, not the admin user's home.
LOGFILE="/var/log/auth.log"
OUTDIR="/var/log/nyagaka"
OUTPUT="$OUTDIR/ssh_alerts.log"
PATTERN="Failed password|Invalid user"
THRESHOLD=20

mkdir -p "$OUTDIR"
echo "=== SSH Login Check: $(date) ===" >> "$OUTPUT"
grep -E "$PATTERN" "$LOGFILE" | tail -10 >> "$OUTPUT"
FAIL_COUNT=$(grep -cE "$PATTERN" "$LOGFILE")
echo "Total failed/invalid attempts logged: $FAIL_COUNT" >> "$OUTPUT"

if [ "$FAIL_COUNT" -gt "$THRESHOLD" ]; then
    echo "ALERT: High volume of failed attempts, possible brute-force activity!" >> "$OUTPUT"
fi
