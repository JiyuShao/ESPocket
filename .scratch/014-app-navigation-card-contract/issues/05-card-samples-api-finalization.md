# 05 — App Card 样例与开发 API 定版

**What to build:** 在真实 Native、Runtime 样例上补齐 App Card 声明、目标 Page 打开和呈现生命周期，并发布对应 Card schema 与语言 API。

**Blocked by:** [03 Card 注册与生命周期](03-card-registry-lifecycle.md)；[04 Native/Runtime 导航绑定](04-samples-api-finalization.md)。

**Status:** ready-for-agent

- [ ] 两种样例均覆盖 Card 打开 Root/目标 Page，目标栈以 Root 为底，PWR Home 后再次打开从 Root 开始。
- [ ] Card ID/目标 Page 失效时降级、配置迁移、错误诊断与 API 错误结果一致。
- [ ] Card 可见、离屏和再次可见的数据请求及生命周期通过组件验证；真实显示与触控至少覆盖对应目标打开和暂停路径。
- [ ] C++ 与 Runtime Card API、版本化声明 schema 和作者职责写入 [开发契约](../../../docs/development/app-navigation-card-api.md)，不修改 Brookesia 的产品无关公开契约。
- [ ] 记录样例与固件/package identity、构建结果和独立真机证据；导航通用证据引用 [008/03](../../008-m8-app-contract/issues/03-run-app-contract-hardware-acceptance.md)，不重新建立一套重复导航验收。

## Comments

- 2026-10-02：由原 ticket 04 的 Card 部分拆出。该拆分只改变任务归属，保留 Native/Runtime Card 样例与 API 的原要求。
