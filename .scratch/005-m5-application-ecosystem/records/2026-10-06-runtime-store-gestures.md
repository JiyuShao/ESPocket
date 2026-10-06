# Runtime、Store 与手势问题排查

Date: 2026-10-06
Scope: 005/11

## Worktree 与基线

独立 worktree 为 `/Users/jiyu/.codex/worktrees/fix-runtime-store-gestures/ESPocket`。初始 `f84e085` 后更新到主分支已提交 `1571929`，本次修改保留为未提交；原 checkout 的未提交工作不进入本次构建。更新前的本次修改另有 Git stash 备份。

## 图标

基线 Launcher 截图中 Calculator、Flappy Bird 和 Weather 图标只出现局部。`launcher_item/icon` 的固定 36dp 容器使用默认 image inner alignment，原图片未等比缩放。修复为 `imageProps.innerAlign=contain`。

Store Installed 原先清空 `icon_resource_id`，改为在 manifest 有 image icon 时复用 Core 的全局资源 ID。新增 `006-store-installed-runtime-icons.patch` 放在既有补丁序列末尾，完整 source/patch/output inventory 核对通过。

## 手势

当前设备镜像 `8d7912fd9`：先从 Watch Face 上滑进入 Launcher，再执行 `(233,400) → (233,100)` 滚动。串口实际记录 `Opened App Store`，随后截图为 Store 页面。证据在 `/private/tmp/espocket-runtime-fix-probes/20261006T005014Z-9768e115-a0bf-4111-8836-b628dbbc1ced/`。旧探针报告虽然写 PASS，但仅表示采集成功，未对 Launcher 前台条件作断言；它不构成手势通过。探针已加入滚动后前台 App 必须为空的断言。

修复由 Shell 在 LVGL indev 层过滤离开 10px 点击容差后的 SHORT_CLICKED/CLICKED；普通滚动、拖动及 RELEASED 继续传播。系统导航识别时取消 pointer 点击候选，Release 才提交。新增 host 回归执行锁定 LVGL 实际 `send_event` 函数，覆盖普通点按、滚动、Edge Back、Release 与下一次点按恢复。共享手势回归同时覆盖取消、模态、息屏与阈值。

新增模态弹窗点按回归先失败，随后修复：弹窗禁止系统导航，但新 Press 的普通点击保持有效，拖动仍抑制点击。Shell timer 在安装 pointer callback 前创建，避免 timer 创建失败后遗留指向已释放状态的 callback；stop 在拆除其他资源前移除 callback。ESP-IDF 编译发现锁定 LVGL 的 `lv_indev_add_event_cb` 返回 void，已按实际 API 修正注册。

## Weather 与安装

Weather 0.2.0 原包 SHA-256：`b72b997ece7f18f138860b9b9cdf6b5a64240c8d242491937fe28b6c2b27f4db`，声明 `super`，未签名且无 ESPocket 导航声明。先前使用 `runtime_tap` 实际打开了 Hello Runtime，不能作为 Weather 的崩溃复现或修复证据。当前未得到 Weather panic/backtrace，不凭异步调用形态调整 16 KiB 栈预算。

实际 Weather 复现使用连续 Launcher 滚动后、截图校准的 `(233,427)` 点按，设备 identity 为 `8d7912fd9`。准入完成 5ms，GUI resource registration 完成后，TaskScheduler 记录 `std::bad_alloc` 与 task execution failed；20 秒观察窗及失败后的额外 12 秒没有捕获 panic，三次 snapshot 均返回 `invalid_state`。报告 FAIL，路径为 `/private/tmp/espocket-runtime-fix-probes/20261006T005635Z-c8e9e924-7057-499e-92d4-1986293aa7c4/`。这证明启动失败与系统 Owner 不再正常响应，尚不证明分配请求来源或用户遇到的所有闪退路径。

GUI Interface `002-return-gui-root-allocation-failure.patch` 在真实 `Runtime::load_file` 边界将 `std::bad_alloc` 转为 `GUI out of memory`，使已有 Core 启动失败路径可继续返回错误。真实方法的 host 回归覆盖异常返回、无文档加载、原解析错误保留和下一次成功加载，原版先失败、补丁版通过。这是失败处理修复，不能称 Weather 已成功运行。

临时 host parser 探针执行锁定版真实 parser 与原 Weather root，文件读取由 host Adapter 提供：解析成功，C++ new 追踪 peak 1,113,291 bytes、保留 590,745 bytes、最大单次分配 98,304 bytes。此数字只描述 host parser，未包含设备 Service/RPC、GUI 构建、图片、缓存和既有 App；不能推断设备的剩余 heap 或改栈预算。探针保留在 `/private/tmp/espocket-parser-probe/`。

既有安装日志显示 AI Chatbot 包含 `data/coze_private_key.pem.example`，Core 返回 `unsafe_package_member`。这是当前私有可写目录与发行内容分离规则触发的具体拒绝；尚未确认它是否涵盖用户所说的其他 App 安装失败。开发者模式只放宽未签名与 super 目标系统，不绕过成员安全或兼容性验证。

从官方目录下载全部 9 个最新 BPK，每个下载 SHA-256 都与 metadata 相符。真实 Core `inspect_runtime_package` 对这些原包的结果如下；Developer Mode 开启，host service/version Adapter 不证明实际设备服务可用性：

