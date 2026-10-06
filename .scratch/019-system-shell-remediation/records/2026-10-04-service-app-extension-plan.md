# Files、手机配网与开发诊断计划访谈 — 2026-10-04

本记录保存 grill-with-docs 访谈和有日期的事实；当前范围、依赖与完成状态由 [Spec](../spec.md)及 [07 诊断](../issues/07-design-development-diagnostics.md)、[11 Files](../issues/11-design-files-integration.md)、[14 配网](../issues/14-design-phone-wifi-provisioning.md)持有。本轮只调查与更新文档，不实施固件、不构建或操作设备。

## 已确定的工作归属

- 用户明确要求 Agent Manager / XiaoZhi 单列，沿 [009/08](../../009-ai-native-foundation/issues/08-connect-a-voice-provider.md)独立设计；本轮不讨论其 Provider/模型/语音产品细节。
- 本轮「其它」指前一轮列出的 Files App、手机配网入口与开发诊断入口；HTTP/Store/Wi-Fi 基础能力已存在，不新增重复迁移票。
- 既有生命周期、Overlay、PWR、真实 Owner 和开发者模式约束继续有效；变更既有约束时须显式提出。

## 先前设计树

| 分支 | 本轮先确认 | 后续依赖决定 |
|---|---|---|
| Files | 首版读写能力、用户可见目录边界 | 文件导入/打开方式、目录和 Page Back、写操作确认/取消、公开 seam 和版本兼容 |
| 手机配网 | 何时进入配网 | 手机协议/引导、成功取消超时、原网络与凭据、Home/息屏/退出、Owner lifetime |
| 开发诊断 | 首版设备页与电脑入口范围 | 字段、采集频率、输出/保留、断开/关闭开发模式、USB 查询方式与性能验收 |

实施顺序由真实依赖确定，不把功能选择和技术 API 事实混为同一问题。三个只读探索分别核查 Files 的存储/导航适配、锁定 SoftAP 的手机机制和恢复行为、已有 Utils/Settings/USB 诊断边界。未返回的事实作为未解决前置，不能把建议写成已实现能力。

## 先前提问 Q17–Q20

- Q17：Files 首版只读浏览名称/大小/容量，还是包含重命名与删除；文本预览并非官方既有用户功能。
- Q18：Files 使用 Core 已有公共分类目录，还是覆盖挂载卷。
- Q19：手机配网仅用户主动发起并保留现有断网重连，还是自动接管首次无网络/断网。
- Q20：诊断首版以电脑只读查询为主，还是同时新增设备独立诊断页。

以上问题未收到逐项答复，不记录为已接受产品行为。用户随后提出默认迁移 Super 全部已实现功能，当前处理方式见下文；不继续使用这组缩减式选择作为迁移前置。

## 本轮只读核查结果

### Files

- 固定上游 Files 0.8.2 从完整 StorageLayout 取得所有 available 卷，直接调用 StorageHelper 的绝对路径 list/rename/remove，没有 apps/system 过滤。项目 `/littlefs` 同时包含公共目录与 App package、cache/data/files、system。锚点：[上游 lifecycle](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/app/brookesia_app_files/src/app/lifecycle.ipp)、[volumes](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/app/brookesia_app_files/src/storage/volumes.ipp)、[项目 Core storage](../../../firmware/managed_components/espressif__brookesia_system_core/src/system/storage.cpp)。
- FileManagerApp 为 final，公开接口没有 root allowlist、read-only 或目录深度/Page 快照配置。普通 IApp wrapper 不足以保证范围；只隐藏按钮也不构成执行约束。Files 目录 Back 的事实在私有成员，不能自动扩大 ADR-0012 的 Settings 例外。锚点：[Files header](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/app/brookesia_app_files/include/brookesia/app_files/files_app.hpp)。
- 官方用户界面目前浏览名称/大小及操作，非目录文件点击进入 Operations，没有内容预览/播放/BPK 安装入口。辅助文本读取不是用户预览功能，修正此前补充核查的概括。圆屏布局、版本兼容和设备行为仍未验证。
- Core 已有 Music/Download/Movies/Pictures/Documents 和 caller-relative AppData/AppFiles 等公开路径类型，接入方式需要尊重这些真实 Owner 关系。

