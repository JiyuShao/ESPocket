# 主题、渲染、电源与启动 Owner 整改

Sequence: 023

Status: active
Blocked by: 真机视觉、性能与启动响应待设备返回；单个阻塞启动阶段仍需耗时治理

## Problem Statement

022 审查发现 Chat 普通颜色固定、System 直接管理 LVGL decoder，以及按 Chat ID 决定常亮；启动 Loading 后同步等待也阻碍系统输入。用户批准分四步整改。

## Solution

主题资源和动态绑定留在 App；解码缓存行为回到 GUI backend；System 消费 Core 已验证的 App 常亮声明；Core 持有分阶段启动、取消和回滚，System 只发起请求并提供维护节拍。

## User Stories

1. Chat 支持产品两主题，导航选中态与文字配对。
2. System 通过窄接口配置缓存预算与读取统计，不依赖 decoder 私有结构。
3. 任一执行模型可声明前台常亮，退出实例后不保留豁免；显式 PWR 与 Home 不受影响。
4. 启动请求返回后继续处理输入，取消或失败不能晚提交 Running 或恢复旧页面。

## Implementation Decisions

- Chat 更新为 0.1.3，普通界面用已注册语义变量；保留 Runtime 包资源归属。
- GUI LVGL 008 持有全局 decoder/cache hook，配置前检查完整 decoder 集合，失败不部分替换，释放不覆盖较新的 Owner。
- Core 024 增加严格 bool `package.keep_screen_on`，缺省 false；由原包信任路径验证内容，不新增权限或安装通道。
- Core 025 请求启动进入原 AppRecord 的 pending phase；重复同实例请求幂等，其他并行请求拒绝。现有同步 start_app 接口保留。
- 同步与分阶段启动共用 Core 私有准入、Runtime start、lifecycle、Running 提交与 GUI／Runtime 清理操作；调度方式保留，准入失败统一沿用原操作提示。见[共享回归](records/2026-10-08-core-start-sharing.md)。
- GUI 准备使用真实 GUI task 与 future，Owner 非阻塞轮询；Runtime load/start 与 lifecycle 分不同节拍。App Record 在 GUI 完成前不得卸载或替换，取消先标记、回滚后完成；stop/deinit 必须 drain。
- Chat 0.1.4 将 Agent discovery、网络探测与启动前 Agent 配置改为原异步桥；按 Running Instance epoch 撤销旧结果。Core 可开启启动阶段 Owner 耗时日志，定位剩余同步阶段。
- Chat 0.1.5 进一步异步读取 AppData 配置与 Coze 私钥；剩余服务绑定、Runtime 和 GUI 同步路径的事实及处理方向见[路径审计](records/2026-10-08-startup-storage.md)。
- 单个阶段内同步包准入、Runtime/Native callback 和 GUI parse 仍不能被强行抢占。250ms 与长阶段的治理保持单独未完成，不能因分阶段关闭响应要求。

## Testing Decisions

- 两主题真实 GUI parser 与实际 JS refresh；原包 trust gate 对 missing/true/false/错误类型声明的回归。
- 真实 decoder policy 生命周期、容量拒绝、超预算、不足连续内存与统计 reset。
- 真实 Core 进度方法验证慢 GUI 等待、重复请求、取消／失败／回滚、重启与清理。
- 统一检查、Markdown、隔离构建及 BPK 逐成员匹配；真机视觉、性能、顶部手势与 PWR 响应另外验收。

## Out of Scope

- 不部署，不访问设备或改变 Store Catalog。
- 不新增 App manager、显示偏好缓存或第二套 trust gate。
- 不宣称任意阻塞 Native callback 可安全抢占。

## Tickets

- [01 — Chat 主题资源](issues/01-chat-theme.md)
- [02 — GUI 解码 Owner](issues/02-image-decoding-owner.md)
- [03 — 前台常亮声明](issues/03-foreground-screen-policy.md)
- [04 — Core 分阶段启动](issues/04-phased-app-start.md)

## Further Notes

- [2026-10-08 离线整改结果](records/2026-10-08-offline-remediation.md)

- [前置审查](../022-loading-code-audit/records/2026-10-08-review.md)
- [分层](../../docs/design/architecture/02-layered-architecture.md)
- [维护补丁](../../docs/adr/0016-maintained-upstream-fixes.md)
