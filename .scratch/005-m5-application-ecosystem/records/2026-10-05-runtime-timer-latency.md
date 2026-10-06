# 原 Store Flappy timer 延迟与联合整合

日期：2026-10-05。目标为减少 33 ms game timer 在 GUI 负载下的实际间隔，分别测量锁等待、布局、回调和绘制。

## 固定边界

同一 ESP32-S3 设备 `A0:F2:62:E3:0B:68`、原 Store BPK SHA256 `ffdf1250f6be38377fe46617b6e0cca196cad4a388f9009edcdf87045165297a`。不改原包、33 ms 请求、输入期限、App 生命周期、Core priority=10、LVGL priority=6、双 40 行或 512 KiB 图像缓存。

两轮各先 IDLE 8 秒，再原 start 输入、无 jump 运行 4.5 秒；测量期间不截图。完整第二 RUNNING 窗口的暂定判据为平均不超过 36 ms、峰值不超过 66 ms，早于本轮候选实测设定；它是本轮工程判据，不等于用户明示的产品 SLA。FPS 使用最后一段 flush 完成后的完整刷新计数，不能用回调次数或空刷新冒充。

测量后捕获不可变帧，再 PWR Home 后下载同一帧，降低游戏与截图缓存同时占用连续内存的压力。所有截图实际检查 start 消失和管道；下载阶段的 timer/解码压力另标 after-game，不纳入运行性能。

## 单变量结果

| 镜像/阶段 | 完整第二 RUNNING timer 平均 | 峰值 | Owner queue 平均 | 判定 |
|---|---:|---:|---:|---|
| 普通基线 fb7055e85 复测 | 46.623 ms | 86.489 ms | 17.844 ms | RED |
| 四线整合、空 Overlay 重试已修 bf9227938；临时 GUI 探针 | 49.299 ms | 78.371 ms | 17.752 ms | RED；消除整合额外取锁，但旧延迟仍在 |
| 不透明 PNG 原生 RGB565 6fb23477d；临时 GUI 探针 | 41.791 ms | 106.181 ms | 12.361 ms | RED；均值有收益，峰值未解决 |
| 即时唤醒 + ESP 等待时钟修复 52d6e9f57；临时 GUI 探针 | 41.543 ms | 106.209 ms | 12.308 ms | RED；启动正常，idle timer 约 34.57 ms，game 仍排队 |
| 保留一个待执行 periodic callback 6f1091374；后来确认增量构建仍含旧 GUI 探针对象 | 42.762 ms | 117.015 ms | 17.459 ms | RED；同步 timer 诊断输出仍在 App 域，不能宣称队列改动已改善性能 |

临时分段探针显示：GUI guard 等待平均约 10–12 ms，最高约 36 ms；guard 内工作约 4.3 ms、props 约 1.7 ms、relative layout 约 1.2 ms。换帧的同步 SetViewSrc 在同一 App 回调域内等待 GUI 完成，也使 game 排队；因此不能把主要延迟归咎于约 1 ms 的布局或继续只改布局。

PNG 候选将完全 alpha=255 的 PNG 在首次解码时转为 RGB565，缓存暖后不逐帧扫描 alpha；透明 PNG、非 RGB565 display 与转换分配失败均保持原 ARGB8888 路径。原背景 196×150 和 icon 不透明，grass/bird/pipe/start 仍有透明度，原文件不改。真实 decoder 调用点覆盖内存/文件来源、16 位像素、alpha=239、padding、其他 display、分配回退及解码失败清理，原版 RED、候选 GREEN。该轮纯 game 的绘制平均约 21.08 ms，普通基线约 24.07 ms；完整刷新样本包含阶段边界，不能据此宣称稳定 30 FPS。

另一个单变量为 Lib utils idle worker 的即时唤醒：保留一轮一个 dispatch 和 busy 后 1 ms 让步，空闲时用 Asio run_one_for 等待新任务/到期 timer，避免 poll_one 后睡完 poll interval 才看到任务。真实 Boost/实际 worker block 的入队唤醒回归旧循环 RED、新循环 GREEN；连续 ready queue 公平性仍 GREEN。首次真机候选 `58cbcb9d4` 90 秒内没有完成启动，未通过，已恢复可启动的 `6fb23477d`。host 唤醒通过不构成该设备路径通过。