### 手机配网

- 锁定 HAL 已有 HTTP captive portal 页面、HTTP/DNS server 和 scan/connect/status endpoints；可以使用现有 TriggerSoftApProvisionStart/Stop。无需产品新建配网 Web server。锚点：[HAL softap](../../../firmware/managed_components/espressif__brookesia_hal_adaptor/src/wifi/softap.cpp)、[Wi-Fi helper](../../../firmware/managed_components/espressif__brookesia_service_helper/include/brookesia/service_helper/network/wifi.hpp)。
- Start 先断开原 STA、停止自动连接，再用 APSTA 测试新网络。Stop 关闭 portal/AP 并恢复 STA 自动连接，不回滚 target，也不保证回到原网络/开关状态。关配网页面不等于撤回已经投递的连接任务。
- 取得 IP 才是连接 success；POST success 只说明提交成功，均不证明互联网/云可用或持久保存已完成。历史凭据保存为异步 Storage，当前没有公开保存提交事件。锚点：[Wi-Fi service](../../../firmware/managed_components/espressif__brookesia_service_wifi/src/service_wifi.cpp)。
- Settings 没有公开配网页面扩展 hook；入口归属待设计。Chatbot 的二维码用于手机加入设备 AP，不是提交家中 Wi-Fi 凭据；其断网即转配网是示例产品策略。

### 开发诊断

- 已有 Settings Debug 控件和 built-in Utils；GetMemorySnapshot 可按需读取。GetDebugSnapshot 为缓存，可能为空或过期；编译开关关闭时不能因为 capability 标签存在就宣称 ThreadProfiler 可用。
- SettingsApp final，无公开菜单扩展点；已有 Adapter 只持有生命周期装饰与导航观察。新增设备页必须评估真实入口 seam，不默认直接往官方页面插菜单。
- ServiceManager 持有 Utils binding，Settings stop 不自动停止全局 Memory/Thread profiling；关闭 Developer Mode 当前也不会停止这些采集。持续采集需明确是观察已有采集还是拥有新会话，不能停止其他 Owner 开启的工作。
- Console 独立 REPL reader 与当前 USB 输入单 Owner 存在竞争，事件参数/命令历史可能包含私有内容。按需有限快照可沿现有只读语义设计，协议与字段仍需用户确认。锚点：[Utils](../../../firmware/managed_components/espressif__brookesia_service_manager/src/service/utils_service.cpp)、[Settings lifecycle](../../../firmware/managed_components/espressif__brookesia_app_settings/src/app/lifecycle.ipp)、[开发者模式契约](../../../docs/design/product/07-developer-mode-testing.md)。

## 用户最新方向与计划调整

用户提出「这个不能 super 实现了啥全部搬过来吗」。本轮将其作为计划方向调整：以固定 Super 实际接通的完整功能为默认基线，已有等价能力保留，缺项纳入迁移范围；只整理圆屏、既有产品契约、锁定接口/资源和真实硬件的兼容差异。分批交付不等于削减最终功能目标。

- Q17 不再等待读写取舍，撤回只读首版建议；Files 浏览、容量/信息、重命名、删除与确认流程均进入目标。
- Q18 不记成全卷无条件授权。官方全卷 raw filesystem 与既有 App/package/system Owner 的冲突由兼容设计明确处理，涉及已接受契约改变时再提出具体决定。
- Q20 撤回电脑优先替代设备调试的建议；直接保留 Super 的 Settings → Utils → Shell overlay 完整链路，USB 导出作为另一个可选增量。
- Q19 移到独立手机配网设计：固定 Super 没有这个入口，不能从「全部搬 Super」推断触发/取消/恢复行为已经决定。此前手动触发建议未获逐项接受。
- Agent Manager / XiaoZhi 保持 009/08 单列。迁移方式、兼容设计和验收仍待完成；本轮不修改 firmware。

