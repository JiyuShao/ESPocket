# 完整能力兼容设计核查 — 2026-10-04

本记录只证明隔离源码核查与设计产出，不证明实现、固件构建或设备通过。当前范围与工作状态由 [Spec](../spec.md) 和 06/07/09/10/11/12/14/15 持有；首批可靠性、Store/Launcher/包安装以及本地 Assistant 不在本线实施范围。

## 输入身份与隔离

- 原项目存在 staged、unstaged 和 untracked 的有效修改。baseline 从当前文件内容复制，包含这些源码/文档；Git HEAD 只是背景身份，不能用于声称 baseline 已提交。
- 隔离根：`/private/tmp/espocket-019-compat-rf9vjyal`；不可修改基线位于 `baseline/`，修改位于 `working/`。复制时排除 `.git`、build/dist、node_modules、managed_components、Board Manager 生成代码、虚拟环境和 cache，产品 SDK 配置保留为只读核查证据，不复制为工作配置。
- 固定上游只读 checkout：`/private/tmp/espocket-brookesia-review-20261004`；本轮 `git rev-parse HEAD` 核对为 `e937455b0db1a3e873b1da61d6d13652f3dcc7e2`。Super 0.8.3 不能代表所有同版本 Registry 内容，按固定 commit 源码核查。
- 本轮读取的锁定公共头、字体索引、Super/Files 源码及相关实现存于隔离根 `evidence/`，SHA256 清单为 `evidence/inventory.json`。这是核查输入，不是新构建的依赖物化或产品 lock。
- 原 checkout 不写入、不 reset/clean/提交；不占串口、不刷写、不重启，不向其他聊天发消息。设备归当前 Store 工作。

## 版本与接口矩阵

完整 component hash 由 baseline 的 [dependencies.lock](../../../firmware/dependencies.lock) 与隔离证据清单持有；此处避免把上游 master 与已锁定产品混为一谈。

| 组件 | 产品锁定版 | 本线结论 |
|---|---|---|
| Core | 0.8.4 | change hooks、font/language/theme 公开 seam 已有；hook 失败与保存结果传播不足；Files 导航例外未批准 |
| GUI Interface / LVGL | 0.8.2 / 0.8.5 | fontSet 与 language/reapply 已有；实际文件字体 backend 当前配置未启用，需要预算与编译证明 |
| ServiceManager / Helper | 0.8.2 / 0.8.4 | Utils snapshots、dataflow VisualOperation 可用；共享采集接口无 caller lease |
| Wi-Fi / SNTP | 0.8.2 / 0.8.2 | portal start/stop 已有；停止配网不是 target/凭据回滚；IsTimeSynced 不等于跨生命周期可信时间 |
| Storage | 0.8.3 | 真实 IO Owner；绝对路径 helper 不是 App 私有数据授权 |
| Device / HAL Interface / HAL Adaptor / Boards | 0.8.2 / 0.8.2 / 0.8.4 / 0.8.0 | Battery 信息/charge state 已有；产品锁定源缺 Expansion API，当前板无 ModuleManagerIface |
| Settings / Store | 0.8.3 / 0.8.2 | 官方已接入，保持其真实 Owner 和 Store 当前施工；Settings Debug 已有完整控制 |
| Files | 产品未锁定；固定参考 0.8.2 | 新增官方 App，需精确版本/hash/资源/导航/操作 seam，不能从依赖存在推导安装完成 |

## 06 状态有效性与状态栏

项目 `firmware/components/shell_circular/src/shell_status.cpp` 已订阅 Wi-Fi GeneralEventHappened、Device PowerBatteryStateChanged、SNTP StateChanged/TimezoneChanged，首次读与周期 refresh 已有。Wi-Fi 过渡态合并 Unlinked，Battery 把缺失/无 percentage/读失败合并 `?`；时钟仅 IsTimeSynced 为 true 才显示。stop 断开 subscription 并清 owner，但 callback 持锁进入 GUI 和 SNTP 同步读取的停止安全仍属于 01–02，不由本线改写。

