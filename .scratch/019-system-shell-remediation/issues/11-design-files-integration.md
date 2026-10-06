# 11 — 对齐完整 Files 功能

**What to build:** 以 Super 的完整 Files 为基线，制定卷/目录浏览、容量/信息、重命名、删除和确认流程的接入计划；完成圆屏、导航、存储 Owner 和锁定依赖适配。

**Blocked by:** 全卷 raw 写与 package/system/私有 App Owner 冲突、官方 Files 导航限定例外待明确决定；官方 0.8.2 无目录策略/导航 snapshot seam。

**Status:** needs-info

- [ ] 固定官方组件/API、注册安装与资源证据；以上游完整已实现功能为目标，不默认裁剪为只读浏览。
- [ ] 保留重命名、删除及相应键盘/确认流程；解决全卷 raw filesystem 操作与 Core 管理的 package/system/App 数据的冲突，不以隐藏按钮代替真实执行边界。
- [ ] 定义 App Page/Back/Home、执行取消与错误结果，保持真实文件 Owner 和既有权限/trust 边界。
- [ ] 比较真实公开扩展点、必要上游 seam 与适配成本；形成产品契约、Exposure Decision、版本/资源前置和真机验收票，涉及既有决定变更时显式提出差异。
- [ ] Markdown 检查通过；组件可编译不替代文件产品体验验收。

## 兼容设计与执行单元

[源码核查](../records/2026-10-04-compatibility-design.md#11-完整-files)确认完整功能与缺 seam。Files 0.8.2 是待加入依赖，当前 lock 未包含；不得把 Super checkout 当已锁定 Registry 构建输入。

1. 精确加入官方组件，显式安装 provider 创建的 FileManagerApp；资源 staging 和 466px 中心安全区列表/操作页布局独立接通。不改 install_registered_apps=false，不导入整个 Super 或影响 Store registry 施工。
2. 保留所有 available 卷、容量/文件信息、目录浏览、rename keyboard、delete destructive confirmation、进度/失败结果。目录/文件选择都沿真实 Files；不增加预览、播放器、BPK 安装。
3. 全卷冲突推荐处理：保留卷容量与公共目录的全功能浏览/写，Core package/system 与他 App 私有区不允许 raw 写，其他目录可见范围需确认。对当前卷根和受保护目录的祖先禁止 rename/delete；检查 destination、separator、规范化、symlink 与跨卷动作。执行时再次判断，不以隐藏按钮实现策略。
4. 官方 Files 增加聚焦 path-policy/operation seam 与 navigation snapshot/request_back。优先上游公开扩展，若必要限定源码补丁，先明确新增能力是否纳入维护授权；ADR-0016 的 bug 修复授权不自动证明任意新 API 已批准。wrapper/final 组合无法访问私有目录事实，必须真实 seam，不能复制第二份路径栈。
5. 导航例外须独立 ADR 限定：官方 Files 持有目录/Page 状态，防腐层映射 files.volumes、files.browser、files.operations。目录内容实例仍同一 Page 类型；canBack 来自深度/volume/Page 真实事实。Root 无 Back，Operations 回来源目录，目录 Back 到父目录，卷根 Back 到卷列表。未知状态报错，不猜 Root；不把 ADR-0012 的 Settings 例外默认为通用许可。
6. 单操作 identity：确认/键盘后是待提交，Home/PWR 与未提交竞争由 03 处理；Storage 已接受 IO 后只是 UI 离开，不能报撤销/rollback。耗时目录/rename/delete 在 Storage 内部 RAM worker 执行并观察终态，generation 防止迟到结果恢复 Files 前台；stop 取消未提交 timer/请求并关闭新 admission，不能杀死正在写 flash 的工作线程。
7. Exposure deferred；未来仅 scoped user-files 能力，delete 单目标确认、高影响，不能开放全卷绝对路径或任何 package install 权限。

### 实施前置与验收

- [ ] 先确认保护范围和导航例外，形成 ADR/公开 seam/补丁授权与哈希基线；同时核查官方 Files 0.8.2 对锁定 Core 0.8.4/helper 0.8.4/Storage 0.8.3 的编译差异。
- [ ] host 行为测试覆盖路径穿越、protected 祖先、rename destination、symlink、跨卷、同名/非法名、移除卷、无容量/读失败；直接绕过 UI 调用也必须拒绝违规操作。
- [ ] 导航回归卷列表/根/多层目录/Operations/Keyboard/Dialog、Back canBack 与未知状态；取消-before-commit、Home-after-submit、失败/迟到终态与 stop，不能只检查按钮存在。
- [ ] [08](08-audit-resource-staging-integrity.md) staging、[09](09-design-language-and-font-support.md) 文件名字体、[03](03-arbitrate-overlay-input-and-deadlines.md) 请求仲裁、[04](04-add-loading-and-responsive-startup.md) 慢 IO PWR 门槛为实际前置；005 安装测试只作为 protected package 不回退证据，不重建其工作。
- [ ] 统一检查与独立完整构建；设备使用全新自有 fixture 目录验证浏览/容量、rename/delete、确认取消、重进与断电前后结果。禁止用真实 App/package 或用户文件做 destructive fixture；无真实外卷仅内卷验收，外卷保持条件未验证。

## Comments

2026-10-04：按用户最新方向对齐完整 Files，Q17 的只读建议撤回；Q18 的全卷范围改作为既有 Owner 契约的兼容分析，不把用户未回答的问题记成同意。文件预览、音视频播放、BPK 安装不属于该固定 Files 已实现功能。事实见[计划记录](../records/2026-10-04-service-app-extension-plan.md)。

2026-10-04 隔离兼容设计：补充锁定 API、真实 Owner、圆屏/资源、停止安全、Exposure Decision 与执行单元；仅文档核查，不计实施/构建/设备完成。详见[核查记录](../records/2026-10-04-compatibility-design.md)。
