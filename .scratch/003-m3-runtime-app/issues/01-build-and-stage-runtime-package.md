# 01 — Build and stage Hello Runtime

**What to build:** A minimal official JavaScript Runtime package built with the pinned Toolkit and staged through the System Core helper into LittleFS.

**Blocked by:** M2 `PASS`.

**Status:** retrospective-resolved

- [x] Runtime JS and QuickJS versions are locked and linked.
- [x] Toolkit doctor/build and package integrity checks pass.
- [x] The staged tree and LittleFS image contain the expected package.

## Resolution

Accepted by M3 build, Toolkit and staging evidence; the debug package is intentionally unsigned.
