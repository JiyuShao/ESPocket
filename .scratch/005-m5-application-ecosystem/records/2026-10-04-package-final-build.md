# 2026-10-04 — 包准入候选最终主机与构建检查

本次承接 [03](../issues/03-enforce-core-package-trust.md) 与 [09](../issues/09-allow-unsigned-developer-installation.md)。用户要求继续收敛当前包安装工作；本记录区分主机、构建、备份与设备结果；实际安装、运行与模式切换只按对应设备证据判定。

## 主机与评审收敛

- 重新执行 `python3 scripts/check.py`，各组件测试和 80 项跨模块主机测试全部通过；Markdown 检查通过（252 files）。原始日志为 `/private/tmp/espocket-continue-host.log`。
- [14:19 检查点](2026-10-04-package-review-followup.md#完整主机门槛尚未通过)的三项失败在当前补丁组合中已通过：queued event 撤销、失败 on_stop 的 Runtime 清理、KeyboardClosed Owner 隔离。既有测试仍先验证未修复上游失败，再验证全部补丁叠加后的真实控制流通过；未修改或弱化断言。本次没有新增这些修复，当前文件中的后续修订已保留前序补丁行为。
- R1 的真实 policy tick 编译回归覆盖停止失败后的有界退避、恢复与重新开启后再次关闭。
- R2 的真实 Card Owner 编译回归覆盖声明、CardKey 顺序、持久配置恢复，以及原本无 Card 的旧版本回滚。receipt 提交之前不持久写新配置；提交后持久写失败返回 `committed_package_card_persistence_failed` 并保留 backup，不撤销已提交包。
- R3 的实际 Core 安装控制流回归注入 failed final 删除失败，断言返回 `rollback_cleanup_failed` 且旧版本 backup、private data 与有效 receipt 保留；没有把 rename 失败测试当作删除失败证据。
- 产品源码的 `git diff --check` 通过。统一 diff 全量检查仍报告 Core 005 补丁中四个仅含空格的空白 context 行；这些是精确 unified patch 的上下文格式，不以删掉上下文空格改变补丁输入。

## 构建恢复与输入

复用 `/private/tmp/espocket-m5-direct-final` 的失败构建副本。复用前确认当前产品 components、Native/Runtime 资源与源码一致，main manifest 的差异仅为隔离构建的精确依赖约束和 override。七个 patch manifest 与 `patch-inputs.json` 一致；从原始锁定组件重新精确应用所有补丁，逐文件对比所得 inventory 与实际构建副本一致。

此前 reconfigure 缺少板级生成配置；已有 `gen-bmgr-config` 生成的目标板配置保留，重新应用 production playback-only Audio 设置后完成 reconfigure。第一次在沙箱内运行因 Component Manager 的 psutil 进程树查询被拒绝而失败；获准在沙箱外运行后通过，不修改工具链或 managed source 绕过限制。磁盘约有 47 GiB 可用，磁盘不足已不是本次构建 blocker。

构建前后分别确认精确 registry lock、七个补丁组件选中路径、playback-only Audio 设置与有效配置字形覆盖通过。完整 ESP-IDF 6.0.1 `idf.py build` 成功。原始 reconfigure/build 日志为 `/private/tmp/espocket-continue-reconfigure.log` 与 `/private/tmp/espocket-continue-build.log`。

## 候选身份

| 项目 | 结果 |
|---|---|
| Image identity | `f6cb09bbd` |
| ELF SHA-256 | `f6cb09bbd666b544997d1f3aaee93b3f3572301472de716d1acba5e914a9a6ca` |
| BIN SHA-256 | `18226606313c55affa6e37dac7453e8e171300f8c99f61c681ecf1fdd3818967` |
| BIN 大小 | `0x6b7810`，7,043,088 bytes |
| App partition | `0xa41000`；剩余 `0x3897f0`，34% |
| 独立保留目录 | `/private/tmp/espocket-m5-reviewed-f6cb09bbd` |

保留目录包含 ELF/BIN、最终 sdkconfig、生成 lock、patch-inputs、源码 fingerprint、主机/build 日志与 `verification.json`。BIN 内嵌的 ELF SHA 与实际 ELF hash 相同；最终核对期间当前产品源码未改变。该候选不是已经刷入或验收的设备镜像。

## 设备只读检查与未完成项

USB hello 确认 `/dev/cu.usbmodem101` 当前仍为 `5bb555ca5`，开发模式协议可用；snapshot 返回 Store Root、display off、inputBusy false。只执行 hello/snapshot，未备份 Flash、刷写、安装或改变设置。原始只读日志为 `/private/tmp/espocket-continue-device-readonly.log`。

锁定 Store 的 Installed row 只有 Uninstall；`handle_primary_action` 的 Installed 分支调用 uninstall，没有 Open/start 入口。不能依靠该页面完成新装外部 App 的启动验收。动态 Launcher 继续由 [04](../issues/04-project-dynamic-launcher-from-core.md) 持有，不在本次擅自扩展。

后续需要按照 [实现交接](2026-10-04-package-implementation-handoff.md#设备与安装路径)和[此前备份限制](2026-10-04-package-implementation-evidence.md#未完成与阻塞)，取得明确的本地备份范围授权：app `0x60000`、size `0xa41000` 与 LittleFS `0xaa1000`、size `0x4e2000`。备份保留于本地；LittleFS 可能包含 App 私有数据。随后只刷 app，保留现有 LittleFS，并验证 Store Cancel/install 与可执行的重启发现路径。实际 launch/PWR、mode-off/re-enable、更新回滚与正式签名成功路径仍未验收，03/09 不关闭。

## 已授权备份与保留 LittleFS 的候选修订

用户在 app 与 LittleFS 本地备份、随后只刷 app 的明确范围问题后回答“要”。此授权已成立，不再作为当前 blocker。没有备份 NVS／全 Flash，也没有刷写生成的 LittleFS。

备份目录为 `/private/tmp/espocket-m5-device-backup`（创建时 umask 077），包含原始数据、文件 inventory 和本地 ledger：

| 分区 | Offset / size | SHA-256 |
|---|---|---|
| App | `0x60000` / `0xa41000` | `14cda84b8fdc558f5099d400a811cf256c65a94c97fb3174cc598f777804fed4` |
| LittleFS | `0xaa1000` / `0x4e2000` | `736a71076bffacb0f28e369c03436512ad33636ac09d45deacfe7169e262354d` |

App backup 内嵌的旧 ELF identity 为 `5bb555ca5`；LittleFS 成功只读挂载。首次 LittleFS 读取中途失败且未产生文件，随后使用 115200 重试完整成功。设备原缓存存在 Flappy Bird `0.3.0`，artifact SHA-256 为 `ffdf1250f6be38377fe46617b6e0cca196cad4a388f9009edcdf87045165297a`，此前未安装。

刷写前发现 Hello Runtime 的 manifest 字节不同：部署版显式包含 `services: []` 并使用多行 systems，当前 source 缺少 services。其余八个 member 相同。为保留已部署 LittleFS，源 manifest 采用相同表示；不放宽 build allowlist 或成员 hash gate。新 manifest SHA-256 为 `efc63a1bca7f933c5f4b1168c9957233e6027b6fe092d4d99d86c4082c6cbd6e`。

修订后完整 `scripts/check.py` 通过（80 项跨模块测试），完整构建生成 `86558ce79`；九个内置 member、七个精确补丁、registry lock、Audio 与 glyph gate 都通过。ELF SHA-256 为 `86558ce79c640479ac189f1a5c540f3ba9dd34c365b0e257cb4260a199cd529c`；BIN SHA-256 为 `55afc9c4387d87b3187c555a952dc6822b6a7601a7033ecdbd642bb8bfb943e1`。仅 app `0x60000` 写入且 Flash hash verify 通过；初始 `f6cb09bbd` 从未刷入。

## 第一次设备启动失败与配置恢复

首次两次 USB hello 没有响应且没有启动日志。显式释放 DTR 再硬复位后捕获了 `86558ce79` 的真实启动日志，反馈稳定为 `Fatal initialization failure: No display output with touch support is available`，没有完成 ESPocket 启动。该镜像不能算设备通过。

配置对比确认，之前未生成板级配置时的 reconfigure 已把 System、Network、Display、Power、Wi-Fi HAL 保存为关闭；之后生成 Board Manager 配置没有重新开启这些缓存值，Audio-only gate 未捕获这一问题。同一板卡已验收副本中的 HAL 设置包含 466×466 LCD、touch、Wi-Fi、KV、Network/HTTP/SNTP 与 Power 实现。本次在独立构建副本中恢复这些 HAL 配置，保留 playback-only Audio，重新构建，并将上述板级能力加入刷写前校验。原始 managed components 未改写。

首次失败与其原始日志保留于 `/private/tmp/espocket-m5-reviewed-86558ce79`；后续成功候选和设备结果另行记录，不能以 host/build 通过覆盖本次失败。

只恢复 HAL 开关后的编译检查进一步拒绝 Wi-Fi event task stack（实际配置 2304，小于锁定源码要求的 3072）。随后完整差异核对发现 PSRAM 与 secondary scheduler 等板级值也未生效。通过 `/private/tmp/espocket-store-glyph-build/firmware/build/espocket.elf` 的 SHA-256 与保留的原设备 `5bb555ca5` 相同，确认该副本的 sdkconfig 是已验收的同板完整输入；改用此完整 sdkconfig，重新应用 production Audio 与 16 KiB Runtime 设置。没有修改上游栈门槛或降低要求。最终校验同时检查 PSRAM、外部任务栈、secondary scheduler、USB console 与 Wi-Fi event 栈；恢复期间的失败 build 日志独立保留。

## 完整板级候选启动与样例回归

恢复已验收的完整板级输入后，ESP-IDF 完整构建成功，独立保留目录为 `/private/tmp/espocket-m5-reviewed-f2791ea1b`。

| 项目 | 最终板级候选 |
|---|---|
| Image identity | `f2791ea1b` |
| ELF SHA-256 | `f2791ea1b921277dfbc072be05f7e6ead124a8b34c4912591eaf04efb2ffb76d` |
| BIN SHA-256 | `8aeb84a07d4beb292dd3608abda905e0ceec278d00ddda464c7d1d007ac55a84` |
| BIN 大小 | 7,689,824 bytes |
| App partition | 10,752,000 bytes；剩余 3,062,176 bytes，约 28% |

Registry lock、七个精确补丁 inventory／选中路径、Audio、字形、完整板级能力、当前源码 fingerprint、九个部署内置 member 与 BIN 内嵌 ELF hash 全部核对通过。仅写 app `0x60000`，Flash hash verify 通过；未改 LittleFS／其他分区。

真实首次启动日志记录 Hello Runtime 重新发现与 `ESPocket started`；USB hello 为 `f2791ea1b`，snapshot 为点亮 Watch Face、无 foreground App、inputBusy false。首次样例探针在串口线状态切换时读到重启标记，尚未执行触摸即失败，原 attempt 保留。改用仓库既有测试相同的默认串口状态，区分连接初始化与测试执行后，`sample-smoke-normal-transport` PASS：Native 与 Runtime 的 Launcher→Root→Detail→Back→PWR Home 全部达到真实 Owner 状态，最终 Watch Face、inputBusy false。该结果使用合成输入，不替代实体按键、触摸硬件或像素验收。

后续 `store-open` attempt 的 Launcher transition timeout 保留为失败。连接阶段日志出现不属于本探针的实体 PWR 操作和 Store 开启，测试起点已改变；已向用户核对是否在手动操作设备。此 attempt 不算 Store 取消、安装通过；后续按稳定设备起点重新验收。

## Store 确认仍需真实弹窗核对

用户明确回答“暂不操作设备，继续自动验收”后，从重启后的稳定状态再次测试。`store-clean-start` 的 20 秒启动等待和随后 hello 超时均保留为失败；后续独立 attempt 首帧收到 request_id 0 的 `bad_request`，该次 hello 未通过，之后 release 与真实 snapshot 成功。没有忽略错误、修改协议能力或把后续 snapshot 补算为 hello PASS。

再一次独立 `store-cancel-stable` 的 hello identity 为 `f2791ea1b`，通过真实 Launcher 与 Store Root Owner 状态；使用慢速、释放前停留的列表滚动后，点击计算得到的包操作位置 `[360,276]`，真实 Shell 在该次点击之后打开 request 1。随后 `[233,266]` 点击未产生该提示的 closed 日志，因此 Cancel 判定失败；没有 Continue install 输入，也没有 Core `Runtime app installed` 正向日志。

实际弹窗文字和按钮位置不能由 Store Root snapshot 推断。已集中请求用户报告屏幕提示标题／按钮；若确为 Developer compatibility install，要求点 Cancel 并报告。USB 监听 `store-dialog-human-check` 只在屏幕关闭时通过既有 PWR 唤醒，未点击未知弹窗；45 秒监听期间没有提示关闭或 Runtime 安装日志，最终快照仍为 Store Root、display false、inputBusy false。未进行安装后 receipt 验证、安装后重启发现或模式切换，不将本轮计算点击当成真机 Cancel/install PASS。

下一步：先取得真实弹窗文字与 Cancel 回调证据，再读取 LittleFS 证明没有安装副作用；随后通过同一官方 Store 路径确认 Continue install，核对 artifact／receipt 和重启 discovery。动态 Launcher 04、外部 App 启动／PWR、mode-off/re-enable、更新／掉电回滚及 08 正式签名成功路径仍未验收，03/09 保持开放。设备当前保留可启动的 `f2791ea1b` 与原 LittleFS，不恢复或覆写原备份。

## 截图镜像与当前设备状态

2026-10-04 后续：用户授权截图，当前已刷入 f3fdd7e82，app-only 写入、Flash hash、启动与 USB identity/capabilities 通过。LVGL 渲染帧捕获和默认 512-byte 分块导出经整帧 SHA-256 验证，实际 Local 页显示 Flappy Bird Installed，Core 启动亦发现该包。此前安装状态未确认的事实保留，但不据此断言当前仍未安装。计算点击在当前位置指向 AI Chatbot，未知提示不算 Flappy Bird 的确认/取消证据；receipt 仍未读取，005/03、09 不关闭。截图实现、失败和独立成功 attempt 见[012 截图记录](../../012-test-automation-contract/records/2026-10-04-rendered-frame-screenshot.md)。
