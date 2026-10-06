# 02 — 完成全量停机与正常重复生命周期

**What to build:** 实现 OVR-012、OVR-014 与 LIF-007–008，停止所有受管 App/产品执行入口，同一 System 对象正常 stop→start、deinit→init 不复活旧状态。

**Blocked by:** [01 初始化与失败清理](01-close-initialization-cleanup-gaps.md)。

**Status:** ready-for-agent

- [ ] stop 覆盖前台、后台受管 App 和产品入口；deinit 释放实例、GUI、绑定和订阅，Service 按实际 Owner/binding 寿命处理。
- [ ] 停止先失效外部访问，处理在途 callback 与 GUI 等待，明确失败结果；清理不依赖 Shell 仍可接收任务。
- [ ] 同对象正常重复运行重新建立输入/请求/订阅关系；旧 Running Instance、句柄和迟到结果不能作用于新运行。
- [ ] 回归覆盖 Native/Runtime、后台 App、pending input/dialog 与重复循环；连续三轮各自 stop→start 和 deinit→init 记录资源及身份结果。
- [ ] 统一检查、独立完整构建和新增真机重复生命周期路径记录通过；引用已接受 Runtime 隔离证据并验证本次相关路径不回退。

## Execution Notes

不承诺关键启动失败后的原地重试。通用导航与 App 回收证据继续引用既有 007/008，不重复其全部矩阵。

## Isolated Candidate

2026-10-04：本线在隔离副本实施并验证源码候选，详见[候选记录](../records/2026-10-04-isolated-lifecycle-candidate.md)。状态和未勾选门槛保留；原 checkout 未整合、设备未操作，不以 host 结果代替 callback/视觉/真机重复生命周期证据。


2026-10-05：隔离交付已三方整合入当前 checkout；新增 Core 补丁按当前组合重新准确应用，整合中两处空 Overlay 重试回归已修复。联合 host checks、构建和设备结果见[联合整合记录](../records/2026-10-05-joint-integration.md)。此前隔离阶段记录保留；本票未满足的条件继续开放。