| App | 包准入结果 |
| --- | --- |
| Weather 0.2.0 | package admitted |
| Calculator 0.3.0 | package admitted |
| Flappy Bird 0.3.0 | package admitted |
| NES Emulator 0.2.1 | package admitted；仍需设备提供 NES |
| Camera 0.2.1 | package admitted；仍需设备提供 VideoEncoder0 |
| Chronos 0.2.0 | unsafe_package_member: files/sounds/alarm_ascending_dual_tone.mp3 |
| 2048 0.3.0 | unsafe_package_member: files/music/excellent.mp3 |
| Music Player 0.2.1 | unsafe_package_member: files/0.mp3 |
| AI Chatbot 0.2.1 | unsafe_package_member: data/coze_private_key.pem.example |

下载与 gate 输出位于 `/private/tmp/espocket-store-audit-20261006/`。未将这些 App 安装到设备。保持 `data/cache/files` 可写内容与受保护发行内容分离；兼容官方旧包的默认音频／数据路径需要重新明确此契约，不能只关闭安全检查。用户所指失败 App、设备安装和重启发现路径仍待确认。

## 验证状态

- 更新基线前统一 `scripts/check.py` 通过：80 个跨模块 host tests，加各 Owner tests 与 228 个 Markdown。
- 最新基线上的共享手势、真实 LVGL 分发与 Store 图标容量回归分别通过。
- 初始完整构建在旧 sdkconfig 的 Kconfig 重试阶段失败，无可刷写修复镜像。改用已配置板级 sdkconfig，在 `/private/tmp/espocket-fixes-build-20261006/` 完整构建；最终结果由后续条目补充。
- 本次修复尚未刷入设备；当前截图是基线故障证据，不能标为视觉修复通过。
- Launcher/Store 图标与手势实现的完整构建加增量构建通过，镜像 `c59867d1b`，BIN SHA-256 `9ff05a2b906c469c146c4ead4b1f8e8ba1518ef69ef58c9719fce83d4fa50e2b`，大小 `0x76c430`，App 分区剩余 28%。此版不含后来新增的 GUI root 分配错误补丁；BIN/ELF 另存 `/private/tmp/espocket-fixes-build-20261006/c59867d1b/`。
- 第一轮最新基线完整统一检查通过：108 个跨模块 tests、全部 Owner suites 和 246 个 Markdown。加入 GUI root 回归后已重新运行统一检查，并正在重建更新镜像；最终结果在后续条目追加。
- 前次其他 chat 的验收日志出现跨客户端 USB 请求混入；已发出具体 App-only 刷写和设备独占确认，未收到答复前不覆盖 `8d7912fd9`。LittleFS 不刷写，真机验证保持未完成。

最终代码统一检查通过：109 个跨模块 tests、全部 Owner suites，246 个 Markdown。包含 GUI root 失败处理的最终增量构建通过，镜像 `70a45d4dc`，BIN SHA-256 `c223e6581ee31b19195795b6a0065dfdb2289497f67b61ebd4c3d7b330285674`，大小 `0x76c4c0`，App 分区剩余 28%。产物为 `/private/tmp/espocket-fixes-build-20261006/firmware/build/espocket.bin` 与同目录 ELF。11 个准确 patched source inventories、manifest 摘要、实际选中组件路径及 registry lock 均重新核对通过；Shell 的 6 个变更输入另有内容摘要并与 worktree 一致。

日志为 `/private/tmp/espocket-fixes-host-check-20261006-final.log`、`/private/tmp/espocket-fixes-build-20261006-incremental.log` 与 `/private/tmp/espocket-fixes-build-20261006-gui-failure.log`。本次没有刷写设备、Git commit 或 push。旧的无修改重复 worktree `runtime-app-fixes` 已归档，保留当前 `fix-runtime-store-gestures`。图标视觉、手势真机、Weather 成功运行和 Store 安装／重启发现仍未完成，ticket 保持开放。

## 用户补充与后续验证

用户再次要求继续，并补充下载期间进度为 0 和私有数据／音频成员遭拒绝。下载路径占用唯一 HTTP worker；实际 Service 的进度发布由同一 scheduler 周期任务执行，无法在阻塞下载期间运行。上游 Kconfig 明确要求默认两个 worker。修复 HTTP worker 数为 2，同时保留最大并发请求数 1；隔离构建入口也会纠正旧 sdkconfig，并在 reconfigure 后核对。配置回归先失败后通过。

私有初始数据兼容方案仅作为可审查草案保存在 `/private/tmp/espocket-private-data-seeds-proposal/`：原包仍完整核对安全路径、CRC、摘要和签名；激活前核对所有解包成员；安装后的 data/cache/files 可写内容不参与不可变资源比较；更新保留旧用户内容，并补入新默认文件。临时真实 Core host 副本通过初始文件安装、写入、更新保留与资源篡改拒绝。自动审批明确拒绝将该方案应用到生产准入边界，要求用户授权该具体规则变化；已提出确认，尚未得到答复。方案及测试未进入 worktree 正常检查，不改变现有 gate。

