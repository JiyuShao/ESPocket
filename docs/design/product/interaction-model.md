# ESPocket 系统交互设计规范

## 文档状态

本文是 ESPocket 的目标交互契约，适用于 Watch Face、Cards、Launcher、Quick Settings、Native App 和 Runtime App。

- 目标模型：`Home → Watch Face`。
- 当前实现：M6 已进入实施，源码已引入 `Home → Watch Face`、PWR Home/息屏/唤醒和自动息屏；真机验收尚未完成。Cards、Quick Settings 与 Edge Back 仍未实现。
- 生效路径：M6 起逐步实现本规范；M1–M5 验收文档继续记录当时的实现与证据，未通过真机门槛的 M6 行为不得描述为已验收。
- 本文中的“必须”“应该”“可以”分别表示强制契约、默认原则和可选能力；示例不自动构成交付范围。

本文只定义交互规则和页面关系，不定义手势阈值、识别优先级或算法。

## 设计目标

- 适配 1.75 英寸 466×466 圆形触摸屏。
- 保持智能手表的交互心智，不缩小照搬手机界面。
- 减少页面层级，明确系统交互与 App 交互边界。
- 使用 PWR 承担 Home、息屏和唤醒。
- 为 Native App 与 Runtime App 提供一致的交互基础。

## 顶层交互模型

ESPocket 的系统中心必须是 Watch Face，而不是 Launcher。

```text
                    Quick Settings
                          ↑
                          │
Cards  ←─────────── Watch Face ───────────→ Cards
                          │
                          ↓
                       Launcher
                          │
                          ↓
                         App
```

顶层模型由以下互斥 Surface 构成：

- **Home Space**：Watch Face 与其左右 Cards 构成的横向空间。
- **Launcher**：寻找并启动 App。
- **Quick Settings**：快速查看或切换系统状态。
- **App Surface**：当前 Native App 或 Runtime App。

任一时刻只有一个顶层 Surface 可见。临时系统层可以覆盖当前 Surface，但不进入普通 Back 栈。

## 表盘（Watch Face）与主空间（Home Space）

Watch Face 是 Home 的固定目标，也是 Home Space 的中心锚点。

| Watch Face 操作 | 行为 |
|---|---|
| 上滑 | 打开 Launcher / All Apps |
| 下滑 | 打开 Quick Settings |
| 左右滑 | 浏览 Cards |
| Edge Back | 无操作 |
| PWR 短按 | 息屏 |

点击表盘快捷操作、长按自定义、更换表盘、Card 排序管理、抬腕唤醒和轻触唤醒不属于 M6–M8 的基础契约。

### 卡片（Cards）

Card 必须是单页、单主题的高频信息或快速操作界面，可以：

- 展示对应 App 的关键数据；
- 提供少量即时操作；
- 打开对应 App。

Card 不得拥有自己的 Detail 栈或复杂流程；需要第二层页面时必须进入 App。

Cards 构成以 Watch Face 为固定锚点的有序序列。模型允许未来增删和排序，但首版可以使用固定默认顺序。到达最左或最右 Card 后继续同方向滑动必须停留在边界，不循环。

```text
Battery ← Brightness ← Watch Face → Weather → Device
```

## 启动器（Launcher）

Launcher 的唯一职责是找到并启动 App。它不是 Home。

- 必须从 Watch Face 上滑进入。
- 应采用适合圆屏的图标网格或蜂窝布局，而不是手机式长列表。
- Edge Back 必须返回 Watch Face。
- PWR 短按必须返回 Watch Face。
- M6 可以继续复用当前固定入口 Launcher；动态 App 同步不属于 M6。

## 快捷设置（Quick Settings）

Quick Settings 必须从 Watch Face 下滑进入，并区分两类操作：

- 直接切换项：立即生效并停留在 Quick Settings；
- 复杂配置项：打开对应 Settings 页面，Back 返回 Quick Settings。

Edge Back 必须返回 Watch Face；PWR 短按必须返回 Watch Face。Quick Settings 不承载复杂配置流程。

首个实现只要求复用已有能力验证 Brightness、Wi-Fi、Battery 状态和 Settings 入口。Bluetooth、Sound、Do Not Disturb、Lock、Music 和 Notifications 不由本规范承诺。

## App 导航

### 页面深度

App Root 必须直接呈现最重要的信息或操作。页面通常应该控制在两至三层：

```text
App Root
   ↓
Detail
   ↓
Optional Detail
```

能在当前页面完成或展示的信息不应该增加 Detail 页面。

### 返回（Back）

Back 是页面级导航，不等同于 Home。

```text
Detail → Back → Parent
App Root → Back → Launch Source
```

App 导航任务只记录一个直接 Launch Source：Launcher、Card 或其他系统 Surface。它不构建任意长度的系统历史链。

