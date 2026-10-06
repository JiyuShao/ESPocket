# ADR-0020: Shell 导航手势在 Release 提交

- Status: `accepted`
- Recorded: 2026-10-05
- Origin: 用户报告滚动手势与 Edge Back 持续触发误点击

## Decision

Home Space 的方向导航、Edge Back、Card step 和 Launcher 下拉回 Watch Face 都在指针 Release 事件上提交 GestureIntent。Pressing 在系统手势越过阈值时请求取消 pointer 的点击候选；Shell 在 Owner tick 对 pointer input 执行 LVGL release wait，Release 才提交导航。

这个规则适用于 System 拥有的默认导航手势。App 拥有的普通滚动、横滑、Long Press 和自定义手势仍由 App Owner 处理；App 接管 Back 时必须使用统一 Back 语义。中断、取消、模态或屏幕熄灭时不得补发 Release 提交。

同一 pointer 序列离开 10px 点击容差后，Shell 的 LVGL indev filter 抑制 SHORT_CLICKED 与 CLICKED 向控件传播，直到下一次 Press。滚动、拖动、Release 与 App 自定义 Gesture 继续交给原 Owner；取消导航不能把已有拖动重新解释为点击。

## Consequences

- 持续按住并越过阈值的滑动不会把旧按钮位置变成新的点击。
- 导航意图确认延迟到手指抬起；阈值识别本身仍在 Pressing 阶段执行。
- Shell 在系统手势识别后取消点击候选，不向 App 释放伪造的原始手势。
- 真实触摸、合成触摸和 Display 手势事件都必须携带稳定的 Release 方向与距离。