按照用户的“继续”进行 App-only 复验：设备 hello 为 `f5f67952c`，已保存对应已知固件和先前 `8d7912fd9` 镜像。完整读取 App 分区的备份尝试因串口传输停止失败，期间没有写入。随后仅向 `0x60000` 写入 `70a45d4dc`，写入和设备 hash 校验成功，没有刷写 LittleFS、NVS 或分区表。日志在 `/private/tmp/espocket-runtime-device-backup-20261006/`。

刷入后 hello 超时；硬复位启动日志显示 `pthread: Failed to create task`，Core 的 `System0` worker 创建失败，System 初始化终止。与已知工作镜像的配置比较发现，候选 sdkconfig 关闭了已知基线的 Core／通用线程外部栈选项及 Service Manager secondary scheduler；Core 的 94,208-byte 栈被要求放入不足的内部 RAM。此失败不能作为图标、手势或 Weather 结果。隔离构建副本已恢复已知工作选项，栈大小保持不变，并加入 HTTP 进度修复重建；后续镜像与设备结论另行追加。

恢复配置并加入 HTTP 第二 worker 的镜像 `6f2fea2b6` 完整构建、App-only 写入和设备 hash 校验通过，BIN SHA-256 为 `97f02d5c6e6d8ebdb3306c437aad0a9c03d4951c4459ff4e7698ba8586a3c62a`，大小 `0x76c5a0`。干净镜像另存构建目录的 `6f2fea2b6/`。启动成功，三个已安装 Runtime App 保持可发现。统一检查通过 110 个跨模块 tests、所有 Owner suites 与 246 个 Markdown；导航设备 suite PASS，报告为 `/private/tmp/espocket-fixes-navigation-6f2fea2b6/20261006T032800Z-cd32d893-c172-4d7a-9319-63a5cb8964f6/report.json`。

不截图的连续 Launcher 滚动后前台 App 为空且 inputBusy=false；Weather 点按仍返回 `GUI out of memory`，随后 snapshot 正常返回 Launcher。该结果验证异常处理避免了此前 Owner 卡住，但 Weather 尚未成功启动。第一次临时探针等待不足 720ms 导致 busy，修正等待后才得出上述结果。

仅隔离构建副本添加临时失败分配 hook 与 parser 完成标记，镜像 `5b3c06652` 仍 App-only 写入。启动时内部 heap free/largest=12,643/7,680，PSRAM=1,065,952/1,048,576；Weather 在 parser 完成标记前失败，请求 2,776 bytes、caps=4096（默认 malloc），内部 heap=10,291/2,560，PSRAM=112/60。证据为 `/private/tmp/espocket-runtime-device-backup-20261006/weather-5b3c06652.log`。这将故障定位到解析阶段的总内存耗尽，而非猜测栈不足。

真实 Weather parser 的两个优化分别及联合测量：children 按已知数量 reserve，并在 interactionRefs 为空时避免复制递归 JSON 子树。联合峰值从 1,113,291 降至 978,901 bytes，保留从 590,745 降至 504,345；466/480 两种环境各三次测量一致，282 个展开 Nodes、全部 spec 与依赖序列化逐字节一致，32 个兼容 fixture 保持成功输出与原错误。host Node 大小与设备 ABI 不同，这些数字不能直接代替真机 heap。维护为 GUI Interface `003-reduce-parser-transient-allocation.patch`，设备复验另记。

Store 实际 Music Player 下载截图中条目出现 `Downloading 1%`，但捕获时弹窗仍为 `0 B / 324 KiB`；捕获不是原子帧，尚不能判定持续进度或弹窗一致性通过。路径 `/private/tmp/espocket-store-download-6f2fea2b6/download.png`。后续使用临时 Store Owner 进度探针核对实际事件与条目，不将一次截图称为完整下载验收。此前 Store 页面采集报告 PASS 只表示打开、采集和状态成功，不代表安装完成。

## 解析优化、字体与最终候选

解析优化镜像 `38ab42854` 通过 Weather 原包的 root 解析，随后返回明确的缺失字体错误：`/weather_home/home_scroll/home_hero/home_city_button/home_city_text_stack/home_city_name` 引用未注册的 `zh_CN`。系统 snapshot 和 Home 继续正常响应，没有把这个结果记成 Weather 启动成功。

同一镜像实际下载原 Music Player 十秒后，弹窗显示 `54.0 KiB / 324 KiB`，条目显示 `Downloading 16%`；截图为 `/private/tmp/espocket-store-download-38ab42854/download.png`。这证明进度调度修复在设备生效；取消、失败、完成和安装结果仍分别验收。Store Installed 探针的截图仍停在 Store tab，不能作为 Installed 图标证据。

System 嵌入 `ESPocket CJK` 字体：从锁定 LVGL 的 SourceHanSansSC-Normal 派生，覆盖 GB2312、可打印 Latin-1 和 en dash，共 7,618 codepoints、1,558,520 bytes；保留 OFL 并重命名派生 family。输出 SHA-256 为 `dfa527244c749fee2473ff433daf0490f80f627bfe0b1ac190fb2312baff7d3a`。真实锁定 TinyTTF 的 outline decoder 验证所有 glyph index，并在 12/18/28/64px 实际渲染代表字形。此资源编入 App，不写 LittleFS。

