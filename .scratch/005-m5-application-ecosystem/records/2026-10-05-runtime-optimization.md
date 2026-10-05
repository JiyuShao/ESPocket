# 2026-10-05 Runtime 分阶段优化

用户授权依次执行 PNG／内存、GUI 更新、锁与调度、显示路径优化。保持 Store 原 Flappy BPK；使用既有 App-only 刷写、受控重启与合成输入授权。不刷 LittleFS，不读取 NVS 或全片 Flash；不改变包信任、Running Instance 或输入期限。

## 基线与判定

前置[硬件／软件诊断](2026-10-05-runtime-bottleneck-diagnosis.md)继续有效。基线 `a2df08485/render-perf/e87f2d92-70a4-4e69-a843-cb2314205a5c/report.json`，诊断循环 `/private/tmp/espocket-assert-playability.py` 再次输出 `FAIL completed FPS median=4.5, timer period=80.19ms`。25 FPS／40 ms 是诊断目标，不新增产品验收契约。

每个候选独立记录准确源码／补丁输入、配置、镜像、无截图游玩窗口、真实 ExecuteBatch 证据、PNG 成功率与内存；截图、Home／重开及完整 Apps 回归另测。性能窗口不保留截图 buffer。失败候选不得成为默认配置，必要时恢复已验证镜像。

## 第一阶段假设

1. 较小缓存若能保留高频 PNG，并减少 Native／Launcher 图片的滞留，则解码和绘制减少，同时截图仍可分配。先试 256 KiB，保持其余代码和输入相同。
2. 如果截图峰值是主要内存障碍，则明确让缓存为截图让出预算、避免捕获期间重新填满缓存，会比单次失败后清空再试更可靠；仅在第一项证据需要时实施，不能重复宣称已失败的 1 MiB 重试方案有效。
3. 如果资源释放频繁使描述符缓存失效，则有缓存仍会反复解码同一帧；先核查真实资源引用和解码记录，不能延长失效描述符生命周期或保留更新前资源。

原包 PNG 只读元数据：背景 196 × 150（ARGB8888 117,600 bytes），管道 80 × 400（128,000 bytes），鸟帧各 57 × 41（9,348 bytes），草地 34 × 30（4,080 bytes），开始按钮 100 × 61（24,400 bytes），图标 92 × 92（33,856 bytes）。全部为 truecolor／RGBA，不能把 `use_indexed` 当作无损降内存开关。256 KiB 足以容纳若干高频图片，但是否抖动或驱逐仍须真机证明。

## 执行状态

先构建 256 KiB 单变量候选。普通源码默认缓存仍为 0；只有性能改善、无解码失败且截图／生命周期回归通过后才改变默认值。GUI、调度和显示候选按顺序在此前已接受结果上推进，具体补丁与结论另追加。

## 256 KiB 单变量结果

镜像 `06589f763`（ELF `06589f763ce2387f93bce13eb31396b9dcbfceddf8dd723510cafeaa4fee58a3`），准确输入核对、App-only 刷写与 boot／hello 通过。原 BPK 未修改。无截图报告 `render-perf/178a0836-ce44-482a-b472-5aadfb2dd308/report.json` 收集通过；10 个完整游戏窗口共 20.402 s，PNG 5.20 次/s、10.55 ms/次，draw 23.41 ms，完成 FPS 中位 8，33 ms timer 实际 72.69 ms（wake 17.18、queue 30.09、callback 5.27 ms）。输入实际执行 8／5 次；有 17 次 snapshot invalid_state 重试和两条日志穿插，不能把缺失窗口当作通过。Home 通过，无 PNG 失败。

截图报告 `cache-screenshot/e100a29a-2d87-46a8-ada0-76049c4ec4b5/report.json` 为 FAIL（internal）。性能窗口 PSRAM free 最低 582,828 bytes、largest 最低 221,184 bytes；466 × 466 RGB565 截图需要 434,312 bytes。采样提示连续块不足，但不能仅凭通用 internal 判定具体失败点。缓存预算暂不推广。

下一候选只修改截图峰值：在 LVGL 锁内保存实际预算，清空并暂停图片缓存，完成捕获后在所有出口恢复原预算；分配失败记录需要／空闲／连续块大小。真实 capture 函数 host 回归先 RED（缓存非零导致 frame allocation 失败），再 GREEN；覆盖成功、内存失败、hash 失败、不完整帧、unsupported、busy 和原预算为零。保持其余 GUI、调度与显示路径不变，再重复真机矩阵。

## 截图暂停缓存候选：拒绝