进一步核查 esp-boost 0.6.0：`posix_event.ipp` 的 ESP 分支以默认 CLOCK_REALTIME 初始化条件变量，但 `posix_event.hpp::wait_for_usec` 使用 CLOCK_MONOTONIC 的绝对期限。新 run_one_for 触发这条不匹配路径，立即返回后反复重试，空闲调度负载上升；这是本次候选暴露的等待时钟问题，不能倒推原 poll_one 基线也一直在该路径运行。新增锁定版 Boost 补丁，仅 ESP 分支改用默认条件时钟 CLOCK_REALTIME，其余平台保留现有等待。真实方法配合默认时钟 pthread condition 的 timeout/early-signal 回归，旧版 RED（20 ms 等待立即返回）、新补丁 GREEN；完整构建与真机联合判定继续执行。

## 失败保留

未修空 Overlay 重试的四线临时镜像 `0ffb3d7ec` 在第二轮测量后的截图下载阶段触发 IDLE0 watchdog；原报告 FAIL，不能算整合验收通过。发生于 after-game-1，backtrace 位于 System0 Runtime 同步 Service 返回；仅凭这次 trace 不宣称根因已修。随后改为捕获后 Home 再下载，bf9227938 和 6fb23477d 两轮序列通过、结束 Watch Face、没有 watchdog。截图下载阶段仍可见长锁等待，排除于纯性能数据但保留为压力证据。

本轮原始证据保存在 `/private/tmp/espocket-m5-reviewed-<identity>/`。基线报告 `47abb07f-b7a2-42fa-9a0b-b0c5098a8d20`，bf9227938 报告 `4995d7e1-a8e9-4299-8143-694d6a5bf4bd`，6fb23477d 报告 `8792d2b5-74a2-4709-95c4-2bc1c829a3de`。GUI 探针属于临时构建，最终必须移除 hook/补丁并复核普通镜像。

四份其他 chat 的交付归[019 联合整合记录](../../019-system-shell-remediation/records/2026-10-05-joint-integration.md)。正式发布、包失效矩阵、物理路径、System 重复生命周期、启动 PWR 250 ms 和 Super 未选择规则不随性能收益关闭。


## 有界 timer 和观察者效应

原 periodic pending 标记同时覆盖已入队和正在执行的回调。015 候选在开始 dispatch 前释放待执行槽，使同一串行 App 域最多一个正在执行和一个待执行；后续到期仍合并，不并发调用 JS、不增长为无限补帧。真实 periodic enqueue/dispatch 回归验证一个回调中到期八次仅排一个后继、后继标记不被旧回调返回误删、Native/Runtime、停止撤销、post 失败清理。原版 RED、新候选 GREEN；单变量真机上未取得通过，故不能仅以该 test 采纳收益。

进一步核对测量本身：TimerProbe 在仍持有 App callback gate 时同步输出每个 2 秒窗口的长串行日志；PNG/绘制探针此前已经异步输出，但 timer 没有。016 候选将不可变 snapshot 投递到不持有 App/GUI gate 的独立诊断 group，每个 timer 最多一个 outstanding report，IO 慢时计数 reports_dropped，post 失败释放槽，停止后的样本只持有自己的计数和共享 probe，不访问 App。真实 TimerProbe 回归从同步日志 RED 到异步队列 GREEN，并覆盖有界消费者、发布失败和 wake/queue/callback 分离。测量判据拒绝有丢报告的完整窗口。此处改变的是诊断输出路径，不能把观察者干扰减少全部算成产品绘制收益；最终以普通联合镜像复测判定。


## 2026-10-06 当前交付状态

异步日志候选 c80a91ded 的完整第二运行窗口仍为 43.529 ms、峰值 109.951 ms、queue 19.106 ms，reports_dropped=0，未达标。日志观察者效应候选没有证明足够收益，不能称其解决了游戏慢。

清理临时 GUI 探针时，恢复源文件保留旧时间戳导致增量构建复用旧对象；nm 确认 6f1091374/c80a91ded 路径仍含临时符号，已重新标记，不能作普通镜像验收。随后强制重编 runtime_render_probe.cpp、GUI backend.cpp/layout.cpp，最终 8d7912fd9 的 ELF 经 nm 与字符串核查均无临时 GUI 符号/日志载荷；源码探针文件已删除。同步工具的内容变更复制会更新时间戳，避免再次复用旧对象。

最终普通联合构建 8d7912fd9（BIN SHA256 b5688bcc0e591238e5202f4c0be8173d898edcb35217827f94779c7396c4d6c2）完整 build 通过，含 staging/resource gate 与 LittleFS 生成；仅构建，不刷文件系统。13 个准确组件 inventory/manifest/path、registry lock、glyph、九个内置成员摘要与 embedded ELF hash 均核对；全部 Owner suites、120 项跨模块 tests 与 271 Markdown checks 通过。

