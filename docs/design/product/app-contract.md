# ESPocket App 交互契约

本文是 Native、Runtime 与第三方 App 共用的最小交互契约。系统实现状态和真机证据由 M7/M8 验收文档判定。

## 导航

- App 使用名为 `main` 的 Screen Flow，并以 `root` 作为初始页面。
- Root 可以进入 `detail`；Detail 的系统 Back action 为 `back_root`。
- Edge Back 在 Detail 返回 Root；在 Root 结束当前 App 导航任务并返回唯一的直接 Launch Source。
- Launch Source 只记录 Launcher、Card、Quick Settings 或其他一个系统 Surface，不建立任意长度的历史链。
- 来源失效时返回 Watch Face。PWR Home 始终返回 Watch Face，不等同于 Back。
- App 被停止或回收后，下一次启动必须从 Root 开始；页面对象、输入焦点、键盘和临时 Overlay 不得视为持久状态。

## 手势归属

- App 拥有 Tap、普通上下滚动、普通横滑和 Long Press。
- 系统只保留左右物理边缘向内的 Edge Back，以及 PWR Home/息屏/唤醒。
- App 不得把 Edge Back 用作业务手势，也不得阻塞 PWR Home。

## 显示与生命周期

- Screen Off 与页面导航正交；未回收时唤醒恢复当前页面。
- 息屏期间忽略触摸，基础唤醒源只有 PWR。
- 页面恢复是 best effort；目标失效或已回收时回 Watch Face，不自动重建旧页面栈。
- App 不得依赖后台驻留。可靠计时、播放、连接或长期业务状态应交给系统能力或持久化业务状态。

## 页面指导

| 类型 | 推荐结构 |
|---|---|
| 信息型 | 大号主数值 + 小号状态 + 可选详情 |
| 控制型 | 状态 + 主要控制项 |
| 列表型 | 单列列表，足够大的整行点击区域 |
| 工具型 | 单一任务 + 大号主要操作 |

圆屏内容优先放在中部；边缘只承载弱信息和系统手势。避免手机式 Toolbar、Tabs、Bottom Navigation 和位于圆屏四角的关键按钮。

## 参考实现

- Native：`Hello Native` 使用 `main: root/detail`。
- Runtime：`Hello Runtime` 使用相同 Flow、页面名和 Back action。
- Shell/System 只识别上述小接口，不了解 App 内部页面实现，也不为不同运行时维护两套导航逻辑。
