# 01 — Fix brightness output identity

**What to build:** Shell brightness reads and writes the real Display output selected by System instead of fixed `OutputId = 0`.

**Blocked by:** None for implementation; M6 `PASS` gates M7 acceptance.

**Status:** ready-for-agent

- [ ] System and Shell share one selected-output fact.
- [ ] Brightness read/write uses a valid output identity.
- [ ] Existing Settings brightness behavior remains intact.
