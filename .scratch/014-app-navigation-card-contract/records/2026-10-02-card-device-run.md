# App Card 设备验证

Date: 2026-10-02
Scope: 014/05 Native/Runtime Card synthetic-input；物理/视觉条件独立。

## 首次 attempt

测试镜像 57bfbc813，CONFIG_ESPOCKET_M8_CARD_SAMPLE_TEST=y，两个 reclaim 开关关闭。写入 App 分区并由 esptool 校验；RAM 序列不写 NVS。

Attempt 20261002T091240Z-318ae700-c6fd-490b-948e-68719238ddf8：FAIL，独立 report.json/serial.log 保存在 /private/tmp/espocket-card-device-attempts/。Native 侧 summary/Root、detail/Detail、末端不循环、Back 回 Root、PWR Home 后重开 Root、Card 自动息屏/唤醒与向内回表盘全部通过。Runtime summary 正确打开真实 espocket.app.hello_runtime Root；Root Edge Back 轨迹却触发页面 Open Detail，实际 pageId=detail。最终 release 成功，快照保留实际状态，无 panic/栈溢出/重启。

不改坐标掩盖问题。修复把默认边缘手势责任与实际 Back 可用性分开：Framework Root 或待决 Back 只消费达到阈值的边缘轨迹，LVGL 等待 release，不发起导航；AppOwned 不保留该手势，普通非边缘横滑/纵向内容仍由 App 处理。Navigator 持有责任事实，System 用 Owner callback 发布原子标志，Shell 不查询第二份栈或新增测试快照字段。共享手势回归先失败再通过，Native/Runtime 共用同一规则。

## 第二次 attempt 与串口分帧

镜像 06cfc0856（ELF SHA-256 06cfc0856cab8003655ff2e6e262f613acbc8d92fc9d9cc67c75fccd0e19828a），Root 默认边缘轨迹消费修复已构建并写入校验。Attempt 20261002T092645Z-d6e72674-bdbd-482b-9b30-1c164d8d148a：FAIL；Native 全部路径再次通过，Runtime summary 打开 Root 后等快照响应超时。原日志同目录保留。

原始日志显示有效 @ESPTEST 响应插在 Runtime 普通日志的半行之后，Driver 的严格行首匹配没有接收它。后续独立只读 liveness 的 hello、release、snapshot 均成功，实际 Page 为 Runtime Root；无 panic、栈溢出或重启证据，不能将此次超时诊断为导航死锁。

Adapter 成功与错误响应统一通过私有分帧函数，在前后写入换行。实际函数的主机回归先复现半行日志后响应不可识别，再修复通过；Driver 保留严格前缀与 request_id 匹配，不新增自动重试。最终 attempt 待补齐；设备物理/视觉与 package replacement 条件保持开放。


## 第三次 attempt 与释放后清理

镜像 f31d531eb（ELF SHA-256 f31d531ebc7852524576882710fe6637510014432eb72b687194e87d9fb0b892，BIN SHA-256 c5352593575260e2908035102f12083fd4ce1d1f835c7a0dc73c2584682ddf96），App 分区写入并校验。Attempt 20261002T094222Z-efce669a-3d28-48be-8db4-93a053381aa9：FAIL。分帧正常，Native 全部通过；Runtime 首次启动 total_ms=492，Owner 最终正确到 Root，但 USB worker 报 Synthetic input tick failed: timeout。最终 release 成功，实际 Root，inputBusy=false；无重启或 panic。

原输入组件在所有点（包括 release）已经发送后，仍先检查轨迹期限；Runtime 启动期间快照读取/GUI 调度使下一次清理延迟，误报未完成轨迹超时。实际组件回归先失败后修复：时钟倒退仍取消，未发送点仍受原 500 ms grace 限制且不补发迟到点；已发送 release 的序列只执行正常清理，成功前保留输入占用。前台 token、断连、息屏等独立取消条件不变。不是增大期限或忽略错误。


## 第四次 attempt 与控制台输出路径

