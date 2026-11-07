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

## Routine: my home IP changed

SSH is allowed only from my current public address, which changes. When SSH times out:

1. Look up my current public address.
2. In OCI, edit the SSH ingress rule on the subnet security list and set the source to that address with `/32`.
3. Confirm no rule allows SSH from `0.0.0.0/0`.
4. Retry. If it still fails, use the console connection, which does not depend on the firewall rule.
