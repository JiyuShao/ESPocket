# 06 — 设备能力映射

## 目的

定义显示、触控、电源、网络、时间、存储和 Runtime 能力从产品调用者到 Framework Interface、Adapter 与硬件的路径。

## 支撑的产品要求

- [OVR-002、OVR-005、OVR-006](../product/01-overview.md)
- [TRU-001–TRU-010](../product/05-runtime-package-trust.md)
- [AIN-004、AIN-005、AIN-008、AIN-012](../product/02-ai-native.md)

## 结构

![ESPocket 设备能力映射](assets/device-capabilities.svg)

| 产品能力 | 调用者 | Framework Interface | Adapter / Platform |
|---|---|---|---|
| 显示启动与背光 | `espocket::System` | Display Helper、`DisplaySource` | GUI LVGL、ESP LVGL Adapter |
| Watch Face 与 App GUI | CircularShell / App | GUI backend、`AppContext` GUI | LVGL、AMOLED |
| 触控与 Edge Back | CircularShell | Display gesture event | Touch driver |
| PWR 短按 | PowerKeyMonitor | GPIO input | Board wiring |
| Battery | CircularShell | Device Helper | Device Service、PMIC |
| Brightness | CircularShell / System | Display Helper | Display Service、backlight Adapter |
| Wi-Fi 与 Time | CircularShell / Settings | Wi-Fi / SNTP Helper | ESP-IDF network、NVS、system time |
| Runtime package | System Core | Package / Runtime Interface | LittleFS、Runtime JS |
| Store network | Official App Store | HTTP Service | ESP-IDF network、TLS |

## 架构不变量

| ID | Invariant |
|---|---|
| CAP-001 | 产品 Module 通过 Framework Interface 使用设备能力，不直接复制 Driver 或 HAL Implementation。 |
| CAP-002 | Display、Touch、System Core 与 Shell 属于启动关键路径；失败时不得伪装成可用系统。 |
| CAP-003 | Wi-Fi、Time 与 Battery 属于可降级能力；失败时保持 Home 并表达不可用状态。 |
| CAP-004 | Runtime package 必须先通过统一信任 Seam，再进入可安装和可启动状态。 |
| CAP-005 | Store、HTTP 或 package 路径的问题不得通过 Shell 私有旁路修补。 |
| CAP-006 | Board 差异只进入 Board Manager、HAL 或能力 Adapter，不扩散到 App。 |

## AI Native

| 能力 | Exposure Decision | Owner |
|---|---|---|
| Brightness | 开放读取、设置与变化语义；不暴露 Output ID 或背光 Driver | ESPocket System + Display Service Adapter |
| PWR | 开放 Home、Screen Off 与 Wake 产品语义；不暴露原始 GPIO 电平 | `espocket::System` |
| Wi-Fi、Battery、Time | 只开放用户可理解的状态与获准 Action | 对应 Brookesia Service Owner |
| Store 与 Runtime package | 只有通过信任和授权规则的安装语义可以开放 | System Core / Store |
| App 自有能力 | 由 App 声明稳定语义，并绑定单次 Running Instance | Native / Runtime App |

## Code Anchors

- [system.cpp](../../../firmware/components/espocket_system/src/system.cpp)
- [power_key_monitor.cpp](../../../firmware/components/espocket_system/src/power_key_monitor.cpp)
- [circular_shell.cpp](../../../firmware/components/shell_circular/src/circular_shell.cpp)
- [Board Manager generated interface](../../../firmware/components/gen_bmgr_codes)
- [idf_component.yml](../../../firmware/main/idf_component.yml)
- [Waveshare 1.75C schematic](https://files.waveshare.com/wiki/ESP32-S3-Touch-AMOLED-1.75C/ESP32-S3-Touch-AMOLED-1.75C-schematic.pdf)

## 非目标

- 记录能力的验收状态或上游阻塞。
- 在产品层重写 Framework Service、HAL 或 Driver。
- 把原始硬件 Interface 自动暴露给 Assistant。