镜像 528e6d047（ELF SHA-256 528e6d0474e784bca1389b698148d5211254dcb176e56b4c934a8bdac6c29608，BIN SHA-256 340aae3b0a5c6b645a588b19f61bf54ad9bd02b9d24e3a0a40caf48d1ee5882a），完整构建与 App 写入校验完成。Attempt 20261002T095807Z-64bf0f74-b0a3-4470-a477-0a1c6df08028：FAIL；Native 目标打开/返回等已通过，等待 Card 息屏时收到 malformed protocol response，17 个已完成步骤。最终 release 成功、快照 seq=708，左 Card 已息屏且 inputBusy=false。

实际 JSON 的字段中夹入普通 backlight Storage 日志的字符，说明换行不足以防止帧内部交叉。本地 IDF 6.0.1 官方 driver/VFS 源码确认：安装驱动不会自动改变默认 VFS 的直接 FIFO 输出；USB ISR 同时输出 Adapter 的队列字节。修复使用官方 usb_serial_jtag_vfs_use_driver，把控制台与完整响应交给同一队列；停止卸载前用 use_nonblocking 恢复控制台。没有修改 IDF/Brookesia，没有放宽 Driver JSON 校验，也没有掩盖失败。此硬件输出竞争不能由纯分帧函数单测证明修复，需再次运行实际 Card attempt。


## 输出队列修复镜像与启动准备

镜像 f09aeeaed（ELF SHA-256 f09aeeaeda4f6716277e34841c88081898de2bec2d4d3e9e0041e20ae15ace4b，BIN SHA-256 c89cff06cbbaf3d0f59882851a5d6c44810e443129e06aaa9b7f898e4785058c），44 项 host unittest、M2 parser、Markdown checks 与完整 Card 配置构建通过，App 写入 hash 校验完成。Card 样例配置只在 RAM，不修改持久 Card 配置；两个 reclaim 开关关闭。独立 BIN/ELF 保存在 /private/tmp/espocket-card-f09aeeaed/。

Attempt 20261002T101140Z-f5de150f-d743-4f4e-aba9-378e9779adaa：准备阶段 FAIL，0 个用例步骤。首次连接收到缓冲中的 ESPocket started 尾行，Driver 按严格启动标记检测拒绝，未忽略该行。随后 release 成功，实际 hello identity=f09aeeaed，最终 seq=1，Watch Face、display=true、inputBusy=false；完整协议帧可解析。清理排空启动输出后，重新运行作为独立 attempt，不覆盖此失败。


## 第六次 attempt 与 Owner 采样边界

Attempt 20261002T101222Z-8ab1e3f7-899b-4989-85ea-c8128918b89e：FAIL，镜像 f09aeeaed，24 个步骤。Native 全组及 Runtime summary/Root、Root Edge Back 负例均通过；默认 Root 轨迹不再误点 Detail，协议帧没有再出现日志字符交叉。Runtime Root PWR Home 后的一次 snapshot 返回 invalid_state：采样开始时 Runtime 尚为前台，读取期间实例停止并恢复表盘；最终 release 成功，seq=733，真实 Watch Face/display=true/inputBusy=false。此失败保留，不把正常最终页面当作用例通过。

USB 线程原先直接读多个 Owner，跨越 Core 停止操作；串行 App Owner 完成 PWR/Runtime/Card 动作后才能取得完整状态。新增单容量 OwnerSnapshotQueue，USB 只提交请求并有限等待，既有 System App tick 执行真实 reader。队列不持有页面缓存、不重新构造栈、不重试 invalid_state；关闭时释放待采样请求，进行中的读取完成后也拒绝发布已退休状态。停止 Adapter 前关闭队列，每次 System start 建立新队列。主机测试锁住生产者不可读取、Owner 完成操作后采样、并发忙碌及关闭中读取；前一项先失败再修复通过。


## 第七次 attempt：队列实现失败

