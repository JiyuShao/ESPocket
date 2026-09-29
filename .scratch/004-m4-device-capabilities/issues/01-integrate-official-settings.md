# 01 — 在圆形目标设备集成官方 Settings

**What to build:** 通过 ESPocket System 安装官方 Settings 与必需 Service，stage 所需资源，并提供可用的 466×466 layout。

**Blocked by:** M3 `PASS`.

**Status:** retrospective-resolved

- [x] 准确的 Settings 与 Audio dependency 可解析并构建。
- [x] 资源按上游原样 stage。
- [x] Settings 在真机上启动、render 并返回 Home。

## Resolution

M4 已接受；未引入私有 Settings framework 或 managed-component patch。
