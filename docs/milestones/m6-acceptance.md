# M6 Home & Display State 验收规范

## 状态

- M6: `NOT ENTERED`
- Dependency: M2 `PASS`
- M3: `BLOCKED`，不阻止 M6 进入
- M4: `BLOCKED`，不阻止 M6 进入
- M5: `BLOCKED`，不阻止 M6 进入

本文定义 M6 的范围与 PASS 门槛。实现前后都必须遵守 [`../design/interaction.md`](../design/interaction.md)。

## 目标

建立最小且完整的 Home 与显示状态闭环：

```text
Boot
 → Watch Face
 → Swipe Up
 → Current Fixed Launcher
 → Hello Native
 → PWR
 → Watch Face
 → PWR
 → Screen Off
 → PWR
 → Watch Face
```

另验证：

```text
App → Auto Screen Off → PWR → Resume App
```

如果恢复目标已被回收或失效：

```text
PWR → Watch Face
```

## Scope

- Watch Face 成为 Home 的固定目标。
- 开机进入 Watch Face。
- Watch Face 上滑进入当前固定 Launcher。
- PWR 短按状态机：
  - Screen Off → Wake / best-effort resume；
  - Screen On + Non-Home → Watch Face；
  - Screen On + Watch Face → Screen Off。
- PWR 长按保持硬件固定开机/关机行为，不增加 System Menu。
- 自动息屏与全局超时设置。
- 息屏不改变当前 Surface 或页面导航。
- App 未被回收时恢复同一可见页面和导航位置。
- 恢复目标失效时降级到 Watch Face，不自动重启 App。
- Screen Off 时忽略触摸。
- BOOT 保持 Reserved。
- Home 后系统可以暂停、保留或回收原 App；持续业务状态只做 best effort。

## Out of Scope

- Cards。
- Quick Settings。
- Edge Back 与 Launch Source。
- 动态 Launcher 或 M5 Launcher sync。
- Watch Face 点击快捷操作、长按自定义或更换表盘。
- Card 编辑。
- 抬腕唤醒与轻触唤醒。
- App keep-awake API。
- 完整后台调度器或低内存杀手。
- Pet、XiaoZhi、AI UI、MCP 或 ESP-Claw。

## Source / Build Gates

| 检查项 | PASS 条件 | 状态 |
|---|---|---|
| Interaction contract | 实现与主交互规范一致 | NOT TESTED |
| Current-vs-target wording | 文档和 UI 不把 M1–M5 的 Launcher Home 误称为 Watch Face 实现 | NOT TESTED |
| Existing Launcher reuse | 使用当前固定入口 Launcher；不把动态同步带入 M6 | NOT TESTED |
| PWR integration | 短按只执行已定义的 Home/Off/Wake；长按不被系统层重定义 | NOT TESTED |
| Display/navigation separation | 息屏不清空或改写有效导航位置 | NOT TESTED |
| Resume fallback | 目标失效时只回 Watch Face | NOT TESTED |
| Touch while off | Screen Off 时页面动作不可被触摸触发 | NOT TESTED |
| BOOT | 不产生日常导航动作 | NOT TESTED |
| Build | 正常固件 clean build/link 成功 | NOT TESTED |
| Static checks | JSON、脚本或项目既有检查全部通过 | NOT TESTED |

## Hardware Acceptance

真机证据是 M6 PASS 的必要条件；Preview、host 测试或日志不能替代物理显示、按键和触摸观察。

### Fixed repetition counts

以下次数均为固定验收要求，且不超过 5 次。任何一次失败都必须记录，不能通过追加成功次数稀释。

| 路径 | 次数 | PASS 条件 | 状态 |
|---|---:|---|---|
| Cold boot → Watch Face | 5 | 每次都显示 Watch Face，无 Launcher 先成为 Home | NOT TESTED |
| App → PWR Home → Watch Face → PWR Off → PWR Wake | 5 | 顺序和可见状态均正确 | NOT TESTED |
| App → Auto Screen Off → PWR → Resume App | 5 | 恢复同一可见页面及导航位置 | NOT TESTED |
| Resume target reclaimed → PWR → Watch Face | 5 | 不自动重启 App，不出现空白或失效页面 | NOT TESTED |

### Required one-pass checks

| 检查项 | PASS 条件 | 状态 |
|---|---|---|
| Screen Off touch | 触摸不触发当前页面操作 | NOT TESTED |
| Overlay + PWR | 临时 Overlay 存在时仍回 Watch Face，可放弃未提交输入 | NOT TESTED |
| BOOT | 不触发 Back、Home、Shortcut 或 Recent Apps | NOT TESTED |
| PWR long press | 仅表现为硬件固定开机/关机 | NOT TESTED |
| Failure scan | 无 panic、watchdog、assert、deadlock、错误触摸执行或持续性资源下降 | NOT TESTED |

## Evidence Rules

- 每次固定循环必须能区分 attempt 编号与结果。
- 串口证据必须与物理观察对应；只打印目标状态不证明屏幕已正确显示。
- App 回收可以使用明确的测试入口模拟，不要求先实现通用资源管理器。
- 页面身份与导航位置需要恢复；输入焦点、键盘、弹窗和进行中的触摸不属于恢复保证。
- 任一必须项缺少证据时不得标记 M6 `PASS`。

## Result

`NOT ENTERED`
