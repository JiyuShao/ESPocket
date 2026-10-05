# 2026-10-05 Runtime 启动性能

用户明确 Hello Runtime 和 Flappy Bird 都慢；测量使用已授权 USB synthetic input，不能证明实体触摸延迟或面板帧率。普通镜像 `f35a6fd90`，Developer On，Flappy 已由真实 Store Continue 提交。全程不刷 LittleFS、不生成发行身份。

## 基线

`/private/tmp/espocket-m5-reviewed-f35a6fd90/perf/b8b1025b-1ef4-4551-a032-c54f704dde91/report.json`：同一普通镜像，点按提交到两次稳定 Owner 状态，包含 USB round trips。Native Root 两次 0.680／0.673 秒；Hello Runtime Root 4.447／4.306 秒；Runtime Detail 0.521／0.477 秒，Back 0.524／0.518 秒，Home 0.193／0.246 秒。启动期间 snapshot Owner deadline 超过原 2 秒，原始错误逐条保留；性能 probe 只继续观测，不把这些错误改判为功能通过。

Core 原 `App started total_ms` 计时从 Runtime package gate 之后开始，日志约 600–650 ms 未包含前置全量成员校验。Hello Runtime 总等待与日志有约 3.6 秒差额。源码路径为 `start_app` → `validate_installed_runtime_package` → `directory_members` → Storage FSList/FSStat/FSRead；built-in 也核对全部部署 member digest，不可直接跳过。

Flappy Launcher 图标／文字截图已采集；随后点按实际启动 Core id(6)，局部 `total_ms(6438)`，30 秒 quiet 采样时 display 已 false，严格状态报告 FAIL，不能将其计作 30 秒启动。唤醒后 Owner 确认 Flappy Running、导航 unavailable，但 rendered screenshot 报 internal；游戏画面尚未取得。

长时间暂停后的串口 backlog 包含实体 PWR 与 App start/stop；单独保存在 `perf/2b7c9929-9c05-4fa4-8c02-364c413a3cd5/pre-attempt-backlog.log`，不混入当前延迟判定。用户确认两者都卡后，新的合成序列单独计时。

## 候选与分段诊断

三项可证伪方向：全量 package admission 占据启动前半段；Storage 每条元数据三次 VFS 查询重复遍历 LittleFS；Flappy 的 runtime/GUI 装载另有成本。先测量后修改，不降低信任或超时要求。

Storage 0.8.3 `make_file_info` 原来分别调用 symlink_status、last_write_time、file_size；真实函数编译回归计数原版每个普通文件三次查询，候选单次 lstat 保留 exists/type/size/file-clock mtime 和软链接（含悬空）处理。原版计数断言失败，候选两项回归通过；依赖 manifest 固定完整源码和 patch hash。Core startup 计时前移到 package admission 之前，并在已有 profile-log 开关下记录该阶段。候选 device 比较尚待完整构建与准确输入核对。

## 完整基线补充与目标 API 修正

`/private/tmp/espocket-m5-reviewed-f35a6fd90/perf/73f8a8c7-fd6a-4d17-8360-879daef2c3c9/report.json` 使用相同普通镜像与原 Flappy 包，两次 synthetic touch 到稳定 Running 为 16.298／15.266 秒，Home 为 0.477／0.465 秒。仅延迟序列完成；Launcher screenshot internal、游戏 screenshot busy 均单独保留，不能将该报告 PASS 当作视觉或无 Owner deadline 失败通过。此前 `perf/42dde012-4bc2-4ef7-a0b8-cfd702081f12` 在 Launcher screenshot internal 后停止，判 FAIL。

首个 Storage 候选完成编译后链接失败：ESP-IDF 6.0.1 无 `lstat` 实现。未刷入。修正为 ESP_PLATFORM 单次 `stat`（ESP VFS 不支持软链接），host 继续单次 `lstat`；新增实际函数 ESP 分支编译回归。三项 Storage 回归与重新执行的完整 host checks（跨模块 95 tests）通过，完整目标构建仍待完成。