镜像 64565216a（ELF SHA-256 64565216a5116d2379dc96e0d6dc98a4cbed182803dfdc73e9d61951a2f849fb，BIN SHA-256 4fd87a8e32fdb20213409f992b70af2177df1ca5cd2472d610d773ec099da972），主机与完整增量 build 通过并写入校验。Attempt 20261002T102803Z-0b08153a-f381-48ee-a4a9-301b489dd457：FAIL，Native summary 第一条触摸时 abort 并重启；release 和最终快照未完成，不能记清理成功。

用独立保存的该 ELF 解码：std::future::get → System snapshot reader → TestProtocol → USB worker；前一条 TaskScheduler 日志报 std::future_error: Promise already satisfied。没有证据证明重复 promise 完成来自哪一层，不能归罪上游已知 bug。新增队列的 future 实现未验收；改用互斥保护的显式 Request result，USB 最多等待 2 秒，Owner 填写结果，关闭时返回错误，不新增 future 异常链路。并发、关闭与 Owner 顺序主机门槛保留；修复仍需实际设备重跑。


## 第八次 attempt：真实 Runtime 重启脚本

镜像 c4dfa5af8（ELF SHA-256 c4dfa5af89ed1a6519b42d2fe684054d4884f720636cc5c2f7a0457f78bf15e4，BIN SHA-256 79f1d38d232935ca7cb3c27cc5fab66f4f0349308ce62a3c898892c449ce292a），显式请求状态版本完整 build/写入校验完成。Attempt 20261002T103831Z-5b9dbabb-f467-431b-a46f-33a2995f1815：FAIL，28 个步骤。Native 全组和 Runtime 首次 Root/负向 Back/PWR Home 均通过；无输入超时、快照竞争、JSON 破坏或崩溃。第二次 Runtime 启动真实失败：SyntaxError: redeclaration of 'navigate'；Core 回落 Watch Face，Card 返回 card_launch_failed。最终 release 成功，seq=454，真实 Watch Face、inputBusy=false。

Hello Runtime 的顶层 const/let 在锁定 JS backend 保留的 realm 中重新执行时重复声明。用现有 Node VM 实际样例测试新增同一 context 二次 evaluate，以及停止旧运行后异步结果不得写新 UI，先复现相同 SyntaxError。样例入口改为 IIFE 局部作用域，仅 globalThis.brookesia_app 导出生命周期；不是修改官方 backend 或另建 JS 实例。主机回归及锁定 Toolkit 1.0.1 实际 debug BPK 构建通过。需刷新 LittleFS 中的真实脚本，并独立记录 App/resource identity；ELF identity 不能单独证明资源已更新。


## 最终 synthetic-input 结果

独立 attempt 20261002T104708Z-f4b946d3-ba7f-475d-81b9-0a8bb6f15ebf：PASS，37 步全部通过（36 个 Card 检查步骤及初始唤醒）。Native 与真实 Runtime 各自覆盖首张 Root、第二张目标 Detail、末端不循环、Root Edge Back 保持 Root、不误点、Detail Back 到 Root、PWR Home 后重开 Root、Card 自动息屏/唤醒和向内返回表盘。Runtime 经真实 Core/JS backend 连续三次启动成功，未再重复声明。

最终 release=ok，seq=763，surface=watch_face、display=true，前台 App/Page 为空，canBack/backPending/inputBusy 均为 false。串口窗口没有 panic、栈溢出、abort、输入/清理失败或 App 启动失败。Runtime 停止期间有两条既有样例日志 `Navigation snapshot error: JavaScript app is stopping`，属于停止实例的在途轮询拒绝；没有据此声称所有日志无错误，也没有把它当作新实例启动失败。样例用 alive/epoch 检查阻止旧结果写入 GUI，旧运行回调条件仍由源码测试覆盖。普通 Storage key 长度提示仍使用既有稳定 hash，不作为协议帧内容；没有忽略任何协议/Owner 错误，前八次失败及各自清理结果均保留。

