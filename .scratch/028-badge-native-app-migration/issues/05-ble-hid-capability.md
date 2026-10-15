# 05 — 接入 BLE HID 与配对资源所有权

**What to build:** 在既有 Bluetooth/BLE HAL 与 Service Owner 内提供完整鼠标 HID、连接与配对能力，不在 App 内创建第二个蓝牙栈。

**Blocked by:** [02 官方 HID 与接口核查](02-source-and-gui-boundary.md)。

**Status:** ready-for-agent

- [x] 完整核实鼠标 HID service、read/report map、report reference/descriptor、安全配对、输入报告和订阅等需求；现有 notify API 不能作为协议完整的证明。
- [ ] 复用既有蓝牙 host/资源管理，对所缺公开能力提出最小扩展并落在真实 Owner；连接、bond、订阅、停止与迟到完成只有一个事实源。
- [ ] 支持首轮手动配对、后续打开 App 或恢复原实例时的有界重连尝试。正确区分设备广播与电脑发起连接，不承诺 Peripheral 可以强行连接电脑。
- [ ] 主机切换/断连前处理持有鼠标状态；失联时明确报告结果，不虚称释放报告已到达电脑。停止实例后无继续发送或复用旧会话。
- [ ] 公开主机身份、连接、配对和灵敏度存储所需的稳定边界；忘记配对经 App 明确入口/确认，不暴露给 AI。
- [ ] 保留既有 Wi-Fi/聊天资源与单一无线 Owner，禁止复制原作关闭系统 Wi-Fi 的策略；启动失败和资源不足可诊断且不阻塞 UI。
- [ ] host 验证协议构造、报告范围、释放/断连、取消、迟到回调及连接失败；macOS/Windows 配对、延迟和共存只在 [09](09-device-acceptance.md) 验证。
- [ ] 必要上游改动按 ADR-0016 维护，运行 firmware 检查并记录 seam。

## Comments

2026-10-09：现有 BLE characteristic 只表达 write/write_without_response/notify，完整 HID 能力尚未实现；源码初查不能关闭本票。

2026-10-15：已核实当前 `PeripheralIface`/NimBLE backend 只生成通用 GATT characteristic，未公开 HID Report Map、Report Reference、HID Control Point 或标准 HID Owner。新增 `espocket_hid` 只承载报告编码和 Endpoint 生命周期契约；生产 factory 明确返回 `unavailable`，没有把 GATT notification 冒充鼠标 HID。真实标准 HID Owner 仍待平台能力补齐，见 [BLE 遥控 README](../../../firmware/native_apps/ble_remote/README.md)。

实现记录：[2026-10-15 BLE 遥控能力与 Native App](../records/2026-10-15-ble-remote-contract.md)。

2026-10-15：补齐 [HID Owner 接入核查与最小扩展提案](../records/2026-10-15-hid-owner-integration.md)。ESP-IDF 支持 NimBLE HID Device，但与现有 backend 直接组合会覆盖全局回调并互相清理 GATT；host coordinator 只有引用计数，不能消除此冲突。现有 backend 还关闭 bonding/SC，缺少安全与主机身份接口。协议需求核查已完成；平台 profile、配对与真实 endpoint 尚未实现。修正 Report/Boot payload 为四/三字节，并补编码回归；不以此关闭本票。