字体 Owner 注册 `zh_CN` 的 13 个原生字号，共享同一嵌入 blob，每个字号 glyph cache 限为 4、禁用 kerning；在 LVGL adapter lock 下创建和释放。Backend 借用期间字体必须存活。真实 Core 生命周期补丁 `013-clean-up-partial-gui-initialization.patch` 回滚部分初始化，GUI cleanup 投递失败后先停止 scheduler、在 backend guard 下销毁 GUI，再执行产品 teardown；仅移除本实例注册的 Service。回归原版 5/5 失败、候选 5/5 通过，保留非 worker 执行生命周期的约束。私有数据准入草案 012 没有应用。

字体资源与 Owner 回归加入后统一检查通过 113 个跨模块 tests、全部 Owner suites 与 246 个 Markdown。加入 lifecycle 和合成触摸正常结束修复后的完整检查、干净镜像 identity 与真机结果由后续条目补充。所有临时失败分配和 Store 进度日志探针已从构建输入移除，精确补丁输入重新准备并核对。

干净字体镜像 `5cadd4f43` 完整构建通过，大小 9,366,432 bytes，BIN SHA-256 为 `8e37f3a91f7e98b48d07648ce3e4db17b207c860cda268e42aef1096add0f706`。11 个精确补丁及实际选中路径、两个 Owner 全部源文件、registry lock、配置与 ELF 嵌入 identity 核对通过，临时探针不在 BIN 中。完整统一检查通过 118 个跨模块 tests、全部 Owner suites；Markdown 246 文件通过。

该镜像 App-only 刷写及 hash 校验成功，启动正常；导航设备 suite PASS：`/private/tmp/espocket-fixes-navigation-5cadd4f43/20261006T043417Z-4aae5dd4-072e-4cfd-99ba-57c227570400/report.json`。Installed tab 点按成功，截图中 Calculator 与 Flappy Bird 图标完整呈现，路径为 `/private/tmp/espocket-store-installed-5cadd4f43/installed.png`；信息 toast 遮挡部分 Calculator 条目，不视为所有页的视觉验收。Weather 现在通过资源校验，但返回 `Out of memory while loading GUI document`；失败后 snapshot 正常返回 Launcher。下一诊断针对页面创建与图像读取，不把资源校验通过当作 Weather 修复完成。

临时镜像 `e0ef59b19` 的失败分配 backtrace 已由其 ELF 解析：`operator new` → `service::helper::Base<Storage>::process_function_result<string>` → `Storage::fs_read_text` → `read_storage_file_bytes` → `load_binary_image_source`。这确认 Weather 背景二进制资源读取期间复制完整 Storage 字符串导致耗尽。GUI LVGL 002 改为 `fs_stat` + `fs_read(RawBuffer)`，直接读入最终 vector，检查文件类型、大小上限与完整读取；实际方法的单缓冲预算回归原版失败、候选通过，短读和错误不返回部分资源。

干净镜像 `076da59af` 完整构建、精确输入核对、App-only 写入与 hash 校验通过，大小 9,367,888 bytes，BIN SHA-256 `2bdf74eff1fe902dbb894a76536ad1b6230bb6cff93a19f4a63435cfbfe7c38d`。121 个跨模块 tests 与全部 Owner suites 通过。Weather 完成 GUI root 构建并进入 RuntimeJS，随后 Storage 报 `std::bad_alloc`，JS module loader 返回无法加载原 `app/weather/lifecycle.js`；这仍是失败结果，snapshot 与 Home 保持可用。

RuntimeJS 002 对入口脚本使用直接 Storage 缓冲读取，import callback 直接读入 `js_malloc` 的最终缓冲并添加 NUL；RAII 释放失败／短读路径，C callback 捕获异常并返回失败。文件读取继续由 cache-safe Storage worker 执行，未改 QuickJS 栈预算。实际 loader 回归验证原版入口／模块超预算、候选在单源预算内成功、重复失败不泄漏 QuickJS 缓冲。

用户明确答复“批准并继续修复、验证安装”。Core 私有初始文件兼容补丁 012 和真实准入回归已应用，保留 013 生命周期修复；此前自动审批阻塞已由此具体授权解除。产品信任契约同步明确初始成员完整验证和安装后私有内容可写边界。真实 Core host 复验通过初始 data/files 安装、可写、更新保留与新增默认文件、不可变资源篡改拒绝及事务恢复；真机安装与重启验收尚待后续候选。

## 原包编译与 Store 完成阶段继续诊断

干净镜像 `198779a91` 完整构建、精确输入核对、App-only 写入和 hash 校验通过，大小 9,370,560 bytes，BIN SHA-256 为 `cef4a2c5de7cde51c524b1ed79d0b8386ec4ddb1092e6c27824b71b10dff7959`。124 个跨模块 tests、全部 Owner suites 与 246 个 Markdown 通过。Weather 进入 JS 编译后返回 `InternalError: out of memory`，失败后 snapshot 和 Home 可响应。第一次 USB 滚动请求超时发生在 Weather 点按前，重启恢复；它与随后可复现的 Weather 内存失败分别保存，不混作同一结论。

