# 10 — 设计即时主题切换

**What to build:** 对齐 Super 已实现的运行中主题刷新与保存偏好链路，补齐 ESPocket Surface/Overlay/App 的兼容、失败和验收设计。

**Blocked by:** 部分刷新失败后的可见规则与偏好保存时机待确认；锁定 Core hook 失败不传播、异步保存无 setter 终态，需要真实 Owner seam。

**Status:** needs-info

- [ ] 对照 [017 主题变量迁移](../../017-theme-token-migration/spec.md)核实已完成覆盖，识别 Surface、Native Overlay 和运行中 App 的实际刷新 seam。
- [ ] 确认切换对键盘草稿、Dialog 请求、App Page/输入及息屏恢复的要求。
- [ ] 选择部分失败时的可见行为与偏好保存时机，保持 05 启动回退规则。
- [ ] 产品/架构/开发契约、真实 Owner 实施票与 dark/light 全路径视觉验收条件形成闭环。
- [ ] 用户确认完整设计，Markdown 检查通过；不把主题资源存在视为全树即时更新。

## 兼容设计与执行单元

[源码核查](../records/2026-10-04-compatibility-design.md#10-即时主题)已定位 SystemGuiAccess setter 的实际结果顺序。017 已完成语义颜色迁移，原生控件仍仅启动解析颜色；不能把该成果当即时切换完成。

1. System 继承 on_theme_changed/on_language_changed；Shell 在同一更新世代重设 Surface 动态 binding、Back、Card hint、Keyboard/Dialog 原生颜色/字体和 Loading。GUI 文档沿 set_theme(id, true) reapply，外部 App 的固定颜色不由系统猜改。
2. 保存策略建议为整体 refresh 成功后才确认持久保存；部分失败保留可用 UI 并显示「未完全应用/未保存」，提供重试但不自动重提业务请求。本策略尚待用户选择；自动回滚也是可选，但必须证明 GUI 环境、hook/native 树和 preference 能一致恢复，不能仅 set_theme(old) 即报事务回滚。
3. 锁定 Core 在 runtime success 后更新 snapshot，hook failure 只 warning，再 persist；因此新增 Core 结果/保存 seam 或在真实 Owner 内修复传播语义，Settings 的真实 Theme/Language 入口必须同次接入，不能只在 Shell 包装一处。同步保存接口存在于内部，不是公开事务 API。
4. 保留 App/Page/Running Instance、键盘 UTF-8 草稿、焦点和 selection、Dialog request/deadline/按钮角色；重设样式不毁树，不通过 stop/start App 或重新弹确认实现刷新。
5. 与 [05](05-fallback-unavailable-saved-theme.md) 共享启动 restore guard，临时默认不覆写保存值；用户成功的新选择才更新。Exposure deferred，不增加 Assistant setting Action。

### 实施前置与验收

- [ ] 策略确认后为 Core seam 形成精确补丁/版本/hash/删除条件；在真实 setter/Settings 调用路径注入 hook、GUI 和保存失败，不用镜像实现的测试冒充控制流。
- [ ] host 回归交叉覆盖 Light/Dark、语言、重复请求、部分刷新失败、保存失败、冷启动 unknown preference、默认资源失败；对 request identity、草稿/Page/instance 的稳定性做行为断言。
- [ ] 与 09 合并环境刷新预算，与 [03](03-arbitrate-overlay-input-and-deadlines.md) 合并 Overlay 顺序与锁规则；不改首批实现。
- [ ] 统一检查、独立完整构建；实际在 Watch Face/所有 Card/Launcher/Quick Settings、Native/Runtime Page、Keyboard/Dialog/Loading 上往返切换，light/dark 圆屏像素逐项证明，息屏/wake 与重启保存分开验收。
- [ ] 新增路径的 PWR 响应引用 [04](04-add-loading-and-responsive-startup.md) 250ms 门槛；连续三轮多次切换记录资源基线、失败与迟到结果。未执行设备验收。

## Comments

2026-10-04 隔离兼容设计：补充锁定 API、真实 Owner、圆屏/资源、停止安全、Exposure Decision 与执行单元；仅文档核查，不计实施/构建/设备完成。详见[核查记录](../records/2026-10-04-compatibility-design.md)。
