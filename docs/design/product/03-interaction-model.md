# 03 — 系统交互模型

## 目的

本模型定义 Watch Face、Cards、Launcher、Quick Settings、App 与 Display State 之间的用户可见关系，确保触控、PWR 与 Assistant 不会产生互相矛盾的导航结果。

## 用户结果

- 用户总能用 PWR 回到 Watch Face，或在 Watch Face 上关闭屏幕。
- 用户能预测 Back 返回哪里，并区分 Home、Back 与 Screen Off。
- App 的普通滚动和横滑不会被系统导航占用。
- 息屏和唤醒不会改写仍然有效的页面状态。

## 产品要求

| ID | Requirement |
|---|---|
| INT-001 | Watch Face 必须是唯一 Home，也是 Home Space 的中心锚点。 |
| INT-002 | 从 Watch Face 上滑必须进入 Launcher，下滑必须进入 Quick Settings，左右滑必须在 Cards 间移动。 |
| INT-003 | 任一时刻必须只有一个顶层 Surface 可见；临时系统层不得进入普通 Back 历史。 |
| INT-004 | PWR 短按在亮屏非 Home 时必须返回 Watch Face，在亮屏 Watch Face 时必须息屏，在息屏时必须唤醒。 |
| INT-005 | Back 必须返回可见 Surface 的直接父级或直接 Launch Source；来源失效时必须返回 Watch Face。 |
| INT-006 | Home 与 Back 必须保持不同语义，不得互相替代。 |
| INT-007 | Screen Off 必须与导航状态正交；目标仍有效时唤醒恢复原页面，目标失效时返回 Watch Face。 |
| INT-008 | 息屏期间触摸不得触发页面动作；基础唤醒入口为 PWR。 |
| INT-009 | 系统只保留 Edge Back 和 PWR；Tap、普通上下滚动、普通横滑与 Long Press 归可见 App 或 Surface。 |
| INT-010 | Cards 必须是单页、单主题内容；需要多步流程时必须进入 App。 |
| INT-011 | Launcher 只负责发现和启动 App，不得成为 Home。 |
| INT-012 | Quick Settings 的直接切换必须立即生效并停留在原 Surface；复杂设置完成 Back 后必须返回 Quick Settings。 |

## AI Native

| ID | Requirement |
|---|---|
| INT-013 | Assistant 必须调用 Home、Back、打开 Surface、读取 Display State 等语义 Action，不能通过模拟坐标或手势实现系统导航。 |
| INT-014 | Assistant 触发导航后必须遵守与触控和 PWR 相同的 Surface、Launch Source 与失效回退规则。 |
| INT-015 | Assistant 不得把 Screen Off 报告为离开页面，也不得把唤醒报告为重新启动仍有效的 App。 |
| INT-016 | 涉及高影响设置的 Action 必须在执行前完成相应确认；打开设置页面不得被报告为设置已改变。 |

## 非目标

- 手势阈值、动画时长、识别算法和内部页面栈实现。
- Watch Face 自定义、Card 编辑、通知中心和完整后台调度。
- 规定 Assistant 的视觉形态或输入供应商。
