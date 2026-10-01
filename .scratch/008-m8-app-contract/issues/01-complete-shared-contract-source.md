# 01 — 既有 Native/Runtime 共享契约源码基线

**What to build:** 保存已提前完成的 Hello Native/Runtime 共享源码、Toolkit 与 staging 基线；新 Navigator 和 Root 无 Back 绑定由 [014/04](../../014-app-navigation-card-contract/issues/04-samples-api-finalization.md) 负责。

**Blocked by:** [003/01 Runtime 构建与 staging](../../003-m3-runtime-app/issues/01-build-and-stage-runtime-package.md)（已完成）。

**Status:** resolved

- [x] Host build、Toolkit、staging 与 static check 通过。
- [x] 两种 App 都提供必需 Root/Detail path。
- [x] 产品文档记录共享契约。

## Resolution

既有源码基线已经提前完成。该终态不证明 2026-10-01 ADR-0011 后的新 Navigator、Root 无 Back 或待决 Back 已绑定到 Runtime；后续实现归 014/04，真实交互证据归 [03](03-run-app-contract-hardware-acceptance.md)。
