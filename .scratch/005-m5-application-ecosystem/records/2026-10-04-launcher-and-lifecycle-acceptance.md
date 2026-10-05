# 2026-10-04 — Launcher 与包生命周期自动验收

本记录对应用户“全部执行”的授权。保留之前的失败与阶段事实；当前状态按本轮实际证据更新。原始日志、截图和备份留在 `/private/tmp`，不提交二进制、签名私钥或设备分区备份。

## Launcher 普通候选

镜像 `0116972e3`：ELF SHA-256 `0116972e367f75abef45f12d5bc68db4988e7891e4eef49987b9ea7b993eb753`，BIN SHA-256 `e55613661b2c05aeec39f6a88b12a7e04b8f61139270f153da21f77ee00464fe`，7,719,408 bytes。仅写入 app partition `0x60000`，Flash hash、启动与 USB identity 通过；未写生成 LittleFS、未读 NVS、未全片擦除。

Core 重启发现实际已安装的 Flappy Bird 0.3.0，Launcher 完整投影显示动态条目、名称及图标。成功截图原始像素 SHA-256 `b6da8038e0b3c344ca8d8f83e38ee6c48e8c74e9953cf5ea8ec7fb40c3a939a6`，证据目录 `/private/tmp/espocket-m5-reviewed-0116972e3/steps/d972c93f-a2f1-47d4-991d-79adbf0c57fe`。固定 Native、Runtime、Settings、Store 四个入口保留。截图显示动态行前有过大空隙，后续候选隐藏空状态 label 并移除旧 bottom spacer。

动态投影的真实 Owner 方法通过主机 GUI fault harness：snapshot/create/row/text/binding/swap 失败保留上一完整 view 与固定入口；失败重试限速；缺 icon 使用文本；图标 lease 在失败、替换及 stop 后平衡；retired view click、重复 dispatch 和 click/uninstall race 不启动；Shell start 重建。模型回归另覆盖 hidden/Native/fixed/untrusted/mode-off filtering、sorting、identity collision 与 runtime identity 更新。主机结果不代替全部设备条件。

## 外部包运行与实际安装事实

Flappy Bird 的 retained archive SHA-256 为 `ffdf1250f6be38377fe46617b6e0cca196cad4a388f9009edcdf87045165297a`，与设备官方缓存包一致。Core receipt 绑定 0.3.0、manifest digest、成员、transaction、platform baseline，并明确 `signing_key=unverified`、`unsigned=true`、`super=true`。只算开发者例外，不算正式发行。

当前 lifecycle 前置备份 `/private/tmp/espocket-ecosystem-device-baseline/littlefs-before.bin`，SHA-256 `94362ac6044de165c86c41add590016ce079cf4e7f78326c963fa0d608b0f77d`。只读 LittleFS 备份，未读 NVS。

点击 Launcher 动态条目后真实 Runtime 启动，第二次启动日志记录 Core `total_ms(6052)`。启动完成的 Owner snapshot 返回实际 `foregroundAppId=brookesia.general.flappy_bird`、空 Page、`navigationAvailable=false`、无 Back。PWR 真实 Core stop 后返回 Watch Face，前台身份清除。

保留的失败：第一次在启动过程中采样遇到 2 秒 Owner mailbox deadline；后续主机旧校验误拒绝“有前台 App、无 Page”的合法兼容状态。新增 regression 先失败，再调整主机仅接受显式 `navigationAvailable=false` 且空 Page/Back；错误 Page/Back 状态仍拒绝。22 个 driver tests 通过。游戏画面尚未成功取得，若截图失败不算游戏视觉通过。

Store Installed 实际显示 Flappy Bird 与 Hello Runtime。截图像素 SHA-256 `b053ee3aeeb43cccc70bb8b6c263e2dfad75d408aa18d7500ac96f7be31afc2f`，目录 `/private/tmp/espocket-m5-reviewed-0116972e3/steps/13cae351-6e76-41c8-bb16-c1cc96038352`。已点击 Flappy Bird Uninstall 并打开 request 2 弹窗，未取得弹窗截图/确认提交证据前不算卸载通过。