`8d9bf3c1e`（ELF `8d9bf3c1ed862ec2ce6206e47e3524348bcba916f04160a978d493dea028aaf3`）准确输入、9 组件 inventory、完整 App 构建、boot／hello 通过。无截图报告 `render-perf/dc816202-994a-4ee4-a058-59f8ab236676/report.json` 收集 PASS，跳跃 ExecuteBatch 9／8；41 次 snapshot 重试及一条不完整 timer 日志保留。10 个游戏窗口 23.153 s：PNG 3.33 次/s、11.51 ms/次，draw 27.69 ms，FPS 中位 6，timer 84.28 ms。与首轮有明显波动，不能把绘制缩短等同于稳定帧率。

截图报告 `cache-screenshot/588f0b75-aa51-4a4e-a83c-d7233294e4ac/report.json` FAIL。前三张已完成下载／摘要核对，但 Flappy 刷新出现 PNG 分配失败，截图完整覆盖不能证明画面内容正确；第三张 Launcher 后重开 Flappy 的 frame allocation 失败。具体 log 为 `need=434312 free=741704 largest=344064 cache=262144`，同时有 busy 重试。不能采纳该候选。

下一候选将 screenshot pixel storage 改为逐行无损 RLE／raw（较小者），每次只分配一行；保留完整覆盖检查、canonical RGB565 SHA256、512-byte 读取、60 秒过期和 release／disconnect／mode-off 清理。捕获仍清空并暂停图片缓存，所有出口恢复预算。fragmented host heap 先拒绝原连续 12-byte frame（RED），逐行候选通过（GREEN）；另覆盖高熵 raw、跨行奇数字节读取、重叠改写、越界及分配失败不产生完整帧。尚待完整构建及真机重新解码／截图／重开验收。

## 逐行截图候选：内存通过，联合门槛待锁等待

`56b4cb1c3`（ELF `56b4cb1c37b816b70ba9cfb78ff0e8c5737098974ef157a027602ba30aa30e1a`）准确输入、9 组件、完整 App 构建与 boot／hello 通过。无截图 `render-perf/b3bd372d-d207-4410-ad22-b57ee2732e52/report.json` 收集 PASS，31 次 snapshot 重试，jump ExecuteBatch 5／7；11 游戏窗口 23.599 s：draw 28.72 ms、PNG 3.60 次/s、11.97 ms/次，FPS 中位 5；game timer 68.63 ms。与此前缓存结果的波动保留，尚不能证明稳定可玩。

`cache-screenshot/deb855df-3124-47d9-a22d-7604a5059e89/report.json` FAIL（最后一张 screenshot: busy）。前三张完整下载／SHA256 与画面检查通过，实际存储 46,140／43,764／32,208 bytes，无 PNG／frame 内存失败；重开后的锁等待三次超时。内存问题与 lock starvation 分开记录，预算仍不推广。受控重启 PASS；完整 Apps `apps-regression/20261005T091444Z-231b9a48-a4f7-4fe7-aa16-f52d01a3f889/report.json` PASS，含 Native/Runtime 导航、待决 Back、自动息屏未回收恢复及新实例重开。

进入 GUI offset-only 候选时只加入 GUI 0.8.5 补丁，截图与 256 KiB 配置保持相同；不会提前采纳调度候选。调度候选已建立真实 Core group callback、Lib utils configure_group 和 Boost strand 的回归：两个 worker 的同域回调分别进入队列后，其中一个等待 gate 会阻挡独立 timer；原版 RED，同域共享 strand 后 GREEN，串行顺序和现有 gate 保留。该补丁另存 scheduler-candidate.json，只有显式 scheduler-candidate 构建选择，production 不变。

## GUI offset-only 候选

`006610fb4`（ELF `006610fb4ae56326b36dc80e8e3ffcb025651e69c22a9f646371896ac82bc905`）10 组件准确 inventory、App 构建与 boot／hello 通过，未加入调度候选。`render-perf/e9c82865-0c78-4beb-8900-d49afa9ad843/report.json` 收集 PASS，jump ExecuteBatch 7／5，14 次 snapshot 重试及一条不完整 flap 日志；10 游戏窗口 20.397 s，draw 24.57 ms，PNG 5.20 次/s、10.73 ms/次，FPS 中位 8.5，game timer 71.02 ms。相对前一轮 draw 有改善，帧率在此前缓存试验的波动范围内，不能宣称解决卡顿。

截图 `cache-screenshot/8f137de8-ca9a-4639-981d-b3e400db62b6/report.json` FAIL（首张 screenshot: busy，三次锁超时），无截图分配／PNG 错误。继续同域调度候选，production 和默认 cache=0 不变。

## 显示实验输入边界