最终镜像尚未刷入：App-only 刷写的自动审批连续两次超时；默认沙箱尝试在打开串口时被 Operation not permitted 拒绝，未开始写入。设备最近成功启动的镜像仍为 c80a91ded（含旧临时探针对象），最近序列结束于 Watch Face。已请求恢复同一已授权 App-only 范围的访问，尚未得到答复。最终普通镜像的 timer/压力/截图/Apps/reset 仍待执行；当前源码未提交 Git。本轮并未完成用户的游戏延迟目标，后续需继续定位同步 source、GUI 锁和 callback 负载，未通过候选不得作为已验收默认交付宣称。


2026-10-06 恢复验收：用户明确同意后，App-only 刷写完成；USB hello 返回 8d7912fd9，出现 ESPocket started，初始 snapshot 为已点亮 Watch Face，无前台 App。先前串口审批阻塞已解除。

普通镜像首轮报告位于 `/private/tmp/espocket-m5-reviewed-8d7912fd9/render-perf/b034f567-b418-4a76-bb6c-2526019bc435/report.json`。序列 FAIL：截图下载到 offset 258560 时混入另一客户端 request_id 的 hello/PWR 响应，随后 screenshot.read 超时；未完成第二轮，不满足双轮验收。没有观察到 panic，清理 snapshot 已回到点亮 Watch Face。已请求其他 chat 暂停同一设备测试，等待独占确认后重跑。

仅作诊断线索，game-0 最后完整窗口为 callbacks=49、periods=49、period_total_us=2091658，平均 42.687 ms、峰值 114.495 ms、queue 平均 18.087 ms、reports_dropped=0；该单轮仍未达标，不能宣称性能通过。暖机运行 PNG 解码次数为 0，说明重复解码已不是这个窗口的主要延迟；同步 game/flap 回调与 GUI 绘制持锁仍需继续处理。最终压力、截图矩阵、Apps/reset 联合验收及 Git 提交尚未完成。


2026-10-06 独占复测：首个无截图采样因连续 invalid_state 未开始，保留失败报告 0145768a-eda9-4db0-939b-687bd74e24c3；日志还出现实体 PWR 短按。受控 reset bec194da-e8b2-4ed8-9dcd-d298a254cfc0 通过 hello/startup/Watch Face 后，两轮无截图序列 1494207c-0dd4-4e94-8818-465a3d3357dc 完整执行并回到点亮 Watch Face，但性能 verdict 为 FAIL：mean=44.946 ms、max=150.157 ms、queue=20.844 ms。该测量没有截图下载，也没有修改原包或 timer 周期。

下一单变量 017：timer 样本虽已在独立 scheduler group 输出，仍使用 priority=10 的共享 Core worker，可能抢占 priority=6 的绘制。仅输出期间降至最多 2，作用域结束恢复原优先级；不修改 App/GUI worker 的正常运行优先级。实际 TimerProbe 输出调用点回归先 RED（输出仍在 10），候选 GREEN（输出最多 2，输出后恢复 10）；有界队列、失败发布与分段指标保持通过。候选性能与稳定性暂待构建、刷入及测量，不能作为已解决结论。


017 真机 ae63fa7d7 构建、准确输入、App-only 启动及两轮无截图序列 cf9f1db8-cabe-4ce5-84a1-1998eb6e8863 通过；性能 FAIL：mean=46.025 ms、max=137.777 ms、queue=20.547 ms，不能宣称降优先级解决游戏延迟。固定第一/第二 game window 对比显示管道进入画面后回调和绘制增加；管道在第 70 tick 创建，原 PNG alpha 仅 0/255。

下一单变量 Decoder 002：仅将二值 alpha PNG 在 RGB565 display 转为 RGB565A8，保留准确 alpha 平面与半 RGB stride；半透明、非 RGB565、绘制格式未启用、分配失败仍使用 ARGB8888。原包的 pipe/start 可使用该路径，grass 和三张 bird 因半透明仍不变。真实 decode 调用点旧路径 RED、新路径 GREEN，包含 file/memory、奇数宽 padding、RGB 与 alpha 像素、半透明及失败清理；尚待完整构建和原包真机测量/截图。


Decoder 002 联合 ed2013289 完整 build、准确输入、App-only 启动和两轮无截图 e63b1a6b-5e1a-4faf-8b44-a99780762bca 通过；性能仍 FAIL：mean=41.860 ms、max=108.825 ms、queue=15.781 ms。全运行样本 draw mean=19.91 ms、max=46.931 ms，暖机 PNG open=0，PSRAM min=400780；较前一候选降低平均/峰值，但不能称达标或持续可玩。

