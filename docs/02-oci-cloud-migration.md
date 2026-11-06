# Stage 1, Block A: Migrating the Lab to Oracle Cloud

> Nyagaka Enterprises is a simulated company. This is a lab migration, not a production deployment.

## Why

Three virtual machines plus a SIEM is too much for one laptop. Oracle Cloud's Always Free tier gives me always-on servers at no cost, and moving the lab there shows how the same hardening holds up on internet-facing hosts.

## Before and after

| | Before (Stage 0) | After (Stage 1) |
| --- | --- | --- |
| Where it runs | All VMs on one laptop | Linux servers in OCI, Windows host stays local |
| Exposure | Private internal network only | Internet-facing, so SSH is locked to one source address |
| Admin access | Direct from the host | Jump host to a private-subnet server |

## What I built

1. **Network:** one VCN (`10.0.0.0/16`), a public subnet (`10.0.0.0/24`) and a private subnet, using the console wizard defaults. The ranges avoid my home LAN and the Stage 0 lab network.
2. **SIEM host:** Arm A1, 2 OCPU / 12 GB, Ubuntu 24.04 (public subnet). Reserved for the Wazuh manager.
3. **Web host:** Arm A1, 1 OCPU / 6 GB, Ubuntu 24.04 (public subnet).
4. **Admin host:** AMD micro, 1 GB, Ubuntu 24.04 (**private** subnet, no public IP).
5. **SSH:** key-only authentication with a dedicated Ed25519 key. SSH reaches the servers from one source address only. The admin host is reached through the web host with `ProxyJump`, and the private key never leaves my laptop.

## Design decisions

- **Free-tier fit:** the Always Free allowance covers 4 OCPU and 24 GB of Arm compute plus two AMD micro instances, so the three servers fit with room to spare.
- **Public vs private:** the admin host is in the private subnet to shrink the attack surface. The trade-off is that the web host doubles as the jump host. In production I would use a separate, hardened bastion or the OCI Bastion service.
- **Per-host firewall rules:** web ports go on a network security group attached to the web server only, not on the subnet-wide security list.

## Hardening applied on each server

- SSH: password authentication off, root login off.
- UFW: default deny, SSH allowed first.
- Fail2ban for the SSH service.
- Logging daemon installed (the minimal image does not ship one), so authentication logs exist for detection work.

## What's next

Python log parsing, then the Wazuh SIEM and a WAF in front of the web server. See the project [README](../README.md).

## Problems hit

See [`mistakes-and-findings.md`](mistakes-and-findings.md).
