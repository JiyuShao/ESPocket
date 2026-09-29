# Local work index

`.scratch/` 是版本化的本地 Markdown tracker。每个 effort 在首次登记时获得一个三位全局 Sequence；目录格式为 `<Sequence>-<slug>`。Sequence 记录主题提出顺序，一旦分配就不重排、不复用。

Sequence 与执行顺序是两件事：前者用于追溯，后者由 ticket 编号、`Blocked by` 和 `Status` 决定。

## Effort registry

| Sequence | Effort | Provenance |
|---:|---|---|
| 001 | [M1 System](001-m1-system/spec.md) | backfilled from milestone proposal order |
| 002 | [M2 Native App](002-m2-native-app/spec.md) | backfilled from milestone proposal order |
| 003 | [M3 Runtime App](003-m3-runtime-app/spec.md) | backfilled from milestone proposal order |
| 004 | [M4 Device Capabilities](004-m4-device-capabilities/spec.md) | backfilled from milestone proposal order |
| 005 | [M5 Application Ecosystem](005-m5-application-ecosystem/spec.md) | backfilled from milestone proposal order |
| 006 | [M6 Home and Display](006-m6-home-display/spec.md) | backfilled from milestone proposal order |
| 007 | [M7 Navigation](007-m7-navigation/spec.md) | backfilled from milestone proposal order |
| 008 | [M8 App Contract](008-m8-app-contract/spec.md) | backfilled from milestone proposal order |
| 009 | [AI Native foundation](009-ai-native-foundation/spec.md) | existing AI Native design effort |
| 010 | [Documentation reorganization](010-docs-reorganization/spec.md) | current migration effort |

Milestone status itself remains authoritative in [`docs/milestones/README.md`](../docs/milestones/README.md).

The M1–M8 Sequence was reconstructed from the known milestone proposal order; it does not invent exact creation timestamps or historical owners. AI Native is not renamed M9, because Sequence is tracker provenance rather than a product Milestone number.

## Allocation rules

- Assign the next unused Sequence when a new effort is first written down.
- Keep the Sequence when the title or slug changes.
- Keep resolved and `wontfix` efforts in place; their number remains part of history.
- Use `Blocked by` for dependency changes instead of renumbering directories.

## Working the frontier

Within an effort, choose the lowest-numbered ticket whose `Blocked by` entries are resolved and whose `Status` is `ready-for-agent` or `ready-for-human`. Cross-effort dependencies written in `Blocked by` take precedence over Sequence.
