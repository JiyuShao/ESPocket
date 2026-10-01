# 03 — 执行 M6 hardware acceptance

**What to build:** 为固定 Home、PWR、Screen Off、resume 与 fallback path 取得真机 evidence。

**Blocked by:** 02 — 增加可控 reclaim fallback seam。

**Status:** resolved

- [x] 四条必需路径各自恰好通过 5 次。
- [x] Touch-off、Overlay、BOOT 与 long-press 检查通过。
- [x] 串口与物理观察中无 fatal signal。

## 当前证据与剩余工作

2026-10-01：四条固定路径和四项单项检查已通过；普通镜像离线 Store 停留约 110 秒并用 PWR 退出，未见 fatal signal。见 [M6 验收](../../../docs/milestones/m6/acceptance.md)及[Store 定向复测](../../../docs/milestones/m6/records/2026-10-01-store-failure-rescan.md)。当时尚缺跨重复操作的资源趋势证据。在线 Store 稳定性归 M5，不是本 ticket 的关闭条件。

## Resolution

2026-10-02：用户完成 10 轮 Native Detail → PWR Home/Off/Wake，屏幕顺序均正确；同状态资源诊断在第 2、4、7、8、10 检查点采到四项指标，首末变化为 `0 / +28 / 0 / 0 B`，无持续下降或 fatal signal。诊断后已刷回普通镜像并确认表盘正常。见[资源趋势记录](../../../docs/milestones/m6/records/2026-10-02-resource-trend.md)。M6 全部门槛通过。
