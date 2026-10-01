# 04 — Native/Runtime 样例与开发 API 定版

**What to build:** 在真实 Native、Runtime 样例上验证声明、导航、Back 和 Card 契约，并发布可调用的语言绑定及版本化声明 schema。

**Blocked by:** 01、02、03。

**Status:** ready-for-agent

- [ ] Native 与 Runtime 样例都覆盖 Root → Detail → Back → Root、Root 无 Back、Card 目标 Page 和 PWR Home。
- [ ] Runtime Adapter 接入 ticket 01 的共同 Navigator，并与 Native Adapter 对相同操作和错误给出相同产品语义。
- [ ] C++ 与 Runtime API 明确线程、参数编码、错误枚举和 Back 超时时长，并链接产品与架构权威文档。
- [ ] 同一行为的两个 Adapter 得到相同结果；不修改 Brookesia 的产品无关公开契约。
- [ ] 真机触控、PWR 和视觉行为按 M7/M8 门槛记录为独立证据，不用合成用例代替。