普通 f35 的 `active-refresh-cancel/3d1ad9da-6a25-40c9-8465-37013ba79dbd` 判 FAIL：窗口内无 admitted index request，不能宣称活动请求取消通过。串口显示当时 Store network_ready true、internet_ready false，缓存启动与 Local scan；本次失败不改判为取消成功。

## 普通性能候选 e16f49178

完整 host checks、259 Markdown、ESP-IDF 构建以及九个 exact patch inventories/selected paths 通过。ELF SHA-256 `e16f49178c5b1d95ff7233fd363ab9daac32dad27126b914cbcf7feb9e071a78`；BIN SHA-256 `e7f07dc4912bc14133f6e1f3e4b79ba3d2fdbd870240549e11c194ba00eeadff`，7,747,376 bytes。核对 lock、板级 HAL、playback-only Audio、字形、源码 checkpoint 与设备原九个 built-in member digest；package fixture 关闭，Core profile-log 开启用于测量。设备刷写与性能判定单独追加。

### 同机比较

e16 app-only hash、启动（37.2 秒）、USB identity 均通过，Flappy 与 Hello Runtime 重新发现。`perf/1f9150d2-2ab7-4d29-8cca-2aaebd3d7a75`：Native Root 0.627／0.679 秒；Hello Runtime Root 2.422／2.586 秒（原 4.447／4.306，均值缩短约 43%）。Owner 分段 package admission 1485／1672 ms、gui_prepare 440／454 ms、runtime_start_app 114／105 ms、on_start 39／41 ms；Core total 2146／2308 ms。上述合成观测包含传输与稳定样本，不能作为面板 FPS。

`perf/2116d246-2b58-4dd4-bcec-9fef152a8af2`：Flappy Root 11.676／11.365 秒（原 16.298／15.266，均值缩短约 27%），Home 0.222／0.370 秒。两轮 Launcher 与游戏整帧 PNG 均成功，画面显示开始按钮与鸟；仅视觉观察不证明实际游玩性能。Flappy 分段 package_admission 3640／3611 ms、gui_prepare 1199／1051 ms、runtime_lifecycle_on_start 5604／5779 ms；剩余主要成本是应用初始化，不能宣称 Flappy 启动已流畅。追加可配置 Runtime service 分段诊断，不改外部原包。

原 1.5 秒 Store 快速退出 `store-cycle/ae089409-0160-4a69-abd8-2e3e7d4156a8` 第一轮仍 FAIL，`Synthetic PWR expired before Owner execution`。metadata 缓存逐条处理与后续 UI 构建仍占 Owner，Storage 优化不能单独关闭 06。


## a89 分段观测与持久验证候选

普通 profile 镜像 `a89ad848a`，ELF `a89ad848a6083fdd5b2134a5f6cb932a24420990ce21c530a8355ba2f04c8f2d`，BIN `df2f1f3bb1e9e1bde6316dfd70c57206d33e5ccdfbfb4cfd2bbaef1dc92ff00c`。`perf/ad373a1b-65d3-4e0a-a7a7-21cf3dc89dba` 的 Flappy 启动为 7.499／7.035 秒，admission 3548／3606 ms；GUI 1053／1019 ms；第二轮 on_start 1493 ms。CreateView 8 次合计约 1.1 秒、SubscribeAction 91／210 ms。相对 e16 的 on_start 波动很大，尚未定位原因，不能宣称运行卡顿已修复；一轮截图 busy 仍保留失败。该镜像没有持久验证复用。

持久候选新增 Core 008 与 Storage 002，记录绑定目录、安装事务、manifest／artifact／member 摘要、规则与信任配置，并以 Core 私有 Storage KV 中的设备本地材料认证。冷启动只读少量认证元数据；RAM 命中不读取成员。未初始化保护不能开启复用。首次迁移、伪造／损坏记录、规则或信任变更走完整验证；pending 安装拒绝普通启动。所有六个 Storage 文件修改入口先检查保护，rename 检查源与目标；Core 安装／回滚／卸载与开发工具提供内部修改作用域。USB PutFile 改经 guarded Storage worker，避免直接 VFS 绕过；普通 data/cache/files 保持可写。祖先目录修改会使尚未发现 App 的持久记录失效。

