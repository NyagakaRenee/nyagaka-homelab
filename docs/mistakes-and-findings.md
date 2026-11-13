# Mistakes and Findings Log

A running record of what went wrong, how I found the cause, and what fixed it. Newest entries at the bottom.

## Stage 0: local lab

| Problem | Cause | Fix |
| --- | --- | --- |
| Monitoring script wrote to the wrong place and failed silently | `$HOME` resolves to `/root` under `sudo` | Use explicit paths in scripts and test them under `sudo` |
| `apt update` failed in a VM | Clock drift made certificates look invalid | Reset the clock with `sudo date -s` |
| VM would not start 64-bit guests | VT-x disabled in BIOS/UEFI | Enable virtualization in UEFI settings |
| Host-to-VM SSH confusing | Mixed up NAT and bridged networking | Use NAT with port forwarding, or a second internal adapter |

## Stage 1: OCI migration

### 1. Wrong public key at launch
- **Symptom:** `Permission denied (publickey)` on the new web server.
- **Diagnosis:** The server was reachable, so the network and firewall were fine, and the login was refused. Another server accepted the same key, so the wrong key had been pasted into the launch form.
- **Fix:** Terminated the instance, created it again with the correct public key.
- **Lesson:** Check the key line (starts with `ssh-ed25519`, one line) before clicking Create. A key can't be swapped on a running instance.

### 2. SSH timed out after locking the rule to my IP
- **Symptom:** `Connection timed out` on port 22 from a laptop that had connected before.
- **Diagnosis:** Earlier logins from the same laptop and network had worked, so an ISP block was unlikely. The security-list rule allowed one source address, and my public address had changed.
- **Fix:** Updated the rule's source to my current address and removed the open-to-all SSH rule.
- **Lesson:** Home addresses change. Keep a console connection as a recovery path and write the update routine down.

### 3. Ports opened too widely
- **Problem:** I added a 443 rule open to the internet on the subnet-wide security list, which would have exposed the SIEM host too.
- **Fix:** Removed it. Web ports will go on a network security group attached to the web server only.
- **Lesson:** A security list applies to every host in the subnet. Per-host rules belong in a network security group.

### 4. Console connection rejected my SSH key
- **Symptom:** The OCI console connection dialog said the public key was invalid.
- **Diagnosis:** The key was a correctly formatted Ed25519 key that works for normal SSH. The console connection dialog accepts RSA keys, so the key type was the problem, not the paste.
- **Fix:** Generated a separate 4096-bit RSA key used only for the console, with a passphrase. The normal SSH key is unchanged.
- **Lesson:** "Invalid key" can mean an unsupported key type, not just a bad paste. Keep one key per purpose so a problem with one does not affect the other.

### 5. Console connection command did not match my tools
- **Symptom:** The command copied from the console connection page did not run on Windows.
- **Diagnosis:** The Windows variant relies on PuTTY (`plink`) and a `.ppk` key. I use OpenSSH with an OpenSSH-format key, so I rebuilt the command as an `ssh` call with a `ProxyCommand`. My first attempts failed because I pasted a placeholder literally, and then because a stray port-forward option ended up inside a variable.
- **Fix:** Put each OCID alone in a PowerShell variable and built the command from those.
- **Lesson:** Check what tool a copied command assumes before running it. When a command fails with an odd parse error, print the variables and look for extra text.

### 6. Host firewall blocked the web ports despite correct cloud rules
- **Symptom:** (caught before it caused an outage) the host's iptables list had `REJECT all` above the allow rules for 80/443, plus a duplicated default set.
- **Diagnosis:** Listing `iptables -L INPUT --line-numbers` showed rules were evaluated top to bottom, so allows placed after the REJECT never matched. Some of the stray rules, including ports 1514/1515, had been added earlier from an unreviewed plan.
- **Fix:** Inserted 80/443 allows above the REJECT to confirm the page loaded, then moved to UFW as the single manager of host rules and removed the stray 1514/1515 rules, including from the saved rules file.
- **Lesson:** Cloud rules and host rules are two separate layers, and both must allow the traffic. Review commands from any source, including another AI, against the live state before running them.

