# 06 — Register one Native App capability

**What to build:** A real Native App capability registers only while its Running Instance exists and uses the proven authorization/result contract.

**Blocked by:** 05 — Verify cancellation and result semantics.

**Status:** ready-for-agent

- [ ] Stop, crash and restart invalidate old handles and subscriptions.
- [ ] Relaunch creates a new capability identity.
- [ ] Persistent behavior is moved to a Service rather than extending App lifetime.