## Super 实际接通功能基线

固定官方提交：`e937455b0db1a3e873b1da61d6d13652f3dcc7e2`。以下为源码核查结果；默认/条件启用不代表 ESPocket 已实现、锁定版可编译或真机已通过。

| 实际能力 | 接通条件与主要源码 | 计划归属 |
|---|---|---|
| Core/System 生命周期、App 安装启动停止、Shell 恢复 | 默认；[lifecycle](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/system_lifecycle.cpp)、[navigation](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/system_navigation.cpp) | 019/01–02、既有 Core 工作 |
| 动态 Launcher、图标/资源回退 | 默认；[Launcher](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_app_launcher.cpp)、[resources](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_app_resources.cpp) | 005/04、019/08 |
| Startup overlay、Shell launch overlay/动画、App Loading | Startup/launch 配置与 Loading 请求；[system](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/system.cpp)、[launch](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_launch.cpp) | 019/03–04、08 |
| Keyboard / MessageDialog / 系统提示 | 请求时启用；[keyboard](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_keyboard.cpp)、[dialog](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_message_dialog.cpp) | 019/03 |
| Wi-Fi、时钟/时区、状态栏展开/peek、手势和 indicator | Service/Display 可用时；[status](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_status.cpp)、[display](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_display.cpp) | 019/03、06 |
| Light/Dark、语言/字体预载与回退、运行时刷新 | 字体资源与支持语言条件；[lifecycle](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/system_lifecycle.cpp)、[font fallback](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/private/font_language.hpp) | 019/05、09–10 |
| Settings / Store / Files | example 引入 provider，Core 默认 install_registered_apps=true；[example manifest](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/system/super/main/idf_component.yml)、[Core config](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_core/include/brookesia/system_core/system/system.hpp) | 已有 004/005、019/11 |
| Settings → Utils Memory/Thread Debug → Shell overlay | Settings 打开相应功能，真实 Profiler 支持；[Super subscriptions](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/system_lifecycle.cpp#L274)、[overlay](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_debug.cpp) | 019/07、13 |
| 非 GUI source 抢占/恢复、Overlay 临时取回 GUI | 存在真实非 GUI source；[routing](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_display_routing.cpp) | 019/12 |
| Expansion 状态/插拔提示 | Device 具有 ModuleManagerIface；[expansion](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_expansion.cpp) | 新增 019/15 |
| 资源 staging、构建工具与硬件配置 | 构建/目标硬件条件；沿已有源码审计与构建工具核查，不视为 App 产品入口 | 019/08、13 |

具体修正：

- Core launch transition 在 Super init 中关闭，但 Super 自有 Shell launch overlay 已接通；不能因此遗漏启动动画。
- Files 不只是 manifest 依赖：其 provider 注册后由 Core 默认安装。本项目 install_registered_apps=false，迁移需要显式装配与资源 staging。
- Super 调试链路不仅有 Utils API：持有 binding、订阅 DebugState/Memory/Thread 事件、首次同步并绘制浮层；停止时断开订阅。ESPocket 还需处理共享 Profiler 的采集生命周期与真实线程构建支持。
- Expansion 在能力可用时先订阅再读初始模块状态、250 ms drain，按 provider/slot 合并系统 Dialog，默认 3 秒关闭；当前产品尚无该订阅路径。迁移必须服从已接受的系统提示与息屏期限规则。
- `open_notifications()` 实际打开 Launcher；`open_quick_control()`、`open_system_monitor()` 返回停用错误。头文件名称不能证明存在完整通知中心或监控页面。
- Super 与 Settings 没有 SoftAP 产品入口；Coze/XiaoZhi/NES 的 manifest 依赖不等于已接通聊天/游戏，独立 Console example 也不等于 Super Debug。

本轮核查及完整迁移清单已写入 Spec；功能对齐方向确定了规划基线，尚未把技术兼容和未完成验收标记为已解决。