锁定 `service_sntp.cpp` 的 function_is_time_synced 使用 `is_time_synced_ || iface.is_time_synced()`；stop_backend/reset_data 清该 bool。公开快照无 last-valid-time/age，因此「离线走时」不能由 Shell 缓存一次 bool 就保证跨 Service stop。BatteryIface.State 可区分 is_present、power_source、charge_state、level_source、optional percentage 和 low/critical，没有 sample timestamp；如显示旧值，age 是接收时间，不是硬件采样时间。

固定 Super [shell_status](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_status.cpp) 使用 Service 状态和时区刷新；[shell_display](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_display.cpp) 接通展开/peek、手势。产品下拉 Quick Settings、App 普通内容手势和唯一 Home 已有规则；迁移 peek 需要专门入口/手势区域，不能导入停用的 Quick Control/System Monitor。

执行范围、状态表与实际验收由 [06](../issues/06-design-status-validity-and-presentation.md) 持有。真正待选的是离线时间/旧 Battery 的呈现；Service 的读取和停止安全不是产品问卷。

## 07 设备调试浮层

锁定 Utils Helper 的 framework/utils.hpp 提供 get_debug_capabilities/config/state/snapshot、get_memory_snapshot、start/stop memory/thread 和 set_debug_config。UtilsService snapshots 有 timestamp_ms；get_debug_snapshot 的 optional memory/thread 缓存不保证新鲜。Settings screen/debug.ipp 的 push_debug_config_to_utils 先 SetDebugConfig，再按保存开关全局 Start/Stop，两种采集没有 caller token。恢复偏好可由 Settings 生命周期发起，所以 Adapter 只拦 on_action 不能实现准入。

当前 sdkconfig 关闭 FreeRTOS trace facility 与 BROOKESIA_UTILS_THREAD_PROFILER_ENABLE_FREERTOS_CONFIG，不能展示 CPU=0 为可用统计。固定 Super [lifecycle](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/system_lifecycle.cpp) 绑定 Utils、订阅三类事件、首次同步，Shell [debug](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_debug.cpp) 绘制 SRAM/PSRAM、每核 top CPU/最低 stack HWM 与阈值警告。其停机行为不是产品共享采集保证。

方案保留完整设备链路；需 Settings admission 和 Utils ownership seam，明确 Settings 退出后浮层会话可持续，mode off/System stop 释放本产品会话，观察者不 Stop 别人的采集。实际行数与圆屏占用、开销测量由 [07](../issues/07-design-development-diagnostics.md) 持有；不默认 Console/USB 增量。

## 09 语言与字体

固定 Super font index 只有 default/en（Telex-Regular.ttf）与 zh_CN/en+zh_CN（NotoSansSC-Regular.subset.ttf）。实际字节及 SHA256 由证据清单持有；磁盘量级约 40 KiB 和 1.5 MiB，不能作为分区/运行内存预算通过证明。subset 不保证全部汉字。字体语言 fallback 先选 default 支持语言，再找支持 requested language 的其他 font，否则回 default 的首种语言；见 [font_language](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/private/font_language.hpp)。

锁定 GUI Runtime 支持 register_font_file、list_supported_fonts/languages、set_language(language, reapply) 与 default font。产品环境仍固定 en，Keyboard/Dialog 等原生 LVGL 使用内置字体；sdkconfig 的 ESP_LVGL_ADAPTER_ENABLE_FREETYPE/LV_USE_FREETYPE 均关闭。照搬 TTF/index 没有 backend 不能证明中文可显示。

方案按 [09](../issues/09-design-language-and-font-support.md) 分别核查 font backend、许可/hash、维护 i18n、动态文件名/输入显示、staging、容量/heap 峰值和像素。中文 IME 不由语言迁移推导，已存在的 manifest localized name 不算产品多语言完成。

## 10 即时主题

[017](../../017-theme-token-migration/spec.md) 已有 semantic colors 和 Shell/Reference App/native Overlay 配色迁移；仍以启动解析原生 palette 为事实，不能保证运行中刷新。