真实 Core wrapper／callback 的 host 矩阵已通过：重复启动和新状态模拟重启均为零目录扫描、零成员／BPK 二进制读取；开发者模式关闭仍拒绝例外；受控内容修改先清记录、改坏内容拒绝、恢复原内容后重新验证；pending、伪造记录、失效删除失败、规则／系统／信任变化、更新／回滚均覆盖。真实 Storage 六个 mutation callsite 的执行测试通过，拒绝时无副作用。exact patch preparer 新增文件支持的十项回归通过，仍拒绝错坐标、覆盖已有文件和路径逃逸。完整 checks、目标构建、刷写和真机复用结果尚待追加；不把 host 冷状态模拟称为设备重启通过。


## 持久复用真机 2698534d2

普通镜像 ELF `2698534d2a6423faba59d9ac907350d20e2ba5d92409a70de868d5b6d80e6dd3`，BIN `614a1bf3e4db79f33effbc57a24c2defeed74c431e22d6a261ce914eaab983ca`，7,777,936 bytes。完整 host checks（跨模块 99 tests）、260 Markdown、ESP-IDF build、九个 exact inventories／selected paths 与 source checkpoint 通过。仅刷 App 分区，首次迁移两个 Runtime 为 source(full)，随后 source(memory)。固件正常使用 Core 私有 KV 保存本地认证材料；没有读取或备份 NVS 分区，没有刷 LittleFS。

`perf/165eda3a-d9a5-4518-a520-1483ffdb0f67`：Native Root 0.573／0.637 秒；Hello Runtime Root 1.009／0.896 秒，package_admission 5／6 ms，无 snapshot 错误；Root/Detail/Back/Home 序列完成。相对 e16 的 2.422／2.586 秒，Hello Runtime 启动均值缩短约 62%。

`controlled-reset/f4f947b0-0e5f-4169-977c-5f9e679b34b6` 真机重启 PASS；两个 Runtime 首次发现均 source(persistent)，随后 memory，无 source(full)。设备 16.740 秒到 ESPocket started，较首次迁移 23.205 秒少约 6.5 秒；两次启动网络背景负载不同，仅作为该次观测。重启复用证据是实际来源日志，不能只用启动时长证明。

`perf/9bb8be91-911e-4baa-b30a-f614323d519d` Flappy 两轮 7.753／6.631 秒，admission 已为约 6 ms；第二轮 GUI prepare 1109 ms、on_start 4704 ms。首轮 Core total 6678 ms、第二轮 5951 ms；合成稳定 Owner 观测还包含传输与超时重试。7 次 snapshot invalid_state 和两次 screenshot busy 保留，性能序列 PASS 不代表这些功能门槛通过，也不能宣称游戏 FPS 改善。

用户进一步指定先量化解码次数、绘制耗时、实际 FPS、timer 延迟，再优先试有上限的 PNG 解码缓存。源码确认当前 `CONFIG_LV_CACHE_DEF_SIZE=0`，esp_lv_decoder 已接入 LVGL image cache；Flappy 原包 PNG RGBA 总量 335,980 bytes。目标先试 1 MiB，保留原包，记录上限及 PSRAM free/largest。Brookesia GUI 已在释放／替换图像 descriptor 前执行 `lv_image_cache_drop`，避免 pointer 复用命中旧内容。新诊断候选尚在构建，不能把预计收益写成结果。

## PNG／绘制／timer 探针与 1 MiB 失败

诊断基线 `f6a7dce95`：ELF `f6a7dce957c8dd24b5c897a3fb1074436774d4c04043f68dac7bbe30914bd533`，BIN `311118713604b0e8b2565d0208804d554ba651f1e11e3ea499dfd7627a0ad04f`，7,784,432 bytes。完整 checks（跨模块 100 tests）、Markdown 和九个准确组件输入核对通过，仅刷 App 分区。cache=0、render profile 与 Core profile 开启，安装包未修改。

`render-perf/d7bc0925-2e34-4de0-a279-626cd65de435` 与 `62fe6ecc-a070-4d4b-8223-62cc6e0b5503` 均 FAIL：旧脚本固定坐标 y=427 实际命中 Weather。第二次 Launcher 截图确认当前 Flappy 位于 y=345；失败不是用户触摸干扰的证据。受控 reset 后修正坐标复测，不把前两次尝试纳入 Flappy 指标。

