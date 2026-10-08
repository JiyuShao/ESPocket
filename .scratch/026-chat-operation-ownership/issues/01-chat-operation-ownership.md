# 01 — App 异步操作归属

**What to build:** 集中 Chat App 内请求归属与等待状态，阻止失效回调写入当前界面。

**Blocked by:** None.

**Status:** resolved

## Acceptance

- [x] App 内实现五类操作归属；不增加平台模块，不取消底层操作。
- [x] 旧请求、A→B→A、重试与事件确认回归通过；当前失败仍可见。
- [x] 本地 0.1.6 包与源文件逐项校验通过。
- [x] 统一 host checks 与 Markdown 通过。
- [x] 全新隔离固件构建与候选归档通过。

## Comments

用户已同意实现。真机验收由 Spec 引用的 020 tickets 持有，本票仅交付离线实现与构建候选。

## Resolution

App 实现、包校验、全部 host 测试、修正后的 Markdown 检查和完整隔离构建通过。未刷机或提交代码。见[离线证据](../records/2026-10-08-offline-verification.md)。