同镜像实际 Music 下载显示 `28.0 KiB / 324 KiB`、`8%`，后续显示 `320 KiB / 324 KiB`、`98%`。Service scheduler 两次捕获 `std::bad_alloc`，安装尚未完成，不能把进度有效视作安装通过。证据为 `/private/tmp/espocket-store-download-198779a91/` 和 `/private/tmp/espocket-store-observe-198779a91/`。

仅构建副本加入失败分配和 VM 内存探针，镜像 `89e9f8d55` App-only 写入并核对身份。Weather 开始读取入口时 PSRAM free/largest 为 340/52 bytes；导入 lifecycle.js 的 34,423-byte 请求失败，PSRAM free/largest 为 70,376/32,768，内部 RAM 为 49,171/30,720。回溯解析为 QuickJS `js_def_malloc` → `js_malloc` → 实际模块 loader；不是 16 MiB VM 限额。启动日志显示 8 MiB PSRAM 只加入 2,930 KiB heap，板级默认 `SPIRAM_FETCH_INSTRUCTIONS` 将约 5 MiB 指令搬入 PSRAM。下一单变量实验关闭此搬运，保留栈预算、原 Weather 包与 cache-safe Storage 读取；实验结果仍待设备验证。

同诊断镜像在新启动后单独打开 Store，Music 安装检查请求 323,664 bytes 时失败，PSRAM free/largest 为 423,316/319,488，内部 RAM 为 53,407/38,912。其 ELF 回溯定位 `inflate_raw_deflate` → `extract_zip_entry` → Core `inspect_runtime_package`，异常离开 Core 后被 scheduler 吞掉，安装弹窗无法完成。Core 014 将该真实准入边界的 `std::bad_alloc` 转为短错误 `Package OOM`，不返回部分验证结果。实际 Core host 中注入同尺寸 mp3 解压分配失败：补丁前进程因未捕获异常终止，补丁后返回错误，解除故障后同一包可重新检查，完整安装／更新／重启恢复回归通过。

单变量诊断镜像 `cd19a06ba` 关闭指令搬入 PSRAM，其余源码与栈预算保持不变。App-only 写入和 hash 校验通过；PSRAM 加入 heap 从 2,930 KiB 增至 8,178 KiB，启动 free/largest 为 6,457,792/6,422,528 bytes。启动约 25 秒，旧探针 23 秒后开始 hello，误把仍在初始化的 `ESPocket started` 当重启；调整等待窗口后身份与启动均正常，没有 panic。原 Weather 按校准坐标启动成功，原 lifecycle/model 全部编译并进入运行；入口前 PSRAM 5,425,944/5,373,952，eval 后 5,187,548/4,980,736。随后原 Open-Meteo 天气和空气质量请求发出，截图显示上海 22°、晴朗、逐小时预报，证据为 `/private/tmp/espocket-store-observe-cd19a06ba/weather-network.png`。该镜像仍含探针，不能作为最终生产镜像。

较慢的 Flash 执行暴露了原三点快速滑动的输入分配问题：LVGL 的多指针分配器把无 track_id 的单点 250px 跳变拆为旧指针 Release 和新指针 Press，导致误点击。真实分配方法 host 回归在原版与仅含此前补丁的版本均失败；GUI LVGL 003 在连续单点且仅一个 active slot 时保持轨迹，多指与明确 track_id 的行为保持不变。Shell 点击过滤同时在各指针的真实 read callback 中累计位移，避免依赖异步 Gesture 采样的先后顺序；实际 LVGL send_event 回归覆盖往返拖动、异步状态重置、多指隔离、正常点按及回调移除。字号补入原 Weather 实际使用的 10、11、15px，避免替用邻近字号。

Music 原缓存包在诊断镜像 `cd19a06ba` 通过完整校验，显示 Developer compatibility install。继续安装后候选快照的 `Storage:FSWrite` 等待超过 5,000ms，事务清理 staging 并显示 `Install failed: Music Player / Wait timeout after 5000 ms`，没有把包兼容通过视作安装通过。Core 015 仅将包快照和解包成员写入的等待设为 30,000ms 上限，stat/read 和其他短操作仍为 5 秒；实际事务 host 注入 9 秒写入后成功，超过 30 秒返回超时，已有安装版本仍可验证。真实 filesystem helper 现在进入该回归，清理错误同时保留 rollback 类别与原始原因。设备完整安装结果由后续镜像追加。

加入同步指针读取过滤、单指轨迹和 PSRAM 配置后的统一检查通过全部 Owner suites 与 126 个跨模块 tests，Markdown 246 文件通过。中间干净镜像 `a9652950e` 完整构建和精确输入核对通过，大小 9,371,904 bytes，BIN SHA-256 `09d76555c4d7e8cf2f36e1967e5cec5cea19a4e13ef3fb73f7e3c4f2c2991060`；尚未写入设备，随后加入包写盘修复，不将这个中间镜像作为最终验收身份。

## 最终干净镜像与原 Music 安装

最终镜像 `2a4049f5d` 包含 Core 015 与全部修复，不含诊断探针。完整构建通过，BIN 为 9,371,904 bytes，SHA-256 `613ffba6c675d5afd34a6388ca0de35aad7d49639459c20d75d4165405ba4d8b`；ELF SHA-256 `2a4049f5de7a38ce89cba2fbc038471e1377d5908c96ed65de6d5af400b9fcc2`。11 个组件准确 inventory、manifest、实际选中路径、System/Shell Owner 源码、registry identity 和配置均核对通过；产物及输入证明在 `/private/tmp/espocket-fixes-build-20261006/2a4049f5d/`。加入 30 秒包写入等待的统一检查再次通过全部 Owner suites 与 126 个跨模块 tests，日志 `/private/tmp/espocket-final-write-host-check.log`。