`render-perf/4aab1bbb-b598-4b09-bffc-592e198c1f32` 完成两轮合成序列，保留 14 次 snapshot invalid_state、4 次 touch busy、1 次 screenshot busy；首轮游戏后的截图显示鸟落地。完整的两个空闲绘制窗口合计 4.184 秒：43 次 PNG open，均成功，平均每次 12.32 ms；36 次绘制，平均 26.21 ms；adapter 完整末次 flush 完成 FPS 样本 8／10。game timer 名义 33 ms，空闲实际 dispatch 平均 70.73 ms（14.14 Hz），平均排队 39.94 ms；游戏合成输入阶段平均 92.38 ms（10.82 Hz），平均唤醒迟到 26.26 ms、排队 42.66 ms、回调 6.46 ms，最大回调 318.887 ms，最大实际周期 593.423 ms。原脚本每 tick 按固定 gameTickIntervalMs 推进背景／管道／物理时间，所以 timer 降频会直接减慢逻辑。实际 FPS 与逻辑频率分别记录，不能相互替代。

首版探针在 LVGL callback 内直接输出，串口出现只剩日志尾部的记录，游戏阶段无完整 render sample。因此上述数据只构成初步诊断，不能作为完整绘制 A/B 基线。改为 GUI 线程只汇总／格式化，单元素有界队列交给独立诊断线程输出；阻塞串口不进入 GUI lock。探针从 on_app_started 开始，不覆盖此前 on_start 的全部解码；FPS 是 adapter 最近一秒完整末次 flush 完成统计，绘制和 PNG 计数为各自约两秒窗口。窗口边界和截图期间数据不混作稳定运行结论。

1 MiB 镜像 `fc37f9e2d`：ELF `fc37f9e2dc6d1aacff318e8c2deb8ab358e88487f45d2aa7c9c77b48f8e412c2`，BIN `80a1bd48c49a1d4bc93122de1eaf3cefa93852a0d86a629b9f2072fa42f9db8b`，7,784,912 bytes，采用独立输出线程。准确输入、完整 checks、build、App-only hash 与启动通过。`render-perf/6f189a0d-74dd-4a50-b4be-69c427d2ee66` 的两轮导航序列完成，但渲染判 FAIL：`png finish read failed`／`Failed to open image`，多个窗口 png_ok=0。正常运行窗口 PSRAM 最低 43,656 bytes、最大连续块仅 9,472 bytes，缓存保留解码缓冲后未给 PNG 临时工作区留下足够余量。这里的 FPS 不能作为性能改善，因为部分图像未成功绘制。原 Flappy BPK SHA-256 为 `ffdf1250f6be38377fe46617b6e0cca196cad4a388f9009edcdf87045165297a`。

后续改为先恢复相同探针的 cache=0，再试 64 KiB；超过预算的图像无缓存绘制。LVGL image cache 与 Native 图像共享，故超预算 fallback 覆盖注册 decoder，且关闭 profile 后仍执行；host wrapper 分别在 profile=0／1 验证 PNG、JPEG、大图、失败与原 callback 转发。64 KiB 的效果和最终设备镜像尚待追加；1 MiB 不作为通过候选交付。

### 截图占用导致的证据更正

进一步核查 `TestProtocol` 与脚本发现：Launcher 的整帧截图在设备上保留 466 × 466 × 2 = 434,312 bytes，直到 `release`、下一次截图或 lease 到期。前述诊断脚本截图下载完后没有立即 `release`，因此在 App 启动和正常运行测量期间额外占用约 424 KiB PSRAM。上述 cache=0／1 MiB／64 KiB 的低内存、碎片和缺图均发生在这个被测试工具施加的约束下，不能用来断言正常使用的 1 MiB 缓存必然失败；此前关于预算过大的因果判断作废，原始失败保留。

受此干扰的进一步尝试包括 `82919f205/render-perf/3708e26d-726b-488d-9690-0d4e55c8870f`（64 KiB，无内存回退，正常窗口新增 PNG 失败）及 `28ca8c6f6/render-perf/c7dcd3dd-b6f1-465c-b6f5-999175c55bc6`（64 KiB，已加回退，截图／息屏后 Home 未到达）。它们均 FAIL，不作为生产缓存选择依据。内存回退本身覆盖 cache budget 之外的临时工作区和连续分配压力，但不保证基础堆一定能分配成功。