设备身份：ESPocket-Waveshare-A0F262E30B68，硬件 USB serial A0:F2:62:E3:0B:68，端口 /dev/cu.usbmodem101。固件 ELF/BIN 为上述 c4dfa5af8；LittleFS SHA-256 a5a5f1cb08c7b02c82f60b996b5882147d494c33f61ec9b6bdbc7a3717096e32，App main.js SHA-256 d7e27a802f1575934348b2d91821bd70ce5fae32c8f2e855f5caf48838063130。debug BPK 0.1.0 SHA-256 967dbc4c6d6f422230b960cc16c8b34f91ee21023d05f6c52f722dc325ae922f；Toolkit 1.0.1。staged main.js 与源码逐字节一致，LittleFS 写入校验通过。资源更新前的备份为 /private/tmp/espocket-pre-runtime-reload-littlefs.bin，SHA-256 19db32f2a7f73e039c9da053367f8bc34da5d19808635ec6ac4107ad8ec5b9c3。

完整固件与资源构建、debug package、44 个 host unittest、M2 parser、173 个 Markdown 检查通过。原始 Driver 日志/报告在 /private/tmp/espocket-card-device-attempts/<attempt>/；构建日志为 /private/tmp/espocket-snapshot-mailbox-build.log、espocket-runtime-reload-build.log。当前设备是 Card RAM 样例镜像，reclaim 开关关闭，持久 Card 配置未修改；普通配置镜像将在物理 Card 检查后恢复。

报告 physicalInputVerified=false、visualVerified=false。已集中请求两侧各一次物理目标打开、普通横滑、Root 手势与 Card 暂停观察；结果待用户。014/03 replacement 事务、014/05 物理/迁移和 008/03 reclaim 条件保持开放。


## 普通配置构建与交接

普通配置完整 build/link 已通过，Card、Native/Runtime reclaim、旧 M6 reclaim 与 resource trace 开关均关闭。最终 Owner queue 的结果发布与 close 判定保持同一临界区，避免读取完成后的关闭竞争；并发/关闭主机检查及全量 44 项检查通过。该补充没有重新冒充设备上的关闭验收。

普通 ELF identity=71567f599，SHA-256 71567f599c68054a4a011a621f22c70bb1e8f85765342b8ff17c3466c4ab8a33；BIN SHA-256 c43c7d0ea2414b92c3e5ff399c101ea34122b1eddda1682c82e46f50cb5ebf0c。LittleFS 仍为上述 a5a5f1cb，staged main.js 校验一致。日志 /private/tmp/espocket-final-owner-normal-build.log、espocket-card-final-host.log。当前尚未刷入普通镜像：等待已发出的 Card 物理问题，保持 c4dfa5af8 样例设备可操作。答复后恢复普通镜像并执行一次新的 navigation Driver，检验新的 Owner 采样对待决 Back 的影响。

## 物理验收发现 Runtime 空白（未修复）

用户报告左侧观察均正常；右侧 Card 点击 Open 后空白，仅留下 Home 方向提示，看起来没有进入 App。该反馈推翻整体验收通过的可能，014/05 不关闭，不能用此前 synthetic PASS 覆盖。

独立诊断目录 `/private/tmp/espocket-runtime-blank-20261002/`。只读 hello 确认设备仍为 c4dfa5af8；初始 snapshot seq=1、surface=app_card.right、display=false、foregroundAppId/pageId 为空。串口连续出现 `Navigation snapshot error: not_started`。未据此断言 crash、启动失败原因或后台实例归属。

`power-fresh-open.json` / `power-fresh-open-serial.log`：唤醒、PWR Home、从表盘向左进入右侧首张 Card 成功；点 Open 后等待 Runtime Root 超时，最终 seq=90、app_card.right/display=true、前台 App/Page 为空，release 成功。没有观察到此次点击的 Core 启动日志。此前直接在异常 Card 唤醒点击也没有打开 App；一次尝试横滑返回超时单独保留，不能从缺少 Card ID 的快照判断它是首张或第二张。

