# 2026-10-03 — Core failed-stop cleanup regression

用户授权用锁定版补丁修复上游缺陷，见 [ADR-0016](../../../docs/adr/0016-maintained-upstream-fixes.md)。

## Deterministic red loop

`python3 -m unittest discover -s firmware/test/host -p test_core_failed_stop.py` 的最初版本执行 Core 0.8.4 `System::stop_app` 的真实 Runtime 分支（抽取编译，依赖 Runtime/backend 替身）。故意让生命周期 on_stop 失败，输出 `FAIL: failed on_stop skipped Runtime cleanup`。该主机 harness 验证真实控制流，不能证明整个 JS backend 或硬件的资源清理。

三个假设：Core 因 lifecycle error 跳过 Runtime stop；Runtime stop/backend 自身失败；已排队事件在 stop 后仍交付。第一次修复只处理第一项。

## Patch and green loop

[Core patch](../../../firmware/patches/espressif__brookesia_system_core/0.8.4/001-unconditional-runtime-stop.patch) 删除 lifecycle success 前提，无条件进入 Runtime stop（Runtime 存在且 ID 有效时）。Runtime::stop_app 已在 backend stop 返回后无条件释放 host resources；生命周期失败原错误保留，不被 backend 结果覆盖。

版本、完整源码 inventory 与补丁 hash 由 manifest 校验。测试现自动运行未修版本的预期失败和准确应用补丁副本的通过；覆盖 lifecycle/backend 两种错误的四种组合，每次 Runtime stop 恰好一次。

## Remaining gates

当前尚未接入产品构建，也未刷入设备。owner-scoped KeyboardClosed 交付与已排队 callback/lifetime 仍需独立回归；本票不关闭。原 fail-closed keyboard latch 保持。后续需要完整构建、真实 Runtime 故意失败 on_stop 及跨 App result 隔离验收，不能把 host stub 通过当作整个隔离契约通过。

## Owner delivery 与 queued event 回归

第二项测试执行真实 Core dispatch_event，用两个 App ID 和虚构测试文本复现 `FAIL: keyboard Text delivered to another App`。补丁在 Runtime delivery seam 校验 SystemCore KeyboardClosed 的 AppId，缺失、错误类型、非匹配 Owner 或畸形 JSON 均拒绝；保持合法 Owner 和普通公开 Event 路径，拒绝停止/错误实例。Paused 仍属于有效 Running Instance，不因此剥夺其公开 Event。

第三项测试执行真实 Core event_dispatcher 队列 lambda，复现 `FAIL: revoked subscription delivered queued event`。每个订阅使用独立原子 active token；unsubscribe/release 在断连前撤销，异步队列在执行时再次检查。相同 App ID 的新订阅不能复活旧 token。停止错误、结果隔离与队列撤销三项 harness 现均自动验证原版失败和补丁版通过。

删除 Runtime service-event 日志里的原始 payload，避免正文通过日志输出。Native 编译内可信监听不在此次 Runtime 隔离范围；服务原 schema 与 owner callback 保持。

构建入口已扩展为显式列出的 Runtime/Core 两个锁定补丁，逐项校验源码/hash、override 选中目录与 registry drift。完整构建正在验证；真实 JS 故意失败 on_stop 与资源释放仍未验收，产品 keyboard latch 不撤销。

Runtime/Core 双补丁完整构建通过，准确选中独立副本，原 registry 依赖无 drift；镜像身份与 [009 构建记录](../../009-ai-native-foundation/records/2026-10-03-semantic-brightness.md)一致。设备未刷入，真实 Runtime 故意失败与跨 App 验证仍待完成。

候选普通镜像 `5e79e3a82` 应用分区刷写校验通过，NVS/LittleFS 未写。真实设备 apps 套件 PASS，attempt `20261002T210416Z-0836daa1-0455-4b3b-8e3a-53a465f97125`（原报告 `/private/tmp/espocket-009-core-apps`），覆盖普通 Native/Runtime 导航与未回收唤醒；是 synthetic-input，不能证明故意失败 on_stop 后恶意订阅隔离。该原始镜像/ELF 保存于 `/private/tmp/espocket-009-core-normal-preserved`，避免后续候选增量构建覆盖身份。

Exposure Decision：键盘隔离、订阅撤销与退出清理是 Core 内部约束，不注册 Keyboard Text 或订阅对象为 AI Context；修复不扩大 Assistant 对文本的读取范围。
