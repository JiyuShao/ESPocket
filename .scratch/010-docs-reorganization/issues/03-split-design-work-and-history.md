# 03 — Split design, work and history

**What to build:** Product contracts, architecture views, milestone acceptance, historical records, upstream facts, guides and local work each have one clear authority.

**Blocked by:** 02 — Extract durable decisions.

**Status:** resolved

- [x] M1–M5 reports move to records and gain concise acceptance summaries.
- [x] M1–M8 specs and tickets are explicit about retrospective or current status.
- [x] AI Native semantics are integrated and its implementation plan moves to `.scratch`.

## Old path mapping

| Old path | New authority |
|---|---|
| `docs/design/policies/package-trust.md` | `docs/design/product/runtime-package-trust.md` + ADR-0004 + M5 Spec |
| `docs/design/policies/launcher-sync.md` | `docs/design/product/application-discovery.md` + ADR-0005 + M5 Spec |
| `docs/design/architecture/07-ai-native-os.md` | `CONTEXT.md` + product docs + architecture views + ADR-0006..0009 |
| `docs/design/architecture/08-ai-native-integration.md` | `.scratch/009-ai-native-foundation/` + upstream local baseline |
| `docs/milestones/mN-acceptance.md` | `docs/milestones/mN/acceptance.md` and `records/` |
| hardware acceptance files | `docs/guides/` |
