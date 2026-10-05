# System 与 CircularShell 初步差异矩阵 — 2026-10-04

本记录为源码审计，不证明故障已在设备复现或修复。审计讨论和当前状态由 [01 ticket](../issues/01-audit-system-and-shell.md) 持有。本轮使用源码与已有证据，不新增测试、构建或设备操作。

## 调查边界

项目读取当前工作区，存在其他任务未提交改动，结论不是单一 Git commit 的完整镜像证明。产品基线应结合 [firmware lock](../../../firmware/dependencies.lock)、[补丁入口](../../../scripts/firmware/build_patched_firmware.py)及各验收记录判断，不把原 managed source 等同补丁后的生产行为。

上游固定为 ESP-Brookesia `e937455b0db1a3e873b1da61d6d13652f3dcc7e2`，只读源码在 `/tmp/espocket-brookesia-review-20261004`；参见 [Super tree](https://github.com/espressif/esp-brookesia/tree/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super) 和 [example tree](https://github.com/espressif/esp-brookesia/tree/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/system/super)。Super 不是行为正确性或可信包发布条件的替代标准。

## 已有覆盖与产品差异

| 范围 | 项目事实 / 参考 | 判断 |
|---|---|---|
| 装配与 Shell carrier | [System](../../../firmware/components/espocket_system/src/system.cpp) 直接继承 Core，显式安装隐藏 Native Shell、Reference Apps、Settings 和 Store | 已有覆盖；不需要引入 Super System |
| 前台与页面 | [lifecycle](../../../firmware/components/espocket_system/src/system_lifecycle.cpp)、[navigation](../../../firmware/components/espocket_system/src/system_navigation.cpp) 跟踪 Core AppId、foreground generation、Navigator 与 Runtime Screen Flow | 项目有额外产品约束；不能以 Super foreground setter 替代 |
| Home / 恢复 | [power](../../../firmware/components/espocket_system/src/system_power.cpp) 实施 PWR Home；失败恢复可回启动来源，正常 Home 到 Watch Face | Super Launcher Home 是不同产品选择，已有 INT/APP 契约不重问 |
| 同类 Overlay 身份 | [keyboard](../../../firmware/components/shell_circular/src/shell_keyboard.cpp)、[dialog](../../../firmware/components/shell_circular/src/shell_message_dialog.cpp) 持有 Owner/request 身份，Core 持有 Dialog 队列 | 已有覆盖；不再创建 Shell 请求队列 |
| 状态 | [shell_status](../../../firmware/components/shell_circular/src/shell_status.cpp) 订阅 Wi-Fi、Battery、SNTP，有首次读取和周期刷新 | 已有覆盖；Super status 同样有 callback 直接进入 GUI 的路径，仅 expansion 显式收集后由 App timer 处理 |
| 动态 Launcher | 当前固定 JSON entry，启动时用 manifest identity 查 Core；[005/04](../../005-m5-application-ecosystem/issues/04-project-dynamic-launcher-from-core.md) 已定义 full reconcile、dirty generation、replacement subtree 后 swap | 已有目标设计尚未实施；Super 先删旧 view 再建新 view，不满足项目失败保留旧完整投影的要求 |
| 主题 | [System theme](../../../firmware/components/espocket_system/src/system.cpp) 在 App 文档前注册 dark/light，并恢复 Core 保存偏好 | 注册顺序已有覆盖；未知保存值/应用失败直接启动失败，回退策略待决 |
| 打包 | [project_include](../../../firmware/components/espocket_system/project_include.cmake)、[main CMake](../../../firmware/main/CMakeLists.txt) 使用 build tree staging 与 Runtime stage dependency | 已有覆盖；字体/语言资源若引入需另补镜像依赖 |

## 生命周期故障边界

- [Display startup](../../../firmware/components/espocket_system/src/system_display.cpp) 在 source.start 成功后，SetActiveSourceRole 失败直接返回；产品 init 在该错误分支未完整回收已获得的 source/binding。确认为代码控制流缺口，尚未注入验证。
- 锁定 Core 在调用产品 on_init 前设 initialized；[System init](../../../firmware/components/espocket_system/src/system.cpp) 在 Core init 失败后主要关闭 Runtime provider 和 Display，未完成部分安装/系统资源的统一回收。更早的 Core 初始化失败也有 initialized guard 限制。清理必须在实际 Owner 内处理；Super 也不能作为完整 rollback 范本。
- Native on_start 失败不经过正常 on_stop。Shell [start](../../../firmware/components/shell_circular/src/circular_shell.cpp) 获得 Display binding 后，gesture 配置失败的分支未 release。需以失败点核对获得与释放关系。
- Core 部分 GUI cleanup scheduling 失败只 warning，业务 on_stop 成功仍可报告 Stopped；这是状态与回收结果的待验证边界，不能推断已发生 GUI 泄漏。
- 产品 stop 当前停止交互入口、Shell 和前台 App；Core stop 本身不等于停止全部 App。deinit 另执行逐 App/Core/GUI 释放。stop→start、deinit→init 与 Shell Error 恢复的产品保证尚待明确。
- Runtime failed-stop cleanup 与 queued callback 已有维护补丁及 [005/07](../../005-m5-application-ecosystem/issues/07-isolate-runtime-keyboard-results.md) 验收路径；不复制任务，不以原版 Core 缺口否定补丁证据。

## Overlay 与输入边界

- 产品未实现 Core App loading 呈现 hook；Core 默认 hook 返回成功空实现。Core 自带可选 launch transition，当前产品未启用。App loading、启动转场和长任务取消是不同责任，新增界面不能证明启动期间 PWR 响应。
- keyboard 与 dialog 分别创建 top layer，跨类没有显式优先级。对象创建和 dialog 重建影响视觉先后，需要产品仲裁规则。
- 默认 Back 在 keyboard/dialog 下隐藏，但 Display gesture 路径只检查 dialog 设置的 modal 状态；keyboard 期间仍可能产生底层 Edge Back。键盘关闭与页面导航的关系待决。
- Shell timer 先交付 keyboard/dialog 选择，再通过 host.tick 消费 PWR。同一消费周期两者都待处理时，当前可能先交付确认；需明确尚未提交与已提交的结果边界。
- Screen Off 保留 Overlay 状态，dialog deadline 继续流逝；system-owned dialog 不随 App stop 自动消失。Home、息屏和自动关闭之间的规则待决，不能把息屏等同停止 App。
- keyboard/dialog LVGL 回调记录选择，App timer 完成请求。dialog hide 失败已有 retry；keyboard 清理失败仍交付结果及 stop 中 userdata 释放需要后续故障回归。
- 当前产品启动后一次选择 GUI source；临时系统层没有非 GUI source 保存/恢复机制。此能力属于非 GUI App 的条件性前置，目前不认定普通 GUI 路径已缺陷。

## 状态、语言与候选增量

- Wi-Fi 部分过渡态合并显示 off/unlinked；Battery 未细分充电/不存在/读取失败；时钟需要 IsTimeSynced 成功才显示，否则 `--:--`。可改进状态表达，先确认产品收益再分配实现。
- callback 持有产品状态锁进入 GUI，SNTP callback 还同步读 Service；线程/停止安全应以锁图和后续回归判断，不从 Super 推断无问题。
- 本项目环境为英文，键盘和弹窗使用 Montserrat，无产品字体索引/语言 hook；manifest 的中文名称不等于中文产品支持。
- 运行中主题变化后所有原生 Surface/Overlay 的刷新尚无产品保证，不能从两套主题资源或 Super 的 refresh_environment 推断全树即时更新。
- 中文字体/语言、Files、非 GUI source、完整诊断界面等列为候选；首批增量范围待用户确认。构建分析可单独实施，当前审计只给建议。

## 后续证据清单

待设计收敛后按具体 ticket 定义失败注入、资源获得/释放、restart、Overlay 竞争、迟到结果、PWR 延迟、息屏计时、持久偏好回退和状态停机测试。本轮不执行，也不凭静态分析勾选设备或视觉条件。
