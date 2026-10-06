# Architecture Decision Records

ADR 记录替代方案代价显著、需要长期保持可追溯的 ESPocket 决策。产品行为以 `docs/design/product/` 为权威，当前与目标结构以 `docs/design/architecture/` 为权威。

`Recorded` 表示 ADR 被正式补录和接受的日期，不代表决策最早出现的时间。无法从历史证据确认首次决策日期时，`Origin` 明确写为未知；迁移来源见[文档拆分记录](../../.scratch/010-docs-reorganization/issues/03-split-design-work-and-history.md)。

| ADR | Status | Decision |
|---|---|---|
| [0001](0001-espocket-is-a-product-layer-over-brookesia.md) | accepted | ESPocket 保持为 Brookesia 之上的产品层。 |
| [0002](0002-watch-face-is-the-only-home.md) | superseded by 0011 | Watch Face 是唯一 Home；旧 Root Back 决定已替换。 |
| [0003](0003-native-and-runtime-share-the-system-core-contract.md) | accepted | Native 与 Runtime App 共享一套产品 lifecycle 契约。 |
| [0004](0004-core-owns-the-runtime-package-trust-gate.md) | accepted | Core 持有单一 fail-closed Runtime package trust gate。 |
| [0005](0005-launcher-projects-core-committed-app-state.md) | accepted | Launcher 投影 Core committed App state。 |
| [0006](0006-ai-semantic-access-stays-with-real-owners.md) | accepted | AI semantic access 保留在真实 Owner 边界。 |
| [0007](0007-ai-authority-comes-from-user-goals.md) | accepted | AI authority 来源于已确认用户目标。 |
| [0008](0008-app-ai-capabilities-follow-the-running-instance.md) | accepted | App AI capability 跟随一个 Running Instance。 |
| [0009](0009-ai-native-is-a-foundational-design-dimension.md) | accepted | AI Native 是底层设计维度。 |
| [0010](0010-app-cards-are-app-surfaces-in-home-space.md) | superseded by 0011 | App Card 是同一 App 在 Home Space 的专门形态；旧 Root Back 决定已替换。 |
| [0011](0011-app-root-has-no-back.md) | accepted | App Root 无 Back；ESPocket 保存 App 页面栈。 |
| [0012](0012-official-settings-keeps-its-navigation-owner.md) | accepted | 官方 Settings 保留导航事实源；ESPocket 适配快照与 Back。 |

| [0013](0013-app-controls-back-presentation.md) | accepted | 所有 App 可定制 Back UI 与手势，不要求可见按钮。 |
| [0014](0014-runtime-card-starts-declarative.md) | accepted | Runtime Card 首版声明式呈现，框架管理生命周期，独立 JS 业务回调延后。 |

| [0015](0015-runtime-async-stack-patch-exception.md) | accepted | Runtime JS 0.8.3 异步栈配置补丁的限定例外。 |

决策变更时新增 superseding ADR，并让新旧记录相互链接。不得静默改写已接受 ADR 的决定。

| [0016](0016-maintained-upstream-fixes.md) | accepted | 允许维护真实 Owner 内的上游 bug 修复，精确应用锁定版本补丁。 |
| [0017](0017-overlay-arbitration-preserves-request-ownership.md) | accepted | Shell 仲裁 Overlay 输入；Core 保持请求身份、队列与期限。 |

| [0018](0018-developer-mode-allows-unsigned-packages.md) | accepted | 仅开发者模式允许未签名 Runtime 包；Core 安装边界与其余验证要求继续有效。 |

| [0019](0019-reuse-protected-package-verification.md) | accepted | 安装完整验证，保护内容修改，重启与启动复用绑定版本和信任配置的持久结果。 |
| [0020](0020-shell-navigation-commits-on-release.md) | accepted | System 默认导航手势只在 Release 提交，防止持滑误触发点击。 |
