# USB 触摸 Owner 接入证据

- 日期：2026-10-02
- Ticket：[012/02](../issues/02-shared-input-and-snapshot.md)
- 前置：[共享仲裁](2026-10-02-shared-shell-gesture.md)、[共同序列](2026-10-02-touch-sequence.md)

## 源码接入

USB `stimulus.touch` 接收整数像素/时间与按下状态的 points；协议准入后委托真实序列校验与共同槽位。tap 至少两点，swipe 需移动的按下点；末点 release 必须与最后按下点同坐标。worker 按时逐点调用 CircularShell，由它执行 Display `inject_touch` 驱动 LVGL，并按该输出实际方向/边缘阈值转换为 `ShellGestureEvent`，调用已有正式仲裁入口。没有通过协议设置 Surface 或 Page 栈。

Shell 硬件回调与注入状态用互斥锁仲裁；合成期间忽略硬件手势事件，Display override 覆盖 LVGL 触摸。物理 PWR 保持可用并优先取消合成触摸，先清除未消费 Shell intent，再执行原 System 语义。不要混合人工触摸与合成轨迹。

完成后给 LVGL 至少 40 ms 观察 release，再清除 Display override。异常取消先清 Shell intent/pull 和 LVGL 按压，再解除 override，不以正常 Release 提交 Launcher 返回或制造点击。超过总时长加 500 ms、App 任务 token 改变、息屏、关模式、物理断连、响应写失败都进入取消。失败清理保留共同槽位，继续重试；Adapter 停止最多五次重试并记录失败，不把清理失败报成成功。

PWR 排队也携带原前台任务 token，System 消费时核对，已换任务则丢弃。丢弃合成 PWR 不会吞掉同 tick 的物理短按。所有刺激共用一个槽位，旧输入不会借 release 提前释放正在执行的 PWR。

## 检查边界

- 真实 C++ 协议用例验证开发者模式关闭不调用 touch Owner、仅绑定能力公布、校验错误透传、touch/PWR 双向 busy 及重复 release。
- 真实序列组件验证时间、范围、release、失败清理与迟到取消；共同队列验证任务 token 原子传递。
- 真实 Shell 仲裁/轨迹转换组件验证方向锁定、严格阈值、真实横边缘阈值、Launcher 过阈值取消不提交、正常完成保留已排队 intent。
- `python3 scripts/check.py`：17 项 unittest、M2 parser、160 个 Markdown 文件通过。
- USB boost::json 解析及 Display/LVGL Owner 调用编入固件；当前没有把它们伪装为在真实设备上执行过的用例。

当前源码 capability 含 hello、snapshot、stimulus.powerShort、stimulus.touch、release。未刷写，设备仍为 013 identity `e8bbe74ff`，不能向设备发送新能力并假设支持。没有新增 synthetic-input 设备 PASS、physical-input 或 visual PASS。USB API 不能检测线缆连接但主机串口关闭，Driver 仍需显式 release；轨迹期限限制遗留输入。

Shell 重建后清理仍直接调用 Display 的幂等解除接口，不仅依赖 Shell 标志。最终固件编译、链接与分区检查通过；012/03 承接真实 Driver 编排、最终快照和日志证据，不以 ACK 判 PASS。

## 最终固件

- ESP-IDF 6.0.1 完整构建通过；最终日志 `/private/tmp/espocket-night-touch-owner-cleanup-build.log`。
- App 大小 `0x5d62a0`，分区剩余 43%。
- BIN SHA-256：`6675c941d0b50be4b2165553ed0fe8048a280ff2ee4edbe15cb69a33dca62040`。
- ELF SHA-256：`3501d6577978f5268fe93ba4a46c37c4c086150ca9de7b5a2a5fc47c831b0d87`。
- 先前两次构建也通过；后续 token 与显式 override 清理修正已在上述最终构建重新验证。只以上述 hash 对应最终提交源码，不以较早镜像冒充最终结果。
- 未刷写，未 push；设备仍保留 013 镜像。
