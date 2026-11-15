# Week 12 — Nginx Hardening on WEB01

## Overview

With the WAF live (Block C) and AD identity work done (Block D, Weeks 10-11),
Week 12 closes a smaller but real gap: WEB01's Nginx was still leaking
information that makes an attacker's job easier, even with ModSecurity/CRS
sitting in front of it. A WAF blocks exploitation attempts; it doesn't stop
the server from handing out its own exact version and software stack to
anyone who asks first.

## What was leaking (real "before" evidence)
curl.exe -sk -I https://140.238.99.235/
Server: nginx/1.24.0 (Ubuntu)

and the default 404 error page footer repeated the same string a second
time in the response body itself. The public site was also still serving
the literal, unmodified Debian default "Welcome to nginx!" page
(`/var/www/html/index.nginx-debian.html`, 615 bytes) — confirmed by `ls -la`
matching the exact `Content-Length: 615` seen in the curl response.

## Changes made

1. **`server_tokens off;`** — enabled globally in `/etc/nginx/nginx.conf`
   (it was present but commented out). Because it's set at the `http {}`
   scope, it applies to every server block at once — both the public-facing
   `waf-frontend` block and the loopback-only backend block in
   `sites-enabled/default` — without needing a per-site edit.
2. **`autoindex`** — confirmed there was no explicit `autoindex` directive
   anywhere in the config at all, meaning Nginx was already running on its
   compiled-in default of `off`. Didn't just trust the absence of a line:
   created a real empty directory with no index file and requested it
   directly, and got a genuine `403 Forbidden`, not a file listing.
3. **Default page replaced** — swapped the stock Debian welcome page for a
   minimal, neutral page with no version/stack hints (112 bytes vs. the
   original 615).

## Verification (real before/after, not assumed)

| | Before | After |
|---|---|---|
| `Server:` header | `nginx/1.24.0 (Ubuntu)` | `nginx` |
| 404 page footer | `nginx/1.24.0 (Ubuntu)` | `nginx` |
| `/testdir/` (no index file) | not tested blind | `403 Forbidden` (real test) |
| Default page | stock 615-byte Debian page | custom 112-byte page, confirmed live through the full proxy path |

All four confirmed with real curl requests against the public HTTPS
endpoint after `nginx -t` + `systemctl reload nginx`, not just a local
config read.

## Re-testing the WAF after the change

A config edit anywhere in the Nginx stack is worth re-testing the WAF
against, in case something in the pipeline got disturbed.

- SQLi payload (`?id=1' OR '1'='1`, URL-encoded) → real `403 Forbidden`
- Legitimate request (`/`) → real `200 OK`
- Confirmed in the actual ModSecurity audit log
  (`/var/log/modsec_audit.log`), not just from the status code: rule
  `942100` ("SQL Injection Attack Detected via libinjection") matched
  `ARGS:id: 1' OR 1'=1`, and rule `949110` ("Inbound Anomaly Score
  Exceeded", total score 8) made the actual blocking decision.

No regression — hardening and WAF blocking both verified working together,
from real traffic and real logs.

## Mistake caught along the way

See `docs/mistakes-and-findings.md` (Finding 22) — the first SQLi re-test
command returned `000` and looked at first like it might mean "something
broke," but was actually a broken test command (unencoded space and quote
characters in the URL that curl's own client-side parser rejected before
the request ever left the machine). Flagged rather than accepted, fixed by
URL-encoding the payload properly, and then re-tested for a real result.

## Next (Week 13)

End-to-end detection validation: a real brute-force burst against SRV01 and
a benign SQLi test string against WEB01, confirming the full alert path
(agent/log shipper → Wazuh rule → dashboard), with real numbers (time to
detect, alerts fired, false positives) feeding the case study write-up.
