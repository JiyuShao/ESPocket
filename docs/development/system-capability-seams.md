# 系统能力兼容 seam

此文档描述目标接口约束，不声称接口已实施。锁定版本差异与源码证据由 [019 核查记录](../../.scratch/019-system-shell-remediation/records/2026-10-04-compatibility-design.md) 持有；未决产品规则仍由对应 ticket 持有。版本升级必须同次核查 manifest/lock、兼容测试、资源和必要设备证据。

## 状态与采样

状态呈现输入必须同时包含 Owner 提供的 value、读取是否成功、可用性及接收时间；Battery absence 是有效设备事实，读失败是 unavailable，不是 absence。Wi-Fi Connecting/Disconnecting 与 Idle/Inited 区分，失败需具体 event/error，不能仅凭 Started 猜连接失败。SNTP 的 IsTimeSynced 不是跨重启 RTC 可信声明；离线持续走时若被接受，validity 必须由 SNTP/时间 Owner 提供，不在 Shell 内以首次 bool 构造永久有效时间。

先订阅、再首次读；首次读与并发 event 的顺序用采样/request generation 核对。每个 Owner 至多一个在途刷新，事件合并为最新有限呈现输入，定时器只在显示需要时刷新。调用失败可再读，不自动发起 Wi-Fi 重连或改时区。停止后旧 callback 不准触达 GUI。相关实现/验收由 [06](../../.scratch/019-system-shell-remediation/issues/06-design-status-validity-and-presentation.md) 持有。

## Settings 与调试

保留 Settings 自有导航与 Debug 业务。准入检查必须覆盖页面进入、动作、启动时持久偏好恢复和开发模式关闭；仅在 Adapter 的 on_action 拦截不能防止 Settings on_start 自动恢复采集。优先增加官方 Settings 的 admission hook；若公开 seam 不足，按真实 Owner 维护有 hash 的限定补丁并核查授权范围，不能以资源隐藏代替准入。

Utils 的 start/stop 与 SetDebugConfig 是共享全局行为。目标为 Utils 内 session/lease 或等价的 caller ownership seam：返回 token，释放只影响该 Owner；独立观察已有采集不调用 Stop。仅记录「我看到 stopped 后调用 start」不能避免竞态。配置阈值也需所有权/冲突结果。Settings Back/Home 退出后，当前用户开启的调试浮层可保持；Developer Mode off 和 System stop 使该产品 session 失效并释放。不能新增另一套 Profiler。

Shell 从 DebugStateChanged、MemoryDebugSnapshotUpdated、ThreadDebugSnapshotUpdated 及首次 GetDebugSnapshot 建立有限呈现；显示 timestamp age，不把空/旧缓存当实时。采用上游 1000 ms 内存、5000 ms 线程间隔和 1000 ms 线程采样默认值，保留 Settings 有效范围及阈值。实际支持同时由 Utils capabilities 和有效编译配置判定。UI 采集开销与输入响应必须实测；USB 导出另有 DEV-003 协议边界，不在本次设计默认加入。

## 环境刷新

字体在 App 文档加载前 register_font_file；根据 list_supported_fonts/languages 设置 default font 与 language，回退语言必须受实际资源支持。文件字体 backend 未启用时不可宣告支持。环境 change hook 负责 Shell 动态文案、Launcher 已提交投影和原生 Overlay 字体/颜色，避免在 LVGL 锁内同步查询 Core。

主题/语言更新应保留对象、Page、草稿、selection 和 request identity；App 的动态 literal text 不会因 GUI environment reapply 自动翻译。每个 App 作者通过其真实 Owner 更新文案；系统不读取隐藏表单或猜测 App 数据。原生控件仅重设 style/font，不清空内容。

Core setter 的刷新 hook 和偏好保存失败如何传播，必须用真实调用控制流验证。目标结果至少区分 applied、partial/failed 与 persisted；具体失败策略见 [10](../../.scratch/019-system-shell-remediation/issues/10-design-live-theme-switching.md)。Settings 实际调用路径也须接到相同事务边界，不能只包装 Product UI 的一个入口而留下旁路。若新增公开 Core seam，保持旧 API 行为兼容并记录 patch/hash/移除条件。

## Files 接入

目标接入官方 Files 0.8.2，显式 install_app；不开启全部自动安装或导入 Super System。新增依赖先精确锁定并验证现有 Core/Storage/helper hashes 没有顺带升级。官方资源通过 build tree staging；修改圆屏资源必须有可维护 override/seam，不改原 managed_components。

建议官方 Files 增加目录策略与导航观察 seam，最终契约须经 [11](../../.scratch/019-system-shell-remediation/issues/11-design-files-integration.md) 的冲突决定：

