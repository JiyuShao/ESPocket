# System Super 参考审计：访谈决定与交付 — 2026-10-04

本记录保存访谈经过与交付边界，工作状态由 [01 ticket](../issues/01-audit-system-and-shell.md) 持有。源码事实见 [差异矩阵](2026-10-04-system-shell-audit.md)，产品要求与架构文档持有规范行为；本记录不证明实现或真机验收。

## 已确认的设计树

| 轮次 | 用户答复 | 决策记录 |
|---|---|---|
| Q1 | A | 完整审计 System 与 CircularShell，覆盖所有已列职责 |
| Q2–Q3 | 全部同意推荐 | 体验与可靠性优先；只使用源码/既有证据，新的验证留给后续任务 |
| Q4–Q5 | 全部同意推荐 | 关键启动失败清理并保留诊断，由显式重启恢复；stop 全部受管 App/入口，deinit 释放资源 |
| Q6–Q8 | 全部同意推荐 | Modal 输入仲裁、键盘 Back、PWR 提交边界、系统提示与息屏计时，写入 INT-028–032 和 ADR-0017 |
| Q9–Q10 | 全部同意推荐 | 保存主题不可用回默认；首批完善现有可靠性，扩展能力保留独立候选 |
| Q11–Q14 | 全部同意推荐 | 等待反馈范围、250 ms PWR 目标、正常重复生命周期与主题临时回退，写入 OVR-014–015、INT-033–034、LIF-007–008 |
| Q15 | 同意，并要求补充后续整改范围 | 首批理解已确认，另提出分批路线图供后续讨论 |
| Q16 | 同意 | 完整后续范围纳入正式路线图；功能扩展、工具与 Assistant 独立推进 |

规范链接：[产品总览](../../../docs/design/product/01-overview.md)、[交互模型](../../../docs/design/product/03-interaction-model.md)、[生命周期](../../../docs/design/architecture/04-boot-lifecycle.md)、[Overlay ADR](../../../docs/adr/0017-overlay-arbitration-preserves-request-ownership.md)。

## 首批后续工作建议

以下为审计交付的工作方向；本轮未实施，也未创建已开工的固件迁移票。后续启动实施时，在新的工作范围或现有适用票中分配具体验收条件。

| 工作方向 | 所需改进 | 后续验证重点 |
|---|---|---|
| 初始化和失败清理 | 获得/释放关系覆盖 partial init 与 Native start 失败，Core 缺口在真实 Owner 内修复 | 逐失败点注入、资源基线、清理结果、关键失败可诊断 |
| 全量停机与正常重复运行 | 所有受管 App/入口停止，同对象正常重复运行重建有效资源 | 后台 App、旧句柄/订阅/输入、stop/start 与 deinit/init 循环 |
| Overlay 输入与期限 | 按已确认规则仲裁，不复制 Core 请求队列；暂停呈现不延长执行资格 | 键盘/弹窗/Loading 重叠、Back、迟到结果、Home、息屏期限 |
| Loading 与启动响应 | 接入等待反馈，分别处理输入和 Core 运行事实 | 慢启动、PWR 与待提交结果竞争，识别后至 Home 的实测时间 |
| 保存主题回退 | 本次临时默认，保留偏好，默认失败走关键错误 | 未知值、apply 失败、重启保留、用户选择更新、默认失败 |

250 ms 是访谈接受的后续验收目标，没有在本轮测量。源码表明当前启动调用与 PWR 消费可能位于同一 App 回调路径，不能用 Loading UI 推断该目标已经满足。

## 条件性增量和既有任务

- 中文/多语言、即时主题更新、Files、完整诊断界面、非 GUI 显示源分别保留为候选，不在首批可靠性范围中隐式交付。
- [005/04 动态 Launcher](../../005-m5-application-ecosystem/issues/04-project-dynamic-launcher-from-core.md) 保留已定 full reconciliation 与失败保留完整投影要求，继续遵守既有 blocker。
- [005/07 Runtime keyboard isolation](../../005-m5-application-ecosystem/issues/07-isolate-runtime-keyboard-results.md)、Store 稳定性及 package trust 仍由原 Effort 持有。Super 示例不替代其证据。
- 停止期间 callback/GUI 等待、锁失败清理与回收结果属于后续可靠性验证边界，静态调查不等于已复现故障。

## 交付边界

本轮只读取项目和固定上游源码，写差异矩阵、Spec/ticket、已确认产品/架构规则及 ADR。只运行 Markdown 文档检查；未新增主机行为回归、固件构建、依赖升级、烧录或设备操作。用户通过 Q15、Q16 确认本轮共同理解后关闭审计票。

## Q15 后补充的完整路线图提案

2026-10-04：用户确认首批并询问后续整改范围。以下阶段为新的范围提案，尚非新功能交付承诺，不替代既有 ticket 的依赖。

| 批次 | 建议范围 | 范围边界 |
|---|---|---|
| 首批：可靠性 | 已确认的失败清理、全量停机/重复运行、Overlay、Loading/PWR、偏好回退 | callback 停止安全、锁失败清理和资源回收结果属于这些项的横向验收，不推迟到后续批次 |
| 第二批：现有状态与维护能力 | Wi-Fi/Battery/Time 状态表达；读失败/旧结果失效；有限诊断快照；新增资源/构建依赖完整性 | 状态来自现有 Service，诊断在开发模式，资源保持 build tree staging；不先造全局状态缓存或泛化资源管理器 |
| 第三批：生态闭环 | 动态 Launcher、localized name/icon fallback、安装/卸载刷新、package replacement 与 Card 迁移 | 沿 005/03–08 和 014/03、05 持有的工作推进；trust/Store/isolation 前置保持有效，不新增 Installer 或重复 App registry |
| 独立扩展批次 | 中文/多语言、即时主题切换、Files、非 GUI 显示源 | 每项另定义产品边界和资源/设备验收；不因 Super manifest 存在就默认可交付 |
| 可并行工具工作 | 构建分析、ccache/目标级并行策略、Profiler 查询 | 单独验证收益与开销；通用 Console 写操作需遵守开发模式与既有 USB 仲裁 |

Assistant 接入继续归 [009](../../009-ai-native-foundation/spec.md)，本审计的 Overlay、取消与生命周期规则作为共同基础，不借路线图扩展成第二个 Assistant 或权限系统。

第二批状态细分、诊断呈现、扩展批次的具体功能规则尚需后续设计，不由本路线图猜定。例如离线但已有有效时间怎样显示、旧 Battery 数据怎样标记、中文字体覆盖范围，都需要具体验收定义。

## Q16 确认与工作归属

2026-10-04：用户答复「同意」，接受上述完整后续范围。正式范围与 tickets 由 [019 整改路线图](../../019-system-shell-remediation/spec.md)持有；本记录保留 Q15 提案经过，不继续作为当前任务列表。

- 首批五项已有行为规则，拆为实施票；callback 停止安全、锁失败清理和回收结果纳入对应票。
- 第二批状态与诊断的具体呈现需要后续设计；当前资源完整性可独立核查。
- 中文/多语言、即时主题、Files 与非 GUI 显示源各有独立设计票；范围确认不等于功能行为已经定案。
- 构建分析、编译策略与 Profiler 先形成收益/开销证据，再决定采用范围。
- 第三批沿 005/03–08 与 014/03、05；005/07 已 resolved，其证据保持有效，不重复分配隔离修复。
- Assistant 保持 009 的任务归属，后续集成继续遵守共同 Owner、授权与生命周期规则。
