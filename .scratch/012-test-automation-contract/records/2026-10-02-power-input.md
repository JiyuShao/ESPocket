# USB 合成 PWR 排队证据

- 日期：2026-10-02
- Ticket：[012/02](../issues/02-shared-input-and-snapshot.md)
- 范围：PWR 输入源码、协议与主机组件；触摸仍未接入。

## 实现与验证

USB `stimulus.powerShort` 仅排队；System 在原有输入任务中调用同一个 `handle_power_short_press`，不会在 USB worker 执行 App 停止或 GUI 导航。物理与合成短按同 tick 合并一次；报告不覆盖 GPIO。

真实 `PowerInputQueue` 与 `TestProtocol` 的 C++ 用例验证：ACK 不执行 Owner、排队时新刺激 busy、snapshot 的 inputBusy、重复 release 安全、期限前保留/1000 ms 到期取消、不执行迟到输入、恰好一次消费，以及执行中 release 不释放槽位/不接收新刺激。开发者模式关闭时不得入队。

Adapter 在物理断连、响应写失败、关闭模式和停止时取消待执行 PWR；正在执行的 Owner 调用不能撤销。USB 物理连接检测不能发现主机仅关闭串口，Driver 仍需显式 release，排队期限提供迟到输入保护。尚无触摸注入，因此不宣称所有输入的断连清理完成。

- `python3 scripts/check.py`：17 项 unittest、M2 parser、Markdown 通过。
- ESP-IDF 6.0.1 完整构建、链接与分区检查通过，日志 `/private/tmp/espocket-night-power-input-build.log`。
- App 大小 `0x5d3310`，分区剩余 43%。
- BIN SHA-256：`34bfc60bc70a63440e5ee9bb7954c50b8d61a7d636e028be4394a5a96b5e8801`。
- ELF SHA-256：`d77b1932f293ddebb103697f49e1cb38495789730cce539caf3944fe8b035270`。

未刷写。设备仍保留 013 镜像 identity `e8bbe74ff`，其 hello 不支持本次新能力；新源码能力不等于设备能力，也没有新增 synthetic-input 真机、physical-input 或 visual PASS。