- Browser snapshot 由 Files 真实 current_directory/current_volume/Page 给出；Root 为卷列表，目录实例不是新 Page 类型。Browser 内目录 Back 返回父目录/卷列表，Operations Back 返回原目录；canBack 同时考虑目录深度与真实 Page，Root 无 Back。
- 读写 policy 在目录枚举、选择、键盘结果和 commit 时使用同一 Owner 检查；rename 检查 source 与 destination，delete 检查整个目标 subtree，不能删除包含 protected 后代的祖先。路径规范化、边界分隔、同名冲突与 symlink escape 必须失败关闭。
- Core 包目录、system、私有 AppData/AppCache/AppFiles 的准入不由 raw Storage Helper 决定；用户公共分类目录继续保留全部 Files 操作。对挂载卷余下范围的可见性选择由 ticket 持有，不能把本建议写成全卷授权。
- I/O 在 Storage 内部 RAM worker 执行，页面线程等待终态不得阻塞 PWR；commit 前可取消，commit 后由 Storage 结果核实。取消 UI 不等于 IO 回滚；迟到结果不恢复已结束的页面。

这是官方 Files 的聚焦扩展候选，不是已批准的 Settings 导航例外，也不允许把完整 App 复制为产品私有文件管理框架。

## 显示源与 Expansion

优先使用锁定 DataFlowRegistry.open_visual_operation、VisualOperation.get_sources/get_active_source、set_active_source_role/set_active_source_named；source name 只表示路由名称，需要配合 operation identity 与 Running Instance。恢复失败保留可用 GUI，报告恢复失败并使 continuation 失效。provider revoke/source removal 后不自动重建 source；输出、buffer 和 producer 的停止由真实 Owner 处理。

Expansion 先检测编译 API 再检查 Device capability；无 API/无接口时路径 unavailable。有能力时先订阅再读初始模块状态，有限 pending 数据按 provider/slot 合并后 250 ms drain，Core Dialog 更新同 slot 的既有 request。自动关闭的目标为 3000 ms 有效呈现时间，息屏不延长操作资格。该功能不建立通知中心或请求队列。

## 手机配网

锁定 API 为 TriggerSoftApProvisionStart/Stop、Set/GetSoftApParams、GetGeneralState、GetConnectAp、GeneralEventHappened/SoftApEventHappened。System 会话归属独立于 Shell 页面；Back/Home 的会话行为待 [14](../../.scratch/019-system-shell-remediation/issues/14-design-phone-wifi-provisioning.md) 确认。复用官方 portal/DNS/Web 页面，不新建 server。

Start/Stop 是操作提交；启动中、AP ready、连接中、取得 IP、portal 已停和持久化结果分别观察。只能展示由 Owner 确认的 AP SSID/密码/地址，不将二维码加入 AP 等同提交家中 Wi-Fi 凭据。不得在日志、USB 快照或未来 Context 中导出密码。恢复原 target 的强保证需要 Wi-Fi/HAL 会话 generation、停止投递/在途任务与保存终态 seam，不能在 Shell 简单 SetConnectAp 冒充事务回滚。

## Exposure Decision

| Capability | Decision / Owner | 未来语义、authority、risk 与 lifetime |
|---|---|---|
| 状态 | deferred；Service/System | 未来 Context 明确 freshness/validity，Wi-Fi/Time/Battery Event 来自 Owner；只读低风险，按 caller/字段准入；订阅随消费方实例结束，06 持有后续设计 |
| 调试 | unexposed；Utils/System | 内存、线程名、阈值和测试控制只在 Developer Mode；不向 Assistant 注册采集/USB Action，避免扩大 DEV-006 |
| 语言/主题 | deferred；Core/System | 未来当前环境 Context 与显式 Set Action；产品 UI 可用，不授权 Assistant；低可逆风险但需 User Intent/Scoped Grant，变更结果 Event 区分显示和保存，09/10 持有 |
| Files | deferred；Files/Storage/Core | 未来 scoped user-files Context 与 rename/delete Action；禁止绝对全卷路径或私有数据枚举；删除为高影响、目标单独确认，运行实例/operation 终态有效；11 持有 |
| 显示路由 | unexposed；Display/System | 内部 source arbitration 不作为 Assistant raw source/HAL Action；App 暴露具体产品能力时另审 |
| 配网 | deferred；Wi-Fi/System | 未来 session 状态 Context、显式 Begin/Cancel Action；网络中断风险需当次 User Intent，密码不读取，操作已提交时不假报撤销；14 持有 |
| Expansion | deferred；Device/Shell | 可考虑模块可用性 Context 与插拔 Event；低风险按 caller/真实 capability 准入，提示不是 Action；15 持有，不创建安装或控制权限 |

Deferred 项在上述工作票中保持可见，不能因对齐功能范围而开放 Assistant 调用。这里不实施 009 Provider/Agent Manager。