### 7. Stage 0 password policy was too weak for internet-facing servers
- **Problem:** The Stage 0 policy used `minlen=3`, convenient for testing but not acceptable on cloud hosts.
- **Fix:** Raised to `minlen=12` with digit, upper, lower and symbol rules and a 5-password history on all three servers, and tested that a weak password is rejected.
- **Lesson:** Lab shortcuts need to be tightened when a system moves to a public network.

### 8. Fail2ban ignored my config file
- **Symptom:** `fail2ban-client get sshd ignoreip` said nothing was ignored, even though `jail.local` listed the jump host.
- **Diagnosis:** The file was correct. Fail2ban had started automatically at install, before the file existed, and `enable --now` does not reload a service that is already running. It was still running on defaults (10-minute ban), on all three servers.
- **Fix:** Restarted the service on each server, then checked the live values (`bantime` printed 3600, and `ignoreip` listed the jump host on the admin server only).
- **Lesson:** Verify the running configuration with the tool's own query command, not just the file on disk.

### 9. A private key was committed to a public repo
- **Problem:** While setting up, a private key file was generated inside the repo folder and committed. It stayed in the history from September until I deleted it in November. It was passphrase-protected, and I confirmed it was not authorised on my GitHub account or as a deploy key, so it could not open anything.
- **Diagnosis:** Deleting a file does not remove it from earlier commits. I searched the full history for key files and private key markers, and compared fingerprints against the keys GitHub lists.
- **Fix:** Rewrote the history to remove the key from every commit, verified that no key material remained and that the final files were identical, then recreated the repository from the cleaned history. Pushes now come from a server using a repository-scoped deploy key.
- **Lesson:** Generate keys with a full path outside any repository (`ssh-keygen -f ~/.ssh/name`), and search the history for secrets before making a repo public.

### 10. My scripts were missing from the repo
- **Symptom:** `lab-scripts` showed as an empty, unclickable folder on GitHub, and a fresh clone had nothing in it.
- **Diagnosis:** `git ls-tree` showed mode `160000`, a pointer to another repository. The folder had been its own git repo, so the main repo stored a commit ID and none of the files, and there was no `.gitmodules` to explain it.
- **Fix:** Removed the pointer with `git rm --cached` and added the script back as ordinary tracked files.
- **Lesson:** After pushing, clone the repo fresh and look at what you get. A folder you can't open on GitHub usually means a nested repository.

### 11. Cron job logged to the wrong place
- **Problem:** The crontab line ended `2&>1` instead of `2>&1`, so output went to a file literally named `1` and the error log stayed empty. Script failures would have been invisible.
- **Fix:** Corrected the redirect, and checked it with `crontab -l` after saving.
- **Lesson:** Read back what you saved. A silent failure log is worse than none, because it looks like everything is fine.

### 12. A detection that could never match
- **Symptom:** The Stage 0 monitor counted `Failed password`, which hardened servers never log, because password login is off. It would have reported zero attempts forever.
- **Diagnosis:** With key-only SSH, failed probes appear as `Invalid user` and `Connection closed ... [preauth]` instead. I proved it by attempting a login as a nonexistent user from the jump host.
- **Fix:** Widened the pattern to include `Invalid user`, and confirmed the count rose from 0 to 1.
- **Lesson:** A detection rule has to be tested against the system it will actually watch. Changing a defence can silently break the detection built for the old setup.

### 13. The detection counted its own audit trail
- **Symptom:** The failed-attempt count on the admin server rose from 1 to 3 in minutes, on a host only the jump server can reach.
- **Diagnosis:** Listing the matching lines showed one real event (my own test login) and two `sudo` entries. `sudo` logs each command I run, and my checking commands contained the words the pattern searches for, so checking the count made it go up.
- **Fix:** Anchored the pattern to the `sshd` process (`sshd[pid]: Failed password|Invalid user`), so `sudo` lines no longer match. The count returned to 1.
- **Lesson:** A detection can match the investigator's own commands. Anchor patterns to the source that produces the event.

