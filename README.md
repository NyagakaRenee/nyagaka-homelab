# Nyagaka Enterprises: Security Home Lab

**Author:** Renee Nyagaka · Nairobi, Kenya
**Focus:** Linux hardening, network segmentation, SIEM/detection engineering, WAF, Active Directory, cloud migration

> **Note:** Nyagaka Enterprises is a **simulated company** built for learning. Everything here was built and tested by me in a lab. It is not a production deployment.

## What this project is

A multi-node network that I build, harden, break, and fix in stages, with every config tracked in Git. The goal is to practise the work of a security engineer: secure the hosts, detect real attacks against them, and measure the results — honestly, including what broke and how it got fixed.

| Stage | What I built | Status |
| --- | --- | --- |
| 0 | Three-node local lab on VirtualBox (2 Linux, 1 Windows), hardened and documented | Complete |
| 1, Block A | Migration of the Linux servers to Oracle Cloud (OCI) | Complete |
| 1, Block B | Python log-detection tooling + central event receiver | Complete |
| 1, Block C | Wazuh SIEM, agent enrollment, Nginx + ModSecurity WAF, custom detection rules, FIM, compliance matrix | Complete |
| 1, Block D | Active Directory Domain Services (local Windows Server 2025 DC) | In progress — Week 10 done |

## Architecture (current)

```
Cloud (OCI, Always Free)                          Local (VirtualBox)
  NYAGAKA-SIEM01   Wazuh manager/indexer/dashboard   NYAGAKA-WKS01  Domain Controller
  NYAGAKA-WEB01    Nginx + ModSecurity WAF            (Windows Server 2025 Server Core,
  NYAGAKA-SRV01    admin/bastion (private subnet)      forest: nyagaka.internal)
```

SRV01 and WEB01 run as Wazuh agents reporting to SIEM01. WEB01 fronts a loopback-only
backend with a ModSecurity-inspecting reverse proxy on 443. WKS01 stays local by design
(not a cost-saving shortcut — a deliberate architecture decision, see `docs/`) and is now
the first domain controller of its own forest, separate from the cloud fleet.

Full network detail: [`docs/nyagaka-network/network-topology.md`](docs/nyagaka-network/network-topology.md)

## What's in the repo

| Path | Contents |
| --- | --- |
| `docs/02-oci-cloud-migration.md` | Block A: migrating the Linux servers to OCI |
| `docs/03-wazuh-siem-install.md` | Block C: Wazuh manager install and sizing |
| `docs/03-siem-waf-custom-rules-and-compliance.md` | Block C (Week 9): custom detection rules, FIM, Kenya DPA 2019 compliance matrix |
| `docs/04-active-directory-domain-controller.md` | Block D (Week 10): promoting WKS01 to a Domain Controller |
| `docs/local_rules.xml` | The actual deployed Wazuh custom ruleset (copied from the manager) |
| `docs/mistakes-and-findings.md` | A running, honest log of what went wrong, how I diagnosed it, and how I fixed it — 20 findings and counting |
| `docs/before-after.md` | Baseline security posture before/after the cloud migration |
| `docs/nyagaka-network/` | Network topology |
| `system-configs/` | Hardened SSH drop-in, Fail2ban jail, UFW/firewall rules, PAM password policy, Netplan files, cron/logrotate configs |
| `lab-notes/` | Raw baseline measurements taken before and after changes |
| `lab-scripts/` | The original Bash detection script (Stage 0) |
| `python-log-shipper/` | The Python detection agent that replaced it — parses auth.log for SSH/account/sudo events, ships JSON to the SIEM |
| `receiver/` | A small Flask stand-in SIEM receiver used before Wazuh was deployed |

## Highlights

**Stage 0 — local lab fundamentals**
- SSH hardening: password login off, root login off, Ed25519 keys with passphrases
- Fail2ban bans a host after repeated failed logins
- Network segmentation: dual-NIC design, static addressing, role-based least-privilege firewalls

**Block A — cloud migration**
- Three servers moved to Oracle Cloud's Always Free tier, re-hardened, with a documented before/after baseline
- SSH locked to a single source address with a console-connection recovery path; no rule ever left open to `0.0.0.0/0`

**Block B — detection in Python**
- Rewrote the Bash SSH-failure monitor as a proper Python log parser (`log_shipper.py`): normalizes events to JSON, tracks SSH failures/account changes/sudo escalation, and pushes to a central receiver

**Block C — SIEM, WAF, and custom detection**
- Wazuh 4.14 deployed and hardened; both Linux servers enrolled as agents
- Nginx + ModSecurity v3 (built from source, ARM64) + OWASP Core Rule Set, reverse-proxied in front of a loopback-only backend
- Custom Wazuh rules for SSH brute-force correlation, account changes, and WAF-block alerting — all verified against real triggered traffic, not assumed
- Real-time File Integrity Monitoring on `sshd_config` and `jail.local`
- A compliance matrix mapping every control to specific, independently-verified sections of the Kenya Data Protection Act, 2019

**Block D — Active Directory (in progress)**
- WKS01 rebuilt fresh and promoted to the first Domain Controller of a new forest (`nyagaka.internal`), verified with real `Get-ADDomain`/`Get-ADDomainController`/service-state output
- Next: Organizational Units, a baseline Group Policy, and (stretch) syncing to a free Microsoft Entra ID tenant via Entra Connect

## Mistakes and findings

I keep an honest log of what went wrong — real bugs, real debugging, real fixes, not a polished retelling. See [`docs/mistakes-and-findings.md`](docs/mistakes-and-findings.md).

## Security note

This repo contains configuration files and detection rules only. No private keys, passwords, or real account identifiers are stored here, and production server addresses are omitted on purpose.

## Contact

[LinkedIn](https://www.linkedin.com/in/renee-nyagaka/) · GitHub: [NyagakaRenee](https://github.com/NyagakaRenee)
