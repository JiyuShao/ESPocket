# M1 验收报告

## 状态

- Implementation: `READY`
- M1: `IN VERIFICATION`
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
| Clean reproduction | 2026-09-25 在无 `build/`、`managed_components/`、`sdkconfig`、`gen_bmgr_codes/` 的隔离副本中重新解析 37 项依赖、生成板配置并完整构建通过；修复后 release 尺寸同为 `0x4970f0` | PASS |
| Firmware / partition size | release `espocket.bin` = `0x4970f0`；factory = `0xa41000`；余 `0x5a9f10`（55%） | PASS |
| IRAM / DIRAM / Flash | IRAM `16384 / 16384`；DIRAM `163125 / 341760`；Flash Code `3225514`；Flash Data `1431988` bytes | PASS |
| Total image size | `4812927` bytes（`.bin` 含 padding 后为 `4813040` bytes） | PASS |
| Boot free internal heap | 待真机启动日志记录 | NOT TESTED |
| Boot free PSRAM | 待真机启动日志记录 | NOT TESTED |
| Largest internal block | 待真机启动日志记录 | NOT TESTED |
| Largest PSRAM block | 待真机启动日志记录 | NOT TESTED |

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
| Boot reaches Launcher | System Core 启动阻塞已解决；Launcher 是否正确显示仍待人工确认 | NOT TESTED |
| Display layout | 待人工确认 | NOT TESTED |
| Touch opens TestPage | 待人工确认 | NOT TESTED |
| Bottom swipe returns Launcher | 待人工确认 | NOT TESTED |
| Home gesture on Launcher is no-op | 待人工确认 | NOT TESTED |
| Clock shows real time or `--:--` | 待人工确认 | NOT TESTED |
| Wi-Fi shows connected / not connected / unknown | 待人工确认 | NOT TESTED |
| Battery shows percentage or unknown | 待人工确认 | NOT TESTED |
| Fatal failure remains diagnosable on serial | 首次启动因 LittleFS mount `-84` 缺失 Storage，随后 Display bind 失败；串口完整记录并停止启动，无自动重启 | PASS |

### 真机启动记录

- 烧录与写入哈希校验：`PASS`。
- 首次启动：`FAIL`。`littlefs_data` 返回 LittleFS mount `-84`；Storage service 未注册，Display 的 Storage 依赖绑定失败；System 按设计停止且保留串口诊断。
- Storage 修复：`PASS`。启用仅针对 `littlefs_data` 的 mount-failure format 后，LittleFS 成功挂载（总容量 5,120,000 bytes，启动时已用 8,192 bytes），Storage FileSystem/KeyValue 与 Display 服务成功启动；NVS 和其他分区未擦除。
- 历史阻塞：Storage 修复后曾在 `SysCore: ... Version: 0.8.4` 后至少 60 秒无后续输出；无 panic、watchdog reset 或自动重启。
- 启动阻塞修复：将背光开启改为在 LVGL worker 启动前同步完成，避免背光 Display 命令与首帧提交形成 Display/LVGL 反向取锁窗口。用户于 2026-09-25 确认问题已解决；本仓库未保存对应成功串口日志，因此这里只关闭该 blocker，不据此判定 Launcher、显示、触摸或手势 PASS。
- 诊断过程曾构建临时 DEBUG/TRACE 镜像，并尝试 JTAG；OpenOCD 因芯片内存保护自动软复位且未取得有效回溯。单次 PC 采样未被作为根因证据。

## Stability

每次记录 `PASS/FAIL + 异常日志摘要`。

### Cold boots

| # | 结果 | 日志摘要 |
|---:|---|---|
| 1–10 | 待执行 | |

### EN / software resets

| # | 结果 | 日志摘要 |
|---:|---|---|
| 1–10 | 待执行 | |

## Result

`IN VERIFICATION`

M1 只有在构建、真机 Smoke 和 20 次启动全部通过后才能标记 `PASS`。此前不创建 `v0.1-system`，不进入 M2。

## Known Issues

- 本机 ESP-IDF 激活环境曾检测到新旧 Python venv 路径不一致；构建时必须记录实际解释器并确认依赖检查结果。
- Registry 的宽泛 `0.8.*` 约束会把 System Core 0.8.4 与 2026-09-18 发布的 USB 0.8.1 / Helper 0.8.5 组合起来，但当前 Registry 最新 HAL Interface 0.8.2 缺少 Helper 0.8.5 引用的 Expansion 头文件。根 manifest 因此固定 USB 0.8.0 与 Helper 0.8.4；不得在未重新构建验证时移除该兼容性锁。
- `brookesia_hal_boards` 0.8.0 内嵌的 Waveshare `brookesia_hal_custom` 0.1.0 仍引用已移除的 `DisplayBacklightIface`。项目通过仅注入该组件编译目标的 `firmware/compat/brookesia_hal_custom_0_1_backlight.hpp` 提供兼容基类，并保留 `group_id = DisplayDevice::LCD_GROUP_ID`；未修改 `managed_components/`。升级到包含官方修复的板包后应删除此兼容头和 CMake 注入。
- Board Manager 0.5.15 会把板 manifest 中的 `${BOARD_PATH}` 强制展开为绝对路径，因此同一源码在不同检出目录生成的 `dependencies.lock` 仅 `manifest_hash` 不同；隔离复演已确认所有解析依赖、版本、组件哈希、目标和最终镜像尺寸一致。仓库记录的 lock SHA-256 仍以本工作树版本为准。
- 官方 System Super 未声明或 CI 验证 Waveshare 1.75C 组合；M1 需要承担首次集成风险。
- 已解决的 System Core 启动阻塞源于启动期背光命令与 LVGL worker 并发；项目将背光开启移到 LVGL worker 启动前并改为同步调用。若未来恢复异步顺序，必须重新验证 Display/LVGL 锁顺序。
- 上游 `brookesia_lib_utils` 0.8.2 的 `ThreadConfig::apply()` 未完整初始化 `esp_pthread_cfg_t::inherit_cfg`。这是独立的已证实未定义行为，但没有证据表明它造成过本项目的启动阻塞；不在 ESPocket 中 patch `managed_components/`，待上游发布修复后再处理。

## M2 Recommendation

待 M1 完成后填写；未经明确批准不得开始 M2。
