# Architecture Decision Records

ADR 记录替代方案代价显著、需要长期保持可追溯的 ESPocket 决策。产品行为以 `docs/design/product/` 为权威，当前与目标结构以 `docs/design/architecture/` 为权威。

`Recorded` 表示 ADR 被正式补录和接受的日期，不代表决策最早出现的时间。无法从历史证据确认首次决策日期时，`Origin` 明确写为未知；迁移来源见[文档拆分记录](../../.scratch/010-docs-reorganization/issues/03-split-design-work-and-history.md)。

| ADR | Status | Decision |
|---|---|---|
| [0001](0001-espocket-is-a-product-layer-over-brookesia.md) | accepted | ESPocket 保持为 Brookesia 之上的产品层。 |
| [0002](0002-watch-face-is-the-only-home.md) | accepted | Watch Face 是唯一 Home。 |
| [0003](0003-native-and-runtime-share-the-system-core-contract.md) | accepted | Native 与 Runtime App 共享一套产品 lifecycle 契约。 |
| [0004](0004-core-owns-the-runtime-package-trust-gate.md) | accepted | Core 持有单一 fail-closed Runtime package trust gate。 |
| [0005](0005-launcher-projects-core-committed-app-state.md) | accepted | Launcher 投影 Core committed App state。 |
| [0006](0006-ai-semantic-access-stays-with-real-owners.md) | accepted | AI semantic access 保留在真实 Owner 边界。 |
| [0007](0007-ai-authority-comes-from-user-goals.md) | accepted | AI authority 来源于已确认用户目标。 |
| [0008](0008-app-ai-capabilities-follow-the-running-instance.md) | accepted | App AI capability 跟随一个 Running Instance。 |
| [0009](0009-ai-native-is-a-foundational-design-dimension.md) | accepted | AI Native 是底层设计维度。 |

决策变更时新增 superseding ADR，并让新旧记录相互链接。不得静默改写已接受 ADR 的决定。
