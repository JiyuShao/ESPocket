# 05 — Verify cancellation and result semantics

**What to build:** The brightness tracer bullet distinguishes canceled-before-submit, committed, failed and uncertain outcomes across UI and Assistant callers.

**Blocked by:** 04 — Enforce user-goal authorization.

**Status:** ready-for-agent

- [ ] PWR or caller cancellation prevents unsubmitted work.
- [ ] Submitted work is observed rather than assumed rolled back.
- [ ] Tests cover Event delivery and Owner failure.
