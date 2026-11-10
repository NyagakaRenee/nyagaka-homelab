# Before and After: Migrating the Lab to Oracle Cloud

> Nyagaka Enterprises is a simulated company. These are lab measurements, not production data.

## What I compared

I recorded each server's state with the same commands: memory, load, listening ports, running services, failed SSH attempts, firewall rules and Fail2ban status. The raw files are in [`lab-notes/`](../lab-notes/).

**About the "before":** the only measurement from the local lab is the single baseline I took on one VM on Sep 13 ([`baseline-metrics.txt`](../lab-notes/baseline-metrics.txt)): 1.6 GiB RAM with 438 MiB used, load average 0.02. I removed the local Linux VMs before taking a fresh local baseline, so I cannot show a like-for-like resource comparison or a laptop-load number. What I can show honestly is how the cloud servers looked when first built, and how a baseline led me to remove an unnecessary service.

## Attack surface: listening ports

Recorded on Nov 8 (before) and Nov 9 (after) with `ss -tlnp`. The local resolver on 127.0.0.x is excluded, since it does not accept outside connections.

| Server | Before | After |
| --- | --- | --- |
| SIEM01 | 22, 111 | 22 |
| WEB01 | 22, 80, 111 | 22, 80 |
| SRV01 | 22, 111 | 22 |

**What happened:** port 111 is `rpcbind`, the service that supports NFS-style remote procedure calls. It was listening on every interface of all three servers. I do not use it, and the firewalls already blocked it from the internet, so it was not exploitable. It was still an unnecessary service, so I disabled and masked it. The baseline made it visible: I would not have gone looking for it otherwise.

The number of running services did not change (23, 24 and 23), so open ports were the more telling measure here.

Files: [`cloud-baseline-*-before-rpcbind.txt`](../lab-notes/) and [`cloud-baseline-*-after.txt`](../lab-notes/).

## Security posture after migration

| | SIEM01 | WEB01 | SRV01 |
| --- | --- | --- | --- |
| Subnet | public | public | private (no public IP) |
| SSH allowed from | one address (cloud layer) | one address (cloud layer) | the jump host only (host firewall) |
| Host firewall (UFW) | deny incoming, allow 22 | deny incoming, allow 22, 80, 443 | deny incoming, allow 22 from jump host |
| Web ports | none | 80, 443 via a per-host network security group | none |
| Fail2ban | on | on | on, ignoring the jump host |
| Password policy | minimum 12, mixed classes, history of 5 | same | same |

- **Failed SSH attempts on the two public servers: 0** (counted with a pattern anchored to the `sshd` process). SSH is limited to my own address at the cloud layer, so scanners never reach the SSH daemon at all. This is the cloud layer doing work before the host layer is involved.
- **Failed SSH attempts on SRV01: 1**, my own test login as a nonexistent user from the jump host, which is how I confirmed the monitor script detects it (finding 12).
- **Fail2ban bans: 0** on all three, as expected when nothing is attacking.
- Login is key-only everywhere and root login is off.

## Resource use (idle, Nov 9)

| Server | RAM total | RAM used | Load average |
| --- | --- | --- | --- |
| SIEM01 | 11 GiB | 560 MiB | 0.12 |
| WEB01 | 5.8 GiB | 530 MiB | 0.11 |
| SRV01 | 954 MiB | 402 MiB | 0.06 |

These are idle figures with the SIEM not yet installed. SRV01 has about 550 MiB free, enough for its admin role and a monitoring agent but not much more, which is why it stays minimal.

## What this does not show

- No before and after failed-login comparison, because I had no Stage 0 baseline for it.
- No performance test. The servers are idle, so these are headroom figures, not capacity.
- The Wazuh SIEM is not installed yet. Detection results come in the next stage.

## Lessons recorded along the way

See [`mistakes-and-findings.md`](mistakes-and-findings.md). The ones that changed how I measure: a detection that could never match once password login was off (finding 12), and a detection that counted its own audit trail (finding 13).