锁定 Core src/system/gui_access.cpp 的 SystemGuiAccess::set_theme/set_language 顺序为：GUI Runtime set/reapply 成功 → 更新 environment/snapshot → 调 on_theme_changed/on_language_changed → hook 错误只 warning → persist preference → return success。src/system/gui_preferences.cpp persist 仅在 restore guard 完成后启用异步保存；内部另有 synchronous save，但不是公开聚合事务接口。固定 Super change hook 调 [refresh_environment](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_app_launcher.cpp) 更新文案/Launcher，不能凭 return success 推断全部 Overlay/保存成功。

需真实 Core seam 和 Settings 调用路径适配，部分失败/保存时机是唯一待选产品规则；推荐保留可用页面、明确 partial/未保存，不以重新启动 App 清草稿。[10](../issues/10-design-live-theme-switching.md) 持有失败注入和两主题视觉验收，05 启动 fallback 规则保持。

## 11 完整 Files

固定官方 [header](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/app/brookesia_app_files/include/brookesia/app_files/files_app.hpp) 为 final；公开只有生命周期/actions/timer 和 Page enum，无真实导航/路径策略配置。lifecycle 读取 Core StorageLayout，volumes 把 available 内外卷作为根，operations 以绝对路径调用 Storage。rename Keyboard 与 delete destructive Dialog 已接通；directory/file Operations 不是预览/播放器/包安装。容量异步 generation 与 stop 取消 timer 已有，不能因此把捕获 this 的全部 callback 判安全。

产品 `/littlefs` 同卷包含 Core packages/system、App data/cache/files 与用户公共分类目录；全卷内部祖先删除也可间接破坏 protected 后代。wrapper/final、资源隐藏和 GUI Screen Flow 都无法给出完整目录深度事实或执行授权。候选为官方 Files 聚焦 path-policy/commit 与 navigation snapshot/back seam；Storage 始终执行 IO，Core 管包，不新增文件 manager。

本轮不批准全卷授权、不自行扩大 ADR-0012。真实冲突决定为：保留完整操作但保护 Core/system/私有数据执行边界，并单独批准 Files 的真实导航 Owner 限定例外，还是明确重新打开既有边界。推荐前者。范围、精确依赖、navigation mapping、slow IO/取消终态、资源/设备验收见 [11](../issues/11-design-files-integration.md)。

## 12 非 GUI 显示源

锁定 ServiceManager 的 DataFlowRegistry.open_visual_operation 与 VisualOperation.get_sources/get_active_source/get_active_source_role/set_active_source_role/set_active_source_named 已存在；base named selection 有不支持其他 source 的 fallback，所以还要核实实际 Display provider override。DataFlowOperation.get_id/get_owner/is_available/close 提供 operation lifetime，provider removal/revoke 使 operation unavailable。

固定 Super [display routing](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_display_routing.cpp) 记录 output/source name，第一次抢 GUI 后不覆盖旧记录，恢复先查 source 是否还注册。产品还需 Running Instance/operation identity，防同名重建误恢复。当前 System 在启动时只 SetActiveSourceRole GUI，没有生产非 GUI App 场景；library dependency 不证明 NES/Video 接通。

方案为首个真实 producer/fixture 上的有限 continuation 与公开 dataflow seam，Home/wake/stop/revoke 和嵌套 Overlay 明确失效。硬件为单选 466×466 触摸 AMOLED output，不默认多输出/视频预算。[12](../issues/12-design-non-gui-display-sources.md) 持有真实 producer 与输出证明，纯 GUI 路径不算新增故障。

## 14 手机配网

锁定 HAL src/wifi/softap.cpp start_soft_ap_provision 断旧 STA、建 AP 与 HTTP/DNS；trigger_provision_connect 排队 SetTarget+Connect。stop 关闭服务器/AP，不撤回已经捕获 SSID/password 的 task。Wi-Fi Service 持有自动连接与凭据历史，Stop 恢复自动连接不保证原开关/target；历史保存异步且无公开保存提交事件。

