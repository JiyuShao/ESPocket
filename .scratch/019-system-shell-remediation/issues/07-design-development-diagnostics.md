# 07 — 对齐 Super 设备调试链路

**What to build:** 以 Super 已接通的 Settings → Utils → Shell 链路为功能基线，制定 Memory/Thread 调试浮层、开关和阈值的迁移计划；补齐 ESPocket 开发模式、圆屏及采集生命周期适配。

**Blocked by:** 锁定 Settings 准入与 Utils 共享采集缺少 caller ownership seam，需完成真实 Owner 扩展兼容证明；线程构建支持及性能/设备门槛未验收。

**Status:** needs-info

- [ ] 固定上游 Settings Debug、Utils 事件/快照和 Super Shell overlay 的完整功能与源码证据；保留内存、线程、阈值和 GUI 调试等已有控制的归属，不重复制造 Profiler。
- [ ] 明确现有 Settings Debug 的准入适配、浮层布局、采样开销与不支持指标的真实反馈；当前配置关闭线程统计时不得报告 CPU 数据可用。
- [ ] 定义订阅/采集在 Settings、Shell、System 停止及开发模式关闭后的清理；区分观察已有采集与本会话发起采集，避免停止其他 Owner 的工作。
- [ ] 电脑只读导出作为现有 USB 协议的可选增量单独列出，不替代设备调试浮层；遵守 DEV-003–006，不复制 Console 的第二个 USB reader。
- [ ] Exposure Decision、实施票、性能/视觉验收和文档路由完成；涉及既有契约变更时明确提出差异，设计确认且 Markdown 检查通过。

## 兼容设计与执行单元

[源码核查](../records/2026-10-04-compatibility-design.md#07-设备调试浮层)已确认完整链路可复用；不再等待设备浮层/电脑查询二选一。准入与共享生命周期是技术前置，保持 needs-info 表示完整兼容设计尚未验证，不是产品功能待选。

1. 保留官方 Settings Debug 的 memory/thread 开关、采样周期、空闲 CPU/stack high-water 与 heap/largest block 阈值、GUI debug 控制。先核查资源与真实 on_start/on_action 行为，再为官方 Settings 增加 Developer Mode admission seam；包括保存的 debug 偏好恢复，模式关闭后已经打开的页面也不能继续写控制。
2. Utils 仍是唯一采集 Owner。比较 caller lease 与已有全局 start/stop：优先在 Utils 内加入 acquire/update/release token，Settings 使用同一会话，System 持有并在 off/stop 释放；观察已有采集只订阅，不抢占配置或 stop。仅在产品中记录布尔标志无法解决 start/stop 竞态，不能作为最终实现。
3. Shell 非交互浮层显示 SRAM/PSRAM free %/bytes/largest、每核 CPU top task、最低 stack high-water 与警告。466px 使用中心安全区域内纵向紧凑条，长 task 名截断但保留完整查询在真实 Owner；关键确认/键盘上方不覆盖输入。Settings 退出后保持用户开启的浮层，息屏停止呈现，wake 重读可用 snapshot。
4. 保留上游默认 1s 内存、5s 线程 interval/1s 采样和原阈值配置范围。GetDebugSnapshot 是缓存，显示 age/不可用；Thread 支持先核查有效 sdkconfig 和 Utils capabilities。本板两核但不等于线程统计已启用。
5. 明确 unexposed；USB 可选导出单独重开 DEV-003 协议决定，不安装 Console reader、不新增 USB 任意 Service 调用。

### 实施前置与验收

- [ ] Settings/Utils 的 seam 设计与兼容编译先完成，新增源码能力需明确授权及 ADR-0016 的补丁适用范围，固定版本/hash/上游草稿/移除条件。
- [ ] host 回归覆盖 Developer Mode off 的进入、动作、偏好自动恢复；两个 caller 并发 acquire/release/config 更新，观察者不停止既有采集；缓存空/旧、线程不支持、采样错误和 stop 迟到 callback。
- [ ] 停止安全引用 [01–02](02-complete-stop-and-normal-restart.md)，视觉仲裁引用 [03](03-arbitrate-overlay-input-and-deadlines.md)；与 [13](13-evaluate-build-and-profiler-tools.md) 协调有效编译开关与测量，不默认打开 production 线程统计。
- [ ] 在相同镜像/路径记录采集关闭与开启两组 heap、largest block、CPU/任务栈、PWR 延迟和帧呈现；每组至少三次 60s 观察，记录增量与稳定性，不先虚构资源预算通过。
- [ ] 完整构建及实际 Settings 开关/阈值、浮层与 App/Overlay 不遮挡、模式关闭及三轮 stop/start 设备证据分别验收。代码、构建和设备均未在本设计完成。

## Comments

2026-10-04：按用户最新「Super 已实现功能全部搬过来」方向调整。此前 Q20 的电脑优先建议不作为默认方案；完整设备调试链路进入迁移目标。事实见[计划记录](../records/2026-10-04-service-app-extension-plan.md)。

2026-10-04 隔离兼容设计：补充锁定 API、真实 Owner、圆屏/资源、停止安全、Exposure Decision 与执行单元；仅文档核查，不计实施/构建/设备完成。详见[核查记录](../records/2026-10-04-compatibility-design.md)。