更正隔离实验摘要中的缓冲类型假设：真实 Generic 分支选择 SPI_WITHOUT_PSRAM，draw buffers 是内部内存，不能把它们写成 PSRAM 双缓冲。当前 profile 为双 40 行；生成板级配置仍为 QSPI 40 MHz、queue depth 2、max_transfer_sz 9,320 bytes。IDF tx_color 按 bus max 分割大块，因此 40 行 LVGL flush 也会拆成多次 SPI transaction，flush parts 不等于 SPI transaction 数。

第四项先试单 80 行：与双 40 行同为 74,560 bytes 名义像素存储，将全屏 LVGL 分块 12→6；不增加总 draw buffer 预算、不改 SPI 频率／queue／bus max。只验证减少 Service/flush 调用是否抵消失去双缓冲重叠的成本；失败或无收益恢复双 40 行。CLI 显式选项记录在 patch-inputs，默认不变。

## 同域调度与显示单变量结果

`93a10f0bc` 保持双 40 行，在 GUI 候选上只加入同域 strand 补丁。无截图 `render-perf/55ab64c8-cfe5-4423-8047-ba4f6cfb942b/report.json` 收集 PASS：draw 22.96 ms，完成 FPS 中位 6.5，game timer 77.19 ms；wake 从 GUI 候选的 21.14 ms 降至 2.99 ms，queue 仍为 46.23 ms，period max 912.84 ms。jump ExecuteBatch 6／7。截图 `cache-screenshot/49451c93-1e3f-486e-8497-729fc711f6d2/report.json` 完成四张，最后 busy；无 PNG／内存失败。调度唤醒改善，但 App 队列仍有长阻塞，不能宣称可玩性通过。

单 80 行 `f274529a1` 的 ELF 为 `f274529a1775dc203d7ea64a5ed425c37a41134c35a966b31650a36ea2d521b0`。无截图 `render-perf/26475d83-c558-4e45-acdb-1467232c3269/report.json` 收集 PASS：draw 22.93 ms、FPS 中位 9、game timer 71.77 ms、wake 3.10 ms、queue 40.38 ms、period max 1069.655 ms；jump ExecuteBatch 8／6。与双 40 行 draw 几乎相同，显示配置不推广。截图 `cache-screenshot/131cb957-ee30-4ae6-96cc-12fa8dc58d5f/report.json` 五张全部 PASS，无 PNG／内存错误，最后回到 Watch Face；这是逐行截图的首个完整真机矩阵通过，但不能由此认定单缓冲改善绘制。

此前 game10s 窗口包含死亡及重置后的 IDLE；原包只有 RUNNING 执行滚动逻辑，IDLE 的 flap 本来为 80 ms。各轮 FPS 中位是混合状态测量，不能用 25 FPS 目标直接判断持续 RUNNING 的可玩性。timer 的实际周期及 Owner queue 延迟仍是独立卡顿证据。保留此前所有数据，不更改 BPK 或用缺失窗口补足指标。

## Shell 队列阻塞假设

在双 40 行同域候选上发现两处 Shell 50 ms timer 的不必要 GUI 等待：`sync_card_hint(false)` 即使没有 hint 对象仍获取无限等待的 LVGL 锁；`refresh_launcher()` 在前台 App 运行期间、5 秒期限检查之前读取 GUI language。Shell timer 与 App 回调共享 serialized App task，这些调用可阻挡所有 App timer。

候选仅在无 hint 且目标为隐藏时提前返回，以及前台 App 可见时跳过隐藏 Launcher reconciliation。保留 50 ms timer、PWR／Back expiry、开发者策略、消息／键盘和输入期限；返回 Shell 后按既有 generation／language／刷新期限重建。真实方法 host RED→GREEN：200 次无 hint 调用不取 GUI 锁，创建／删除仍取锁；200 次前台 App reconciliation 不读 GUI language、不 prepare，返回后原有首次刷新、失败保留和 rate limit 测试继续通过。

独立 `espocket-ecosystem-check-shell.log` 的 Owner checks 和跨模块 106 tests PASS；不沿用较早源码的 check-clean 日志。候选 `68f5aad1e`（ELF `68f5aad1e464cb97e7095302f8f03849da2e69a46f7a0b42fc15c7a6c0c725ac`）App 构建与 10 组件准确 inventory 通过，恢复双 40 行。真机性能与联合回归继续执行，尚不推广候选。

## Shell 首轮与截图锁公平性

`68f5aad1e/render-perf/7da20b8e-bd1a-404d-8a28-16ca7b24c45a/report.json` 首轮 FAIL：最终 snapshot invalid_state，第二轮未执行，不能作为完整验收。已采样 game timer 36.32 ms、wake 3.33 ms、queue 3.70 ms、callback 1.11 ms；IDLE timer 36.15 ms。它支持 Shell 阻塞假设，但不证明持续 RUNNING 帧率。

