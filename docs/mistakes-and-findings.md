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
