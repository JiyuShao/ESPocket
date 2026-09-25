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

**Launcher**：
Circular Shell 中用于进入可用应用或明确的 Shell 内部目标的系统界面。

**Home**：
返回系统主界面的导航意图。V0.x 中其目标是 Launcher，而不是独立页面。
_Avoid_: Home page

**Shell Overlay**：
Circular Shell 的系统覆盖层，容纳状态呈现与 Home 手势等跨页面的 Shell 能力。

**Status View**：
Shell Overlay 中呈现时间、网络和电池状态的区域；它不是传统手机式 Status Bar。
_Avoid_: Status Bar
