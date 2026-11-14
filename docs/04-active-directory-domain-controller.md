# Week 10 — Promoting WKS01 to a Domain Controller

## Overview

Block D moves from the Linux/cloud SIEM-and-WAF stack (Blocks B/C) into Windows
Server and Active Directory. WKS01 — originally a plain local workstation in
the Baraka v1 lab network — is promoted to the forest's first Domain
Controller, staying local in VirtualBox rather than moving to the cloud, per
the project's original architecture decision.

## What was built

- **Host:** `nyagaka-wks01` — a freshly installed Windows Server 2025
  Standard Evaluation, **Server Core** (no GUI, matching real enterprise DC
  hardening practice of minimizing attack surface on a domain controller).
  Rebuilt from scratch rather than password-recovered, because the previous
  WKS01's local admin password was lost.
- **Networking:** static IP `10.0.2.50/24` on the VirtualBox NAT adapter
  (DHCP explicitly disabled — a domain controller needs a stable, known
  address since DNS and AD both depend on it), gateway `10.0.2.2`. DNS was
  temporarily pointed at a public resolver (`8.8.8.8`) before promotion for
  internet access, then switched to self-referential (`127.0.0.1`, with
  `8.8.8.8` kept as a secondary forwarder) after promotion, since the DC is
  now its own DNS server for the domain.
- **Forest/domain:** `nyagaka.internal` (NetBIOS `NYAGAKA`) — a brand-new
  forest, not a join to an existing domain. Named to match the rest of the
  project's `nyagaka-` convention rather than the original placeholder idea
  of `baraka.enterprise`, and `.internal` specifically because it's a real,
  IANA-reserved special-use domain suffix (RFC 9476) meant for exactly this
  kind of private/lab use, rather than a public-style name nobody owns.

## A real debugging story: a misleading, parameter-shifting error

Promotion didn't go smoothly on the first pass. Repeated calls to
`Install-ADDSForest` and `Test-ADDSForestInstallation` failed with:

```
Verification of prerequisites for Domain Controller promotion failed.
The specified argument '<X>' was not recognized.
Context  : Test.VerifyDcPromoCore.DCPromo.General.77
Status   : Error
```

The confusing part: `<X>` kept changing across retries — `DomainNetbiosName`,
then `InstallDNS`, then `DomainNetbiosName` again — including on an attempt
where that parameter wasn't even supplied. A genuine unrelated typo
(`DomaininNetbiosName`) showed up along the way too and briefly looked like
the explanation, but fixing it reproduced the identical error.

**The actual cause:** an earlier attempt had already succeeded. Once a
server is a domain controller, re-running forest-*creation* cmdlets against
it runs into the module's demote-context validation logic instead of
fresh-forest validation — which surfaces as this same generic,
parameter-shifting error rather than a clear "this is already a domain
controller" message. See `docs/mistakes-and-findings.md` (finding 20) for
the full writeup.

This was **confirmed directly**, not assumed from a description of log
output — the following was run for real and matched:

```powershell
Get-ADDomain
Get-ADDomainController
Get-Service NTDS,DNS,Netlogon,Kdc
ipconfig /all
```

Results:
- `Get-ADDomain`: `DNSRoot: nyagaka.internal`, `DomainMode: Windows2025Domain`,
  `NetBIOSName: NYAGAKA`, `Forest: nyagaka.internal`
- `Get-ADDomainController`: `HostName: nyagaka-wks01.nyagaka.internal`,
  `IPv4Address: 10.0.2.50`, `OperatingSystem: Windows Server 2025 Standard
  Evaluation`, holding Schema Master / Domain Naming Master / PDC Emulator /
  RID Master — the FSMO roles expected on the first DC of a new forest
- `Get-Service`: `DNS`, `Kdc` (Kerberos Key Distribution Center), `Netlogon`,
  `NTDS` (Active Directory Domain Services) all `Running`
- `ipconfig /all`: primary DNS suffix `nyagaka.internal`, DNS servers
  `127.0.0.1` (self) and `8.8.8.8` (forwarder)

## Next (Week 11)

Build Organizational Units (e.g. `Baraka-Production`, `Baraka-Admin`), a test
domain user, and a baseline Group Policy Object (password complexity/length,
account lockout after 5 attempts) — plus a stretch goal added to the
tracker: sync this forest to a free Microsoft Entra ID tenant via Microsoft
Entra Connect, a real hybrid-identity pattern that combines this home lab
with concurrent SC-900 study rather than treating Entra ID as a substitute
for self-managed AD DS (it architecturally can't be — no Kerberos/NTLM/GPO
support — see the tracker entry for the full reasoning).
