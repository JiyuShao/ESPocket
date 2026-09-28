# M1 验收报告

## 状态

- Implementation: `READY`
- M1: `PASS`（2026-09-25）
- M0: `WAIVED`（2026-09-25，非 PASS）
- System Core startup blocker: `RESOLVED`（2026-09-25；成功串口日志未保存在仓库中）

## Environment

| 项目 | 值 | 状态 |
|---|---|---|
| ESP-IDF | 6.0.1（完整目标构建已通过） | PASS |
| ESP-Brookesia reference | `e937455b0db1a3e873b1da61d6d13652f3dcc7e2`（2026-09-22） | PASS |
| Brookesia resolved components | v0.8 Registry 组件；详见 `firmware/dependencies.lock` | PASS |
| Board selector | `esp32_s3_touch_amoled_1_75c` | PASS |
| Chip target | ESP32-S3 | PASS |
| Connected chip identity | `/dev/cu.usbmodem2101`：ESP32-S3 QFN56 revision v0.2，8 MB embedded PSRAM | PASS |
| `board_info.yaml` metadata version | 1.0.0 | PASS |
| `dependencies.lock` SHA-256 | `70f96fd3492ed64a1b125dc6c2c898e050304bcf5a507f9686e8f5b5b1ad5d78` | PASS |

说明：当前 Brookesia master/v0.8 官方兼容矩阵对 ESP32-S3 等非 S31 目标声明 ESP-IDF `>=6.0, <=6.2`。System Super 的官方 CI/README 未列出该 Waveshare 板，因此不能把目标组合描述为已由官方验证。

## Build

| 项目 | 结果 | 状态 |
|---|---|---|
| Dependency resolution | ESP-IDF 6.0.1；37 项目标板依赖已解析并锁定 | PASS |
| Board config generation | Board Manager 已解析 `esp32_s3_touch_amoled_1_75c` 并生成 ESP32-S3 配置 | PASS |
| `idf.py build` | ESP32-S3 编译、链接、镜像生成与分区尺寸检查完成 | PASS |
| Clean reproduction | 2026-09-25 在无 `build/`、`managed_components/`、`sdkconfig`、`gen_bmgr_codes/` 的隔离副本中重新解析 37 项依赖、生成板配置并完整构建通过；当时的启动顺序修复基线尺寸为 `0x4970f0` | PASS |
| Firmware / partition size | release `espocket.bin` = `0x497080`；factory = `0xa41000`；余 `0x5a9f80`（55%） | PASS |
| IRAM / DIRAM / Flash | IRAM `16384 / 16384`；DIRAM `163125 / 341760`；Flash Code `3225514`；Flash Data `1431876` bytes | PASS |
| Total image size | `4812815` bytes（`.bin` 含 padding 后为 `4812928` bytes） | PASS |
| Boot free internal heap | `99507` bytes（2026-09-25 最终 UI 镜像软件复位后） | PASS |
| Boot free PSRAM | `4530332` bytes（同次启动） | PASS |
| Largest internal block | `31744` bytes（同次启动） | PASS |
| Largest PSRAM block | `4456448` bytes（同次启动） | PASS |

### 可复现命令

从仓库根目录执行：

```bash
export ESP_IDF_VERSION=6.0.1
export IDF_PATH="$HOME/.espressif/v6.0.1/esp-idf"
source "$IDF_PATH/export.sh"
idf.py -C firmware set-target esp32s3
idf.py -C firmware reconfigure
BOARD_PATH="$PWD/firmware/managed_components/espressif__brookesia_hal_boards/boards/waveshare/esp32_s3_touch_amoled_1_75c"
idf.py -C firmware gen-bmgr-config -b "$BOARD_PATH"
idf.py -C firmware build
idf.py -C firmware size
idf.py -C firmware size-components
```

## Hardware Smoke

物理观察不得仅凭串口日志判定 PASS。

| 检查项 | 结果 | 状态 |
|---|---|---|
| Boot reaches Launcher | 用户于 2026-09-25 真机确认设备进入 Launcher | PASS |
| Display layout | 用户于 2026-09-25 确认最终 UI 镜像显示正常；顶部状态条无圆边裁切，状态文字无重叠 | PASS |
| Touch opens TestPage | 用户于 2026-09-25 真机确认 | PASS |
| Bottom swipe returns Launcher | 用户于 2026-09-25 真机确认 | PASS |
| Home gesture on Launcher is no-op | 用户于 2026-09-25 真机确认 | PASS |
| Clock shows real time or `--:--` | 用户于 2026-09-25 确认最终 UI 显示正常 | PASS |
| Wi-Fi shows connected / not connected / unknown | 用户于 2026-09-25 确认最终 UI 显示正常；紧凑状态文案不与相邻项重叠 | PASS |
| Battery shows percentage or unknown | 用户于 2026-09-25 确认最终 UI 显示正常；紧凑状态文案不与相邻项重叠 | PASS |
| Fatal failure remains diagnosable on serial | 首次启动因 LittleFS mount `-84` 缺失 Storage，随后 Display bind 失败；串口完整记录并停止启动，无自动重启 | PASS |

### 真机启动记录