保存异常证据后，用 esptool chip-id 的 hard-reset 重启一次，不改分区或资源。`reset-open.json` / `reset-open-serial.log`：重启后的同样右侧首张 Card → Open 成功，真实 foregroundAppId=espocket.app.hello_runtime、pageId=root、display=true，release 成功。这是重启后的对比结果，不是修复；当前 Root 的视觉确认已询问用户。尚需找到异常的具体运行触发条件并建立回归，暂未修改实现或声称根因确定。

用户随后确认重启后确实看到 Hello from JavaScript 和 Open Detail，证明该次 Root 实际画面正常。继续执行两个独立缩小路径：`mixed-20261002-211842` 覆盖 Native Root、Runtime Root、Native Detail、Runtime Detail、Runtime 重开与各自 PWR Home；`app-button-20261002-212031` 覆盖 Runtime App 自带 Open Detail 按钮、Detail 普通非边缘横滑保持、Edge Back 回 Root、PWR Home、Card 重开 Root。两者合成输入均 PASS，release 成功，没有重现初始异常；不能据此关闭空白 bug 或声称找到根因。两者原始 serial.log/report.json 位于同一诊断目录。已返回 Watch Face，并启动一次物理 Open 的实时串口采集，等待用户单次操作反馈。

用户在实时采集期间实际执行右侧首张 Card → Open，答复“正常出现”。`live-physical.log` 同时记录 Core `App started: id(5), manifest(espocket.app.hello_runtime), total_ms(482)`；该窗口没有观察到 panic、abort、栈溢出或 App 启动失败。采集完成后主动结束串口进程，退出 130 来自采集器 KeyboardInterrupt，不是设备崩溃。

`app-sleep-20261002-212339` 又独立验证真实 Runtime Root 自动息屏、PWR 恢复 Root、PWR Home、Card 重开 Root，合成输入 PASS，最终 release 成功、seq=507、实际 Runtime Root/display=true。该项没有增加用户验收轮次。初始异常仍未修复；已询问最初空白之前是否曾启动/切换 Runtime，以缩小生命周期状态差异。当前没有 firmware 源码变更、没有换镜像，也没有把所有右侧物理步骤标为通过。


## 当前验收接受

用户明确“没问题就过吧”，接受当前 Card 交互结果，停止重复请求同一路径操作。左侧物理反馈正常，右侧重启后的 Root 画面与一次物理 Open 已确认正常；其他路径采用既有独立 synthetic/组件证据，不新增未发生的物理结果。此前空白仍记录为根因未确定、重启后未再复现，不标为已修复。014/05 的当前样例交互条件接受；实际 package replacement/配置迁移和 008/03 回收门槛不因本次接受而关闭。

## 恢复普通配置后的独立导航回归

当前 Card 交互接受后，恢复普通镜像 71567f599，仅写 App 分区 0x60000，esptool 输出 Hash of data verified；NVS/LittleFS 不修改。普通 ELF/BIN SHA-256 与上述已构建值一致；Card fixture、Native/Runtime reclaim、旧 M6 reclaim、resource trace 均关闭。启动原始日志 `/private/tmp/espocket-post-card-normal-startup.log`，写入日志 `/private/tmp/espocket-post-card-normal-flash.log`。

一次新的 navigation attempt `20261002T135831Z-cf301c99-7fab-45fe-8c36-a475c6308db9`：PASS，34 步（初始亮屏无需唤醒步骤）；目录 `/private/tmp/espocket-post-card-normal-attempts/<attempt>/`。覆盖最终 OwnerSnapshotQueue 实现下的 Native Detail Back、Root 负向 Back、确认取消/允许、重复请求、超时与迟到确认、PWR 中断待决、重开 Root、Home Space 返回与显示切换。最终 release=ok，seq=360，Watch Face/display=true，foregroundAppId/pageId 为空、canBack/backPending/inputBusy=false。窗口没有 panic、栈溢出、abort、App 启停失败或 synthetic-input 清理失败。仍是 synthetic-input，不追加物理/视觉声明。
