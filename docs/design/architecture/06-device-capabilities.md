# 设备能力映射

这张图回答：产品看到的显示、触控、电源、网络、时间和存储能力，最终由什么框架接口与硬件实现。

![ESPocket 设备能力映射](assets/device-capabilities.svg)

## 能力路径

| 产品能力 | 首要调用者 | 框架接口 | 平台落点 |
|---|---|---|---|
| 显示启动与背光开关 | espocket::System | Display Helper / DisplaySource | LVGL Adapter、面板驱动 |
| Watch Face 与 App GUI | CircularShell / App | GUI backend / AppContext GUI | LVGL、AMOLED |
| 触控与 Edge Back | CircularShell | Display 手势事件 | Touch driver |
| PWR 短按 | PowerKeyMonitor | Board Manager 设备句柄 | PWR 输入 |
| 电池状态 | CircularShell | Device Helper | Battery / PMIC |
| 亮度 | CircularShell | Display Helper | 背光实现 |
| Wi-Fi 状态与切换 | CircularShell / Settings | Wi-Fi Helper | ESP-IDF Wi-Fi、NVS |
| 时间同步 | CircularShell / Settings | SNTP Helper | 网络与系统时间 |
| Runtime App 文件 | System Core | Package / Runtime 接口 | LittleFS |
| App Store 网络 | Official App Store | HTTP Service | ESP-IDF 网络与 TLS |

## 降级与故障归属

- 显示输出、触控输出、System Core 或 Shell 无法启动时，产品启动失败。
- Wi-Fi、SNTP 和 Battery 不可用时，Shell 应显示降级状态，不阻塞 Home。
- App Store HTTP worker 的上游崩溃与动态包信任门属于框架或生态路径，不应绕过接口直接在 Shell 中修补。
- Audio 当前受上游 PlaybackIface 组合限制阻塞，因此不把未形成可用路径的音频能力画成既有产品能力。

## AI Native Exposure Decisions

| 能力 | Exposure Decision | Owner 边界 |
|---|---|---|
| 显示亮度 | 注册读取、设置与变化语义，作为首条能力 seam | ESPocket System + Display Service Adapter |
| PWR 物理输入 | 不把原始按键或 Board handle 暴露为 AI 能力 | PowerKeyMonitor / ESPocket System |
| Wi-Fi、Battery、Time | 延后；先保持现有产品状态路径并分别建立 ticket | 对应 Service Owner |
| Store 与远程 Runtime 包 | 信任门和在线稳定性通过前不暴露安装 Action | System Core / Store |
| App 自有能力 | 由每个 App 作 Exposure Decision，并绑定 Running Instance | Native / Runtime App |

表中的“注册”描述目标架构关系，不表示当前固件已实现。实施状态只由 Spec、ticket 和 Milestone 证据判定。

## 源码锚点

- firmware/components/espocket_system/src/system.cpp
- firmware/components/espocket_system/src/power_key_monitor.cpp
- firmware/components/shell_circular/src/circular_shell.cpp
- firmware/components/gen_bmgr_codes/
- firmware/main/idf_component.yml
