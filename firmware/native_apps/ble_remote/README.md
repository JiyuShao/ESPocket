# 蓝牙遥控

蓝牙遥控 Native App 复用了既有 Native Content 和受控多点输入，提供触控板与空中鼠标两种模式：触控板内圈发送相对移动，外圈发送滚轮，点击发送左键；空中鼠标消费 IMU 加速度，并保留触摸点击降级。

当前 ESPocket 的 BLE HAL 是通用 GATT Peripheral。它尚未公开标准 HID Device 的 Report Map、Report Reference、HID Control Point 和配对/键盘鼠标报告 Owner，因此 `espocket_hid::create_board_endpoint()` 明确返回 `unavailable`。App 不把鼠标报告伪装成 GATT notification，也不在 App 内初始化第二套蓝牙栈。真实 HID endpoint 接入后，可以替换该 factory 而不改变玩法状态机。

Host tests 覆盖 boot mouse 四字节报告编码、±127 限幅、触控板点击/拖动/滚轮、空中鼠标样本和断连清理。配对、Report Map 被 macOS/Windows 接受、连接间隔、延迟、Wi-Fi 共存和真实 IMU 轴向仍属于 [028/09](../../../.scratch/028-badge-native-app-migration/issues/09-device-acceptance.md)。