## Routine: my home IP changed

SSH is allowed only from my current public address, which changes. When SSH times out:

1. Look up my current public address.
2. In OCI, edit the SSH ingress rule on the subnet security list and set the source to that address with `/32`.
3. Confirm no rule allows SSH from `0.0.0.0/0`.
4. Retry. If it still fails, use the console connection, which does not depend on the firewall rule.

### 14. Sudo never asked for a password
- **Symptom:** Testing the new sudo-failure detector, `sudo` never prompted at all, even after `sudo -k`.
- **Diagnosis:** `grep -r NOPASSWD /etc/sudoers.d/` showed cloud-init grants the `ubuntu` account `NOPASSWD:ALL`. This is Oracle's own default, not a local misconfiguration.
- **Decision:** Left as is. SSH is already key-only with no password fallback, so the key is the real access boundary — a sudo password on top of it wouldn't add a second gate, since whoever has the key already controls the account.
- **Lesson:** Not every surprising finding is a bug to fix. Understanding *why* something behaves unexpectedly matters more than reflexively "correcting" it.

## Finding 15: a deferred cleanup from Block A quietly blocked an unrelated new feature in Block B

**What happened:** building the Week 5 forwarding agent, opening port 5000 on SIEM01 for the central receiver, the connection failed instantly from both WEB01 and SRV01 despite correct NSG and UFW rules on both sides.

**Root cause:** back in Block A, a stale iptables ruleset from an earlier (non-UFW, third-party-suggested) hardening attempt was found on WEB01 and SIEM01. It was removed from WEB01 at the time, but the SIEM01 copy was deliberately left in place with a note to deal with it "in Block C" — it carried its own small hardcoded allow-list (SSH, 443, and the Wazuh agent ports 1514/1515) and rejected everything else, sitting in the live `iptables` table *ahead of* UFW's own chain. It wasn't in the persisted `/etc/iptables/rules.v4` file, only in the running table, so it was invisible to a config review and would have silently disappeared on the next reboot — but until then, it rejected any new port that wasn't on its original 2026-era allow-list.

**Fix:** cleared the legacy rule block from the live `INPUT` chain, leaving UFW as the sole firewall manager on SIEM01 (same end state the other two servers already had).

**Lesson:** "defer until later" on a known firewall oddity is a real liability, not a neutral placeholder — it broke the very next unrelated feature that needed a new port, two blocks later than planned, and cost real debugging time to re-diagnose from scratch.

## Finding 16: a custom log source reaching the agent isn't the same as reaching the dashboard

**What happened:** after enrolling WEB01 and SRV01 as Wazuh agents and confirming via `ossec.log` that the agent was actively tailing `events.jsonl` with zero errors, searching for the events in the dashboard's Discover view (`wazuh-alerts-*`) returned nothing.

**Root cause, in two layers:** (1) Wazuh only writes to the alerts index when an event matches a detection rule — custom JSON fields with no matching rule are processed but silently produce no alert, which is expected behavior ahead of writing real rules in Week 9, not a bug. (2) Enabling raw event capture (`logall`/`logall_json` on the manager) only writes archive data to a local file on the manager's disk — it does not by itself ship anything to the indexer. That requires Filebeat's `wazuh` module to have its `archives.enabled` setting flipped from the installer's default of `false`, a setting the installer leaves off. A red herring along the way: the manager's own log showed `IndexerConnector` activity, which looked like a second possible ingestion path, but that component only handles vulnerability data, not archived events.

**Fix:** enabled `logall`/`logall_json` in `ossec.conf`, enabled `archives` in Filebeat's wazuh module config (`/etc/filebeat/filebeat.yml`), restarted both services, then created a matching `wazuh-archives-*` index pattern in the dashboard (an index existing in OpenSearch doesn't automatically mean a dashboard can query it — that's a separate object).

