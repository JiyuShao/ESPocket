# AI Native 设计所用本地源码快照 — 2026-09-29

本页记录一次**本地、只读**的依赖锁与 API 核对，不是升级建议、持续同步状态或 Milestone 验收。未来实施前须重新核对届时的锁定源码。长期关系见[AI Native 架构](../design/architecture/07-ai-native.md)；当前结构见[架构总览](../design/architecture/README.md)。

## 版本锁

权威依赖文件是 [`firmware/dependencies.lock`](../../firmware/dependencies.lock)，本次 SHA-256：`8265e7a72808bec2455436bbcbc9429f3fa33b966e14e51552f231395332a212`。本地 ESP-IDF 源码为干净的 `v6.0.1`；[`firmware/main/idf_component.yml`](../../firmware/main/idf_component.yml) 允许 `>=6.0,<6.3`，manifest 本身没有精确固定补丁版本。目标为 `esp32s3`，Board Manager selector 为 `esp32_s3_touch_amoled_1_75c`。

| 组件 | 锁定版本 |
|---|---|
| Brookesia System Core／Runtime Manager／Runtime JS | 0.8.4／0.8.2／0.8.3 |
| Service Manager／Service Helper | 0.8.2／0.8.4 |
| GUI Interface／GUI LVGL | 0.8.2／0.8.5 |
| HAL Adaptor／HAL Boards／HAL Interface | 0.8.4／0.8.0／0.8.2 |
| Settings／Store／Audio Service | 0.8.3／0.8.2／0.8.2 |
| Device／Display／HTTP／SNTP／Wi-Fi Service | 均为 0.8.2 |
| Storage／USB Service | 0.8.3／0.8.0 |
| Board Manager／Waveshare 板级目录所在的 Brookesia HAL Boards／该目录的 `brookesia_hal_custom` | 0.5.15／0.8.0／0.1.0 |
| CO5300／CST9217／esp_codec_dev | 2.2.0／1.0.4／1.5.11 |
| QuickJS-NG／LVGL | 0.14.0／9.5.0 |

Agent Manager、XiaoZhi 和 ESP-Claw 未进入当前依赖锁。当前 Runtime 是 JS，不是参考文档示意的 Lua。`managed_components/` 是生成依赖，不能作为 ESPocket 产品改动位置。

当前 Waveshare 板级支持来自 `espressif/brookesia_hal_boards` 的 `boards/waveshare/esp32_s3_touch_amoled_1_75c/` 目录；本地 `brookesia_hal_custom` 锁定路径也指向该目录。`dependencies.lock` 没有单独的 Waveshare BSP 包及其独立版本号；触控驱动 `waveshare/esp_lcd_touch_cst9217` 另行锁定为 1.0.4。

## 源码核对

| 已核对事实 | 源码 | 不能据此推断 |
|---|---|---|
| `IApp` 有启动、暂停、恢复、停止回调；Core 有 Installed、Starting、Running、Paused、Stopping、Stopped、Error 状态 | [`iapp.hpp`](../../firmware/managed_components/espressif__brookesia_system_core/include/brookesia/system_core/app/iapp.hpp)、[`types.hpp`](../../firmware/managed_components/espressif__brookesia_system_core/include/brookesia/system_core/app/types.hpp) | Core 已有 AI 能力注册 API |
| ESPocket System 有 App 启停 hook 与前台 generation | [`system.cpp`](../../firmware/components/espocket_system/src/system.cpp) | 前台 generation 可直接作为通用能力令牌 |
| Runtime HostBridge 检查 Service manifest，并在释放 App 资源时清理 binding、订阅与异步调用；仅 System Core、GUI、Timer 三项有既存隐式准入 | [`host_bridge.cpp`](../../firmware/managed_components/espressif__brookesia_system_core/src/runtime/host_bridge.cpp) | Assistant 可以替 Runtime App 绕过声明或 Owner 检查 |
| Display Helper 有亮度读写 Function 和亮度变化 Event | [`display.hpp`](../../firmware/managed_components/espressif__brookesia_service_helper/include/brookesia/service_helper/media/display.hpp) | 亮度示例就是通用 AI API |
| Display Service 的亮度写入按输出 ID 查找；同值写入成功但不发变化 Event；实际变化后尝试发布 Event，调用方仍须按需读回 | [`display_backlight.cpp`](../../firmware/managed_components/espressif__brookesia_service_display/src/display_backlight.cpp) | 一次写入成功必定伴随 Event，或读回值可证明肉眼效果 |
| Service Manager 提供 RAII `ServiceBinding`，`ServiceBase` 有 Function／Event 注册接口 | [`manager.hpp`](../../firmware/managed_components/espressif__brookesia_service_manager/include/brookesia/service_manager/service/manager.hpp)、[`base.hpp`](../../firmware/managed_components/espressif__brookesia_service_manager/include/brookesia/service_manager/service/base.hpp) | ESPocket 的 Assistant Service 已有可直接照抄的注册、线程和生命周期方案 |
| Service Helper 的异步 Function 调用只返回提交成功与否，没有单次调用取消句柄；同步等待超时不取消已提交的工作 | [`base.hpp`](../../firmware/managed_components/espressif__brookesia_service_manager/include/brookesia/service_manager/helper/base.hpp)、[`base.cpp`](../../firmware/managed_components/espressif__brookesia_service_manager/src/service/base.cpp) | 用户取消或调用方超时后，Owner 一定未产生副作用 |
| Service Helper 内有 XiaoZhi 工具接入的 schema 头文件，但 Agent Manager／XiaoZhi 未进入本项目锁定依赖 | [`xiaozhi.hpp`](../../firmware/managed_components/espressif__brookesia_service_helper/include/brookesia/service_helper/agent/xiaozhi.hpp)、[`dependencies.lock`](../../firmware/dependencies.lock) | 可直接把 Display 原始 Service Function 暴露给 AI，或据此断言 Provider 已可构建 |

**亮度示例的已知源码缺口**：当前 Shell 的亮度读取和加亮都向 Display Service 传 `OutputId = 0`（[`circular_shell.cpp`](../../firmware/components/shell_circular/src/circular_shell.cpp)）；锁定版 Display Service 从 `1` 分配输出 ID，亮度读写按该 ID 精确查找（[`display_lifecycle.cpp`](../../firmware/managed_components/espressif__brookesia_service_display/src/display_lifecycle.cpp)、[`display_backlight.cpp`](../../firmware/managed_components/espressif__brookesia_service_display/src/display_backlight.cpp)）。`System::start_display()` 已通过 `GetOutputs` 保存真实 ID。按当前源码，Shell 的亮度按钮会遇到 `0` 不可用；这是真机待确认的静态发现，不能用 M4 Settings App 的亮度验收替代 M7 Shell 路径验证。后续若选亮度作 AI Native 校验场景，必须从真实输出 ID 读写，并区分亮度目标值与屏幕点亮状态。

动态包信任仍受[产品契约](../design/product/runtime-package-trust.md)和[M5 验收](../milestones/m5/acceptance.md)约束；这份源码快照不能证明第三方 Runtime App 已经 AI-ready。本次文档核对未执行新的固件 Build、测试或真机验证，也没有修改依赖。
