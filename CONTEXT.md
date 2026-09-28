# ESPocket

ESPocket 是基于 ESP-Brookesia、面向 ESP 系列轻量智能设备的应用平台。本词汇表统一项目中的产品与应用术语。

## 平台边界

**ESPocket**：
位于应用与 ESP-Brookesia 之间的产品平台层。V0.x 只面向 Waveshare ESP32-S3-Touch-AMOLED-1.75C，但 ESPocket 本身不等同于该设备或某一种 Shell。
_Avoid_: ESPocket OS、PocketOS、PocketPet、Circular Shell

**ESP-Brookesia**：
ESPocket 使用的上游基础应用框架，提供 System Core、GUI、Runtime、Services 与 HAL 等能力。它不是 ESPocket 的组成副本，也不由 ESPocket 重新包装。
_Avoid_: ESPocket framework、vendored Brookesia

**ESPocket System**：
ESPocket 的产品级系统装配与生命周期边界，负责把所需的 Brookesia 能力和当前 Shell 组成可启动的产品系统。
_Avoid_: ESPocket Platform、ESPocket Framework

**Shell**：
系统拥有的主要交互环境，负责系统级启动界面、导航与覆盖层；它是产品角色，不是第三种应用执行模型。

**Circular Shell**：
ESPocket 为圆形触摸设备实现的第一个 Shell。它是 ESPocket 的一个系统组件，不代表 ESPocket 整个平台。
_Avoid_: ESPocket、通用 Shell Framework

## 应用模型

**Native App**：
编译进固件并由 Brookesia System Core 管理的应用执行模型。

**Runtime App**：
通过受支持的软件包动态安装，并由 Brookesia System Core 管理的应用执行模型。
_Avoid_: Plugin

**System App**：
由系统提供或预装的应用产品角色；其执行模型仍然是 Native App 或 Runtime App，而不是第三种应用类型。

**Shell App**：
承载 Shell 的隐藏 Native App。这里的 App 指底层执行模型；Shell 不出现在普通 Launcher 应用列表中。

## Shell 交互

**Watch Face**：
Circular Shell 的系统主界面，也是 Home 的固定目标和 Home Space 的中心锚点。
_Avoid_: Home page、Launcher

**Home Space**：
由 Watch Face 与其左右有序 Cards 构成的系统一级内容空间；Watch Face 是固定锚点。

**Card**：
Home Space 中围绕单一主题提供一眼可读信息、少量即时操作或对应 App 入口的单页内容。
_Avoid_: App、Detail page、generic UI card

**Launcher**：
从 Watch Face 进入、用于找到并启动可用 App 或明确 Shell 内部目标的系统 Surface。
_Avoid_: Home

**Quick Settings**：
从 Watch Face 进入、用于快速查看或切换系统状态，并可进入对应 Settings 页面的系统 Surface。

**Home**：
无条件结束当前导航任务并前往 Watch Face 的系统级导航意图；它不等同于 Back，也不保证原 App 继续驻留。
_Avoid_: Back、Launcher、Home page

**Back**：
返回当前导航层级的 Parent 或直接 Launch Source 的页面级导航意图；Watch Face 没有 Back 目标。
_Avoid_: Home

**Launch Source**：
App 当前导航任务的直接启动来源，只保留 Launcher、Card 或其他系统 Surface 中的一项，不构成跨 App 历史链。
_Avoid_: Recent Apps、navigation history

**Display State**：
与当前 Surface 和页面导航正交的屏幕点亮或熄灭状态；息屏本身不改变导航位置。

**Shell Surface**：
任一时刻占据主要交互区域的顶层系统界面，包括 Home Space、Launcher 与 Quick Settings。

**Shell Overlay**：
Circular Shell 中覆盖当前 Surface 或 App 的系统层，用于状态呈现或临时系统交互，不属于普通 Back 栈。

**Status View**：
Shell Overlay 中呈现时间、网络和电池状态的区域；它不是传统手机式 Status Bar。
_Avoid_: Status Bar
