# 05 — App Card 样例与开发 API 定版

**What to build:** 在真实 Native、Runtime 样例上补齐 App Card 声明、目标 Page 打开和呈现生命周期，并发布对应 Card schema 与语言 API。

**Blocked by:** [03 Card 注册与生命周期](03-card-registry-lifecycle.md)；[04 Native/Runtime 导航绑定](04-samples-api-finalization.md)。

**Status:** ready-for-human

- [ ] 两种样例均覆盖 Card 打开 Root/目标 Page，目标栈以 Root 为底，PWR Home 后再次打开从 Root 开始。
- [ ] Card ID/目标 Page 失效时降级、配置迁移、错误诊断与 API 错误结果一致。
- [ ] Card 可见、离屏和再次可见的数据请求及生命周期通过组件验证；真实显示与触控至少覆盖对应目标打开和暂停路径。
- [x] C++ 与 Runtime Card API、版本化声明 schema 和作者职责写入 [开发契约](../../../docs/development/app-navigation-card-api.md)，不修改 Brookesia 的产品无关公开契约。
- [ ] 记录样例与固件/package identity、构建结果和独立真机证据；导航通用证据引用 [008/03](../../008-m8-app-contract/issues/03-run-app-contract-hardware-acceptance.md)，不重新建立一套重复导航验收。

## Comments

- 2026-10-02：由原 ticket 04 的 Card 部分拆出。该拆分只改变任务归属，保留 Native/Runtime Card 样例与 API 的原要求。

- 2026-10-02：Native summary/detail Card 工厂和独立 GUI 文档已作为框架接入 slice 实现，整票不关闭。Runtime Card 需要明确声明式首版范围，或上游提供隔离执行实例 seam；已提出范围选择，未收到回答前不擅自缩小可执行回调要求。03 的 package update 条件、双方实际触控/暂停与镜像证据仍保留。见 [Card 接入记录](../records/2026-10-02-card-owner-presentation.md)。

- 2026-10-02（范围答复）：用户接受声明式 Runtime Card 首版并要求继续。按 ADR-0014 实现版本化 cards.json、真实安装校验/模型工厂与 Core 元数据刷新；不创建独立 JS 实例，不支持 JS 业务回调。API/schema 作者边界已明确，package 更新事务与硬件条件保持开放。

- 2026-10-02（实施）：声明式 Runtime Card、实际安装模型工厂、两张参考 Card、默认关闭的 RAM 样例入口及组件检查已实现。见 [首版实施证据](../records/2026-10-02-declarative-runtime-card.md)；迁移事务和真机条件仍开放。
