# Week 11 — Organizational Units, a Test User, and Domain Account Policy

## Overview

With `nyagaka-wks01` promoted and verified as the forest's first Domain
Controller (Week 10), Week 11 builds the first real pieces of directory
structure on top of it: Organizational Units to hold accounts, a test user
placed inside that structure, and a domain-wide account policy (password
complexity/length + lockout after repeated bad logons) — proven with a real
deliberate lockout, not just confirmed configuration values.

## What was built

- **Organizational Units:** `Nyagaka-Production` and `Nyagaka-Admin`, created
  with `New-ADOrganizationalUnit`, mirroring a real small-business pattern of
  separating day-to-day accounts from administrative ones rather than leaving
  everything in the default `Users` container.
- **Test user:** `testuser`, created with `New-ADUser` and placed inside
  `Nyagaka-Production`, verified afterward with
  `Get-ADUser -Identity testuser -Properties *` rather than assumed from a
  lack of visible error.
- **Domain account policy:** password complexity, minimum length, and an
  account lockout threshold of 5 failed attempts, configured with
  `Set-ADDefaultDomainPasswordPolicy` and confirmed with
  `Get-ADDefaultDomainPasswordPolicy`.

## The key scoping lesson: domain root, not an OU

The one thing that would have been easy to get wrong here: password
complexity and account lockout policy, set through `Set-ADDefaultDomainPasswordPolicy`
or an equivalent GPO, **only take effect when applied at the domain root**,
not when linked to an OU. A GPO linked to `Nyagaka-Production` or
`Nyagaka-Admin` containing the same settings would silently do nothing for
password/lockout rules specifically — AD applies these particular policies
once, domain-wide, from the Default Domain Policy (or an equivalent linked
at the root), regardless of which OU an account sits in. Other GPO settings
(software deployment, script policies, most security settings) *do* respect
OU-level linking; account password/lockout policy is the specific exception.
Knowing this up front meant the OUs were built for organizing accounts, and
the policy itself was deliberately configured at the correct scope from the
start.

## Proving it with a real test, not just configuration values

Confirming `Get-ADDefaultDomainPasswordPolicy` shows the right numbers is not
the same as confirming the policy actually enforces anything. To prove
enforcement for real:

1. Built a `PSCredential` for `testuser` with a deliberately wrong password.
2. Attempted to authenticate with it 5 times in a row (matching the
   configured lockout threshold).
3. Checked the account's real state:

```powershell
Get-ADUser -Identity testuser -Properties LockedOut,BadLogonCount
```

Result: `BadLogonCount: 5`, `LockedOut: True` — the account was genuinely
locked out by the policy, not just configured to look like it would be.

4. Unlocked it afterward and confirmed the unlock:

```powershell
Unlock-ADAccount -Identity testuser
Get-ADUser -Identity testuser -Properties LockedOut
```

Result: `LockedOut: False`.

## Note: built-in Administrator is exempt

The built-in `Administrator` account is exempt from account lockout policy
by default (a deliberate Windows safeguard against locking out the one
account that can always recover the domain), so any lockout testing has to
use a regular user account like `testuser` — testing against `Administrator`
itself would never show a lockout regardless of whether the policy works.

## Mistakes made along the way

See `docs/mistakes-and-findings.md` (Finding 21) for the `New-ADUser`
parameter typo that failed silently-ish twice before a corrected third
attempt succeeded, and why that meant verifying the user's existence
directly rather than trusting "no error" as proof of success.

## Next

- Stretch goal still open: sync this forest to a free Microsoft Entra ID
  tenant via Microsoft Entra Connect (hybrid identity, alongside concurrent
  SC-900 study) — tracked separately in the roadmap, not required for Block D
  to be considered functionally complete.
- Resolve the duplicate `03-` prefix between `docs/03-wazuh-siem-install.md`
  and `docs/03-siem-waf-custom-rules-and-compliance.md` (cosmetic, not
  blocking).
