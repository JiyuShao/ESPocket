# 03 — 主机 Driver 与证据分类

**What to build:** 可重复运行的 USB 主机 Driver，按协议发刺激、等待快照、保存镜像和设备 identity，并区分合成、物理与视觉证据。

**Blocked by:** [02 共享输入与快照](02-shared-input-and-snapshot.md)（已完成）。

**Status:** ready-for-human

- [x] 失败和超时先执行 `release`，再采集最终快照及日志；重试作为新 attempt 保留原失败。
- [x] 用例断言等待快照序号和目标状态，不以固定 sleep 或成功投递响应判 PASS。
- [x] 报告明确 `synthetic-input` 不满足触摸硬件、PWR GPIO 或画面门槛。
- [ ] 至少覆盖表盘到 Launcher/Card、子页面 Back、Root 无 Back、PWR Home 与息屏唤醒的自动化路径。

## Comments

- 2026-10-02：Driver、466px 输入 profile、快照断言与错误清理已实现；30 项主机 unittest、M2 parser、Markdown 和固件增量构建通过。真实协议响应测试覆盖 ACK 不代表页面成功、busy、错误不重试、序号停滞、最终清理失败、设备错误日志与独立 attempt。没有将假 transport 输出算成设备 PASS。
- 自动化路径已编排 Launcher、Card、Quick Settings、Native Detail/Back、Root 无 Back、PWR Home/息屏/唤醒；坐标由当前资源推导，尚未在设备运行。设备仍保留 013 smoke 镜像，新 capability 尚未刷入，因此最后一项保持未勾选；早晨完成 013 单次 smoke 后统一安排镜像和一次 Driver 路径，无需重复十轮手动检查。证据见 [Driver 记录](../records/2026-10-02-host-driver.md)。

## 待验收

1. 收到既有 013 smoke 结果后，按统一安排刷入具有本票输入 capability 的明确镜像；开启设备开发者模式并核对 hello identity。
2. 对单个设备清单 ID 跑一次 Driver，保留独立 attempt 的 report 与原始 serial.log。全部步骤及最终 cleanup/快照符合预期才勾选最后一项。
3. 若坐标、状态或日志失败，保留失败 attempt；调整实现/profile 后作为新 attempt，不覆盖原结果。合成结果不勾选任何物理或视觉条件。
