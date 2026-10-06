# 06 — 设计现有状态的有效性与呈现

**What to build:** 对齐 Super 实际 Wi-Fi/时钟/时区、状态栏展开与 App 内临时呈现能力，并为现有 Battery 等产品状态输出有效性矩阵和实施/验收工作。

**Blocked by:** 离线时间有效性与 Battery 失败旧值的呈现规则待精确确认；公开 SNTP 无跨停止有效时间快照。状态栏兼容方案已形成。

**Status:** needs-info

- [ ] 以现有 Service 为事实源，核实状态、首次读取、订阅、失败与刷新路径，不建立全局状态缓存。
- [ ] 对照 Super 状态栏展开/peek 和手势路径，复用已有 Quick Settings/导航能力并适配圆屏；不迁移已停用的 Quick Control/System Monitor 页面。
- [ ] 明确连接中/失败/关闭、充电/缺失/读取失败、离线有效时间/未同步的用户可见区别；确认旧结果的失效与降级规则。
- [ ] 区分状态表达与 callback 停止安全；后者引用首批 01–03 的真实 Owner 验收，避免延后可靠性修复。
- [ ] 已接受行为进入产品文档，Exposure Decision 按 009 契约记录；具体实施票包含停止/恢复、读失败和迟到结果验收。
- [ ] 用户确认完整设计，Markdown 检查通过；设计阶段不宣称状态表达已实现。

## 兼容设计与执行单元

事实与产品规则分别见[源码核查](../records/2026-10-04-compatibility-design.md#06-状态有效性与状态栏)、[SCA-001–002](../../../docs/design/product/08-system-capability-alignment.md)。保持 needs-info，仅以下真实规则未选定：已同步后离线是否继续走时；Battery 失败是否展示明确标旧值的最近数据。推荐离线持续走时并标离线、失败 Battery 显示未知；尚未接受。

1. 建立 Wi-Fi/Device/SNTP 的状态解析与 validity seam，记录 Owner、sample generation、可用性与错误；首次读取和订阅按先订阅再读合流。Wi-Fi Idle/Inited 为未开启或未运行，Started 为运行未连接，Connecting/Disconnecting 为过渡，Connected 为已连接；error/unexpected 与未知枚举分别呈现，不把 Started 推断为失败。Battery absence、charging/full/fault、未知 percentage、读取错误分别处理。
2. 时间 validity 若跨 Service stop 保留，先在 SNTP/时间 Owner 增加可审查 seam，不在 Shell 制造有效时间缓存；TimezoneChanged 触发重格式化，不重设导航。冷启动未同步显示 `--:--`，不能以固件编译时间冒充当前时间。
3. Shell 维护圆屏 compact status 与展开详情；Watch Face 下拉复用 Quick Settings。App 内只从专用顶部入口/短暂 peek 显示，不把普通纵向内容滚动或 Edge Back 改为新 Home；若照搬 Super 顶部手势会冲突，使用明确的系统手势区域。状态层不拦 PWR、键盘和确认请求。
4. Exposure Decision 为 deferred，未来只读状态必须带 validity/age，禁止隐式网络写操作；接口约束见[开发 seam](../../../docs/development/system-capability-seams.md#状态与采样)。

### 实施前置与验收

- [ ] 产品规则确认后形成完整状态表；代码解析回归覆盖未知值、空/错类型、断开、读失败、旧 generation、事件与首次读交错。
- [ ] GUI 更新采用共同停止安全方案；callback/锁/迟到结果的共同门槛引用 [01](01-close-initialization-cleanup-gaps.md)、[02](02-complete-stop-and-normal-restart.md)，不另建 Service cache。
- [ ] 圆屏测试覆盖 Watch Face、Card、Quick Settings、Native/Runtime App peek，Keyboard/Dialog 优先级依赖 [03](03-arbitrate-overlay-input-and-deadlines.md)。peek 进入退出不改变 Page/canBack，PWR 路径依赖 [04](04-add-loading-and-responsive-startup.md) 的 250 ms 门槛。
- [ ] 统一 host checks 与完整生产补丁构建；设备分别验证无网络冷启动、同步后断网/时区、充电/缺电池/读取故障注入与显示恢复，记录实际值和人工像素。设备条件未验收。

## Comments

2026-10-04 隔离兼容设计：补充锁定 API、真实 Owner、圆屏/资源、停止安全、Exposure Decision 与执行单元；仅文档核查，不计实施/构建/设备完成。详见[核查记录](../records/2026-10-04-compatibility-design.md)。
