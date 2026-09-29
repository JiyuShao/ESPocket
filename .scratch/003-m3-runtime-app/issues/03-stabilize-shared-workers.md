# 03 — Stabilize the shared worker baseline

**What to build:** A firmware worker configuration that survives clean boot and combined App use while retaining measured reserve.

**Blocked by:** 02 — Prove Runtime lifecycle and Native coexistence.

**Status:** retrospective-resolved

- [x] System worker overflow and secondary-buffer failures are preserved as failed canaries.
- [x] Stable System and Service worker values are derived from observed use.
- [x] The project-owner exception for independent file-install evidence is recorded without inventing a log.

## Resolution

M3 passed on 2026-09-28 with the explicit evidence exception in acceptance.
