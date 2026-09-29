# ESPocket

ESPocket 是基于 ESP-Brookesia、面向 ESP 系列轻量智能设备的应用平台。本词汇表规定产品、应用、交互和 AI Native 的统一语言。

## 平台边界

**ESPocket**：
基于 ESP-Brookesia 组织 System、Shell、App 与 Service 的产品平台；它不等同于目标设备或某一种 Shell。
_Avoid_: ESPocket OS、PocketOS、PocketPet、Circular Shell

**ESP-Brookesia**：
ESPocket 使用的上游基础应用框架，包含 System Core、GUI、Runtime、Service 与 HAL 等能力。
_Avoid_: ESPocket Framework、vendored Brookesia

**ESPocket System**：
将 Brookesia 能力、产品策略和当前 Shell 组成一个可启动产品的系统装配与生命周期边界。
_Avoid_: ESPocket Platform、ESPocket Framework

**Shell**：
系统拥有的主要交互环境，包含系统 Surface、导航和 Overlay；它是产品角色，不是应用执行模型。

**Circular Shell**：
ESPocket 面向圆形触摸设备的首个 Shell 实现。
_Avoid_: ESPocket、通用 Shell Framework

## 应用模型

**Native App**：
编译进固件并由 Brookesia System Core 管理的应用执行模型。

**Runtime App**：
从受支持的软件包加载并由 Brookesia System Core 管理的应用执行模型。
_Avoid_: Plugin

**System App**：
由系统提供或预装的应用产品角色，其执行模型仍是 Native App 或 Runtime App。

**Shell App**：
以隐藏 Native App 承载 Shell 生命周期的框架角色；它不属于普通 Launcher 应用集合。

**Running Instance**：
App 从一次成功启动到停止、崩溃或回收之间的单次运行身份。
_Avoid_: App installation、persistent app identity

## Shell 交互

**Watch Face**：
Circular Shell 的系统主界面，也是 Home 的固定目标和 Home Space 的中心锚点。
_Avoid_: Home page、Launcher

**Home Space**：
由 Watch Face 与其左右有序 Card 组成的系统一级内容空间。

**Card**：
Home Space 中围绕单一主题提供一眼可读信息、少量即时操作或 App 入口的单页内容。
_Avoid_: App、Detail page、generic UI card

**Launcher**：
从 Watch Face 进入、用于查找并启动可用 App 或明确 Shell 内部目标的系统 Surface。
_Avoid_: Home

**Quick Settings**：
从 Watch Face 进入、用于快速查看或切换系统状态并进入对应 Settings 页面的系统 Surface。

**Home**：
结束当前导航任务并前往 Watch Face 的系统级导航意图。
_Avoid_: Back、Launcher、Home page

**Back**：
返回当前导航层级的 Parent 或直接 Launch Source 的页面级导航意图。
_Avoid_: Home

**Launch Source**：
App 当前导航任务的一个直接系统来源，不构成跨 App 历史链。
_Avoid_: Recent Apps、navigation history

**Display State**：
与当前 Surface 和页面导航正交的屏幕点亮或熄灭状态。

**Shell Surface**：
任一时刻占据主要交互区域的顶层系统界面，包括 Home Space、Launcher 与 Quick Settings。

**Shell Overlay**：
覆盖当前 Surface 或 App 的临时系统交互层，不属于普通 Back 栈。

**Status View**：
Shell Overlay 中呈现时间、网络和电池状态的区域。
_Avoid_: Status Bar

## AI Native

**AI Native**：
ESPocket 的基础产品与架构设计维度，使 Assistant 能在既有 Owner、授权和生命周期边界内使用产品语义。
_Avoid_: AI layer、AI App、第二套系统

**Owner**：
对一项状态、副作用和生命周期负最终责任的 System、Shell、Service 或 App。

**Semantic Registration**：
Owner 对外声明稳定 Context、Action 或 Event 及其授权与生命周期边界的设计关系。
_Avoid_: method export、GUI automation、raw API exposure

**Exposure Decision**：
一项系统设计对其 AI Native 语义选择注册、明确不暴露或延后处理的结论。

**Brookesia 防腐层**：
在选定能力上转换 ESPocket 产品语义与锁定版 Brookesia 公开接口的 Adapter seam。

**Context**：
由真实 Owner 提供、按授权读取的语义状态快照。
_Avoid_: UI text dump、object dump、state cache

**Action**：
指向真实 Owner、具有明确目标和副作用的语义操作请求。
_Avoid_: GUI 自动点击、原始硬件调用

**Event**：
由真实 Owner 发布、描述已经发生之事的语义事实。
_Avoid_: submitted Action、global event bus

**Permission**：
一次 Context 读取、Event 订阅或 Action 执行在产品授权与 Brookesia 准入共同约束下的有效准入结论。

**User Intent**：
系统可确认由用户在当次交互中直接提出的有边界任务目标。
_Avoid_: App prompt、Agent request

**Scoped Grant**：
用户授予 Assistant、限定能力范围与有效期限的产品授权。

**Action Risk**：
ESPocket 对一次具体 Action 的影响范围与可逆性所作的风险分类。

**Capability Discovery**：
当前可用 Semantic Registration 的最小描述，不包含能力状态或使用权。

**Assistant**：
关联 User Intent、实际调用者与获准 Semantic Registration 的统一 AI 入口。
_Avoid_: XiaoZhi、ESP-Claw、Agent Manager