仅向 `0x60000` 写入最终 App，设备 hash 校验成功，LittleFS、NVS 与分区表未刷写。最终镜像原 Music Player 0.2.1 下载快照显示 `19.0 KiB / 324 KiB`，随后完整校验进入 Developer compatibility install。第一次下载截图传输超过 60 秒 capture 生命周期，`screenshot.read` 返回 `invalid_state`；它不是设备崩溃。串口日志恢复的前 314 行画面为 `/private/tmp/espocket-store-download-2a4049f5d/partial.png`，只作为部分画面证据，不冒充完整摘要截图。将临时探针串口读取超时从 50ms 降至 5ms 后完整截图正常，未改变产品截图协议。

点击已获用户授权的 Continue install 后，事务期间两次 Owner snapshot 返回 `invalid_state`；USB hello 和后续唤醒仍响应。最终画面明确显示 `Installed Music Player`、Store 从 6 个待安装 App 减为 5 个、空闲空间从 1.13 MiB 降为 320 KiB。完整截图为 `/private/tmp/espocket-store-observe-2a4049f5d/install-wake.png`。原包的 4 个 `files/*.mp3` 成员随完整校验和真实 Core 事务安装成功；没有更改包内容或关闭校验。

Installed 页面完整截图 `/private/tmp/espocket-store-observe-2a4049f5d/installed-final.png` 显示 Calculator 与 Flappy Bird 原图标完整呈现。安装后受控重启启动成功，hello 匹配 `2a4049f5d`，启动日志再次记录 `Runtime app installed: id(7), manifest(brookesia.general.music_player)`；证明新安装持久发现。重启日志为 `/private/tmp/espocket-runtime-device-backup-20261006/boot-2a4049f5d.log`。原 Music 属于 developer Super App，缺少页面导航契约的 warning 符合已接受兼容规则，不是安装失败。

最终镜像导航设备 suite PASS：`/private/tmp/espocket-fixes-navigation-2a4049f5d/20261006T061437Z-ea601dcf-f8d8-45eb-8287-b00b882bda42/report.json`。涵盖快速三点方向手势、普通点按、Edge Back、App 确认取消／允许／超时、Home、息屏与唤醒。新增 Music 后 Launcher 完整截图 `/private/tmp/espocket-store-observe-2a4049f5d/launcher-after-scroll.png` 显示 Calculator、Flappy Bird、Music 与 Weather 图标完整；滚动后 snapshot 没有前台 App。首次 Weather 探针在惯性滚动结束前点按未启动任何 App，不是 Weather 闪退；增加等待至 4 秒后原坐标可稳定启动。

最终镜像原 Weather 成功启动，Core 记录 `total_ms(15426)`，snapshot 返回其 Running Instance，没有 GUI／JS 内存异常或 panic。真实 Open-Meteo forecast 和 air-quality 请求分别记录 `shanghai forecast updated` 与 `shanghai air quality updated`。完整联网画面 `/private/tmp/espocket-store-observe-2a4049f5d/weather-network-final.png` 显示上海 22°、晴朗、最高 22°／最低 13° 和逐小时温度、降水概率。随后 Home、相同原包再次打开、截图、Home 回归通过，日志为 `/private/tmp/espocket-weather-visual-2a4049f5d/serial.log`，结束 snapshot 为 Watch Face、没有前台 App。第三方 Super 包未声明 ESPocket Page，`navigationAvailable=false` 符合兼容范围；实体手指与物理 panel 仍需人工验收。

Native/Runtime Apps 完整设备 suite PASS：`/private/tmp/espocket-fixes-apps-2a4049f5d/20261006T062021Z-0f4fa928-2b14-4bea-8379-46e12e0fc802/report.json`。含两种模型的根页／详情、普通横滑、Edge Back、确认取消／允许／超时、自动息屏后的详情恢复、Home 和新 Running Instance。Runtime Hello 在最终 Flash 执行配置的打开／重开为 1,093ms／1,044ms；未将此小 App 时间外推为 Weather 的启动性能。

原 AI Chatbot 0.2.1 的 `data/coze_private_key.pem.example` 与音频成员通过完整 Core 检查并显示 Developer compatibility install；继续真实安装后正确返回 `Required services are unavailable`。Core 分别记录 AgentManager、XiaoZhi、Coze 要求 0.8.1，而设备均未注册这些 Service。完整错误画面为 `/private/tmp/espocket-store-matrix-2a4049f5d/ai-service-error.png`，日志为同目录 `ai-service-error.log`。没有再返回 `unsafe_package_member`，也没有用例外跳过 Service 准入。Store 其它 App 依然必须符合设备实际能力，不能把 AI、NES 或 Camera 宣称为当前产品已支持。