**Lesson:** "the agent is reading the file with no errors" proves only the first hop of a multi-hop pipeline. Proving data all the way to the dashboard needed checking every hop separately: agent → manager rule match → manager archive write → Filebeat forward → indexer → dashboard index pattern.

## Finding 17: testing for a false positive and getting a clean result is still a finding

**What happened:** after deploying Nginx + ModSecurity + OWASP CRS at paranoia level 1 on WEB01, confirmed SQLi detection and blocking work correctly (rule 942100 fired on a real injection payload, rule 949110 blocked it with a 403). Expected to also find a false positive on legitimate traffic — the plan anticipated "a detection that broke" as a natural part of this build. None occurred, even after deliberately raising to paranoia level 2 to probe for one.

**Why:** WEB01 currently serves a single static page with no forms, no cookies, no complex request bodies — exactly the kind of request shape that doesn't exercise the more aggressive pattern-matching that higher paranoia levels add. A false-positive problem needs real complexity to trigger against.

**Decision:** kept paranoia level 1. Raising it would add real performance cost and future false-positive risk without any present benefit, since there's nothing on this site complex enough to need the extra scrutiny yet. Revisit once the app has real dynamic input surfaces worth the added strictness.

**Lesson:** a debugging methodology section being honest doesn't require manufacturing a failure. Testing a real hypothesis (does PL2 introduce false positives here?) and getting a clean, well-reasoned null result is itself evidence of sound testing practice, not a gap in the write-up.

## Finding 18: a custom JSON field name silently collided with a built-in ruleset

**What happened:** writing Week 9's custom Wazuh rules, custom SSH-failure events were reaching Wazuh (confirmed via the agent's logcollector read-offset matching the file size exactly) but produced zero alerts for my own rules, even the most basic catch-all one.

**Root cause:** feeding a real captured event straight into `wazuh-logtest` showed it being classified under Wazuh's built-in rule 86600, "Suricata messages" — not mine. My JSON schema used the key `event_type`, which is also the hallmark field name in Suricata's native `eve.json` log format. Wazuh's generic JSON decoding apparently routes any JSON-decoded log containing that key into the Suricata rule tree before my own location-based rule ever got a chance to match, with no error anywhere to flag the collision.

**Fix:** renamed the field to `nyagaka_event_type` in both the Python log shipper and the rule file's field references. Confirmed the fix by re-running the same real test and watching the alert count for my own rule go from 0 to 15.

**Lesson:** a custom log schema can silently collide with a well-known security tool's field-naming convention, even when decoded with a fully generic JSON decoder and even when the log lives at a completely unrelated file path. Namespacing custom field names (a unique prefix) avoids this category of bug entirely.

## Finding 19: a correlation rule referenced the wrong kind of field

**What happened:** the brute-force rule (5+ SSH failures from one source within 10 seconds) never fired, even after confirming the individual per-event rule was matching correctly 15 times in a tight burst.

**Root cause:** the rule used `<same_source_ip />`, which only compares Wazuh's internal, static `srcip` field — a field that is populated only by a decoder explicitly assigning it (e.g. via an `<order>` tag). Wazuh's generic JSON decoder exposes JSON keys as dynamic fields under their own literal names (`src_ip`, with an underscore) and never auto-promotes a differently-named key into the static field, no matter what it's called.

**Fix:** replaced `<same_source_ip />` with `<same_field>src_ip</same_field>`, Wazuh's correlation tag for matching on any named dynamic field rather than only the reserved static one. Verified with a real 5-attempt SSH burst: the correlation rule fired cleanly with the source IP correctly substituted into the alert description.

**Lesson:** "static" and "dynamic" fields are a real distinction in Wazuh's rule engine, not just naming — a correlation tag built for one will silently never match data that only exists as the other, with no warning. When in doubt, test with real traffic through the full pipeline rather than trusting that a rule option "should" work on a given field.
