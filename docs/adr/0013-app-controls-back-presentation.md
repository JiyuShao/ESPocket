# ADR-0013: App 可定制 Back 呈现与手势

- Status: `accepted`
- Recorded: 2026-10-02
- Origin: 用户明确确认所有 App 都可单独定制返回形式与返回 UI，Settings 无可见 Back 可以接受

## Context

此前开发契约要求接管默认 Back 的多级 App 自带可见按钮。官方 Settings 真机检查中没有可见 Back，但 Edge Back 正常。用户确认按钮不是必要条件，并把自定义返回形式的权利明确扩展到所有 App。

## Decision

ESPocket 保留默认可见 Back 与 Edge Back，App 可接管两者，自行选择返回控件、边缘滑动或上下滑动等形式，也可不显示可见按钮。框架不以缺少可见 Back 拒绝多级 App 声明，不为官方 Settings 补按钮。

普通 App 自定义返回入口调用同一 `requestBack`，不绕过 Navigator 只切换 GUI。返回呈现不改变导航事实所有权、待决确认、Root 无 Back 或 PWR Home。[ADR-0011](0011-app-root-has-no-back.md) 的这些决定继续有效。

[ADR-0012](0012-official-settings-keeps-its-navigation-owner.md) 的官方 Settings 适配例外继续有效；其中“自带可见 Back”改为可选呈现，存在时仍汇入官方 Back 动作。

## Consequences

- App 作者负责其自定义手势与内容滚动的冲突处理和交互可发现性。
- 页面快照中的 `canBack` 表示导航能力，不承诺页面上存在按钮。
- 默认 Back 仍可供 App 使用；当前 `AppOwned` 接管两种默认入口，不新增独立开关。
