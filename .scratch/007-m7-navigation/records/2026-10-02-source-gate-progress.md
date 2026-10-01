# M7 source gate 进展（2026-10-02）

- 已刷入 App 镜像 SHA-256：`45d55827dc910baa6472af7611439f4432fba6aa343a7db61dbbb087b4a2841f`
- 构建：`firmware/build/manual-clean-abs`，ESP-IDF 整机构建完成。
- 写入：仅 App 分区 `0x60000`；esptool 报告 `Hash of data verified`。
- 启动串口：`/private/tmp/espocket-m7-source-gate-boot.log`；观察到 `Hello Native installed`、`Circular Shell started`、`ESPocket started`，未检出 panic、assert 或 watchdog。

## 源码检查

- Brightness Card 和 Quick Settings 使用 System 选定的真实 Display output。Wi-Fi 使用已绑定的服务。操作失败返回错误，由 System Core 记录；原控件同时显示 `unavailable`，不继续显示可能过期的成功状态。
- Home Space 反向手势、Launcher 顶部下拉仅在无前台 App 时产生系统导航意图；Edge Back 仅在前台 App 允许 Back 的子页面启用。Root 不响应 Edge Back。
- `PageNavigator` 公开接口主机测试通过；Shell Action 唯一性检查和 `git diff --check` 通过。没有引入通用 Card SDK 或跨 App history stack。

## 限制

- [默认 Back 真机样机](../../014-app-navigation-card-contract/records/2026-10-02-default-back-prototype.md)覆盖 Native Hello 的 Root/Detail、可见 Back、Edge Back 和 PWR Home；触控时的镜像早于本次失败文案改动。用户已要求缩减重复真机验证，因此本镜像只做自动启动检查。
- Settings 与 Store 尚未接入共同 Navigator。M7 默认 Back source gate 不关闭；失败文案路径也未通过故意断开服务的真机注入测试。
- 随后补充了 Card 目标失效的统一诊断回调；主机测试与整机构建通过，后续源码镜像 SHA-256 为 `c6e6e0fa0556d7b72ce537ace7d658a5b8d1321dbcac8eb6294788e5ee93a736`。该镜像尚未刷入，设备仍运行上方已刷入镜像；Card 动态入口尚未启用。