```text
Launcher → App Root → Back → Launcher
Card → App Root → Back → 原 Card
Quick Settings → Settings → Back → Quick Settings
```

如果 Launch Source 已失效或无法恢复，Back 必须降级到 Watch Face。第一阶段不支持任意 App-to-App 返回链；App A 打开 App B 时，不保证 `B → Back → A`。

### App 手势边界

| App 操作 | 行为 |
|---|---|
| Tap | Primary Action |
| 普通上下滑 | Scroll |
| 普通横滑 | App Defined |
| 左右任意边缘向内滑 | Back |
| Long Press | 场景定义的 Secondary Action |
| PWR 短按 | Home |

Edge Back 必须只表达 Back；普通横滑必须仍可由 App 使用。具体判定方式不属于本文。

## PWR、BOOT 与显示状态

PWR 长按开机或关机是硬件固定行为，系统交互层不得增加 Power Menu 或其他长按语义。BOOT 保持 Reserved，不承担 Back、Home、Shortcut 或 Recent Apps。

### PWR 短按

| 当前状态 | PWR 短按 |
|---|---|
| Screen Off | 唤醒并尽力恢复息屏前页面 |
| Screen On + Non-Home | Home，前往 Watch Face |
| Screen On + Watch Face | Screen Off |

```text
App / Settings / Launcher / Quick Settings
                │
             PWR 短按
                ↓
           Watch Face
                │
             PWR 短按
                ↓
            Screen Off
                │
             PWR 短按
                ↓
           Watch Face
```

PWR Home 必须覆盖普通导航。键盘、对话框或其他临时 Overlay 显示时，短按 PWR 仍必须前往 Watch Face，并可以放弃未提交输入。

### Home 与 App 生命周期

Home 必须结束当前页面导航任务并前往 Watch Face。再次从 Launcher 或 Card 启动 App 时必须从 App Root 开始。

系统可以暂停、保留或回收离开前台的 App，不保证其继续驻留。持续业务状态应尽量保留，但这不是系统强保证；资源不足时允许直接回收后台 App。需要可靠跨 App 生命周期存在的计时、播放或连接状态，应该由系统服务或持久化业务状态承担。

### Screen Off 与 Wake

Display State 与当前 Surface 和页面导航正交：Screen Off 不是页面，也不执行 Home 或 Back。

自动息屏可以在任何页面发生。基础版本中，用户操作重置全局自动息屏计时，到期后息屏；`Never` 是全局设置，不提供 App 自定义 keep-awake 能力。

Screen Off 时必须忽略触摸输入，基础唤醒源只有 PWR 短按。抬腕唤醒和轻触唤醒属于未来可选能力。

唤醒恢复是 best effort：

- 当前 App 未被回收时，必须恢复同一个可见页面及导航位置；
- 不保证恢复输入焦点、键盘、弹窗或进行中的触摸；
- App 或页面已失效时，必须降级到 Watch Face，不自动重启 App 或重建丢失的页面栈。

## 圆屏 UI 原则

- 重要信息和主要操作应该位于屏幕中部。
- 边缘适合手势区域、状态信息、弱信息和 Page Indicator。
- 不得把关键按钮放在圆屏四角。
- 列表应该使用足够大的单列点击区域，并尽量直接显示当前值。
- 不建议使用手机式 Toolbar、Tabs 或 Bottom Navigation。
- 动画应该短、快，并清楚表达页面方向，不得阻碍操作。

推荐的基础布局：

```text
          Title

        Main Value

      Secondary Info

         Action
```

## App 页面类型指导

以下是页面指导，不要求同时实现模板框架：

- **信息型**：Big Value + Small Status + Optional Detail。
- **控制型**：Status + Primary Controls。
- **列表型**：Single Column List。
- **工具型**：Single Task + Large Primary Action。

第三方 App 必须遵守 PWR Home 与 Edge Back 的系统边界；Tap、Scroll、普通横滑和 Long Press 可以由 App 定义。

## 交互不变量

1. Home 的目标始终是 Watch Face。
2. Back 返回 Parent 或一个直接 Launch Source；Home 与 Back 不得互换。
3. Watch Face 是导航根节点，Back 在此无操作。
4. Cards 是 Home Space 的单页内容，不是 App 或导航栈。
5. Display State 不改变导航状态。
6. 唤醒尽力恢复息屏前页面，目标失效时回 Watch Face。
7. 系统不保证后台 App 驻留；资源不足时可以回收。
8. PWR 长按只执行硬件开机或关机；BOOT 保持 Reserved。
9. 系统手势不得占用 App 的普通上下滑与普通横滑。
10. 示例功能不自动成为 Milestone 交付范围。

## 一句话原则

> 表盘是中心，左右看 Cards，上滑找 App，下滑调系统；App 内上下滚动、普通横滑交给应用、边缘向内滑返回；PWR 短按负责 Home、息屏和唤醒，长按只负责硬件开关机。