更正动作证据解释：host_bridge 的 ExecuteBatch profile 只输出耗时至少 20 ms 的调用；以上各轮计数是慢调用日志次数，不是全部输入执行次数。零日志不能证明动作丢失，非零也不能独自区分 jump／death／reset。临时 runner 改为保留慢调用计数及该限制；独立画面验证开始按钮消失与 pipe 出现，不降低输入期限、不修改 BPK。

截图 `cache-screenshot/f30318ff-59cd-4f2f-801a-5998d8579c51/report.json` 首三张通过：IDLE 开始按钮画面、RUNNING 无开始按钮且右侧有 pipe、Launcher-after-cache。实际查看前两张，无缺图。第二次打开的 IDLE 捕获连续三次 busy，矩阵 FAIL。USB task 的正常 priority=3，Core worker=10，LVGL=6，持久的低优先级锁等待仍存在。

新增候选仅在 capture_display_screenshot 作用域内将 caller priority 提至 max(原值、Core worker、LVGL task)，在解锁后及所有失败／异常出口恢复；不提高普通 USB task、App 或 GUI worker 的全局优先级，不改变 2 秒锁期限。真实 capture host 回归在低优先级等待模型先 RED，修复 GREEN，覆盖成功、busy、unsupported、row allocation、hash、不完整帧、原预算零，以及原 caller priority 已高于 GUI 的情况。尚待新镜像联合矩阵，不能提前采纳。

临时截图 runner 的重试 helper 曾因替换错误递归调用自身；该运行已中止、作废，修正后才执行上述三张成功的矩阵。此错误未进入固件源码。跨模块检查分别使用独立日志，避免不同源码代次共写同一证据文件。

## 截图锁候选与连续运行窗口

`68f5aad1e/render-perf/979fe0c0-c5b2-4e27-b8c5-fe4d62b1a608/report.json` 修正 runner 后两轮收集 PASS，最终 Watch Face。17 次瞬态 snapshot 重试、两条不完整 timer profile 保留；慢 ExecuteBatch 日志 17／8。IDLE 的 game timer 36.25 ms、queue 6.23 ms；混合游戏窗口 draw 26.03 ms，timer 97.80 ms、queue 56.60 ms、callback 15.96 ms、period max 4968.089 ms。Shell 修复解决了无必要的待机 GUI 等待，但真实负载中的同步 GUI／动画调用仍能产生秒级等待。

截图锁候选 `8967a7734`（ELF `8967a773466cdc75d554790806534b67deeebb31c00899020ad1c55378133e94`）完整 App 构建、准确输入与 boot／hello PASS。`render-perf/1fb1df26-1129-4c3a-9459-851ff18c2d46/report.json` 是两次 start 后无 jump 的 4.5 秒窗口，窗口结束才截图；第一根 pipe 到达鸟的最短时间约 4.9 秒，因此查看无开始按钮且 pipe 在右侧的画面可确认该段运行工作负载。两张完整 SHA256 和像素检查通过，不修改 BPK。四个 render 窗口的 FPS 6／3／7／5、draw 41.17 ms；有截图跨越的后续 timer 窗口，不能把其 14 秒 queue 等待算入纯性能阶段。初轮两个完整 game timer 样本约 36 ms、callback 4.05／11.25 ms，逻辑频率改善而画面仍慢。此窗口只验证运行负载，不宣称持续游玩通过。

`cache-screenshot/7d2fbaa2-fc1e-4e65-9b71-fc7b03abf5b9/report.json` 五次捕获全部下载，stored 为 46,140／43,596／32,208／46,228／43,384 bytes，无 busy，最终 Watch Face；caller 最小栈余量 20,432 bytes。但最后游玩／退出前 PNG 的 128-byte aligned 128,000-byte 分配失败，伴随 `png_ok < png_open` 与 pressure evictions，联合状态仍 FAIL。说明锁等待得到改善，而碎片化后 decoder 分配仍未保证；不可推广该缓存配置。

下一独立候选保持全部源码、GUI／Core、双 40 行和截图锁修复，只把隔离 sdkconfig 的 decoded cache 从 262,144 增为 524,288 bytes，以检验容纳背景／pipe／鸟帧后减少驱逐是否同时改善性能和分配失败。普通源码默认仍 0。原候选完整 Apps 回归继续执行，不提前更新镜像 pointer。

## 512 KiB 与 LVGL 调度对照