脚本修正为每次下载 Launcher 截图后立即 `release`，然后才启动／测量；游戏后的截图也立即释放，退出前独立处理息屏唤醒。正在用已验证零缓存基线与带内存回退的 1 MiB 候选重新比较，判定以这次修正后的证据为准。持久验证的实际 source(memory/persistent) 证据、完整 host matrix 和包完整性结果仍有效。

零缓存 `a2df08485` 的完整普通 Apps 回归 `apps-regression/20261005T034858Z-2176ed80-9ee1-4661-8715-a3e7ffa92f7e` PASS，覆盖 Native／Hello Runtime Root、Detail、Back、待决 Back、自动息屏恢复、Home 和重新打开；该 suite 没有保留 Launcher 截图缓冲，不受上述干扰。


## 无截图占用的最终 PNG 缓存对照

零缓存 `a2df08485` 的修正后早期报告 `render-perf/98a44db4-e7e3-4b20-bc40-22087b8e03c0` 已立即释放 Launcher 截图；正常 idle/game 窗口 PNG 全部成功，game 解码 11.14 次/秒、平均 16.15 ms，绘制平均 37.99 ms。最低 PSRAM free 734,128 bytes、largest 507,904 bytes。该次游戏后截图阶段不进入性能比较。

1 MiB 加内存回退候选 `329ad8074` 的第一次修正后尝试 `render-perf/d5a4744d-7412-4fcd-8b58-d5dd201b5a47`，第一轮 PNG 全部成功、pressure_evictions=0，第二轮 Launcher 截图申请连续 434,312 bytes 失败，序列 FAIL。这是缓存保留内存与截图整帧分配的冲突，不是 PNG 解码失败。后续性能脚本移除全部截图。

`329ad8074/render-perf/453049bf-07e4-4f83-a656-b2c9747bea74` 两轮无截图序列完成，172 次 PNG open 全成功，无截断样本或压力清缓存；保留四次启动 snapshot invalid_state、三次 touch busy。但两个 game 阶段没有观测到跳跃的 ExecuteBatch，不能以 input ACK 认定已进入游玩，也不将其用于最终游玩 A/B。

最终比较固定原包、两次停止／重新打开、8 秒 idle、开始按钮按住 400 ms、跳跃按住 180 ms 并间隔采样 0.5 秒；全程没有截图缓冲。两镜像均开启相同 Core／render profile，零缓存镜像不执行缓存压力回退，因此回退的代码差异不影响该分支。缓存候选在完整 Apps suite 后测量，零缓存在受控 App-only 复刷后测量；不是随机化或长期统计实验。

- cache=0：`a2df08485/render-perf/e87f2d92-70a4-4e69-a843-cb2314205a5c/report.json`，game-0／1 各观测六次跳跃 ExecuteBatch；390 次 PNG open 全成功。启动保留 93 次 snapshot invalid_state 重试；没有截断样本、touch busy 或渲染失败。
- cache=1 MiB：`329ad8074/render-perf/fa273d26-3d69-40d1-a003-0c7bfea14396/report.json`，game-0／1 各观测七／六次跳跃 ExecuteBatch；158 次 PNG open 全成功，pressure_evictions=0。保留四次启动 snapshot invalid_state；没有截断样本、touch busy 或渲染失败。

只汇总完整且至少 1.5 秒的正常窗口，平均耗时按实际次数加权。game 指合成游玩输入阶段，可能包含死亡／回到开始画面，不能解释为全程存活的游戏 benchmark。

