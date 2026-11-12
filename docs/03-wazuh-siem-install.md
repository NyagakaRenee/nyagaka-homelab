# Wazuh SIEM Install (SIEM01)

## What was installed
Wazuh 4.14 all-in-one (manager, indexer, dashboard together) on SIEM01 via
the official installation assistant (`wazuh-install.sh -a`). Ubuntu 24.04,
ARM64/aarch64 — confirmed officially supported before installing.

## Sizing, honestly
Wazuh's documented minimum for even the smallest deployment (1-25 agents)
is 4 vCPU / 8 GiB RAM. SIEM01 runs on 2 OCPU / 12 GiB — the OCI console
would not allow resizing it higher under the current Always Free
allocation, despite the stated 4 OCPU/24 GB account-wide budget suggesting
more should be available. RAM is well above the minimum; CPU is half of
what's recommended. Documented as a known-undersized lab deployment: this
is a 1-3 agent home lab, not a 25-agent SOC, and all three services came
up healthy with no crash loops or OOM kills on first install.

## Access
Dashboard reachable at `https://<SIEM01 public IP>:443`, locked at both
the cloud (`siem01-nsg`) and host (UFW) layers to one IP only — the same
two-layer, IP-restricted pattern used for SSH since Block A, not opened to
"Anywhere" since this is an admin console with real credentials behind it.
Default installer-generated admin password rotated after first login.

## Next
Week 7: enroll WEB01, SRV01, and (once rebuilt) WKS01 as agents, and
retire the standalone Flask receiver built in Week 5 once the manager is
taking real agent traffic.