`8967a7734/apps-regression/20261005T102831Z-a92caa8f-32d9-4f54-a2e3-d6d4fae50ebb/report.json` 完整 Apps PASS，受控 reset `5057c2e7-0bae-4761-9e97-bf54599eba4b` PASS。只证明合成输入的导航／生命周期，不覆盖物理触摸／PWR GPIO；PNG 截图故障仍使联合门槛失败。

512 KiB／LVGL priority=6 的 `3f3078b4c`（ELF `3f3078b4ce41d70dbb1f13bbd4f51223d6a58889f4fe8a959507acd0355aed44`）App 构建、准确 inventory、App-only flash、boot／hello PASS。`render-perf/3c5b94d8-c61f-4bd0-bc3a-e5af6c5f2ddc/report.json` 两轮短窗口及窗口后两张截图收集 PASS，无 PNG 失败；9 次瞬态 snapshot 重试及三条不完整 profile 保留。IDLE timer 36.49 ms、queue 4.42 ms；RUNNING 采样 draw 34.67 ms、FPS 7／0／0，窗口有 4.53 秒及迟到的 profile，不能作为稳定帧率改善。PSRAM free／largest 最低 313,236／188,416 bytes。完整截图矩阵继续执行，默认仍为 0。

运行短窗口同时揭示 timer 通常接近目标而 render 完成次数仍低。Core 有三个 priority=10 的 worker（Core 0／1／无绑定），LVGL 固定 Core 0、priority=6；频繁 GUI callback 可能挤占低优先级绘制机会。下一单变量候选保持 512 KiB、全部补丁、双 40 行，仅把隔离 sdkconfig 的 LVGL task priority 提至 10，与 Core 匹配；不改变 Core、Service Manager、输入期限或原包。配置完整保存于各镜像 sdkconfig，未验收前不改变生产构建规则。

## 512 KiB 单变量后续与 priority=10 初测

`3f3078b4c/cache-screenshot/8c1739a7-8357-430a-9473-faf33b2fe3e4/report.json` 五张截图 PASS，20 次瞬态状态重试保留，无 PNG／busy 故障，最后 Watch Face。但随后的原跳跃序列 `render-perf/4e6f057d-1c33-4b43-82db-029d3e0f00ba/report.json` FAIL，日志出现 `esp_lv_adapter_lock` 获取失败，runner 据 device error 停止；不是 panic／watchdog，也没有 PNG 失败。混合窗口 draw 40.50 ms、timer 60.44 ms、queue 26.72 ms、period max 3189.064 ms，FPS 6／0／0／0／5／5／2／0／0／0。扩大缓存的内存矩阵改善不能代替锁／可玩性通过。

priority=10 单变量候选 `6176d7c9b`（ELF `6176d7c9b279da9cda62818fea9fda3d63e3e0e00e475bd1474f5c3f40209789`）准确输入、普通 App 构建、App-only flash、boot／hello PASS。其唯一运行配置差异为 LVGL task priority 6→10；Core、Service Manager、双 40 行、512 KiB 保持相同。`render-perf/c3256460-989f-4d17-a038-d4ad7635ee2c/report.json` 两轮原跳跃序列收集 PASS，16 次瞬态 snapshot 重试保留，无 PNG／锁错误，最后 Watch Face。IDLE game timer 36.41 ms、queue 4.85 ms。混合游戏窗口 draw 20.88 ms、PNG 3.93 次/s、9.82 ms/次，FPS 3／3／6／5／15／17／5／3／4／5／29／15；game timer 87.25 ms、queue 52.09 ms、callback 6.01 ms、period max 5175.886 ms。PSRAM free／largest 最低 305,776／180,224 bytes。

此轮平均 draw 有改善，但包含 DYING／IDLE，29 FPS 的孤立样本不能说明背景滚动时可达 29 FPS；timer 仍有秒级等待。继续相同 RUNNING 短窗口、截图和完整 Apps 联合验收，不提前宣称流畅性修复或切换生产默认。

## Hidden Shell 状态刷新阻塞

`6176d7c9b/render-perf/6ffe70a0-5554-4f05-b962-bb07388f587b/report.json` 两轮 RUNNING 短窗口收集 PASS；实际查看两张图，第一张无开始按钮且 pipe 位于右侧，第二张无开始按钮但尚无 pipe，timer 发生 3.77 秒停顿导致第二轮尚未到生成 pipe 的 tick。完整日志中的截断 profile 保留，不计算为完整样本。四个 render 样本 FPS 6／3／5／3；提高 LVGL priority 未显示连续 RUNNING FPS 改善，因此恢复 priority=6。该候选的完整截图 `cache-screenshot/5e954d86-a599-4985-95be-9bcac4ebc60c/report.json` 五张 PASS，无 PNG／busy 故障，最后 Watch Face；不以此推广优先级配置。

