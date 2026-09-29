# 04 — Project dynamic Launcher entries from Core

**What to build:** Trusted dynamic Apps appear and disappear from Launcher according to complete Core snapshots while fixed entries remain stable.

**Blocked by:** 02 — Diagnose/adopt an online stability fix; 03 — Enforce the Core-owned package trust gate.

**Status:** needs-info

- [ ] Launcher uses Core committed state as its only dynamic source.
- [ ] Lost or merged notifications recover on full reconciliation.
- [ ] Failed refresh preserves the last complete projection.
- [ ] Launch resolves current runtime identity from manifest identity.

## Implementation decisions recovered from the original policy

- Fixed product entries stay in the Shell document and cannot be removed, reordered or shadowed by dynamic reconciliation.
- Dynamic eligibility requires a visible Runtime App, exclusion from the fixed manifest set, successful trust admission and presence in Core's committed list.
- Install/uninstall hooks only advance a dirty generation. A Shell-owned timer on the App task reads a complete snapshot after the hook returns; Shell start performs an initial reconciliation for reboot discovery.
- The dynamic region uses the existing JSON UI template APIs. Instance identity is a deterministic collision-checked digest of manifest identity, never `std::hash`, and the in-memory mapping is rebuilt from Core.
- Entries sort by Core-resolved localized display name and manifest identity. Missing icons fall back to text; icon preload follows view lifetime.
- One shared dynamic Action records a manifest identity from the event path. The App-task dispatcher lists Apps again, rechecks eligibility, resolves the current `AppId`, starts once and clears the intent.
- Reconciliation builds a replacement subtree and swaps only after every view is ready. Failure destroys the temporary subtree, preserves the last complete view and retries with log rate limiting.

## Required matrix

- [ ] Filter hidden, Native, fixed, incompatible and untrusted Apps.
- [ ] Cover deterministic sorting, name fallback, instance collision and icon fallback.
- [ ] Merge repeated notifications without duplicate entries.
- [ ] Update metadata without duplicating identity and dispatch to the new `AppId`.
- [ ] Reject click/uninstall races and cancel a removed pending target.
- [ ] Rebuild after Shell restart without persistent Launcher state.
- [ ] Keep fixed entries usable through every reconciliation failure.
