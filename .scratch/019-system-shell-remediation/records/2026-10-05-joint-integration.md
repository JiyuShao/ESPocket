# 019 四线联合整合与回归

日期：2026-10-05。用户授权把四个 chat 的交付整合入当前 checkout，同时继续原 Store Flappy timer 延迟优化。

## 整合范围

| 交付 | 合入内容 | 尚未完成的条件 |
|---|---|---|
| System 可靠性 | Display 已启动但角色选择失败的清理；Core partial init；Shell 失败启动清理；全量受管 App stop；保存主题不可用时临时 Dark 回退；关键启动失败诊断 | 在途 callback 停止安全、System-owned pending dialog 撤销、同对象各三轮产品生命周期与关键失败真机路径 |
| Overlay 与 Loading | Core 请求有效性查询；Dialog/键盘/Loading 仲裁；键盘 Back；PWR 提交边界；呈现计时与 Owner 期限分开；隐藏失败保留 userdata；现有 App Loading seam | 同步启动中的 PWR 响应、250 ms 目标、Super Startup 与图标动画、真实触摸/实体键竞争路径 |
| 资源构建与视觉 | staging 删除旧成员；产品资源门槛；Board Manager override relocation；锁定版构建工具核查；017 剩余证据归属 | Light/Dark 普通按钮、箭头、字形和物理面板的剩余视觉证据 |
| Super 功能兼容设计 | 状态、调试、多语言、即时主题、完整 Files、显示源、手机配网、扩展提示的 Owner 与依赖设计 | 设计中明确的四组产品规则仍待选择；未导入新功能实现或组件 |

三方整合以每条隔离交付的 baseline/working 为基础，保留当前原包性能优化；备份及合并记录保存在 `/private/tmp/espocket-019-integration-20261005T220401/`。49 项直接应用、12 项自动三方合并、6 处冲突逐处处理；最终结果以当前代码与 checks 为准。

Core 原 001–011 补丁完整保留；新增 `012-initialization-cleanup.patch`、`013-overlay-request-validity.patch`、`014-refresh-staged-package.patch`。三项均在当前前序补丁后重新生成并准确应用，canonical 与 scheduler alias 使用同一组合，manifest 固定源 inventory/hash 和移除条件。没有改写 managed_components 原件。

## 整合后发现的回归

Loading 与 Dialog 成功隐藏后仍保留 invalidated，每 50 ms Shell tick 重试空 Overlay 并取 GUI 锁。单独修 Loading 后回归仍 RED，定位到 Dialog 的同类路径。两者均在没有 overlay 时提前返回，成功删除后清 invalidated；GUI hide 失败仍保留原重试和 userdata 安全边界。

真实 Shell tick 回归验证关闭后连续五次 tick 不取 GUI 锁，INVALID_APP_ID 的空 Loading hide 也不取锁；RED/GREEN 原日志在 `/private/tmp/espocket-loading-{red,green}.log`。Shell 失败启动 guard 同时 reset Loading 状态。该修复消除整合带来的空锁，不能据此宣称原 Flappy 延迟全部修好。

Host 夹具同步了真实 Loading、mutex、Overlay 与包验证复用接口；干净 CI 的依赖准备工具补齐实际读取的 14 个锁定组件，源码 hash 验证通过，不下载或手改依赖源码。

## 验证边界

整合后全部 Owner suites 与 117 项跨模块 host tests 已通过。App 联合构建与实际镜像准确输入已核对；性能优化后的最终普通镜像和设备结果在[延迟优化记录](../../005-m5-application-ecosystem/records/2026-10-05-runtime-timer-latency.md)归档，四线 ticket 保持各自未完成条件。

设备操作仅 App 分区 `0x60000`、受控 reset、USB 合成输入及截图；不刷 LittleFS/NVS。合成输入和 reset 不替代物理断电、真实触摸或实体键证据。正式发布的发布者、签名目录与 Catalog 权限仍未准备。


2026-10-06 更新：联合全部 Owner suites 与 120 项跨模块 tests 通过，271 Markdown checks 通过，完整固件 build/resource staging/LittleFS 生成通过。最终无临时 GUI 探针 ELF 为 8d7912fd9，准确输入已核对；因串口审批超时与默认沙箱访问拒绝，尚未刷入及完成最终联合真机验收。具体候选失败、旧对象清理、设备当前镜像和未完成的性能条件以 005 延迟记录为准，所有 tickets 保持开放。


2026-10-06 恢复：用户同意后，8d7912fd9 App-only 刷入并完成启动、hello 与 Watch Face snapshot。首轮性能/截图序列因另一 USB 客户端请求混入而 FAIL，未完成双轮与最终联合验收；先前访问阻塞已解除，现待设备测试独占确认。详见 005 延迟记录。


2026-10-06 最终联合验收：普通镜像 f5f67952c 完整构建、13 个准确补丁输入、全部 Owner suites、120 项跨模块 tests 通过。原包两轮稳态 timer mean=35.416 ms、max=50.032 ms、queue=3.288 ms 达到本次工程门槛；含启动边界最高 68.063 ms。70 秒前台压力、最终两轮待机/运行与 Launcher 五图（全部实际查看）、受控 reset 和完整 Apps 回归均 PASS，结束为点亮 Watch Face、无前台 App。主要修复以有界 FIFO 恢复上游异步 source 接受契约，避免 App 回调同步等待 GUI；具体镜像摘要、报告和语义边界见 005 延迟记录。四线已整合，Super 保持设计交付；上表的未完成条件、持续 30 FPS 与物理/发布门槛未关闭。