另一个可复现源路径为 Shell 每 30 秒的 `refresh_status()`：在共享 App callback task 上同步调用 SNTP／Wi-Fi／Battery／Brightness，再通过 GUI 更新隐藏的状态节点。foreground App 可见时原版仍执行所有查询与 GUI 调用。真实 refresh_status host 先 RED，候选 GREEN：200 次 foreground 请求不执行五个 refresh helper，置 pending；返回 Shell 时执行一次并清 pending；没有 foreground provider 保留原 standalone 行为。50 ms home timer 对 pending 进行重试，返回后补刷新；原 30 秒周期、PWR／Back／消息／键盘与输入期限保留。

旧候选 `6176d7c9b/render-perf/f1ecaad4-bab7-4b6a-bc59-72eb7711886a/report.json` 的前台 70 秒状态压力测量覆盖至少两次状态刷新；只在 360px playfield 外的白色边缘点击以维持正常活动，不改变息屏期限。收集及窗口后截图 PASS，无 PNG 故障；IDLE game timer 54.50 ms、queue 21.89 ms、period max 16,841.673 ms，flap max 16,892.479 ms；纯 RUNNING 短段约 36.32 ms。这证明前台仍有长时间 App 队列停顿，但没有单独的 Native Shell callback 耗时日志，不能仅由周期相关性认定所有停顿均来自状态刷新。

新候选恢复 LVGL=6、保持 cache=512 KiB、双 40 行与全部先前源码，只新增 hidden status deferral；以 `3f3078b4c` 的相同配置作为源码单变量对照。独立 `espocket-ecosystem-check-status-deferral.log` 的 Owner checks 与跨模块 106 tests PASS，App 构建与真机 70 秒压力、原跳跃序列、截图和 Apps 继续执行。

## 背景状态延后结果与 source 队列崩溃

`6176d7c9b/apps-regression/20261005T105722Z-69fcc7e3-1e88-4ca9-9e96-9215cccbc9ba/report.json` 完整 Apps PASS，受控 reset PASS。仍不采纳 LVGL=10，因为 RUNNING FPS 对照无改善。

hidden status 候选 `2903ed3d7`（ELF `2903ed3d7b207eac0a6fe0fe5eeaf89449cb909e95bbeb89b41656d3e49b49ee`）准确输入、App 构建、App-only flash、boot／hello PASS。前台压力首轮 `render-perf/39b11003-07c0-4a6a-9645-130d3389f1de/report.json` FAIL（Core 0 abort，设备重启），原 runner 未保留完整 backtrace。从受控 reset `3fc6e48c-a5e5-48d5-a14d-845fb2259bd4` 后再测 `render-perf/2d687235-40bb-4972-a7d1-ebe030138b81/report.json`，前台 70 秒完整 timer 测量支持状态延后：game timer 36.04 ms、queue 3.38 ms、period max 64.891 ms，相比旧前台 70 秒的最长 16.84 秒停顿明显改善。33 个完整 game timer 窗口保留；render 仅 15 个完整窗口，PSRAM free／largest 最低 60,608／48,128 bytes，不能由 timer 改善宣称稳定。

重测在窗口后截图下载期间再次 FAIL：PNG decode 失败，随后 Core 0 abort；raw panic 后追加 15 秒回溯。准确 ELF 解码为 `lock_init_generic` → `_lock_init_recursive` → `pthread_cond_init` → Boost condition_variable／promise → LibUtils `TaskScheduler::create_handle` → Core `post_gui_input_task` → `gui_set_view_src` → Runtime `SetViewSrc`。IDF locks.c:77 在 `xQueueCreateMutex` 返回空时 abort，是真实内部 mutex 分配耗尽；不是包校验、签名或硬件损坏的证据。

原 `gui_set_view_src` 每次接受请求就异步 post 独立任务，调用方可继续产生更新，GUI 慢时每个任务还持有 timer／promise／mutex。新增 `011-bound-image-source-dispatch.patch` 仅进入 scheduler-candidate：改为既有 `run_task_sync` 的真实 GUI Owner 更新，保留每个 source 的次序，应用成功后返回成功，未加载文档／应用失败则返回错误；不合并或丢帧、不改原包／动画／生命周期。真实 call site 与真实 run_task_sync 模板 host 回归用慢 GUI Owner 执行 200 次更新，原版 queued tasks 大于 1（RED）；候选待执行来源更新最多 1（包括已返回结果、正在销毁的任务时瞬时 handle 上限 2）、全部 200 次按序更新、错误透传（GREEN）。此回归证明背压，不把 allocator 源路径推断写成完全已验证的设备修复；仍须原 70 秒及截图压力复验。

