# 04 — Native/Runtime 导航绑定与开发 API 定版

**What to build:** 将真实 Native 与 Runtime 样例接到共同 Navigator/Back 分发，发布可调用的语言绑定及版本化 Page 声明 schema。

**Blocked by:** [01 Page Navigator](01-page-declaration-navigator.md)；[02 Back 分发](02-back-dispatch.md)；[003/01 Runtime 构建与 staging](../../003-m3-runtime-app/issues/01-build-and-stage-runtime-package.md)（已完成）。

**Status:** ready-for-agent

- [ ] Native 与 Runtime 样例具备 Root → Detail → Back → Root、Root 无 Back、PWR Home 和待决 Back 的可控路径。
- [ ] Runtime Adapter 使用 ticket 01 的共同 Navigator；对声明、push/pop/replace/resetToRoot、快照和错误给出与 Native 相同的产品语义。
- [ ] C++ 与 Runtime API 明确线程、参数编码、错误枚举和 Back 超时时长，并链接产品与架构权威文档。
- [ ] 对相同声明、导航操作、重复/超时 Back、PWR token 失效与呈现失败，两种 Adapter 的组件验证得到相同结果。
- [ ] 当前 Native 固件与真实 Runtime package 的 clean build/link/staging 通过；不将旧 Root Back 模型的构建结果算作新绑定验证。
- [ ] 开发指导覆盖信息型、控制型、列表型和工具型页面，以及圆屏中部优先、单列列表、避免手机式 Bottom Navigation、不依赖后台驻留。

## 验证边界

真机触控、PWR、息屏恢复和回收证据由 [008/03 App 交互验收](../../008-m8-app-contract/issues/03-run-app-contract-hardware-acceptance.md) 承接。本票负责绑定与组件/构建条件；App Card 目标页面和 Card API 样例由 [05](05-card-samples-api-finalization.md) 承接。

## Comments

- 2026-10-02：原 ticket 同时要求 Native/Runtime Page/Back 与 Card 样例，且依赖 Card 生命周期 ticket 03。迁移后 Card 部分拆至新 ticket 05；本票只依赖 Navigator 与 Back，实现 Runtime 导航无需等待 Card 机制。没有把任何待验收路径标记为通过。
