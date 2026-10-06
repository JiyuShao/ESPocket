# 15 — 对齐条件性扩展模块提示

**What to build:** 以 Super 已接通的 Expansion 模块状态/插拔提示为基线，制定 Device capability 条件启用、系统 MessageDialog 和清理的适配计划。

**Blocked by:** 锁定 Device 0.8.2/Helper 0.8.4/HAL Interface 0.8.2 缺 Expansion API；当前板无 ModuleManagerIface，需精确依赖升级/上游 seam 与真实支持硬件。

**Status:** needs-info

- [ ] 核查固定 Super 的 capability 检查、先订阅后首次读取、按 provider/slot 合并、更新/关闭提示及 stop 清理；记录锁定版本接口差异。
- [ ] 对齐真实已实现提示范围，不把 Notifications API 名称当作通用通知中心；硬件不支持时明确 unavailable，不制造插拔事件。
- [ ] 将提示接入已有系统 MessageDialog Owner 与 03 仲裁、Home/息屏/期限规则；不新增通知队列或另一份 Device 状态事实。
- [ ] 形成兼容实施票与能力可用/不可用、连续插拔、停止/迟到事件、圆屏呈现的验收条件；当前无真实硬件证据的路径保持未验证。
- [ ] Exposure Decision 和文档路由完成，Markdown 检查通过；设计确认后再实施。

## 兼容设计与执行单元

[源码核查](../records/2026-10-04-compatibility-design.md#15-expansion)确认实际接口差异；不是可直接在当前配置订阅的功能。本票保持条件性范围和未验证状态，不请求是否迁移、不因硬件缺能力关闭完整目标。

1. 先以编译/API 门槛和 runtime GetCapabilities 两级判定；当前锁定接口不存在 GetExpansionModuleInfos/ExpansionModuleChanged/ModuleManagerIface。比较精确升级 Device/Helper/HAL 的传递影响或官方兼容 seam；新依赖必须独立锁定/hash/完整构建/现有回归，不能添加字符串事件伪装可用。
2. 当前 466px 板未声明 ModuleManagerIface，无真实插槽/模块驱动；普通产品不启动 timer 或显示伪模块。支持板实现仍归真实 HAL Device Owner，本票不为不支持硬件制造适配器。
3. 能力可用后沿 Super 先订阅后初始读取，pending state 按 provider/slot 有限合并并在 Shell App timer 每 250ms drain。并发首次读不能覆盖更新事件，需 generation/序列或重新读取 Owner 验证，不能仅凭订阅先后保证因果。
4. 使用 Core system MessageDialog request，slot 相同更新既有请求；检测/移除/unsupported 文案与圆屏长名换行由 Shell 呈现。3秒有效呈现自动关闭，遵守 03 的系统提示 Home/息屏/期限；Core 队列仍唯一，不新建通知中心。
5. Stop 关闭 admission、断 subscription、释放弱状态、停 timer、hide 自有 Dialog 并核实结果，最后 release binding；timer/hide 失败沿首批真实清理，不借 App 已停宣称全部释放。重复 start 获得新 generation，旧模块事件不得生成新提示。
6. Exposure deferred，只考虑真实模块可用性 Context/插拔 Event，不授权 Assistant 控制模块或安装 App；运行模块接口不由系统 Dialog 增加权限。

### 实施前置与验收

- [ ] 固定可用的 Device/Helper/HAL 新 API 组合与 lock/hash，兼容 proof 覆盖当前 unavailable 分支；任何升级不得顺带替换 production 的 Store/Core 已验收补丁。
- [ ] host 回归无 Service/无 iface/无编译 API、初始/并发插拔、同 slot 多次更新、多个 provider、unsupported、malformed payload、stop/迟到事件、Dialog show/update/hide 失败和息屏计时。
- [ ] 字体/语言依赖 [09](09-design-language-and-font-support.md)，请求仲裁依赖 [03](03-arbitrate-overlay-input-and-deadlines.md)，清理依赖 [01–02](02-complete-stop-and-normal-restart.md)。有限合并不保存另一份 Device 状态。
- [ ] 独立完整构建；当前板证明无伪事件/无新增占用，支持硬件再证明初始模块、连续插拔、圆屏提示与 Home/off/wake。mock 不能代替实际 ModuleManagerIface 硬件证据；支持板路径保持未验收。

## Comments

2026-10-04：完整 Super 功能核查发现此前路线图漏列此条件性能力。按用户默认完整对齐方向补票，源码事实见[计划记录](../records/2026-10-04-service-app-extension-plan.md#super-实际接通功能基线)。

2026-10-04 隔离兼容设计：补充锁定 API、真实 Owner、圆屏/资源、停止安全、Exposure Decision 与执行单元；仅文档核查，不计实施/构建/设备完成。详见[核查记录](../records/2026-10-04-compatibility-design.md)。
