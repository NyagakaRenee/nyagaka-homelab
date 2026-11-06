# Nyagaka Enterprises: Security Home Lab

**Author:** Renee Nyagaka · Nairobi, Kenya
**Focus:** Linux hardening, network segmentation, detection engineering, cloud migration

> **Note:** Nyagaka Enterprises is a **simulated company** built for learning. Everything here was built and tested by me in a lab. It is not a production deployment.

## What this project is

A small multi-node network that I build, harden, break, and fix in stages, with every config tracked in Git. The goal is to practise the work of a security engineer: secure the hosts, watch them, and measure the results.

| Stage | What I built | Status |
| --- | --- | --- |
| 0 | Three-node local lab on VirtualBox (2 Linux, 1 Windows), hardened and documented | Complete |
| 1, Block A | Migration of the Linux servers to Oracle Cloud (OCI) | In progress |
| 1, Block B | Python log-detection tooling | Planned |
| 1, Block C | Wazuh SIEM and WAF (Nginx + ModSecurity + OWASP CRS) | Planned |

## Architecture

```
Stage 0 (local, VirtualBox)              Stage 1 (hybrid)
  NYAGAKA-SRV01  192.168.50.10             OCI: NYAGAKA-SIEM01 (Wazuh, planned)
  NYAGAKA-WEB01  192.168.50.20             OCI: NYAGAKA-WEB01  (Nginx, public subnet)
  NYAGAKA-WKS01  192.168.50.30             OCI: NYAGAKA-SRV01  (admin, private subnet)
  internal network: nyagaka-internal-net   Local: NYAGAKA-WKS01 (Windows, VirtualBox)
```

Full detail: [`docs/nyagaka-network/network-topology.md`](docs/nyagaka-network/network-topology.md)

## What's in the repo

| Path | Contents |
| --- | --- |
| `system-configs/` | Hardened SSH drop-in, Fail2ban jail, UFW rules, PAM password policy, Netplan files, cron jobs |
| `docs/` | Network topology and per-stage write-ups |
| `lab-notes/` | Baseline measurements taken before changes |
| `lab-scripts/` | Detection and monitoring scripts |
| `docs/mistakes-and-findings.md` | What went wrong, how I diagnosed it, how I fixed it |

## Stage 0 highlights

- **SSH hardening:** password login off, root login off, Ed25519 keys with passphrases.
- **Automated defence:** Fail2ban bans a host after repeated failed logins (10-minute window, 1-hour ban).
- **Network segmentation:** dual-NIC design, NAT for updates and a private internal switch for lab traffic, with static addressing.
- **Least-privilege firewalls:** default-deny with role-based rules per host (UFW on Linux, Windows Firewall on WKS01).
- **Safety rails:** shell aliases and a confirmation wrapper to prevent accidental overwrites and deletes.

## Stage 1: cloud migration (in progress)

Moving the Linux servers off the laptop to Oracle Cloud's Always Free tier, so the lab can run a SIEM without overloading one machine.

- One VCN built with wizard defaults; public subnet for the web and SIEM hosts, private subnet for the admin host.
- SSH locked to a single source address, with no password login and a recovery path through the OCI console connection.
- The admin host has no public IP and is reached through a jump host.

Write-up: [`docs/02-oci-cloud-migration.md`](docs/02-oci-cloud-migration.md)

## Mistakes and findings

I keep an honest log of what went wrong. See [`docs/mistakes-and-findings.md`](docs/mistakes-and-findings.md).

## Security note

This repo contains configuration files only. No private keys, passwords, or account identifiers are stored here, and server addresses are omitted on purpose.

## Contact

[LinkedIn](https://www.linkedin.com/) · GitHub: [NyagakaRenee](https://github.com/NyagakaRenee)