下一候选 018 针对根因同步 source 等待：上游 SetViewSrc 原本异步接受，011 为防止无上限 source tasks 分配失败，改成阻塞 App 等 GUI。现在以真实 Core Owner 的有界 FIFO 恢复原契约：返回接受/拒绝，渲染错误按上游在 GUI Owner 报告；最多 8 条/32 KiB 待处理，最多一个执行批次与一个排队后继，所有被接受的 source 保留顺序，满队列立即拒绝，不静默改成最新帧。buffer 绑定 document，停止、卸载、partial-start unload 与全量 deinit 撤销；同一 preload DOM 重启也创建新 buffer，旧闭包持有的 buffer 已失效。

真实 Core 方法/队列回归旧同步路径 RED（GUI 阻塞 100 ms 时 App 提交不能在 50 ms 内返回），候选 GREEN：接受前 8 项、拒绝 200 项超额、最多一个等待任务、按序应用、延后渲染失败报告、同 DOM stop/reopen 撤销、全量关闭撤销、调度失败后可重试、字节上限。这里有意撤销 011 增强的“返回时已绘制及立即返回 source 错误”语义，恢复锁定上游的“已接受异步任务”含义；原包、timer、JS 生命周期及输入 TTL 均不修改。候选仍待全量 checks、构建、真机性能/压力/视觉验收。


018 联合普通测量镜像 f5f67952c（ELF SHA256 f5f67952c07b01f74c186b3f52ffcac6f4dbfb04f8cddd626fe2c8fbc06bacb5，BIN SHA256 6cce51775ad276e1d5c41140124b922a94a886c2e14e682c2b3970782bc176ae）完整 build、13 个准确输入、原内置成员、App-only 启动、120 个跨模块 tests/全部 Owner suites 与文档检查通过。两轮无截图原包报告 f2d71bf6-aadd-4c40-9c53-8fa3a2a5edf2 完整通过；固定第二 RUNNING 窗口 verdict 首次 PASS：mean=35.416 ms、max=50.032 ms、queue=3.288 ms，reports_dropped=0。前一普通候选同口径为 44.946/150.157/20.844 ms，延迟均值约减少 21%，App 排队约减少 84%。全 RUNNING 标记下（含启动边界）平均 35.26 ms、最高 68.063 ms，不能把 50 ms 描述为所有阶段的硬上限。

70 秒前台压力 bc8f0cb8-97e0-4877-80a2-0a8f07423ae1 PASS：33 个纯 IDLE 绘制窗口，PNG open=0，PSRAM min=400388，largest min=294912；后续 RUNNING game 平均约 35.33 ms、峰值 51.772 ms，绘制约 20.29 ms，PNG open=0。没有 source 队列满/应用失败、decode failure、watchdog 或 panic；截取不可变帧后先 Home 再下载，最终回到点亮 Watch Face。active-0.png 已实际查看，启动按钮移除、鸟/上下管道/背景和草地均可见。截图/退出阶段的解码和长绘制被保留为 after-game，不能用于宣称游戏帧率或 timer 回归。

二值 alpha ed2013289 的两轮待机/运行与 Launcher 五图 b94dce39-9d7c-4f1d-963c-735c03177d22 PASS，并已实际查看五图；透明管道和启动按钮无可见黑底/错位，返回后 Launcher 完整。最终 f5f67952c 的五图 f4498d39-0de2-4a52-bff6-9f50759e830d PASS，五张图均实际查看：两轮新启动的待机/运行画面及缓存后的 Launcher 完整，无可见透明黑底或损坏。受控 reset 92f07257-360d-4f29-863a-7417f295cf97 与完整 Apps 回归 20261006T024421Z-56b49bf7-b76c-4f15-aa99-b9991557b2ea 均 PASS，hello 确认 f5f67952c，结束 snapshot seq=1212 为点亮 Watch Face、无前台 App。短窗口完成 FPS 曾到 31/32，但存在阶段混合和显示工作负载，持续 30 FPS/可玩性仍不据此关闭。当前性能改善主要来自避免 App strand 同步等 GUI source；布局约 1 ms、正常运行 PNG 重解码不是剩余 timer 的主要原因。


最终原始 Apps 报告：`/private/tmp/espocket-m5-reviewed-f5f67952c/apps-regression/20261006T024421Z-56b49bf7-b76c-4f15-aa99-b9991557b2ea/report.json`。本次 timer 优化与四线代码/设计整合的联合交付完成；各票中的持续 FPS、包失效矩阵、产品规则和物理/发布门槛保持开放。source FIFO 回归另覆盖执行中八项后继的全部十六项按序应用，最多两个任务（一个执行、一个后继）。