## Source 背压候选输入

`d3e80b2de`（ELF `d3e80b2de663d541fb4a0946893650aee69e3c49dd9b890d7c50f9626a4ee14b`）App 构建、10 组件准确 inventory、既有内置 member digest 与 107 跨模块 tests／全部 Owner checks PASS。仍为 cache=524,288、LVGL=6、Core=10、双 40 行；相对 `2903ed3d7` 只加入 011 source 背压。不是 production 输入，不关闭可玩性或正式发布 ticket。

## Source 背压真机结果与声明预加载缺陷

`d3e80b2de/render-perf/f8394754-a5b8-4c9d-93fb-118b1de48cde/report.json` 的 70 秒前台及结束后截图收集 PASS，无 PNG／mutex abort；PSRAM free／largest 最低 356,468／303,104 bytes，比旧状态候选最低 60,608／48,128 明显改善。IDLE game timer 平均 61.94 ms、period max 161.831 ms；同步 flap callback 平均 98.94 ms，说明背压消除了无限生产更新的风险，但调用方等待仍使逻辑变慢。短 RUNNING 两个完整 render 窗口 FPS 5／12、draw 33.68 ms，timer 87.09 ms。实际查看结束后截图，开始按钮消失但尚未生成 pipe，不能据此声称持续 RUNNING 流畅。

`render-perf/2e9f9027-ad55-4c8c-aac0-cb51b77210cb/report.json` 两轮原跳跃序列收集 PASS，无 PNG／lock／panic，最后 Watch Face。混合游戏窗口 draw 26.48 ms、PNG 4.82 次/s、11.35 ms/次，game timer 64.81 ms、period max 228.285 ms；FPS 6／10／27／9／5／5／6／6／12／16／6／6，不把混合状态单个 27 FPS 当可玩性通过。`cache-screenshot/f97741e1-3ef2-4c63-be8e-0d6525a46ea7/report.json` 五张全部 PASS，实际查看画面和 Launcher 无缺图，11 条瞬态 snapshot 重试保留。

完整 Apps 首轮 `apps-regression/20261005T130850Z-6e4fefc9-8778-4446-af89-cf11a8a72511/report.json` FAIL：Native 自动息屏通过，但 Runtime Detail 自动息屏 35 秒内未出现；其余已执行导航／Back 步骤通过。受控 reset `ac254c98-4081-4e89-a385-74ab58994719` PASS。保留原期限并重跑同镜像，不将截图及压力通过当完整联合通过。

继续读取原 BPK 的 `res/images/index.json`：三张鸟帧都声明 `preload: true`。GUI Interface 0.8.2 `update_image_source` 在切走旧帧时仍释放其 automatic reference，最终释放 descriptor 并使 LVGL decoded cache 失效，随后再使用同一帧重新走 Storage 加载。新增 `001-preserve-declared-image-preloads.patch` 保留这些已经声明／装载的文档资源到 unload；普通非声明 automatic source 仍释放，manual release 和 unload 使用原资源 Owner。真实 update／release／unload 方法 host RED→GREEN，200 次三帧循环无新增 load 或 release；普通资源释放、其他 view 引用、manual ref、失败回滚及非 Image 拒绝保留。只加入显式 GUI／scheduler candidate，原包和缓存预算不变，等待独立构建及原序列验收。

同镜像 reset 后完整 Apps 重跑 `apps-regression/20261005T131325Z-eac7cc5c-8001-4b0e-a169-e71fc202d25b/report.json` PASS，Native／Runtime 自动息屏与唤醒、Back、Home、重进均通过；reset `9efe9883-ee4b-486b-abbf-f5f4f07214aa` PASS。首轮息屏失败仍保留为间歇风险，重跑不删除失败证据。新增预加载候选的独立 host checks 包含 108 跨模块 tests／全部 Owner checks PASS。

## 声明预加载候选结果

`fb7055e85`（ELF `fb7055e853c9437115f0716e69d15447a9119f9c85243e2378f05e6d194667c4`，BIN `1f29d2fd2d3cc9ad5881b6cf7512a7b6907b28ea00788be9809f2be144967126`，7,791,232 bytes）11 组件准确 inventory、registry lock、源码 checkpoint、九个内置 member digest、108 跨模块 tests／各 Owner checks、App 构建与 App-only flash／boot／hello PASS。仍为 cache=512 KiB、LVGL=6、Core=10、双 40 行，相对 d3 只增加 GUI Interface 声明预加载归属修复。