| 指标 | cache=0 | cache=1 MiB |
|---|---:|---:|
| idle render 窗口／覆盖时间 | 7／14.614 s | 6／12.624 s |
| idle PNG 解码频率 | 6.09 次/s | 3.80 次/s |
| idle 每次绘制平均／最大 | 26.52／185.854 ms | 33.58／53.549 ms |
| game render 窗口／覆盖时间 | 10／20.627 s | 12／25.123 s |
| game PNG 解码频率 | 12.61 次/s | 3.70 次/s |
| game 单次 PNG 解码平均 | 18.23 ms | 10.75 ms |
| game 每次绘制平均／最大 | 53.53／202.627 ms | 26.96／67.850 ms |
| game 完整刷新完成 FPS 样本中位数 | 4.5 | 5.5 |
| game timer 请求周期 | 33 ms | 33 ms |
| game timer 实际 dispatch 周期／频率 | 80.19 ms／12.47 Hz | 74.05 ms／13.50 Hz |
| game timer 平均唤醒迟到 | 25.98 ms | 20.09 ms |
| game timer 平均 Owner 排队 | 27.90 ms | 27.15 ms |
| game timer 平均回调 | 5.26 ms | 7.77 ms |
| game timer 最大实际周期 | 422.469 ms | 273.874 ms |
| game PSRAM 最低 free／largest | 730,524／540,672 bytes | 265,840／192,512 bytes |

零缓存 game FPS 样本为 4,5,4,9,5,4,3,5,21,4；1 MiB 为 6,1,7,8,8,5,4,5,7,36,5,1。它们来自 adapter 最近一秒完整末次 flush 完成计数，包含突发，不能用峰值 36 宣称稳定 30 FPS；不是面板光学测量。timer 的 flap 实际周期也由 131.43 ms 降到 117.08 ms（请求 80 ms）。

这组游玩阶段观测中，解码频率约少 71%，平均绘制约少 50%，game timer 实际周期约短 8%。收益主要是重复 PNG 工作与长绘制减少；idle 平均绘制未改善、timer 仍远慢于请求，不能关闭“游戏流畅”问题。Flappy 脚本每 tick 按固定间隔推进时间，13.50 Hz 的实际逻辑频率仍会使其变慢；GUI 同步调用、Owner 排队和大面积重绘需要后续定位。两轮 Core 启动总耗时 cache=0 为 6,294／7,886 ms，1 MiB 为 2,556／2,454 ms，admission 均约 4–6 ms；这些不是端到端面板首屏测量。

### 采用预算与回归

采用 `CONFIG_ESPOCKET_RUNTIME_IMAGE_CACHE_BYTES` 默认 1,048,576 bytes，最多 2 MiB，可设 0 关闭；不预分配，不包括当前绘制缓冲、decoder 工作区和管理开销。超预算图像无缓存绘制，PNG 分配前按最大连续块和 64 KiB 临时余量清缓存；资源释放／替换先使旧条目失效。render profile 默认关闭，仅验收镜像启用。BPK 不改，停止／重启仍执行原生命周期。

`329ad8074/apps-regression/20261005T043506Z-00654608-910f-4d9e-8931-ad662c650e6d/report.json` PASS：Native／Hello Runtime Root、Detail、Back、确认与待决 Back、息屏恢复、Home、停止后重新打开均通过。此前零缓存完整 Apps suite 也 PASS。由默认 0 改为 1 MiB 后，目标工程重新配置／build 成功，显式配置仍为 1 MiB，ELF／BIN 与已测候选完全相同；九个 exact inventories、selected paths、源码 checkpoint、built-in 摘要重新核对通过，证据保存在 `329ad8074/input-revalidation/7488e9cb-f00e-4437-950c-482b08df9de2`。

截图冲突另修：在既有 GUI lock 内，首次整帧分配失败后释放可回收图片缓存，再重试一次；基础堆仍不足时继续返回 internal。真实 allocator host 回归覆盖无压力不驱逐、缓存释放后成功、重试仍失败。该修复的完整构建、真机截图与最终文件摘要核对结果另追加，不把缓存候选 Apps PASS 自动继承成新镜像设备结果。


### 最终截图候选与包保留证据

截图修复候选 `f13728f7c`：ELF SHA-256 `f13728f7c6b38f7ff9fc9d286ffeaf3282f7dbe01ade61acb5bee2654d4f9622`，BIN `e15914a75441d6a6b7ef707f41ee7f84dc304f63fccf7448793262885f40ca67`，7,785,232 bytes。完整 scripts/check.py PASS（跨模块 100 tests，另包含新增 Owner screenshot allocator 回归），260 Markdown PASS，完整目标 build、九个准确组件 inventory／selected paths、源码 checkpoint 和内置文件摘要核对 PASS。缓存仍为 1 MiB、render/Core profile 为此次验收开启，package acceptance fixture 关闭；最终设备结果另追加。

