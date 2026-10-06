# 14 — 设计手机 Wi-Fi 配网入口

**What to build:** 使用已有 Wi-Fi Service 定义设备发起手机配网的产品流程，补齐开始、成功、失败、取消、超时与恢复规则。

**Blocked by:** 固定 Super 无手机入口；主动/自动触发及取消恢复策略尚未选定，锁定 HAL Stop 不回滚 target/在途 connect/历史凭据。

**Status:** needs-info

- [ ] 核实锁定 Wi-Fi/Helper 的 SoftAP provisioning 接口、实际手机协议和 STA/AP 行为；不把 Service API 存在等同产品入口完成。
- [ ] 用户确认主动入口/未配置网络提示、断网重连与配网的关系，不重新实现基础 Wi-Fi 服务。
- [ ] 成功、失败、Back/Home、息屏、取消/超时和恢复原网络/凭据的行为明确定义。
- [ ] App/System/Service 的 Owner、导航与生命周期、Exposure Decision 及实现路径确定。
- [ ] 产品要求、实施依赖、必要失败回归和真机手机配网验收票完成，用户确认共同理解且 Markdown 检查通过。

## 兼容设计与执行单元

[源码核查](../records/2026-10-04-compatibility-design.md#14-手机配网)核实既有 portal。真正待选的是产品策略，非 Service API 是否存在。推荐从 Quick Settings 主动进入、5分钟会话期限、Back/Home/取消停止 portal，已提交连接按 Wi-Fi 终态继续核实、不承诺旧网络/凭据 rollback；尚未接受。自动首次/断网进入是另一明确选择，不能从迁移 Super 推断。

1. 优先 Quick Settings → System-owned provisioning Surface（不是 Launcher App/Provider）；保留 Watch Face 固定 Home。官方 Settings final 无扩展菜单 seam，不擅自修改 Settings 页；之后如果需要 Settings 链接再显式增加入口。
2. System 持有 session identity、deadline、original on/off/target 的有限引用与 state（starting、AP-ready、connecting、linked、stopping、ended/failed）；Wi-Fi 持有真正 STA/AP/历史凭据，不在 Shell 存密码历史。页面只显示 Owner 已确认的 AP SSID/密码/地址或二维码、步骤和错误。
3. Start 暂停自动连接并断开旧 STA；SetSoftApParams 如有本会话设置，需要按 Owner 的实际返回确认，不能在二维码中猜固定地址/默认密码。使用 HAL 自带网页、DNS、scan/connect/status，手机加入设备 AP 不等于提交目标路由器配置。
4. 成功以本会话目标的取得 IP 为连接事实；POST 接受只表示排队，AP stopped 也不证明成功。不能把原 target 自动重连当本次配网成功；若公开事件缺 session/target，先在 Wi-Fi/HAL 增加 correlation seam。互联网/云可用不纳入 Wi-Fi success。
5. 若接受不承诺 rollback：取消/超时关闭 portal 并报告 submitted connect 的真实后续状态，后续 Wi-Fi 自动连接依 Owner；若要求恢复旧网络/凭据：增加真实 Wi-Fi/HAL begin/cancel generation、任务屏障和 Storage 保存终态，再证明停止后不会有旧提交覆盖恢复，不能只 SetConnectAp(old) 冒充取消成功。
6. 建议息屏保留会话并继续真实 deadline；wake 先读有效 session，超时已结束不恢复 portal。System stop 必须停本会话 portal、关闭 admission、撤订阅；未提交取消与已提交连接分开，迟到结果不重开页面/Provider。
7. Exposure deferred；未来 begin/cancel 属中断网络副作用，需当次 User Intent/Scoped Grant；密码不进入 Context/USB/log，009 实施不在本票。

### 实施前置与验收

- [ ] 明确主动/自动触发、会话期限、Home/息屏规则与 rollback 强度；对应事实不足必须在 Wi-Fi/HAL Owner 补 seam，保留原扫描/重连既有验收。
- [ ] host 回归 session matching、快速 start/cancel、错密码/无 AP、Start/Stop 失败、deadline、旧 connect 后到、失败持久化与 System stop；日志不记录密码。
- [ ] UI 复用 [03](03-arbitrate-overlay-input-and-deadlines.md) 输入与 [06](06-design-status-validity-and-presentation.md) 状态事实，配网前确认网络中断不能阻止 PWR Home；若需要资源由 [08](08-audit-resource-staging-integrity.md) 持有 staging。
- [ ] 统一检查、独立完整构建；Android/iOS 至少各一个真实机型验证 captive portal 及手动浏览器备用、AP 加入、正确/错误密码、IP、取消/超时、原网络结果、息屏/重启历史恢复；凭据保存无公开提交事件时不能关闭持久化门槛。
- [ ] 当前 Store 占用设备，不执行手机/串口/刷写，所有新增手机和真机路径未验收。

## Comments

2026-10-04：用户要求完善 Agent Manager / XiaoZhi 之外的计划。配网作为产品入口增量在本票单列，Wi-Fi 扫描/连接/NVS 重连既有验收保持有效；不混入 009 Provider 会话设计。

2026-10-04：用户改为默认对齐 Super 的实际完整功能。固定 Super 未接通手机 SoftAP 入口，本票继续作为独立示例增量，不从该方向推断 Q19 手动/自动触发已经选定。事实见[计划记录](../records/2026-10-04-service-app-extension-plan.md)。

2026-10-04 隔离兼容设计：补充锁定 API、真实 Owner、圆屏/资源、停止安全、Exposure Decision 与执行单元；仅文档核查，不计实施/构建/设备完成。详见[核查记录](../records/2026-10-04-compatibility-design.md)。