`render-perf/63713f1b-a52b-4e8d-91bf-d45573727b84/report.json` 两轮相同原跳跃序列收集 PASS。预热后的 IDLE／game 完整窗口 PNG open 都为 0；IDLE flap callback 从 d3 的 95.87 ms 降到 13.04 ms，实际周期 82.07 ms，game timer 35.30 ms。混合游戏窗口 draw 从 26.48 ms 降到 16.30 ms，game timer 从 64.81 ms 降到 41.05 ms，period max 130.432 ms；FPS 12／33／39／12／12／12／12／32／37／10／12／12。IDLE 的 12 FPS 是原包每 80 ms 切一张鸟帧的正常行为，不作为游戏滚动掉帧。混合窗口中的高帧率仍需独立 RUNNING 确认。

`render-perf/76ef8071-2695-45da-a8c5-2261a5e97276/report.json` 前台 70 秒压力与窗口后截图 PASS，无 PNG／lock／panic；34 个 IDLE 完整窗口 PNG open=0、draw 11.01 ms、game timer 35.37 ms、period max 57.438 ms，flap callback 12.83 ms／period 82.24 ms，PSRAM free／largest 最低 328,880／184,320 bytes。启动后的两个 render 窗口 FPS 12／33，其中首窗口含 IDLE→RUNNING 过渡；纯滚动后窗为 33 FPS，draw 合并平均 20.31 ms，game timer 42.78 ms。实际查看性能窗口后的截图：开始按钮消失、右侧上下 pipe 完整、鸟／背景／地面无缺图，确认运行负载。窗口后的截图下载影响 GUI／timer，after-game profile 单独保留，不计纯性能结论。五图、重复运行和完整 Apps 尚待联合结果，不提前推广默认。

声明预加载候选五图 `cache-screenshot/bcf0c698-3a9f-467e-9893-37ecb929f72c/report.json` PASS，实际查看五图无缺失；stored bytes 46,060／43,388／32,208／46,060／43,528，完整 RGB565 SHA 与覆盖检查通过，caller 最低栈余量 20,244 bytes。受控 reset `9ba94d69-1725-4e0f-bbd6-b6d2aae5d021` PASS；完整 Apps `apps-regression/20261005T133637Z-9e46856c-746b-4c15-b6d5-d3174f5d3213/report.json` PASS，包括 Native／Runtime 自动息屏、唤醒、Back、Home、重进和确认路径。继续两次重启后原包短运行窗口，确认独立 RUNNING 与缓存重新预热；不把 synthetic input 等同物理触摸／PWR GPIO 验收。

重启后两次短运行 `render-perf/0f2c2699-7ecb-4a2c-b984-6e31ca938220/report.json` 收集 PASS，两图实际查看均无开始按钮、右侧 pipe 完整。IDLE 所有窗口 FPS=12；RUNNING 后窗样本约 25／26／28 FPS，draw 合并平均 24.17 ms，PNG open=0，game timer 45.46 ms、period max 85.871 ms。PSRAM free／largest 最低 241,320／90,112 bytes。窗口后的截图下载产生更高的绘制／解码／queue 成本，after-game 窗口独立保留，不纳入纯运行结论。该重复运行确认收益，但不是持续稳定 30 FPS 的证明。

## 默认组合采纳

根据上述联合门槛，将 GUI Interface 声明预加载、GUI LVGL offset-only、Core 同域 strand 与 source 背压纳入默认 production，缓存默认设 512 KiB。普通源码的 Shell 三处隐藏工作跳过、逐行截图和 capture 作用域 priority 同时交付。`gui-candidate`／`scheduler-candidate` 保留相同组件／补丁的兼容入口；Core canonical 与 scheduler manifest 保持相同有序 11 项 patch。默认显示仍双 40 行、LVGL=6；单 80 行与 LVGL=10 不采纳。生产默认组合准确输入和构建待最终复核，不把选择采纳提前等同最终构建 PASS。

最终默认 production App 构建 PASS，ELF／BIN SHA256 与已完成上述真机联合验收的 fb7055e85 完全相同，无需重复刷写。准确输入复核位于 `input-revalidation/0fc1a447-fab4-4ff8-a207-36ec0da63b01`（以 production-adoption.json 绑定的路径为准），确认 11 个选中组件、canonical Core manifest、锁定 registry、源 checkpoint 和九个内置 member digest。最终统一检查的全部 Owner suites 与 108 跨模块 tests PASS，Markdown 检查 PASS。设备留在 fb7055e85／Watch Face；原 BPK 未修改、LittleFS／NVS 未刷写，正式发布与物理门槛保持未验。仍需降低纯 RUNNING game timer 的约 41–45 ms 周期及约 86–104 ms 峰值，当前不宣称持续稳定 30 FPS。
