# 12 — 设计非 GUI 显示源支持

**What to build:** 对齐 Super 已实现的显示源切换、Overlay 临时取回 GUI 和恢复逻辑，按真实硬件/source 能力形成条件启用与验收计划。

**Blocked by:** 锁定 VisualOperation 可用但无当前产品非 GUI App/source 场景；需独立 producer fixture、source lifetime 和真实 466px 输出证明。

**Status:** needs-info

- [ ] 核对实际 Display source/role API 与 Super 的临时源恢复方式，明确目标硬件支持和 source lifetime。
- [ ] 确认 Home、系统提示、键盘/Dialog、Screen Off/wake 对原源的切换与恢复规则。
- [ ] 原源已停止/移除或恢复失败时有明确降级，不复活失效 Owner；不将该能力认定为当前纯 GUI 路径的已复现故障。
- [ ] 产品/架构规则与 Exposure Decision 收敛，实施票有 source identity、失败注入和真实硬件矩阵。
- [ ] 用户确认完整设计，Markdown 检查通过；没有真实场景时保留 planned 功能范围，不先造通用显示管理器。

## 兼容设计与执行单元

[源码核查](../records/2026-10-04-compatibility-design.md#12-非-gui-显示源)确认锁定 dataflow 路由 seam 存在。功能范围 planned/条件性，没有纯 GUI 已复现缺陷或 NES/Video 可用证据；保持 needs-info，不伪造设备完成。

1. 首个真实非 GUI producer/测试 fixture 通过既有 Display dataflow 注册 source，System 使用 open_visual_operation 控制选定的 466px output。不先建立通用显示 manager，不因 linked library 存在就开放游戏/视频入口。
2. 第一次系统 UI（status peek、Keyboard/Dialog/Loading）取回 GUI 前保存 output + source name + operation identity + Running Instance + foreground generation；重叠 UI 只引用同一有限 continuation，不覆盖原记录；最后有效层退出才尝试原 named source。
3. 恢复时核对 source/operation 仍注册、Owner 未停/未回收、当前前台和 output 一致；同名 source 重建不能通过。外部 source takeover/revoke 更新路由资格，不能用旧 token 强抢。
4. Home 清除恢复 token、激活 GUI、到 Watch Face；不停止 source producer 之外的 Owner，但原 App 的结束仍按 Core。Screen Off 关闭输出/暂停 UI，保留仍有效的 resume 信息；wake 重新判定 App/source，失效回 GUI Watch Face。键盘/Dialog 原请求资格与 03 一致，不以重新发请求恢复。
5. 切 GUI 失败：不显示虚假 overlay success、不交付输入结果，报告失败并按实际 Owner 安全退出；restore 失败：保留可用 GUI/错误反馈、清 token，不复活 source。关闭 operation/binding 不在 GUI 锁下等 producer frame completion。
6. Exposure 明确 unexposed；source arbitration 是内部系统动作，未来具体媒体 App 语义另审。

### 实施前置与验收

- [ ] 使用自有固定帧 producer fixture 验证锁定 Display provider 是否真正实现 named-source selection、buffer ownership 与 revocation；不要在 production 放临时入口。
- [ ] host seam 回归 nested UI、Home、screen-off/wake、source removed/replaced same name、Owner stop/reclaim、foreground change、switch/restore timeout；检查旧 continuation 不应用于新实例。
- [ ] 与 [01–03](03-arbitrate-overlay-input-and-deadlines.md) 合并停止/仲裁，[06](06-design-status-validity-and-presentation.md) peek 与本票共享一个路由 continuation；帧采样/截图也需明确当前 active source，不冒充 LVGL 像素是物理 non-GUI 输出。
- [ ] 统一检查、独立完整构建；466px 真输出 producer ↔ GUI、重叠 Overlay、Home、off/wake、source revoke/失败降级各有实际画面与 Owner 证据。没有设备场景时保持功能条件未验收，不默认禁用最终范围。

## Comments

2026-10-04 隔离兼容设计：补充锁定 API、真实 Owner、圆屏/资源、停止安全、Exposure Decision 与执行单元；仅文档核查，不计实施/构建/设备完成。详见[核查记录](../records/2026-10-04-compatibility-design.md)。
