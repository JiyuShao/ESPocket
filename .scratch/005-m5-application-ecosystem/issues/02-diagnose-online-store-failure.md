# 02 — Diagnose the online Store failure

**What to build:** A source-backed diagnosis that distinguishes TLS allocation containment from the remaining cancellation race.

**Blocked by:** 01 — Integrate the official Store.

**Status:** retrospective-resolved

- [x] 2/2 and 1/1 policies are recorded separately.
- [x] The final crash is symbolized through TLS handshake and HTTP worker code.
- [x] An upstream-ready draft and sanitized evidence exist.

## Resolution

The 1/1 policy reduced allocation pressure but device-failed on cancellation; no further unsafe reproduction is required.