首次所谓下载取消探针实际进入已缓存 AI 的开发者确认，Home 正常关闭对话框、停止 Http 并返回 Watch Face；没有活动 `.bpk` HTTP 请求证据，因此不算活动下载取消通过。后续通过 Store Local 的 Long Press 仅删除可重新下载的 AI 原包缓存以建立真实下载样本，保留所有已安装版本和用户 data/files；实际活动取消和同摘要缓存恢复结果由后续条目记录。

带同步截图的活动取消探针实际提交 AI 原包下载 request 5，但截图后提交的 Synthetic PWR 在 1 秒输入有效期内未被 Owner 消费，记录 `Synthetic PWR expired before Owner execution`，该 attempt FAIL。没有 panic、watchdog 或重启，后续 Owner snapshot 正常、下载完成并再次通过完整包校验。它不能计作退出成功，也不把合成指令过期误报为闪退。

列出进度更新占用 Owner、截图锁竞争、合成输入有效期三种原因后，单变量移除取消前截图，下载及 3 秒后 Home 时机不变，实际取消 PASS。日志 `/private/tmp/espocket-store-matrix-2a4049f5d/no-capture-active-cancel.log` 记录 AI 原包 request 6 提交，随后 `Canceled HTTP request: id(6)`、Http Service 停止、Store 停止，最终 snapshot 为亮屏 Watch Face、没有前台 App、inputBusy=false；没有指令过期或设备错误。截图扰动足以改变该验收结果，最终普通取消证据使用不截图的输入路径；未增大产品或测试指令期限。旧 06 的完整 1.5 秒退出／重复压力门槛仍由原票持有，不据此关闭其它未完成验收。

取消后重进 Store，AI 条目为可重试 Remote，截图 `/private/tmp/espocket-store-matrix-2a4049f5d/canceled-download-reopen.png`；未将 cached startup 的容量文字当作实际 partial 文件清理测量。重新下载 request 7 成功并再次经过摘要与全部成员检查，显示 Developer compatibility install，完整截图 `/private/tmp/espocket-store-matrix-2a4049f5d/ai-cache-restored.png`。该缓存恢复到原官方 AI 包，未安装缺少 Service 的版本、未删除用户私有文件。下载失败／取消／完成及单一 terminal 结果在真实 HTTP host 方法中通过，网络故障的设备 UI 注入未执行；实际成员准入、Service 拒绝和活动取消证据分别保存。

最终取消不支持 Service 的 AI 安装确认并 Home，snapshot 为亮屏 Watch Face、无前台 App、inputBusy=false，测试输入和 screenshot capture 已 release。证据为 `/private/tmp/espocket-store-matrix-2a4049f5d/final-home.log` 与同名 PNG。最终 `git diff --check` 通过，Markdown 检查 246 个文件通过。保留已成功安装的原 Music 与恢复的原 AI 缓存、全部既有 App 和用户私有文件；当前固件仍为干净 `2a4049f5d`。本 worktree 没有 commit、push 或 merge。

## 整合最新 main

用户随后要求完成整体修复后合并到 main、删除其它分支。原已验收修复先保存为 detached commit `450293a`；main 在此期间已前进到 `96ca9e2`，包含 System/Shell 初始化与退出清理、Overlay 仲裁、资源 staging、异步图片队列、Boost 时钟与 PNG 解码优化。在隔离 worktree 上整合两边实现，保留 main 的状态清理和请求身份约束，并保留本票的字体借用顺序、失败时 backend guard、私有初始文件与手势点击保护。主 checkout 的三处未提交修改属于其它工作，不纳入本票。

Core 本票补丁重新编号为 `019-admit-verified-private-data-seeds.patch`、`020-clean-up-partial-gui-initialization.patch`、`021-return-package-inspection-allocation-failure.patch`、`022-bound-package-write-wait.patch`；原 012–018 保持 main 已接受实现。020 在 main 的生命周期补丁之后补齐 worker self-join、外部 Service 所有权核对和 GUI 锁定销毁，继续保留 initializing/product_init_entered 与完整状态清理。键盘期间 Edge Back 保持取消输入语义，并在 Release 提交；普通模态点按与拖动点击过滤继续独立。Shell 启动异常现在在释放手势状态前移除 pointer filter，真实 on_start 故障注入覆盖该清理。

整合检查的首轮失败包括旧测试替身缺少新生命周期字段、删除 018 后仍应用依赖它的 020，以及图片队列替身重复调用一次性回调。更新替身和基线范围后，队列测试用 `std::exchange` 明确清空回调，并用 worker 屏障确保初始批次完全提交后再绘制；容量、FIFO、并发后继、撤销与投递失败断言保持。源文件没有因此改变图片队列产品行为。

独立完整生产构建位于 `/private/tmp/espocket-integrated-build-v2-20261006`，精确核对 13 个补丁组件、所选路径、受控 firmware 源码、registry lock、生产配置与嵌入 ELF identity。生成板级文件此前携带主 checkout 绝对路径，修正 worktree 的忽略生成文件后重新创建独立 workspace，未修改构建入口的路径拒绝规则。最终镜像 `55b5e929b`：ELF SHA-256 `55b5e929b4f1bd7cfadab54fb638b86cc634807e4e61f96d1424529e4f95648d`，BIN SHA-256 `ed5db9de565b6a55ef00e552b0aca2b13fe4465b505a37fc05838d9fe0cb43f0`，9,392,464 bytes，小于 App 分区。输入核对证据为同 workspace 的 `55b5e929b/verification.json`；完整构建日志为 `/private/tmp/espocket-integrated-build-v2.log`，最后增量确认日志为 `/private/tmp/espocket-integrated-build-final.log`。旧 `2a4049f5d` 的验收只证明整合前候选，整合镜像验收另行记录。

