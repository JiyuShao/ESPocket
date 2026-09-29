# ESPocket

**ESPocket is a lightweight application platform for ESP-powered smart devices, built on ESP-Brookesia.**

**ESPocket 是一个基于 ESP-Brookesia、面向 ESP 系列轻量智能设备的应用平台。**

ESPocket 负责产品平台层；ESP-Brookesia 提供基础应用框架。V0.x 只面向 Waveshare ESP32-S3-Touch-AMOLED-1.75C 开发和优化，但 ESPocket 不等同于 Circular Shell 或该硬件。

## 当前阶段

当前已完成 M1–M3；M4、M5 仍受阻。**M6 — Home & Display State** 已完成主机侧实现，等待真机验收；M7、M8 的源码已提前开发，但按阶段依赖尚未进入验收。以下为当前固件装配入口：

```text
app_main
   └── espocket::System
       ├── HelloApp                 # visible Native App
       ├── Hello Runtime            # staged JavaScript package
       ├── Settings                 # official Native App
       ├── App Store                # official Native App
       └── CircularShell            # hidden Native IApp
           ├── fixed product Launcher entries
           └── ShellOverlay → Home Gesture → stop active app → Launcher
```

M1 已于 2026-09-25 通过并保存在 `v0.1-system`。M2 已于 2026-09-26 通过：normal/stress 完整镜像、真机 50-cycle lifecycle/heap gate，以及 Launcher → Hello → Increment → Home → Launcher 物理交互均已验证。M3 已完成 Runtime JS 0.8.3 / QuickJS-NG 0.14.0、unpacked staging、Toolkit 1.0.1 debug `.bpk`、clean-image Runtime 生命周期、Home 与 Native/Runtime 双向交替；仅 Core `.bpk` file-install 路径仍未验证。M4 的 clean Settings 圆屏 smoke、Wi-Fi 页面、亮度、时间、设备信息与 Home 已通过；系统键盘与 Wi-Fi 10/10 候选已于 2026-09-27 app-only 写入并通过 90 秒启动验证，Wi-Fi 初始化、保留 NVS 下的联网与 SNTP 同步均有脱敏真机证据，键盘 provider 已有一次真机 open/close，但掩码、模式、输入、确认/取消与清理语义尚未逐项确认，Storage/Battery/Developer 仍未测，Audio playback-only 仍受上游边界阻塞。M5 的 clean offline Store 启动/Home 已通过；先前在线真机成功拉取并缓存远程索引与部分 HTTPS 元数据，但后续并发请求/取消阶段发生一次 `LoadProhibited`、两次 `StoreProhibited` 与三次自动重启。`-0x008D` 已确认为内部 RAM TLS 分配失败；HTTP worker/并发限制为 1/1 的 containment 镜像已 app-only 写入并通过 written-data hash、单 ROM banner 90 秒启动验证以及缓存态 Store/Home 生命周期。随后显式 Refresh 真机验证成功提交远程索引/图标请求并多次写入 index cache，且未再出现 `-0x008D`；但一次 index 连接超时并进入重试后，Store refresh timeout 紧接触发 `LoadProhibited`（`EXCVADDR=0x8`）与自动重启。符号化崩溃栈位于 HTTP worker 的 `mbedtls_ssl_handshake_step()` → `esp_http_client_open()`，因此 1/1 只缓解了已观测的 TLS 分配压力，未解决在线稳定性。package trust、Runtime 键盘事件 owner isolation、catalog compatibility、Launcher sync 与兼容发布路径也继续阻塞。M0 仍为 `WAIVED`，不是 `PASS`；M6 未进入。

文档总入口见 [`docs/README.md`](docs/README.md)，长期边界见 [产品总览](docs/design/product/overview.md)，阶段状态与证据入口见 [Milestone 总览](docs/milestones/README.md)。HTTP 与 Audio 上游 blocker、Issue 草稿和脱敏附件统一收录在 [Upstream Tracking](docs/upstream/README.md)。

## 构建

当前验证基线为 ESP-IDF 6.0.1 与 `firmware/dependencies.lock`；目标板选择器为 `esp32_s3_touch_amoled_1_75c`。lock 已固定 Runtime JS 0.8.3 与 QuickJS-NG 0.14.0；Toolkit 1.0.1 与 debug `.bpk` 的验收边界见 M3 验收报告。

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
```

`managed_components/`、`sdkconfig` 与 `components/gen_bmgr_codes/` 均为生成内容，不提交；`dependencies.lock` 必须保留。

## License

Apache License 2.0。见 [`LICENSE`](LICENSE)。
