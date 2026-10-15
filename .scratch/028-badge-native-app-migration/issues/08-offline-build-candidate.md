# 08 — 离线回归与隔离构建候选

**What to build:** 为七个 Native App 与必要能力产出源码输入可追溯、host 检查通过的隔离构建候选。

**Blocked by:** [03](03-system-lifecycle-and-activity.md)、[04](04-imu-capability.md)、[05](05-ble-hid-capability.md)、[06](06-native-games-and-toys.md)、[07](07-native-ble-remote.md) 离线实现完成；来源与公共接入清单由 [02](02-source-and-gui-boundary.md) 持有。

**Status:** ready-for-agent

- [ ] 运行统一 firmware 与 Markdown 检查，修复本次变更导致的失败；覆盖既有 Native/Runtime App 与系统恢复关键路径。
- [ ] 使用现有隔离候选流程，记录完整源码 identity、上游来源、锁文件、补丁 hash、配置与产物摘要；准确应用补丁，原始 managed_components 不修改。
- [ ] 完整构建确认固件/资源适配现有分区与限制，记录尺寸变化、编译问题及未验证项，不通过复制原项目分区回避空间不足。
- [ ] 可用的 host/simulator 仅用于玩法与 UI 离线检查，模拟 IMU 和传输报告不计真实传感器、配对或实际电脑输入验收。
- [ ] 在 records 保存可读结果与候选身份，原始日志按仓库规则保存在本地/CI artifact；不刷写、不配对、不发送实际 HID 输入。
- [ ] 将设备 gate 保留在 [09](09-device-acceptance.md)，本票完成只表示构建候选可供测试，不表示迁移 Effort 已完成。

## Comments

2026-10-09：用户设备不在身边，本票覆盖能独立完成的离线交付。

2026-10-13：泡泡纸、打砖块、弹球与水池的阶段候选和回归见 [水池记录](../records/2026-10-13-water-touch.md)及其历史链接。本票仍未关闭：太阳系、重力迷宫、IMU、BLE HID 与蓝牙遥控尚未完成，阶段候选不代表七 App 的统一门槛已满足。

2026-10-14：太阳系阶段候选已完整构建，并通过最终统一检查、生产回归、sanitizer 和产物/输入校验，见 [本批记录](../records/2026-10-14-orbit-native.md)。太阳系离线实现已完成；本票仍等待重力迷宫、IMU、BLE HID、蓝牙遥控及统一最终候选，不以阶段候选关闭总体门槛。

2026-10-15：纳入重力迷宫触摸版及遥控离线页面的构建过程见 [HID Owner 核查与阶段构建记录](../records/2026-10-15-hid-owner-integration.md)。IMU/HID backend 与遥控交互尚有代码缺口；即使阶段构建通过，也不关闭本票的完整实现门槛。

2026-10-15：最终 v3 阶段候选完整构建通过，277 tests 及两个跳过项的独立补跑通过；115 份归档大小/hash、冻结输入及 147 个相关源码文件已复核。固件 12,445,008 bytes，App 分区余量 15%。候选仍关闭 Bluetooth，不能替代 04/05/07 的实现门槛；本票保持未关闭，未部署且未获物理证据。
