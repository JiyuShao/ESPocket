# ADR-0012: 官方 Settings 保留导航事实源

- Status: `accepted`
- Recorded: 2026-10-02
- Origin: 用户确认官方 Settings 适配例外、源码提交与升级边界，并同意先实施最小导航适配

## Context

[ADR-0011](0011-app-root-has-no-back.md) 要求 ESPocket 保存 App 页面栈。锁定版官方 Settings 已有私有页面状态和 Back 业务处理，公开 GUI 接口能读其 Screen Flow，但没有 Settings 专用的 Page／Back 契约。复制一份栈会造成两个事实源；改官方源码或复制 Settings 则会增加升级与业务回归成本。

## Decision

[ADR-0013](0013-app-controls-back-presentation.md) 后续明确所有 App 可定制返回 UI 与手势，不要求可见 Back；Root 与导航事实所有权不变。

为官方 Settings 增加明确、限定版本的适配例外：Settings 持有页面导航事实源，ESPocket 防腐层读取真实 Screen Flow，映射稳定 Page ID 并提供统一页面快照。ESPocket 不为它建立第二份页面栈。普通 Native／Runtime App 继续使用 ESPocket Page Navigator；这不是 App 开发者可自行选择的第二套导航协议。

ESPocket 的组合式 `IApp` Adapter 持有官方 SettingsApp，转发生命周期、动作与计时器回调。系统 Edge Back 委托给 Settings 的官方 Back 动作，保留它的业务清理；自带可见 Back 与该动作汇合，不叠加 Overlay Back。Root 无 Back、PWR Home 和息屏恢复规则保持一致。此决定只修订 ADR-0011 对官方 Settings 栈所有权的要求。

允许绑定 Settings 0.8.3 的私有 Flow、页面和动作名称。未知页面或不可读取的 Flow 使快照报错、适配 Back 停用，不能静默报告 Root。适配只覆盖观察与 Back，不公开 Settings 的通用 push/pop，也不承诺覆盖任意界面或业务定制。

提交 ESPocket Adapter、兼容测试与契约文档，不修改生成的 managed components。升级依赖时，在同一次审查中更新 manifest／lock 与必要的映射和兼容测试；完整构建及必要真机检查通过前保留旧基线。深度定制出现明确需求时，再比较上游公开扩展点与 ESPocket 自有 Settings App。

## Consequences

- ESPocket Page 快照可来自 Navigator 或已明确适配的真实 Owner，不能仅由缓存的控件文字推断。
- 官方 Settings 的私有名称是有版本约束的兼容成本；升级测试不能代替真机业务行为检查。
- Store 当前只有一屏，按单 Root 接入；若升级新增真实子页面，需要重新评估该声明。
- 新的自有 Settings App 可继续使用 Brookesia GUI 与 Service，但需要承担页面、业务编排和回归验证。

## Alternatives rejected

- 复制官方 Settings 页面栈：状态可能与真实 GUI 分叉。
- 将 managed component patch 作为产品基线：与 [ADR-0001](0001-espocket-is-a-product-layer-over-brookesia.md) 冲突，升级需要重复维护补丁。
- 现在重写完整 Settings：当前需求只需要页面观察和 Back，尚无明确深度定制范围。

接口事实见 [2026-10-02 上游源码快照](../../.scratch/014-app-navigation-card-contract/records/2026-10-02-upstream-settings-store-gui-baseline.md)，适配契约见 [开发 API](../development/app-navigation-card-api.md)。
