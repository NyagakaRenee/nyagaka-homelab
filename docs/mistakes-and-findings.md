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
