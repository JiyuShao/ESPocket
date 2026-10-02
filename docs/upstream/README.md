# Upstream Tracking

本目录记录 ESPocket 的锁定上游源码核查与无法在产品层诚实规避的 Brookesia 上游问题。

## 当前入口

- [2026-09-28 上游状态核查](status-2026-09-28.md)
- [2026-09-29 AI Native 本地源码快照](ai-native-local-baseline-2026-09-29.md)
- [2026-09-29 Runtime package trust 本地源码快照](package-trust-local-baseline-2026-09-29.md)
- [2026-10-02 Settings 与 Store GUI 本地源码快照](settings-store-gui-local-baseline-2026-10-02.md)
- [Runtime JS 异步 GUI 栈溢出最小复现](issues/runtime-js-async-stack-overflow.md)
- [HTTP CancelRequest/TLS handshake race Issue 草稿](issues/http-cancel-race.md)

## 边界

- `status-*.md` 是特定日期的版本与公开仓库核查快照，不代表持续同步。
- `*-local-baseline-*.md` 是特定日期对本地依赖锁与源码的只读核对，不代表架构实现或阶段验收。
- `issues/` 保存可提交给上游的最小复现说明和脱敏附件。
- 产品侧 containment、验收状态和剩余风险记录在 [.scratch](../../.scratch/README.md) 对应的 Spec、ticket 与 records 中。
- 发现上游修复后，先更新状态核查，再在独立构建和所需真机验收通过后关闭对应 ticket。
