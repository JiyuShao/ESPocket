# 03 — Run the Native lifecycle and heap gate

**What to build:** A default-off stress path and verifier that prove 50 complete Native lifecycle cycles without sustained heap loss.

**Blocked by:** 02 — Close the Home and cleanup loop.

**Status:** retrospective-resolved

- [x] 50/50 cycles reach Running and Stopped.
- [x] GUI negative probe confirms unload.
- [x] Four heap loss metrics remain within 1,024 bytes.

## Resolution

Accepted raw record is linked from M2 acceptance.
