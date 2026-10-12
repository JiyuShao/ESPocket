# 02 — 锁定上游来源与确认公共 GUI 接入

**What to build:** 获取可复现的 The-Badge 源码输入，逐项核实七个 App 的真实依赖、资源许可和公开 GUI 接入路径，形成后续实施所需的确定边界。

**Blocked by:** [01 完整共同理解确认](01-confirm-migration-contract.md)。

**Status:** resolved

- [x] 锁定上游完整 commit、源码来源与摘要；保留 MIT/LICENSE/NOTICE 及实际迁移素材的归属，不把浏览 main 计为来源已锁定。
- [x] 审计 app_games.c、app_water.c、orb.c/h、app_mouse.c、host_pick.c、port.h、相关 BLE/板级实现和实际引用资源；按 App 列出 GUI、音频、触摸、IMU、持久化依赖，排除原作 Launcher/Settings/锁屏/电源与分区实现。
- [x] 核实官方 QMI8658、HID 实现与当前锁定组件的适配条件；模拟数据与真实驱动明确区分。
- [x] 为原作自绘选定现有 GUI Interface/LVGL Backend 可支持的接入方式，保留 App 页面身份、卸载、线程锁、系统覆盖、输入取消和资源回收所有权。公开 Canvas 存在不等于已经支持原作动态绘制。
- [x] 如确需扩展公开 seam，在真实 GUI Owner 内提出最小 API、生命周期与失效行为；不取私有 handle、不直接接管全局 screen、不复制 GUI Runtime 或图形 Manager。按 ADR-0016 维护必要补丁，不修改原始 managed_components。
- [x] 核查公开多点触摸和音效接口，不复制原作 driver_data magic、直接 BSP 或原作音频 Owner；所缺能力显式列出。
- [x] 在 records 写入可审阅的最终依赖/API/许可证清单与未决项。发现需要改变已确认产品行为或既有架构决定时重新讨论该分支，不用 fallback 静默降低范围。
- [x] 文档检查通过；新增验证实现时按 firmware 检查要求执行。

## Comments

2026-10-09：已有源码与头文件初查，详见 [记录](../records/2026-10-09-scope-and-capability-frontier.md)。完整来源与接口结论未完成；本票不是实施已成功的证据。

2026-10-12：[完整来源与边界核查](../records/2026-10-12-source-and-boundaries.md)已锁定上游及官方 QMI8658 2.0.0 对应源码，28 个原始文件进入版本化输入并有摘要/许可门槛。自绘、多点输入公共 seam 已选定有界挂载方向，实际实现验证转交 10；不将原作模拟器或源码存在当作 App 已移植。

## Resolution

来源、素材归属、七个 App 实际依赖、官方 IMU/HID 兼容条件与最小 GUI 接入方案已经记录。公开挂载和输入资格的实现/失效回归由 10 持有，03–07 的代码仍需实施。来源锁测试和 Markdown 检查通过；本票关闭只代表核查/接入选择完成，不代表新 App、驱动或无线已可运行。
