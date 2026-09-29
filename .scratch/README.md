# Local work index

`.scratch/` 是版本化的本地 Markdown tracker。每个 Effort 首次登记时获得一个三位全局 Sequence；目录格式为 `<Sequence>-<slug>`。Sequence 记录主题提出顺序，一旦分配就不重排、不复用。

Sequence 负责追溯提出顺序；执行顺序由 ticket 编号、`Blocked by` 和 `Status` 决定。

## Effort registry

| Sequence | Effort | 来源 |
|---:|---|---|
| 001 | [M1 System](001-m1-system/spec.md) | 按 Milestone 提出顺序回填 |
| 002 | [M2 Native App](002-m2-native-app/spec.md) | 按 Milestone 提出顺序回填 |
| 003 | [M3 Runtime App](003-m3-runtime-app/spec.md) | 按 Milestone 提出顺序回填 |
| 004 | [M4 Device Capabilities](004-m4-device-capabilities/spec.md) | 按 Milestone 提出顺序回填 |
| 005 | [M5 Application Ecosystem](005-m5-application-ecosystem/spec.md) | 按 Milestone 提出顺序回填 |
| 006 | [M6 Home and Display](006-m6-home-display/spec.md) | 按 Milestone 提出顺序回填 |
| 007 | [M7 Navigation](007-m7-navigation/spec.md) | 按 Milestone 提出顺序回填 |
| 008 | [M8 App Contract](008-m8-app-contract/spec.md) | 按 Milestone 提出顺序回填 |
| 009 | [AI Native foundation](009-ai-native-foundation/spec.md) | 既有 AI Native 设计 Effort |
| 010 | [文档重组](010-docs-reorganization/spec.md) | 本次文档迁移 Effort |

Milestone 状态仍以 [`docs/milestones/README.md`](../docs/milestones/README.md) 为权威。

M1–M8 Sequence 根据已知 Milestone 提出顺序重建，不虚构准确创建时间或历史 owner。AI Native 不改名为 M9，因为 Sequence 记录 tracker provenance，不是产品 Milestone 编号。

## 分配规则

- 新 Effort 首次写入时分配下一个未使用 Sequence。
- 标题或 slug 变化时保留 Sequence。
- `resolved` 与 `wontfix` Effort 继续保留，其编号属于历史记录。
- 依赖变化写入 `Blocked by`，不重排目录。

## 推进 frontier

在一个 Effort 内，选择编号最小、`Blocked by` 已解决，且 `Status` 为 `ready-for-agent` 或 `ready-for-human` 的 ticket。`Blocked by` 中的跨 Effort 依赖优先于 Sequence。