Helper 有 TriggerSoftApProvisionStart/Stop、SoftApParams、General/SoftAp event；网页 POST accepted 与取得 IP 不同，IP 与互联网不同。固定 Super 和 Settings 无手机配网入口；Chatbot 示例二维码用于加入设备 AP。因此推荐主动 Quick Settings 入口、5分钟期限、不承诺 rollback 仍是产品提案，不能把未答 Q19 写成已接受。

[14](../issues/14-design-phone-wifi-provisioning.md) 将普通策略与强 rollback 所需 Wi-Fi/HAL generation/barrier/Storage terminal seam 分开，避免 Shell 复制凭据或建立 portal。首批停止/PWR 与真实网络/手机证据保持独立。

## 15 Expansion

这是本轮发现的具体版本缺口：固定参考 Device Helper 有 GetExpansionModuleInfos、ExpansionModuleChanged、ExpansionModuleInfos 与 HAL ModuleManagerIface；锁定产品 Device 0.8.2/Helper 0.8.4/HAL Interface 0.8.2 的源码没有这些声明/实现，不能直接编译复制来的 Super 订阅代码。

固定 Super [expansion](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_expansion.cpp) 先 capability 检查，再订阅后初始读，按 provider/slot 合并，每250ms drain，以系统 Dialog 提示 detected/removed/unsupported，3000ms 自动关闭，stop 断开、停 timer、hide 自有请求、release binding。先订阅后读仍需处理 snapshot/event 因果，不能让旧初始结果覆盖新插拔。

当前板 board_devices.yaml 及 custom device 无 ModuleManagerIface 声明，不能以依赖升级代替硬件支持。路径保持 unavailable，计划仍保留；[15](../issues/15-design-expansion-notifications.md) 持有精确接口组合、当前无伪事件回归和支持硬件后续验收。不新增通知中心。

## 真正待确认的产品规则

1. 状态：推荐已同步时间离线继续走时并标离线；Battery 读失败显示未知，不把最近 percentage 当当前。若允许标旧值需明确 age/失效门槛，时间有效性由真实时间 Owner 持有。
2. 环境刷新：推荐 partial 保留可用界面、明确未完全应用/未保存，整体成功才确认偏好保存；自动回滚需另一套真实事务保证。
3. Files：推荐完整卷/公共文件功能与 protected Core/system/App 私有数据边界并存，并单独批准官方 Files 导航 Owner 例外；这不授权全卷 raw 写，也不扩展 Settings 例外为任意 App 可选协议。
4. 配网：推荐主动 Quick Settings 发起、5分钟期限，Home/取消关闭 portal、息屏继续 deadline；已提交连接继续核实，不保证恢复原凭据/网络。若自动触发或强 rollback，必须明确选择与 seam 门槛。

以上为待确认建议，未写为 accepted；其他项沿用户完整 Super 对齐授权推进技术设计，不再询问是否迁移。新增公开扩展超出单纯 bug 修复的情况，实施前需明确其上游 seam/维护授权范围，不把 ADR-0016 自动当所有新接口的授权。

## 验证与交付边界

本线仅修改 Markdown，执行 `python3 scripts/docs/check.py --markdown`。检查通过（258 Markdown files）。首次检查因隔离时排除旧生成依赖导致旧链接目标缺失；仅复制旧文档引用的真实文件和 Board Manager 目录到独立副本后重跑，清单位于隔离根 docs-link-inputs.txt，复制品不进入 patch。结果与日志路径由隔离根 handoff 文件记录；未运行 firmware 全量 host checks 或完整固件构建，因为没有 firmware 改动，也未加入/升级依赖。后续每项实施票已经列出 host、完整构建与真实设备门槛，不能以本次 Markdown 通过代替。

原源码 checkout 的其他任务可继续推进。整合以 baseline→working patch 为准，先核对新改动，不能应用为 HEAD diff；共享 Spec/README 和首批/Store 关联文档只合并本线新增设计，不覆盖协调者最新内容。全部设计/设备未完成状态保持可追溯。
