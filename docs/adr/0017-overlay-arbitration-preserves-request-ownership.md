# ADR-0017: Shell 仲裁 Overlay 输入，Core 保持请求所有权

- Status: `accepted`
- Recorded: 2026-10-04
- Origin: System Super 参考审计访谈，用户接受 Q6–Q8 推荐

## Context

键盘、确认弹窗与 Loading 可同时存在，按 GUI 对象创建顺序决定输入会让更新改变前后关系。为解决此问题复制 Core 请求队列或暂停真实请求期限，会引入第二份生命周期事实，并可能在息屏后恢复已经失效的请求。

## Decision

CircularShell 在现有请求关系上仲裁呈现和输入：确认弹窗优先，键盘可暂停输入并保留草稿，Loading 优先级最低。Core 继续持有请求身份、Dialog 队列与完成/失效事实，Shell 不新增请求队列或通用 Overlay 生命周期管理器。

同一处理周期中的 PWR 优先于未提交选择；已提交结果仍由真实 Owner 核实。息屏只暂停提示自动关闭的呈现计时，不暂停操作期限、授权或 Owner 生命周期。恢复键盘或提示前检查原请求仍有效。

## Consequences

- 键盘期间 Back 是取消输入，不改变底层 App 页面栈。
- GUI 更新、暂停与恢复不能改变 Owner/request identity，也不能授予 Permission。
- 系统提示不被等同为前台 App 请求；Home 后可保留，PWR 保持已有导航/显示语义。
- 实际用户行为要求由 [系统交互模型](../design/product/03-interaction-model.md) 持有；审计决定见 [018](../../.scratch/018-system-super-reference-audit/spec.md)，实现与验收由 [019](../../.scratch/019-system-shell-remediation/spec.md) 的后续工作定义。