缓存候选 `329ad8074/filesystem-final/2c53eb02-7ada-473f-ad74-30b78f54acc1/package-preservation.json` 为只读 LittleFS 核对：仅读取 `0xaa1000+0x4e2000`，没有 NVS 或 full Flash。Flappy 原 BPK SHA-256 与全部 21 个 archive member digest、九个 built-in member digest 都一致；没有 `espocket.test.store_hello` 安装残留。保留两个既有 acceptance 状态 marker（`original-mode`／`phase`）与 Store 的 ai_chatbot `.bpk.part`，本次未修改；因此不宣称文件系统没有测试或下载痕迹。读完受控 reset PASS。


### 最终判定修订：保留试验能力，撤回默认启用

`f13728f7c` App-only hash、启动与 USB identity 通过，四个 Runtime 发现均 source(persistent)，未发生重新全量校验。截图验收 `cache-screenshot/a5de1816-d89c-4bba-8c18-d1c704e6c465` FAIL（Flappy 内 GUI lock busy）；有限重试的 `0d118fbb-e8df-4f9a-83eb-8477b8633135` FAIL（先 busy，再 internal）；仅验证 Home／Launcher／重开的 `381cd326-79c7-460a-b7db-600f4f78b784` 在 Launcher-after-cache screenshot internal 后 FAIL。上述原始失败均保留，不能把缓存候选 Apps PASS 解释成截图门槛通过。Flappy 内分配前 PSRAM free 约 367 KiB、largest 180,224 bytes，远小于截图所需连续 434,312 bytes；清解码缓存重试不能保证碎片合并。

因此撤回此前“采用默认 1 MiB”的决定：默认维持 0，撤销未解决真机失败的截图重试实现及其试验测试；保留四项探针、有上限缓存配置、超预算绕过和 PNG 内存压力回退，1 MiB 仍是已测实验预算。设备恢复此前完整 Apps PASS 的 `a2df08485`（cache=0），恢复结果另追加。1 MiB 的 A/B 解码与绘制收益仍有效，但不作为无回归生产候选；后续需要解决截图连续大块分配，例如由截图 Owner 提供分段存储，再重新验收。没有修改包、提高原输入 TTL 或改变 Running Instance 生命周期。


设备已恢复 `a2df08485`；`reflash/e7f91093-2e40-45af-8f79-8461c0caca41` App-only 写入 hash、启动、hello identity 和 Watch Face snapshot PASS。LittleFS 保持原数据，未刷文件系统。该镜像的零缓存性能与完整 Apps suite 证据继续有效；当前源码默认 0，保留可配置实验能力。撤回截图试验代码后，完整 checks／精确构建输入重新验证，退出后的 Launcher 截图恢复结果另追加。


零缓存恢复后，`a2df08485/cache-screenshot/f85af4c9-4e1d-429e-8837-183b10b907aa/report.json` PASS：两次 Flappy 启动／Home／重新打开、退出后的同一路径 Launcher 截图完整下载与 SHA-256 校验、立即 release、最终 Watch Face 稳定快照通过；没有 PNG 解码／渲染失败。实际查看 PNG 确认 Flappy Bird Launcher 行和其他应用条目可见。相同 Launcher 截图路径在 1 MiB 候选失败，恢复零缓存后成功，进一步支持拒绝本次默认启用。最终完整 scripts/check.py 与 260 Markdown 重新执行 PASS；移除试验代码后的候选准确构建结果另保留，设备继续使用上述已验证零缓存镜像。

撤回截图试验后完整目标 build 与九个 exact inventories／selected paths、源码 checkpoint、内置摘要核对再次 PASS，候选产物为 `espocket-m5-reviewed-329ad8074`；构建配置保留实验用 1 MiB，而源码默认仍为 0。该候选不再部署，设备／current-reviewed pointer 已明确恢复为 `a2df08485`。