最终全部 Owner suites 和 138 个跨模块 host tests 通过，日志 `/private/tmp/espocket-integrated-host-check-pass.log`；Markdown 274 个文件通过。统一差异补丁文件的空行必须保留前导 context 标记，不剥离它们来消除 Git 的 whitespace 提示；其它源文件与文档 `git diff --check` 通过。

刷写前设备仍为本票 `2a4049f5d`，最终只写入 App 分区 0x60000，esptool 核对 written hash 成功；没有写入 LittleFS、NVS 或分区表。日志 `/private/tmp/espocket-integrated-flash.log`。重启后实际 identity 为 `55b5e929b`，26,074 ms 到 ESPocket started，原 Music Player 与 Weather 均被发现并安装到 Core。日志 `/private/tmp/espocket-runtime-device-backup-20261006/boot-55b5e929b.log`，未出现 panic。导航 PASS：`/private/tmp/espocket-integrated-navigation-55b5e929b/20261006T071454Z-d9e1a2fe-250b-4c18-b917-b5a04e67fa8b/report.json`；Native/Runtime App 的 Root/Detail、普通横滑、待决 Back、Home、未回收息屏恢复和重新打开均 PASS：`/private/tmp/espocket-integrated-apps-55b5e929b/20261006T071609Z-85eabbef-2d38-48e9-83c4-afc1b90f3fb0/report.json`。

整合镜像原 Weather 首次启动 13,727 ms 并更新上海预报；临时截图 helper 的 5 ms readline 将协议响应分片误当成完整 JSON，截图 FAIL。释放 capture 后 PWR 已被接受，但 4 秒时 Owner snapshot 返回 invalid_state；后续真实停止日志在 Http 取消之后约 13.5 秒完成，恢复 snapshot 为 Watch Face，镜像 identity 未变。保留失败日志 `/private/tmp/espocket-weather-visual-55b5e929b/serial.log` 和恢复日志 `/private/tmp/espocket-integrated-weather-recovery.log`，不把该路径计作快速退出通过。旧 06 的 1.5 秒退出门槛仍未关闭。

独立重试 helper 缓冲串口分片，不修改固件、协议或原 Weather 包。启动 14,392 ms、上海预报更新，完整画面为 `/private/tmp/espocket-weather-visual-retry-55b5e929b/weather.png`，中文城市、天气、小时预报与图标完整。air-quality 请求本次返回 ESP_ERR_HTTP_CONNECT，原 App 走 fallback；不能声称本次空气质量在线更新通过。HTTP 结束后 Home 正常完成，最终 snapshot 为亮屏 Watch Face、无前台 App、inputBusy=false；日志为同目录 `serial.log` 和 `/private/tmp/espocket-integrated-weather-retry.log`。这些结果仍仅证明 USB 合成输入与渲染帧，实体手势验收保持独立。

最终 Store 标准用例的两次 80 ms Refresh 合成点按均未观测到对应 HTTP 提交，报告分别为 `/private/tmp/espocket-integrated-store-55b5e929b/20261006T072440Z-7d3c97f6-ad36-4b72-b175-6961d529384b/report.json` 和同目录 `20261006T073025Z-334f8d5c-8389-40c3-9701-bf60564de1fe/report.json`，均保留 FAIL。画面确认按钮启用、坐标正确，无模态覆盖。独立真实点按同一按钮后 request 5 下载远端索引并实际写入缓存，证据 `/private/tmp/espocket-store-buffered-55b5e929b/refresh-retry.log` 和同名 PNG；LocalNetworkReady/network_ready=true 可提交该请求，internet_ready=false 本身没有阻止刷新。

单变量把 Refresh press 从 80 ms 延长到 250 ms，其它标准场景步骤和参数不变，完整 Store 场景 PASS：`/private/tmp/espocket-integrated-store-long-tap-55b5e929b/20261006T073427Z-a2c95553-91dd-4e9f-818c-1f64c28c41fd/report.json`。包含 Refresh 后实际远端索引写入、PWR Home、停止保持、HTTP 停止后重开与再次 Home；没有只用 cached startup 作为在线成功证据。该探针只存在于临时 helper，未放宽原仓库标准测试或修改产品实现。短合成输入遗漏的具体机制与实体短点按仍未确认，不能把 250 ms PASS 改写为 80 ms PASS；本票的手势误点击修复与下载安装证据继续有效，短点按可靠性另行实测。最终亮屏 Watch Face、无前台 App、inputBusy=false，测试输入与 capture 已 release。

按用户授权将整合修复提交并快进到本地 main，继续保留 `96ca9e2` 的其它修复。核对 main 的三个无关未提交文件（AI Native ticket/spec 与 LICENSE）的完整 binary diff，与整合前一致；不暂存、不重写这些内容。本地原本只有 main 分支，没有其它本地分支需要删除；完成后归档任务的干净修复 worktree。未执行 remote push 或 remote branch 删除。