## 截图可靠性后续

同一镜像仍有 `busy`、`screenshot.read invalid_state` 和单个 read timeout 的失败尝试。失败没有保存 PNG，不能以先前成功图覆盖。ESP-IDF 物理 USB SOF monitor 仅使用 3 ms gap 窗口；新候选增加 200 ms sustained-loss confirmation 和断连清理日志，主机覆盖短 gap、恢复、持续断开和重连。真机可靠性仍以新候选结果判定，不声称原因已完全证明。

## 签名准备与外部发布边界

使用锁定 `@brookesia/packager` 0.1.7 的准备脚本生成并验签测试 0.2.0；测试公钥 SHA-256 `0284fa5b9a1aa3accfd42c96693ad8bf6fa08cdd1b86c1da3834228865420c18`。成功产物 SHA-256 `16c1eed80d06be9788867adc4b3bbdaa864aa9efb372e8adf30f436c5e96dbed`，目录 `/private/tmp/espocket-release-preparation-check2`。第一次准备暴露 SDK 会规范化为 `.release.bpk` 的输出名，修正后 SDK signature/member verification 通过。URL 使用 `.invalid`，明确没有上传、没有生产发布者身份，也没有设备接受声明。

2026-10-04 只读核查[官方 Store 文档](https://docs.espressif.com/projects/esp-brookesia/en/latest/app/store.html)（页面源 revision `e937455`）及[开发插件文档](https://docs.espressif.com/projects/esp-brookesia/en/latest/plugin.html)。Store 文档描述读取 remote index、download/install/remove，未提供本设备的 publisher credential 或 catalog 写入授权；插件列出 pack/verify/release，不能仅凭工具名推断已获得发布权限。锁定 Store 0.8.2 的默认 API root 为 `https://brookesia-app-store.espressif.com/api/v1`，读取 `index.json` 与 `apps/<package_name>/versions/<version>/metadata.json`。正式发布者身份、已有 signing key、设备 trust root 和受支持写入权限仍缺少，不生成身份或假装发布完成。

## 隔离测试候选

默认关闭的 package acceptance fixture 使用真实 Core/Storage/Developer Mode API，两个专用 signed versions、公开测试公钥，以及一次激活 hook 故障。只操作 `espocket.test.store_hello` 与 fixture 自有文件；Flappy Bird 用于运行中关闭模式、保留安装、拒绝启动、重新开启与 PWR 的矩阵。计划在正常模式验证 signature 成功、update/rejection/rollback/private data，分别在 pending activation 和提交后执行受控 reset/reboot，核对 discovery/uninstall，再移除测试输入并恢复初始模式。

当前完整构建与设备结果待本轮继续补充。fixture 的 PASS/COMPLETE 之前不勾选设备验收；之后必须刷回关闭 fixture、没有测试 trust root 的普通镜像。

### 首次隔离运行失败与修复

隔离镜像 `3ae4e62bb`（ELF SHA-256 `3ae4e62bb3454b98ad60047b516530bcf844862cd782b8f85cf6a004c1c1de63`；BIN SHA-256 `eb6cd0705d90150e9d4eb94bab918f2d9803cfa7f3ec7415604a84e311f29722`，7,754,256 bytes）完整构建、主机检查、app-only Flash hash、启动及 USB identity 通过。自动 fixture 首次普通模式切换发生 `esp_task_stack_is_sane_cache_disabled()` 断言，零个生命周期 checkpoint 通过。原始失败保存在 `/private/tmp/espocket-m5-reviewed-3ae4e62bb/package-acceptance/`。

该 ELF 回溯明确为 `tick_package_acceptance` → `DeveloperMode::set_enabled` → `write_mode` → `nvs_set_u8` → Flash cache disable；App Owner stack 位于 PSRAM。安装事务尚未执行。修复将 mode 持久化交给真实 Storage Service，其内部 RAM worker 执行 Flash IO；沿用 `espocket/dev_mode` 布尔 `uint8` schema，不复制／读取整个 NVS、不创建第二个存储线程。缺键默认关闭，服务失败保持 fail closed，保存成功后才更新内存 gate。该设备 fixture 是实际外部栈失败路径的回归，普通主机 stub 无法证明 IDF cache-safe。修复后的完整构建及相同真机回归另行记录，不将此失败计为通过。

重新检查前次 Store 原始日志发现卸载操作实际上已调度，最终报目录删除 `Wait timeout after 5000 ms`；`3ae4e62bb` 重启只发现 Hello Runtime，未发现 Flappy。此前“未确认卸载”的观察不足以判断操作是否执行。fixture setup 在 identity 缺失时，通过真实 Core gate 恢复官方缓存中的原 Flappy 0.3.0，绑定原 artifact SHA-256、manifest identity 与 version；这只恢复先前用户安装的基线，不计为 Store UI 安装验收。fixture 每个测试阶段在需要时点亮屏幕，避免长事务后 PWR 仅唤醒被误判为 Home 失败。

修复候选 `da8537b55` 完整构建与全部 host checks 通过，七个精确补丁 inventory/selected paths、lock、板级 HAL、Audio、字形、当前源 fingerprint 及设备九个 built-in member digest 通过。ELF SHA-256 `da8537b555fd41be96e25e73aebfa37234e89a96bf979c5cd0be68f60867c516`；BIN SHA-256 `65f36f4adb94da8a0ac9f4a5d5445b5c1a080d5ba543ebb098113cc3c61f9224`，7,755,472 bytes。设备 lifecycle 结果在下一段补充。

### da8537b55 真机推进及保留的失败

app-only Flash hash、启动、USB identity 与 mode 持久化均通过，未重现 Developer Mode 直接写 NVS 的断言。首次 fixture setup 被 Core 以 `developer_confirmation_required` 拒绝，原模式恢复成功；该失败保存于 `package-acceptance-setup-failed`，未绕过 gate。随后通过真实 Store Local 安装恢复用户的 Flappy。

Store UI 的顺序证据如下，均位于 `/private/tmp/espocket-m5-reviewed-da8537b55`：

- Local 未安装截图 `steps/d542d86f-c923-4ed3-8ec0-77f2d8a87fec`，像素 SHA-256 `733bf9871505af0f0467d32cdebfab469ad1b80f14d4efa135af27025e418c6a`。
- 点 Flappy Install 后显示真实 “Developer compatibility install”，Cancel／Continue install 坐标分别为 `(233,265)`／`(233,320)`；`modal-steps/2d50f6eb-43f7-466e-b026-5c05c6ab1783` 像素 SHA-256 `e89c8e867b9edacf524922b52dde937e0aa3b70a76e26635b006cadb03f52e12`。
- Cancel 关闭 request 2，`steps/d8b82a9f-9990-4bd6-ba8a-063d13a28c3e` 返回完全相同的未安装 Local 像素摘要，无 install 调度日志。重新 Install 打开 request 3。
- 正文可滚动；`modal-steps/eead8637-07c7-46c7-adae-6cf6484e9a46` 显示关闭模式会停止／禁止启动、保留安装内容，以及未签名发布者未经验证，像素 SHA-256 `1ba9fbe38daee6ae77c8bfe91d17b92eb607154bf73a6a17df119ee38763c5a6`。提示不要求虚构导航。
- Continue 后 request 3 关闭、真实 install request 4 打开。此次 `modal-steps/964eac95-7754-4cee-9c55-dbabd64b84e4` 截图 response timeout，保留失败。15 秒后采集 Owner 状态仍可响应；最终 `steps/a9f28ff8-238c-45d9-b766-87394482b139` 显示 “Installed Flappy Bird” 与 Installed 按钮，像素 SHA-256 `46ae844df0f6ad50cb1d9f6ceb00d52ec109dfae24f68a5b2b2aa83f22928d18`；随后受控重启 Core 重新发现 Flappy。

安装期间发生 `task_wdt`（IDLE0 未及时运行），当前任务 `SvcMgrSec0`，回溯为 Storage `function_fs_stat` → `make_file_info` → LittleFS `getattr/stat`。没有自动重启，最终安装成功，但不满足无 watchdog 门槛。真实 scheduler worker 只在空队列 sleep，持续 ready queue 没有 Idle window；提取实际 worker dispatch block 的主机回归使旧版失败，候选 `poll_one`＋busy 时 1 ms sleep 通过，空队列保留原 polling interval。维护锁定 `brookesia_lib_utils` 0.8.2 补丁，全部源码 inventory/hash 固定；不降低 watchdog 门槛或修改 Idle 监控。该候选仍需相同 Store 真机回归，主机通过不证明已解决全部 LittleFS 耗时原因。

受控重启后的 signed fixture 实际通过普通模式 v1 安装和 receipt、真实 Root 启动，以及 corrupt signed update 拒绝。注入 v2 activation failure 后 Card rollback 持久化触发另一处 `esp_task_stack_is_sane_cache_disabled()`；精确 ELF 回溯为 `restore_replaced_card_state` → `CardConfigurationStore::save_current` → `write_cards` → `nvs_set_str`，并非 package 文件 IO。修复将 Card KVGet/KVSet 交给 Storage 内部 RAM worker，保持原 `espocket/cards_v1` raw JSON string schema，避免 typed string helper 增加转义。原失败保留在 `package-acceptance`；后续候选需完成真实 rollback/recovery 才计通过。重新执行 fixture 前只清理被同一测试公钥验证、artifact SHA 与两个固定输入一致且 private marker 为 `preserve-me` 的专用测试安装；未知 identity/version/artifact/data 均拒绝，不删用户 App。

### Card 与 scheduler 修复候选

`a2f85c1a1` 完整构建、全部 host checks 与文档检查通过；构建确认全部八个准确应用的补丁 inventory/selected paths、lock、完整板级配置、Audio、字形、当前源 fingerprint 与设备 built-in members 一致。ELF SHA-256 `a2f85c1a1e7bc27329eb961a76a99b5d04d9c2558e99e6fcd1d501a141037e44`；BIN SHA-256 `461619de687eddd0220520014eeea6dd2dbdf53c08684489c9c00e446bc2becb`，7,758,544 bytes。Card adapter 的真实方法编译回归验证旧 raw JSON 读取／写回不转义、缺键、错误类型／超大值、服务失败和 binding 不可用；主机结果不替代内部 RAM 真机门槛。首轮编译因 Timeout 命名空间错误失败，改为公开 helper 命名空间后完整构建成功。

隔离输入只包含公钥和固定测试包；普通固件 `CONFIG_ESPOCKET_PACKAGE_ACCEPTANCE_TEST=n` 不包含 fixture 或测试 trust-root 配置。当前候选设备矩阵和最终普通镜像身份、结果继续按实测追加。

`a2f85c1a1` app-only Flash hash、启动、USB identity 通过。真实 fixture 在 350.695 秒内获得最终 `PASS COMPLETE`，两次受控 reset 全部完成，串口原始记录与 report 位于 `/private/tmp/espocket-m5-reviewed-a2f85c1a1/package-acceptance`。矩阵通过普通模式 signed v1 安装／receipt／Root 启动、corrupt signed update 拒绝、activation hook 故障回滚至 v1 并保留 private marker、pending v2／v1 backup 时 reset 后恢复 v1 和 private data、普通模式 v2 更新／启动／PWR Home、外部 Flappy 无虚构 Page 运行、mode off 实际 stop/Home／保留 receipt／拒绝 start／Launcher 隐藏、mode on 重新准入／运行／PWR Home，以及提交 v2 后 reset 的 discovery／private data／Root 启动／uninstall／receipt 和 retained archive 移除。随后删除专用包、私有 marker、v1/v2/corrupt BPK 与公钥，恢复初始 Developer Mode。

整个 monitored run 无 panic、assert、task watchdog 或非预期 reset；监测器明确把 task watchdog 判为失败。只有测试声明的两次 reset；`power_supply_cut_verified=false`，物理断电恢复未验证。新 scheduler 延迟使 boot discovery 约需 69–76 秒，功能与稳定性结果不代表启动性能已优化。

最终普通候选 `a963c55b8` 已完整构建、同一源码全部 host checks、Markdown 及八个 patch inventory/selected paths 校验通过。ELF SHA-256 `a963c55b8606e6851ab097aaae5004660745455ad4777b73cfac4b4f0b7fb54c`；BIN SHA-256 `c1ceacccbc74171264f14627ef5cce2b3388652e860bf39f494f1d38e51fbc24`，7,722,576 bytes。sdkconfig 关闭 package acceptance，不提供测试 trust-root。普通镜像的刷写和 UI／Store 回归在后续追加。


### 普通镜像回归与新失败

`a963c55b8` 已 app-only 刷入，Flash hash、启动、USB hello/snapshot 通过。最终普通 sdkconfig 关闭 fixture，没有测试 trust-root。Native/Runtime 完整 apps 套件通过，证据 `/private/tmp/espocket-m5-reviewed-a963c55b8/apps-regression/20261004T143203Z-c7f9163e-c823-40a3-af79-61a4474f975f/report.json`；覆盖 Root/Detail/Back、deferred Back cancel/allow/timeout、息屏/wake、PWR Home 和新 Running Instance。之前一次 Runtime 启动瞬间 snapshot `invalid_state` 保留；测试增加 8 秒启动 quiet window 后严格核对真实状态。USB driver 新增 assert/task-watchdog 拒绝，回归先红后绿，23 driver tests 与全量 host checks 通过。

在线 Store 尝试 `/private/tmp/espocket-m5-reviewed-a963c55b8/store-online/20261004T143502Z-c9885be3-f928-4d7f-a323-c1ecf2122fb4` 判定 FAIL。启动只读取 cache；Refresh 实际提交 index request 1，并写入新的 cache/index.json，首次 PWR Home 与重进通过。重进后很快再次 PWR，在 HTTP service stopped 之后检测到 `A stack overflow in task SvcMgrSec1`，随后 panic/reset。回溯只到 FreeRTOS overflow hook，末端损坏，不能证明具体业务调用。此失败不能用在线提交成功或前次镜像结果覆盖；06 保持开放。

随后最小 Store 打开/退出循环在每次启动后等待 12 秒，连续 5 轮 PASS，无 overflow/watchdog/reset；目录 `store-cycle/66f466d3-9796-41e1-b00d-b6ffd75561a2`。这只证明等待启动的路径，尚未定位快速退出与 Refresh 的贡献。另保留首次 hello timeout、快速退出 snapshot invalid_state 与探针脚本方法名错误的失败，不计产品通过。

用户再次确认正式发布者身份、签名目录和 Catalog 权限尚未准备。08 的外部发布 blocker 保留，不生成生产身份，不执行上传。物理断电恢复仍未验证。


### Store 快速退出的最小复现与候选

`store-cycle/303c4def-6259-4ae5-a52d-b7ac18b3475d` 在打开约 1.5 秒后发送 PWR：第一轮停止后缓存 callback 报 View already exists；第二轮 Core 已 stop 后仍打开 message dialog，随后 `LoadProhibited`。不需要在线 Refresh。探针直接发送合成 PWR，8 秒后核对 Home，排除启动期间 snapshot mailbox deadline 对 verdict 的干扰。

锁定 Store 0.8.2 的真实 `FSReadText` result handler 在 Storage `call_function_task` 完成线程直接调用 `handle_cached_index_load_result`，进入 parse/index/UI 和同步 Storage 操作；generation 只在函数入口检查，无法阻止处理期间与 App stop 重叠。该路径同时与内部 Storage worker 栈预算压力相关；原 overflow hook 回溯不证明每次崩溃具有相同直接原因。

新增 `004-owner-service-completions.patch`：每个 Running Instance 使用独立 shared mailbox，Service callback 仅移动 owned result/HTTP event，App periodic timer 执行处理。stop 首先关闭并清空 mailbox，然后停止 timer；旧 callback 不读取 `context_` 或已销毁 App 状态，也不能进入新会话。Storage/Device/HTTP results 与 HTTP events 全部经此边界。主机提取真实 cached-read submit 方法：旧回调在非 Owner 线程处理，明确断言失败；候选通过 Owner 执行、退出丢弃、关闭后返回及重进隔离。候选构建和原故障设备复验独立判定。


Store Owner 修复普通候选 `069f542d0` 的 88 项跨模块主机回归、全部组件检查、Markdown 和完整构建通过。ELF SHA-256 `069f542d0a7684f4afe535d8dd848f896aa7fbb65de73c96727a3b75115e5f8c`；BIN SHA-256 `e41622c124786d2afe7b29475af682208a8ece37638d25bb59ce3c016fddc809`，7,745,440 bytes。八个准确补丁 inventory/selected paths、registry lock、源 checkpoint、板级 HAL/Audio/字形、原设备九个 built-in member digest 与 embedded ELF hash 全部通过。普通镜像 fixture 关闭，不配置测试公钥。刷写和原失败复验在后续追加。


`069f542d0` app-only Flash hash、启动与 USB identity 通过。第一轮原 1.5 秒退出时序 `store-cycle/d21cdff0-3430-4eb1-a5fd-d907eb234cfe` 判 FAIL：缓存处理已转到 App Owner，占用期间合成 PWR 超过原期限，日志 `Synthetic PWR expired before Owner execution`；没有将其计作通过，也没有提高输入 TTL。硬件 PWR 在该负载窗口未验证。

早于 cache result 的 0.3 秒退出场景 `store-cycle/a65e2aaf-473b-415a-b78c-f67d102b125d` 连续 5 轮 PASS：每轮退出与重进完成，无 View already exists、旧对话框、panic/assert/watchdog/reset。此证据验证 stop 后到达的 completion 不进入旧或新会话，不能替代 1.5 秒窗口的合成输入期限门槛。

普通在线第一次 `store-online/20261004T150919Z-fc0120c5-9c14-46c7-a6b9-71562f77b12e` 在 Refresh 真实提交新 index、Home、HTTP stop 后，通过前两次重进 snapshot，但在缓存处理过程中第三次 snapshot 遇到 Owner mailbox `invalid_state`；保留 FAIL。Store 场景的两次启动采样增加 8 秒 quiet window，之后仍严格核对 Root、Home、cache commit 和故障日志；快速退出另有独立路径，不将延后采样视作快速退出通过。


### 069f542d0 在线／离线与剩余事务失败

在线完整套件 `store-online/20261004T151217Z-b50a0ca1-a9ae-4b3a-8ee9-be006039c789` PASS，覆盖真实 index 写入、Home、HTTP stop 与重进。启动等待后的 Host-only 采样 follow-up 通过完整 checks，固件 checkpoint 差异为空。

活动取消尝试保留全部 FAIL：`active-refresh-cancel/201c0b3f-136f-48d6-8a4c-614d2a8c58b2` 启动 snapshot deadline；`8c07ea49-6056-406f-900f-6e5d1430288f` 真实 request 3 Canceled、HTTP stopped，但退出 snapshot timeout；`81f4d9ad-592d-41bf-b068-51ce83343beb` 提交 request 4 后立即 PWR 超过原 1 秒输入 TTL；`cd2112a8-eb70-43fb-9b70-ee7b4c928e5f` 延后 3 秒时 index 已完成，PWR 仍在随后 parse 工作中超期，不能算活动取消。没有提升或绕过 TTL。

Quick Settings `steps/0d5187f5-b11b-4492-b56f-c81b1e036baa` 为 Wi-Fi Linked，Developer On；`b8e25cbe-e481-4d44-8bed-4f4892630b55` 切为 Unlinked。离线尝试 `c4f9d011-729c-4739-94fe-b0585e76b1df` 读取实际 cached index，startup/Refresh 分别报告 Offline/network_ready(false)，没有 HTTP request 或新的 index write，截图显示 Network unavailable。锁定 Store UI 在 network_ready=false 时隐藏远程列表，不能把隐藏内容称为离线目录可见；Installed/Local 独立核查。首次恢复 toggle 因自动息屏后 surface 已回 Watch Face 而失败，重新进入 Quick Settings 后 `ffc934a8-81c3-44f5-8a2c-57a0e8c262d8` 截图已恢复 Linked，Developer On。

Installed `c8ddff14-bf24-43e5-a0be-21b450582649` 确认第一行 Flappy、第二行 Hello Runtime。仅点击 Flappy Uninstall；request 9 打开后 Storage FSRemove 超过 5 秒，Store 报 Failed to uninstall runtime app。等待 45 秒也不能掩盖已报告 timeout，普通卸载验收 FAIL，无 watchdog 判定仍不是卸载成功。后续须恢复 Flappy 基线。

两个新增回归先红：真实 deferred-refresh 方法证明远程 Refresh 启动不必要的本地 BPK scan；真实 Core filesystem helper 在 6 秒后端下以 5 秒预算失败。候选移除远程 Refresh 的重复 local scan，startup/Local 扫描保留；Core 递归 removal 单独使用 30 秒有界预算，普通 stat/read 保留 5 秒，成功后仍核对路径不存在。超出 30 秒、后端失败、目录残留、空路径不计成功。候选需完整构建与相同设备路径复验。


`069f542d0` 受控 reset `controlled-reset/9d647968-f12e-49b9-9578-e65076c5c5d8` 启动/USB 通过；只重新发现 Hello Runtime，失败卸载后的 Flappy 不再出现在 committed discovery。原缓存 Flappy BPK 仍可由 Store Local 扫描，`steps/1da36535-067e-481f-bd47-e2ec17b7007b` 显示未安装；`modal-steps/e089ae2c-ca3d-49ba-8fcf-f5c04b3ca419` 显示真实开发者兼容提示。Continue `steps/cf756054-205e-4c05-a20e-df0ce642bc54` 成功恢复，Core id(6) 安装、Launcher Reconciled 1 和 Installed Flappy Bird 截图成立，事务约 41.319 秒，无 timeout/assert/watchdog/reset。恢复属于旧普通镜像，不替代新候选卸载验收。

新普通候选 `4be6858d8` 完整构建及 92 项 host checks 通过；Core 新 helper 引入后测试 stub 先因缺少 src include path、随后因缺 LOGI 宏失败，补齐 host stub 与编译路径后全量通过，没有修改产品逻辑来迁就测试。ELF SHA-256 `4be6858d8d92d381e3090ed77435d5094527de6cb90be0fd979c2db09f5ccf4f`；BIN SHA-256 `ff11812cb3e20d1a2427b2de3ee67eb854d3e587e5d24f12b6ad263821843075`，7,745,424 bytes。八个精确 patched inventories/selected paths、lock、源 fingerprint、板级 HAL/Audio/字形、原设备九个 built-in member 和 embedded ELF hash 核对通过。fixture 关闭，不配置测试 trust root。

### 2026-10-05 普通镜像卸载与 Launcher 点击诊断

`4be6858d8` app-only Flash hash、启动（约 59.9 秒）及 USB hello/snapshot 通过。活动 Refresh 取消探针 `active-refresh-cancel/dfd6dba6-bc51-4885-923c-07fd19a3597a` 没有获得 HTTP admission/requestId：日志为 SNTP 时间同步等待／超时，因此保留 FAIL，不绕过 TLS 时间策略。

真实卸载 `steps/86ad80d3-b50c-4661-95d4-b95d085082ef` PASS：request 3 约 361960 ms 开始，369614 ms `Removed runtime app directory`、369617 ms `App uninstalled: id(5)`，370485 ms Launcher `Reconciled 0 dynamic App entries`。约 7.65 秒，超过旧 5 秒期限；30 秒删除预算下无 timeout/assert/watchdog/reset。截图显示 Flappy 已卸载、只剩 Hello Runtime。

卸载后 Launcher 截图 `steps/11cfb018-66c3-45b1-9570-1d705ea6b02a` 显示四个固定按钮。Store 中心、350 ms 长按、侧边和上缘点击都得到输入 ACK，但 Owner 始终无前台 App，未出现 Store start 日志；Home、息屏／唤醒后也未恢复。因此固定 entry 的真实可点击门槛尚未通过，不能由 GUI fault harness 的存在性断言替代。Native 点击实际成功启动 `espocket.app.hello`，第一次探针错误预期 `espocket.hello_native` 而报告 FAIL，保留原始失败并依据正确 Owner identity 缩小诊断范围。当前 Flappy 缺失，需在修复后通过真实 Store 恢复基线。

后续检查原始串口发现此前 compact marker filter 漏掉 `Opened App Store`；Store 点击实际到达 Shell 并返回成功，并非没有收到点击。`steps/1d34fb17-3613-4ffb-a4e7-39a7960e68c2` 在 470591 ms 启动 Store，470994 ms 又启动 Native；此前 helper 连续滑动造成第二个固定 Launcher 动作。Home 随后只停止 Native，Store 留在 Core Running state 但不再可见；后续 `start_app` 对 Running state 直接返回，不能恢复前台。空 dynamic region 遮挡假说未获证实。

固定 Launcher `on_action` 原来只检查 Surface 和 pull 阈值，未像 dynamic dispatcher 一样拒绝已有前台 App 或 modal 时的旧动作。新增真实方法编译回归 `test_launcher_action_gate.py`：Store start 后排队的四种固定动作使原代码明确失败；候选在前台／modal gate 下拒绝，再 Home 后允许重新启动。没有修改 Core Running 的幂等语义或伪造 foreground token。临时 hit-test instrumentation 已移除，诊断 build 未刷入；后续普通候选须验证快速连续动作、Home、Store 重进与同一路径安装卸载。

### f35a6fd90 普通修复候选

全部主机检查（含 9 项 Shell 测试和 92 项跨模块测试）、Markdown、完整构建及八个精确 patch inventories/selected paths 通过；ELF SHA-256 `f35a6fd90818bd773b685eb5b7d803974a20e9b425942620cebd612faa54b44d`，BIN SHA-256 `f22408450e46f1b7dbd8eeaa7462664b0d78b5bfacd80ca817e881c4e96e5979`，7,745,472 bytes。fixture 关闭、无临时诊断日志。App-only Flash hash、启动及 USB identity 通过；无 Flappy 时启动约 24.4 秒。

`steps/4c2b4906-6ba7-4aa5-a7b2-5a1f0a553105` 复验连续滑动 PASS：Store 启动后没有再启动 Native，Home 实际停止 Store，随后 Store 重新启动／Home 均成立；不再形成不可见 Running Store。SNTP 此次实际 `Synced`。

Local 第一行明确为 Flappy Bird（未安装），第二行为 NES Emulator。真实兼容安装提示截图 `modal-steps/8ccc80c2-cfa3-40ac-b5a7-75eb97b25af5`；Cancel `steps/ae979c12-ee46-4e59-a8de-bceebd947261` PASS，request 2 关闭，截图仍为 Flappy Bird Install，无安装调度／提交日志。Continue 与后续 Launcher/运行/重启/在线结果单独追加，不由此 Cancel 证据代替。


f35 Continue `steps/122c7ae9-4863-4cd9-b870-99fbe26e566b` 实际提交 Flappy：310895 ms request 4 开始，351432 ms 安装 Core id(6)，352686 ms Launcher Reconciled 1，353664 ms dialog close，约 40.5 秒，无 watchdog/timeout/assert/reset。但后续 Local scan 占用 Owner，snapshot invalid_state，capture wake 后也未通过；该整体 attempt 保持 FAIL，安装事实不提升为整条验收通过。

2026-10-05 用户报告 Hello Runtime 与 Flappy 都慢；先进行同机启动基线和完整性能候选构建，见[启动性能记录](2026-10-05-runtime-startup-performance.md)。活动取消 f35 `active-refresh-cancel/3d1ad9da-6a25-40c9-8465-37013ba79dbd` 无 admitted request，保持 FAIL。
