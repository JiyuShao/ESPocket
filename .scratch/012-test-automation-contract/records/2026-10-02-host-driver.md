# USB 主机 Driver 与验收边界

- 日期：2026-10-02
- Ticket：[012/03](../issues/03-host-driver-evidence.md)
- 固件源码基线：`65f8302`，本 slice 只新增 Driver、profile、测试与文档。

## 实现

[Driver](../../../scripts/firmware/interaction_driver.py) 严格比对指定镜像 identity 并要求当前协议能力；设备 ID 来自操作者清单，报告明确标记来源。不会自动刷写、重启或开模式。

刺激 ACK 后等待至少两个新序号、目标匹配且 inputBusy=false 的快照。Root 无 Back 还逐样本观察有限窗口。协议错误不自动重试；非前台页面、序号停止/倒退、设备 panic/tick/清理错误均失败。每次成功或失败先 release，再取最终 snapshot 并收集尾部日志；失败的 release、仍忙碌或设备错误不能判 PASS。

每次 CLI 建立新 UUID attempt 目录，保留 report.json 和 serial.log；同一个 Driver 实例不能复用 attempt。报告包括镜像、设备清单 ID、协议版本、坐标 profile、各步骤与快照、失败和最终清理。所有结果标记 synthetic-input，physicalInputVerified/visualVerified 恒为 false。

[466px profile](../../../scripts/firmware/interaction-profile-466.json) 由当前 Shell/Native GUI 资源推导，标注尚未设备验证；手势起点尽量避开当前按钮，tap 只点 Native 和 Open Detail。编排覆盖 Watch Face→Launcher→Home、Brightness Card→Home、Quick Settings→Home、Native Root→Detail→Edge Back→Root、Root Edge Back 不返回、PWR Home/息屏/唤醒。profile 不是导航事实 Owner。

## 自动检查

- 真实 Python Driver 配合可控响应 transport 验证：ACK/busy 不能满足目标状态；无目标变化必须超时；错误不可自动重试；序号停滞及布尔类型错误；失败后 release→snapshot 顺序；release 失败仍采最终状态；镜像不匹配不发刺激；Root no Back 的瞬时违反；旧响应/普通日志不冒充当前响应；设备错误与尾部 panic 不判 PASS；partial write 失败；每次 attempt 新身份。
- 套件编排检查核对上述 Owner 断言和路径存在；不模拟产品导航，也不把可控响应输出保存为设备结果。
- `python3 scripts/check.py`：30 项 unittest、M2 parser、Markdown 通过。
- `python3 -B scripts/firmware/interaction_driver.py --help` 正常，不需要串口或 pyserial 导入。
- ESP-IDF 6.0.1 增量构建、分区检查通过；没有修改生产固件，最终镜像与 012/02 相同。日志 `/private/tmp/espocket-night-driver-build.log`。
- BIN SHA-256：`6675c941d0b50be4b2165553ed0fe8048a280ff2ee4edbe15cb69a33dca62040`；ELF SHA-256：`3501d6577978f5268fe93ba4a46c37c4c086150ca9de7b5a2a5fc47c831b0d87`。App `0x5d62a0`，剩余 43%。该镜像 hello identity 为 `3501d6577`。

## 尚未设备验收

没有连接 Driver 执行新能力，没有刷写，设备仍是 013 identity `e8bbe74ff`。012/03 保留最后一项并标记 ready-for-human；不是整票或 012 Spec 完成。先保留已有单次 013 smoke，再统一安排新镜像的一次自动套件运行，失败保留 attempt。

本记录没有真实设备 PASS 报告，不满足触摸硬件、PWR GPIO 或视觉门槛；007/03、008/03 与 013 待验收条件不变。
