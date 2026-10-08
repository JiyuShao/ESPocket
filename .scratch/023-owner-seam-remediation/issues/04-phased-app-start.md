# 04 — Core 分阶段启动

**What to build:** 原 Core 持有启动进度与取消／失败回滚，GUI 等待释放 App Owner；明确单阶段阻塞与 250ms 尚未完成。

**Blocked by:** 真机验收需设备返回。单个阻塞阶段的耗时治理与 250ms 门槛仍待解决。

**Status:** ready-for-agent

## Acceptance

- [ ] 单个阻塞阶段耗时治理完成，启动期间顶部下拉与 PWR 响应达到 250ms。

- [x] 实现与有意义主机回归通过。
- [x] 固件主机检查、Markdown 和完整产品构建通过（统一命令的文档失败已单独复查修复）。
- [ ] 真机对应视觉／性能／电源／启动响应验收完成。

## Comments

真机未验证时保持开放；离线 evidence 另写入 records。

[离线结果与未验证条件](../records/2026-10-08-offline-remediation.md)。

2026-10-08 后续治理：真实 Chat on_start 在注入 500ms Agent 查询时同步占用 App Owner 500ms；已建立并运行失败回归。Agent discovery、网络探测与启动前 Agent 配置改为现有 async bridge，并按 Running Instance epoch 撤销旧结果。Core 各启动阶段补可开启的 Owner 占用诊断，GUI prepare 复用既有分步骤 profile。服务绑定、本地配置读取、GUI parse 与其他 App callback 仍待真实耗时治理，250ms 验收不关闭。

[启动阻塞治理与回归证据](../records/2026-10-08-startup-responsiveness.md)。

2026-10-08 继续治理：Chat 0.1.5 的配置／Coze 私钥慢读已有红灯复现，现改为原 StorageRead async bridge。剩余服务绑定的慢调用复现仍失败，Runtime 与 GUI 锁的同步路径已核对；后续按真实 Owner 治理 pending bind 清理和 GUI／Runtime prepare，不能关闭 250ms 条件。见[路径审计与配置读取证据](../records/2026-10-08-startup-storage.md)。

2026-10-08 审查收敛：同步与分阶段启动共用私有阶段操作和失败分类，developer-mode 提示一致性由修复前失败、修复后通过的真实入口回归验证。服务绑定与 GUI／Runtime 阻塞仍开放；见[共享实现证据](../records/2026-10-08-core-start-sharing.md)。
