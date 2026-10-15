# BLE 遥控能力与 Native App（2026-10-15）

## 结果

- 核实锁定版 BLE HAL：`PeripheralIface` 是通用单连接 GATT Server，characteristic 只有 write/write-without-response/notify；它不表示标准 HID Device。
- 新增 `espocket_hid`：`MouseReport`、boot mouse 四字节编码、Endpoint 生命周期和明确错误状态。报告在编码边界限幅到 HID 相对值 `[-127,127]`。
- 新增 `espocket.app.ble_remote`：触控板内圈移动、外圈滚轮、点击，以及空中鼠标 IMU 控制与触摸降级；取消、暂停、断连和停止都会清理按键与输入状态。
- 当前 `create_board_endpoint()` 返回 `UnavailableEndpoint`。没有标准 HID Owner 时，App 只展示不可用状态，不会把报告写入普通 GATT notification，也不会启动第二套 Bluetooth 栈。

## 验证

- `firmware/components/espocket_hid/test/test_mouse_model.py`：3 项通过，覆盖报告限幅、触控板点击/拖动/滚轮、IMU 样本和断连丢弃。
- 真实 HID Report Map、配对、主机重连、连接间隔、macOS/Windows 行为和 Wi-Fi 共存仍由 [05](../issues/05-ble-hid-capability.md)、[07](../issues/07-native-ble-remote.md)、[09](../issues/09-device-acceptance.md) 负责。