- 最终 UI 镜像于 2026-09-25 烧录至 `/dev/cu.usbmodem2101`；bootloader、分区表和应用镜像均通过 esptool 写入哈希校验，未擦除整片 Flash，未写入 NVS 或 `littlefs_data`：`PASS`。
- 烧录后两次软件复位均观察到 `ESPocket started`；第二次完整记录还包含 Display `466x466`、Circular Shell 启动，以及 heap `99507/31744`、PSRAM `4530332/4456448`（free/largest）：`PASS`。
- 首次启动：`FAIL`。`littlefs_data` 返回 LittleFS mount `-84`；Storage service 未注册，Display 的 Storage 依赖绑定失败；System 按设计停止且保留串口诊断。
- Storage 修复：`PASS`。启用仅针对 `littlefs_data` 的 mount-failure format 后，LittleFS 成功挂载（总容量 5,120,000 bytes，启动时已用 8,192 bytes），Storage FileSystem/KeyValue 与 Display 服务成功启动；NVS 和其他分区未擦除。
- 历史阻塞：Storage 修复后曾在 `SysCore: ... Version: 0.8.4` 后至少 60 秒无后续输出；无 panic、watchdog reset 或自动重启。
- 启动阻塞修复：将背光开启改为在 LVGL worker 启动前同步完成，避免背光 Display 命令与首帧提交形成 Display/LVGL 反向取锁窗口。用户于 2026-09-25 确认问题已解决；本仓库未保存对应成功串口日志，因此这里只关闭该 blocker。
- 用户于 2026-09-25 真机确认 Launcher、触摸进入 TestPage、底部上滑返回 Launcher，以及 Launcher 上 Home 手势 no-op 均正常。
- 同次真机检查发现旧镜像顶部状态条在圆屏边缘被裁切，且 `Wi-Fi: not connected` 与 Clock/Battery 重叠。修复将状态条收进 466×466 圆形安全弦，Clock 独占上行，Wi-Fi/Battery 使用固定且互不相交的下行槽位与紧凑文案；release 镜像（SHA-256 `d0ee1df184dbfba4a9377768827bd52962d9d46cdb60d4d511ef38bce64bd17e`）已烧录并成功启动，用户于 2026-09-25 确认最终 UI 正常。
- 诊断过程曾构建临时 DEBUG/TRACE 镜像，并尝试 JTAG；OpenOCD 因芯片内存保护自动软复位且未取得有效回溯。单次 PC 采样未被作为根因证据。

## Stability

每次记录 `PASS/FAIL + 异常日志摘要`。

### Cold boots

| # | 结果 | 日志摘要 |
|---:|---|---|
| 1–2 | PASS | 真正断电后重新上电，分别在 3.9 秒和 3.7 秒到达 `ESPocket started` |
| 3–5 | PASS | 真正断电后重新上电，分别在 4.2、4.0、4.4 秒到达 `ESPocket started`；中途断电或空串口尝试均未计入结果 |

### EN / software resets

| # | 结果 | 日志摘要 |
|---:|---|---|
| 1–2 | PASS | 烧录后经 esptool 硬复位，均到达 `ESPocket started`；第 2 次记录 heap/PSRAM 指标 |
| 3–10 | PASS | 每次约 4.6–4.7 秒到达 `ESPocket started`；未检测到 panic、watchdog、assert 或 heap corruption |

## Result

`PASS`（2026-09-25）

构建、真机 Smoke、5 次冷启动和 10 次 EN/软件复位均已通过。M0 仍为 `WAIVED`，不是 `PASS`。未经明确批准不创建 `v0.1-system`、不进入 M2。

## Known Issues

- 本机 ESP-IDF 激活环境曾检测到新旧 Python venv 路径不一致；构建时必须记录实际解释器并确认依赖检查结果。
- Registry 的宽泛 `0.8.*` 约束会把 System Core 0.8.4 与 2026-09-18 发布的 USB 0.8.1 / Helper 0.8.5 组合起来，但当前 Registry 最新 HAL Interface 0.8.2 缺少 Helper 0.8.5 引用的 Expansion 头文件。根 manifest 因此固定 USB 0.8.0 与 Helper 0.8.4；不得在未重新构建验证时移除该兼容性锁。
- `brookesia_hal_boards` 0.8.0 内嵌的 Waveshare `brookesia_hal_custom` 0.1.0 仍引用已移除的 `DisplayBacklightIface`。项目通过仅注入该组件编译目标的 `firmware/compat/brookesia_hal_custom_0_1_backlight.hpp` 提供兼容基类，并保留 `group_id = DisplayDevice::LCD_GROUP_ID`；未修改 `managed_components/`。升级到包含官方修复的板包后应删除此兼容头和 CMake 注入。
- Board Manager 0.5.15 会把板 manifest 中的 `${BOARD_PATH}` 强制展开为绝对路径，因此同一源码在不同检出目录生成的 `dependencies.lock` 仅 `manifest_hash` 不同；隔离复演已确认所有解析依赖、版本、组件哈希、目标和最终镜像尺寸一致。仓库记录的 lock SHA-256 仍以本工作树版本为准。
- 官方 System Super 未声明或 CI 验证 Waveshare 1.75C 组合；M1 需要承担首次集成风险。
- 已解决的 System Core 启动阻塞源于启动期背光命令与 LVGL worker 并发；项目将背光开启移到 LVGL worker 启动前并改为同步调用。若未来恢复异步顺序，必须重新验证 Display/LVGL 锁顺序。
- 上游 `brookesia_lib_utils` 0.8.2 的 `ThreadConfig::apply()` 未完整初始化 `esp_pthread_cfg_t::inherit_cfg`。这是独立的已证实未定义行为，但没有证据表明它造成过本项目的启动阻塞；不在 ESPocket 中 patch `managed_components/`，待上游发布修复后再处理。

## M2 Recommendation

M1 已完成。下一阶段可按独立授权进入 M2 Native App Validation；在获得明确批准前不创建 `app_hello`、不进入 M2。
