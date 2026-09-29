# 02 — 证明 keyboard、Wi-Fi 与 status capability

**What to build:** 通过官方接口工作的产品 keyboard，以及真实 Wi-Fi、time、battery、brightness 与 device-state path。

**Blocked by:** 01 — 在圆形目标设备集成官方 Settings。

**Status:** retrospective-resolved

- [x] Keyboard provider 按已确认的屏幕语义打开和关闭。
- [x] Wi-Fi 完成初始化、从 NVS 重连并到达 SNTP。
- [x] Brightness、Time、Battery 与 Device info 获得真机确认。

## Resolution

已接受的观察、关键数值和判定保存在 M4 record；原始构建与串口日志不长期保存在源码树。
