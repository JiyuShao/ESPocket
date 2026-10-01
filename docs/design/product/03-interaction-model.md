# 03 — 系统交互模型

## 目的

本模型定义 Watch Face、Cards、Launcher、Quick Settings、App 与 Display State 之间的用户可见关系，确保触控、PWR 与 Assistant 不会产生互相矛盾的导航结果。

## 用户结果

- 用户总能用 PWR 回到 Watch Face，或在 Watch Face 上关闭屏幕。
- 用户能预测 App 内 Back 返回哪里，并区分 Home、Back 与 Screen Off。
- 完整 App 页面的普通滚动和横滑不会被 Home Space 导航占用。
- 息屏和唤醒不会改写仍然有效的页面状态。

## 产品要求

| ID | Requirement |
|---|---|
| INT-001 | Watch Face 必须是唯一 Home，也是 Home Space 的中心锚点。 |
| INT-002 | 从 Watch Face 上滑必须进入 Launcher，下滑必须进入 Quick Settings，左右滑必须在 Cards 间移动；四种周边页面都属于 Home Space。 |
| INT-003 | 任一时刻必须只有一个顶层 Surface 可见；临时系统层不得进入普通 Back 历史。 |
| INT-004 | PWR 短按在亮屏非 Home 时必须返回 Watch Face，在亮屏 Watch Face 时必须息屏，在息屏时必须唤醒。 |
| INT-006 | Home 与 Back 必须保持不同语义，不得互相替代。 |
| INT-007 | Screen Off 必须与导航状态正交；目标仍有效时唤醒恢复原页面，目标失效时返回 Watch Face。 |
| INT-008 | 息屏期间触摸不得触发页面动作；基础唤醒入口为 PWR。 |
| INT-010 | Card 是 Home Space 中的一级位置，可展示 Shell 内容或同一 App 的专门 App Card 形态；需要多级流程时进入完整 App 页面。 |
| INT-011 | Launcher 只负责发现和启动 App，不得成为 Home。 |
| INT-017 | 从 Launcher 向下、Quick Settings 向上、左右 Card 向表盘方向滑动时，必须能返回 Watch Face；周边页应有轻微的返回方向提示。 |
| INT-018 | Launcher 应为纵向滚动列表；列表在顶部继续下拉，越过阈值并松手后才返回 Watch Face。拉动期间应有伸展与箭头反馈，达到阈值时提示松手返回，并取消本次触摸的 App 点击。 |
| INT-019 | 用户可增删和排序左右 Card；Quick Settings 与 Launcher 的位置固定。 |
| INT-020 | 所有页面不得显示 Shell 常驻顶部状态栏。App 自行呈现所需状态信息；临时系统告警可覆盖当前页面。 |
| INT-022 | Home Space 周边页以反方向手势返回 Watch Face；App 的子页面 Back 返回 App 页面栈的上一项，App Root 没有 Back。 |
| INT-023 | App 子页面默认提供可见 Back 与 Edge Back；App 可以接管两种默认入口，自定义返回 UI 与手势，也可不显示可见 Back；自定义返回使用统一 Back 语义。普通滚动、横滑与 Long Press 归 App；PWR Home 不可关闭。 |
| INT-024 | App Card 上的横滑由 Home Space 处理；Card 内纵向交互与轻量操作归 App。Card 打开完整 App 后，PWR Home 直接返回 Watch Face。 |
| INT-025 | 完整 App 页面的 Back 请求可由 App 暂缓确认；待决期间不得重复执行 Back，超时必须取消并报告错误。PWR Home、App 停止或崩溃使待决请求失效。 |
| INT-026 | Quick Settings 的直接切换必须立即生效并停留在原 Surface；进入完整 Settings App 后遵守 App Page 栈与 Root 无 Back 的规则。 |

旧要求的替代关系：INT-005 → INT-022、INT-023；INT-009 → INT-023、INT-024；INT-012 → INT-026；INT-014 → INT-027。旧 ID 保留在 Git 历史中，不再表示当前产品要求。

## AI Native

| ID | Requirement |
|---|---|
| INT-013 | Assistant 必须调用 Home、Back、打开 Surface、读取 Display State 等语义 Action，不能通过模拟坐标或手势实现系统导航。 |
| INT-015 | Assistant 不得把 Screen Off 报告为离开页面，也不得把唤醒报告为重新启动仍有效的 App。 |
| INT-016 | 涉及高影响设置的 Action 必须在执行前完成相应确认；打开设置页面不得被报告为设置已改变。 |
| INT-027 | Assistant 触发导航后必须遵守与触控和 PWR 相同的 Surface、App Page 栈、Root 无 Back 与失效回退规则。 |

## 非目标

- 手势阈值、动画时长、识别算法和内部页面栈实现。
- Watch Face 自定义、通知中心和完整后台调度。
- 规定 Assistant 的视觉形态或输入供应商。
