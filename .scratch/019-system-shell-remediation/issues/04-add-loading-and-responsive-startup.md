# 04 — 增加 Loading 并验证启动期间 PWR

**What to build:** 实现 INT-033–034 的启动等待/App 主动等待反馈，保持 App 启动期间有效 PWR 短按识别后至 Watch Face 不超过 250 ms。

**Blocked by:** [01 失败清理](01-close-initialization-cleanup-gaps.md)；[03 Overlay 仲裁](03-arbitrate-overlay-input-and-deadlines.md)。

**Status:** ready-for-agent

- [ ] 接入锁定 Core 的 App loading seam，覆盖启动成功/失败与 App 主动等待；反馈不改变请求 Owner。
- [ ] 对齐 Super 实际 Startup overlay 和 Shell launch overlay/图标动画，完成圆屏资源与缺图标回退；不因 Core launch transition 被关闭而遗漏 Super 自有启动链路。
- [ ] 检查同步启动与 PWR 消费的真实执行路径，在 Owner 边界解决阻塞；只增加 Loading UI 不构成完成。
- [ ] 具体操作的进度、超时、取消和结果由实际 Owner 定义；Home 后已提交操作的迟到结果不恢复前台或作出虚假取消结论。
- [ ] 在慢 Native/Runtime 启动、失败启动与输入竞争中记录 PWR 识别时刻和 Watch Face 到达时刻，各场景三次测量均满足 250 ms，保留实际值与失败。
- [ ] 统一检查、独立完整构建及真实 PWR/显示验收通过；Loading 的显示与退出分别有证据。

## Execution Notes

250 ms 起点是短按已被识别，不能把按钮按下时间混入同一指标；同时记录识别耗时以免隐藏输入阻塞。测试注入只在测试入口，不能留在普通产品行为中。

## Comments

2026-10-04：隔离副本完成 Core App Loading seam 和启动/主动等待的兼容反馈；同步 startup/PWR 阻塞已核实，250 ms 无测量且尚未解决。Super Startup 与 Shell launch/icon 动画尚未迁移；01、03 前置没有关闭。详见[隔离实施记录](../records/2026-10-04-overlay-isolated-implementation.md)。本票保持未完成。


2026-10-05：隔离交付已三方整合入当前 checkout；新增 Core 补丁按当前组合重新准确应用，整合中两处空 Overlay 重试回归已修复。联合 host checks、构建和设备结果见[联合整合记录](../records/2026-10-05-joint-integration.md)。此前隔离阶段记录保留；本票未满足的条件继续开放。
