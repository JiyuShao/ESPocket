# 07 — Register one Runtime App capability

**What to build:** A trusted Runtime App exercises the same semantics and Running Instance lifetime through Runtime/HostBridge admission.

**Blocked by:** 06 — Register Native capability; M5 package trust and Runtime isolation gates.

**Status:** needs-info

- [ ] Runtime manifest and HostBridge permission checks remain effective.
- [ ] Stop failure cannot leak capability or keyboard ownership.
- [ ] Remote package identity is trusted before capability discovery.
