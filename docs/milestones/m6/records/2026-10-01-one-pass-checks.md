# M6 单项真机检查（2026-10-01）

## 对象

- 设备：ESP32-S3，USB 串口 `/dev/cu.usbmodem101`。
- 普通固件 App SHA-256：`786f618a56015fb714474e1b6b3a062611ee1f29313875e4a33715ed219cb9ab`；回收测试开关关闭。

## Screen Off touch

用户进入 Native Detail，等待自动息屏后触摸原本的 Back/Detail 控件位置，再短按 PWR。用户确认亮屏仍为 Native Detail。串口依次记录 `M6 display state: Off`（uptime 97447 ms）、`On` 和 `Wake`（106426 ms）；其间监听到的页面事件没有 Back 或其他转换。该单项检查 PASS。

## BOOT

[Waveshare 官方文档](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75C)确认该板有 PWR 与 BOOT 两颗侧边键。第一次试按后页面回表盘，串口同步记录 `PWR short press duration=200ms` 和 App 停止；用户当时不能区分两颗键，因此这次不能判作 BOOT 失败。随后让用户在 Native Detail 亮屏时按另一颗侧边键：用户确认屏幕无变化，监听窗口未记录该动作对应的 PWR 或页面转换，之后仅出现正常自动息屏。以两颗实体键的对照识别另一颗为 BOOT，该单项检查 PASS。

## PWR long press

用户在屏幕亮起时长按已识别的 PWR，报告 2–3 秒按压没有可见反应。串口记录 `PWR long press left to hardware duration=1440ms` 与 `duration=2600ms`，没有将这些事件报作短按 Home。随后用户将 PWR 按住约 6 秒，确认设备关机；串口设备同步消失。短按 PWR 后串口重新连接并记录 `ESPocket started`，用户确认首次亮屏为表盘。长按没有执行 App Home/Back 导航，硬件关机和重新开机均得到物理与串口对应，该单项检查 PASS。

## Overlay + PWR

用户在 Settings → Wi-Fi 的密码页打开系统键盘，串口记录 `System keyboard opened`（uptime 124879 ms）。短按 PWR 后，串口依次记录 `PWR short press`、`System keyboard closed`、Settings App 停止；用户确认直接回到表盘。再次打开同一密码键盘，输入无意义测试文本但不确认，然后短按 PWR；串口再次记录键盘关闭和 Settings 停止。重新进入同一网络的密码页后，用户确认测试文本未保留，也没有发起连接。该单项检查 PASS。

Failure scan 仍按[验收规范](../acceptance.md)单独判定。
