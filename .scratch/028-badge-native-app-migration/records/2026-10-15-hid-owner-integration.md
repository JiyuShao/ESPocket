# 2026-10-15 BLE HID Owner 接入核查

## 结论与输入

ESP-IDF 6.0.1 提供 NimBLE HID Device 实现，不需要因为原作使用 Bluedroid 就切换蓝牙栈。但锁定版 Brookesia BLE backend 与 `esp_hidd_dev_init()` 都直接控制全局 GATT 服务与 host 回调，不能并行初始化，也不能仅靠 `BluetoothHostCoordinator::Token` 安全组合。当前保留 `UnavailableEndpoint`；本批没有启用 Bluetooth、修改 HAL 原始源码或创建第二个 host。

核查基于产品源码 `ceb2c1a`，ESP-IDF commit `8c19b156084a0753687347cca1f5355782893533`，HAL Adaptor 0.8.4、HAL Interface 0.8.2（组件版本以 `firmware/dependencies.lock` 为准）。以下 SHA-256 固定本次实际读取的源码字节：

| 输入 | SHA-256 |
|---|---|
| HAL Adaptor `src/bluetooth/ble/backend.cpp` | `cab133d98ebe98dc6656284f6761576bb6b87b008c4bd07d19bdfe2932f5babc` |
| HAL Adaptor `src/bluetooth/host_coordinator.hpp` | `7dbe94e2f25d61645a05cdef02c5508e6f24d4a856ec0853adfda819b8c4a10c` |
| HAL Interface `interfaces/bluetooth/ble/types.hpp` | `0742d6959a695478eb815f6f0c9f0fb4f9c5a9c7aff35a23dfc6f2d8f9bb88e8` |
| ESP-IDF `components/esp_hid/src/nimble_hidd.c` | `561557d36cfa1ebcc26b085ccd8ec693bbcbd8ebe74b285f5b5cd362ae562d25` |

## 代码事实

- ESP-IDF `components/esp_hid/CMakeLists.txt` 在 `CONFIG_BT_NIMBLE_ENABLED` 下编译 `nimble_hidd.c`；实际 Device 实现另外要求 `CONFIG_BT_NIMBLE_HID_SERVICE`。当前目标是支持集成 BLE Controller 的 ESP32-S3，当前配置却关闭 `CONFIG_BT_ENABLED` 和 `CONFIG_BROOKESIA_HAL_ADAPTOR_ENABLE_BLE_DEVICE`。这是配置与接口缺口，不是硬件不支持的证据。
- HAL backend 的 `init()` 调用 `nimble_port_init()`，覆盖 `ble_hs_cfg.reset_cb/sync_cb/gatts_register_cb`，设置 `sm_sc=0`、`sm_bonding=0`、`sm_mitm=0`、空 `store_status_cb`。`handle_gap_event()` 没有安全配对/加密、passkey 或 bond 管理事件。
- HAL backend 的 `start()` 拥有 host task，`stop()` 停止 host 并执行 `ble_gatts_reset()`，`deinit()` 释放 NimBLE/controller。它通过 `active_instance_` 限制单个 peripheral backend。
- `BluetoothHostCoordinator` 的 token 仅计数；它不调度 profile 注册、不分发全局回调，也不接管 host init/deinit。多拿一个 token 不会阻止 backend 的停止路径清空 GATT。
- ESP-IDF 的 `esp_ble_hidd_dev_init()` 同样覆盖三个 host 回调，初始化 GAP/GATT/HID/DIS/BAS/SPS 服务并注册 GAP listener。`nimble_hidd_dev_deinit()` 全局停止 GATT 并清理上述服务；这不是可以无条件挂到既有 peripheral 上的独立 service。
- 该 IDF 实现的连接事件处理未先排除失败的 CONNECT 就查询 connection 并 assert；输入路径对 report/mbuf 使用 assert；deinit 路径未见对应 GAP listener 注销。直接复用仍须验证失败、内存不足与反复重开，不能因官方提供实现就认为这些生命周期条件已满足。
- 现有 `CharacteristicConfig` 只有 write/write-without-response/notify，没有 read、descriptor、静态值和安全权限；`CharacteristicId` 仅由 service/characteristic UUID 组成，不能区分同一 service 内多个同 UUID Report characteristic。ConnectionInfo 也不提供 bond identity、加密或认证状态。

## 协议边界

| 项目 | 必须落实的内容 |
|---|---|
| HID Service `0x1812` | HID Information `0x2A4A`、Report Map `0x2A4B`、HID Control Point `0x2A4C`、Input Report `0x2A4D` 及 Report Reference `0x2908`；通知通过 CCCD `0x2902` 订阅 |
| 报告格式 | 本次鼠标 Report payload 为三键/X/Y/滚轮共四字节；report ID 在 Report Reference/Map 中匹配，不重复塞进 GATT payload |
| Boot 协议 | 若公开 Protocol Mode `0x2A4E` 与 Boot Mouse Input `0x2A33`，按主机选择发送三字节三键/X/Y，不能发送四字节滚轮布局；也可先仅提供一致的 Report 协议 |
| 安全与 readiness | 连接、加密/配对成功、Input Report 订阅、HID suspend 状态分别持有；连接成功本身不等于可发送 |
| bond 与主机 | 使用持久 identity 而非临时 connection handle/RPA 做主机及灵敏度 key；只移除用户确认的 bond，处理持久存储失败 |
| 断开与停止 | 连接仍有效且可发送时先尝试归零；断开或失败不能报告电脑已收到；停止后禁止旧 generation 的回调、报告及复用 connection handle |
| 恢复与广播 | Quick Settings 只停输入并尝试归零、保留连接；息屏/Home 停广播并断开；同次实例恢复开启有界广播等待电脑连接，超时可重试，不能强连电脑 |

原作 `hid_mouse.c` 的文件首注释把带 wheel 的四字节格式比作 boot mouse，不能作为标准依据。本批将 `encode_mouse_report()` 明确为四字节 Report payload，`encode_boot_mouse_report()` 修正为三字节 Boot payload；两者均对相对轴限幅并屏蔽未声明按键位。尚未注册 Report Map，因此编码测试不构成 HOGP 验收。

## 最小平台接入提案

以下是 [05](../issues/05-ble-hid-capability.md) 的后续实现范围，不是已提供的接口：

1. 在现有 `BleDevice`/backend 增加专用 HID mouse profile 能力，底层仍由同一 backend 持有 NimBLE/controller、GAP、安全存储与 GATT；profile 配置只允许在 idle 时选择。已有通用 Peripheral 路径默认行为保持兼容，运行中禁止另启 HID host 或切换数据库。
2. 优先在该 Owner 内复用 NimBLE `ble_svc_hid` 底层服务与厂商 descriptor 定义；不直接并用会覆盖回调的 `esp_hidd_dev_init()`。若必须复用后者，先把服务注册/解绑与 host 管理分离，并验证回调、共享服务及 listener 的对称清理。
3. HAL 公共能力提供带 generation 的状态快照（lifecycle、peer identity、security、subscription、protocol、suspend、错误），以及有界 start/stop、报告提交、选定主机广播、bond 列表和指定 bond 删除。启动/停止在 Owner worker 推进，不在 App timer 或 GUI 线程等待配对或断连。
4. `espocket_hid::Endpoint` 适配该公开能力。现有 `bool connected()`、`Peer{address,name}` 和 `void clear_buttons()` 不足以表示完整 readiness、持久主机身份与释放结果；接入时扩充公开契约及回归，不能把调用成功当远端收到。按电脑保存灵敏度属于 App 数据，密钥与 bond 属于 BLE Owner。
5. 真实 Owner 内用带 session 身份的 host adapter 验证失败连接、订阅前发送拒绝、配对/持久化失败、OOM、停止超时、迟到回调和 connection handle 复用；在隔离副本维护版本/hash 锁定补丁，按 ADR-0016 记录移除条件。通过这些门槛后再替换生产 factory 并启用 BLE 候选配置。

不以扩展通用 GATT 任意 descriptor API 作为本票必需前置，也不另造一个 Bluetooth 资源管理器。Wi-Fi/聊天继续由原 Owner 控制，App 不关闭 Wi-Fi。macOS/Windows 配对、连接间隔、延迟、共存和物理输入仍归 [09](../issues/09-device-acceptance.md)。

## 离线验证

鼠标专项 4 tests 通过，包括 Report/Boot 长度、极值限幅、按键掩码和归零；真实发送、配对和设备验收未执行。统一 host 检查与最新隔离候选结果由 [08](../issues/08-offline-build-candidate.md) 另行记录。

## 隔离构建过程

本批使用 ESP-IDF 6.0.1、production 补丁和已验证的太阳系 v4 板级配置，构建目录均在 checkout 外。

- `/private/tmp/espocket-028-hid-build-v1` 在配置阶段因 sandbox 拒绝 Component Manager 的 `psutil/sysctl` 进程枚举失败，未进入源码编译。原始日志为同名 `.log`。
- `/private/tmp/espocket-028-hid-build-v2` 经受审查的构建权限重跑，通过配置和输入检查；实际 GCC 编译在 `mouse_model.cpp` 的两处同一行控制语句触发 `-Werror=misleading-indentation`，停止且未生成 candidate。本批拆开该两处及两个新增 App 中的同类 pause/stop 语句，不关闭警告、不改变分支语义。
- 使用 v2 的实际 `compile_commands.json`、锁定 include/config 与 Xtensa 编译器，对最终 checkout 的 IMU/HID/重力迷宫/遥控共 8 个 translation units 单独预编译，全部通过。输出仅在临时目录，未修改 v2 的冻结源码，也未归档候选；日志为 `/private/tmp/espocket-028-hid-xtensa-preflight.log`。
- 首轮统一检查 277 tests 通过，其中两个 LittleFS tests 在默认 Python 跳过；已用太阳系 v4 的 `littlefs_py_venv` 分别补跑通过。对应日志为 `/private/tmp/espocket-028-hid-checks-v1.log`、`/private/tmp/espocket-028-hid-builtin-update.log` 和 `/private/tmp/espocket-028-hid-littlefs-migration.log`。

为给最终构建留出空间，在记录上述结果后，仅清理本批失败 v1 的 `firmware/managed_components` 与失败 v2 的 `firmware/build`、`firmware/managed_components`；这些是可重建依赖/产物，不含成功 candidate。失败源码、补丁副本、冻结输入 inventory、配置/lock 和外部日志保留。最终修正另用新 v3 workspace 冻结并构建，不把 v1/v2 当作成功候选。

## 最终阶段候选

最终源码修改后，`python3 scripts/check.py` 再次通过：共 277 tests，跨模块 187 tests 中两个 LittleFS tests 在默认 Python 跳过，已按上文分别补跑通过。Markdown 检查通过 369 文件。完整 ESP-IDF 构建通过；新增代码不再触发 misleading-indentation。构建另有上游 GMF Video 的 unused-function 警告以及既有 Kconfig 提示，未通过关闭警告掩盖它们。

仅 `/private/tmp/espocket-028-hid-build-v3/candidate` 是本批成功候选。基线为 `ceb2c1a` 加本批冻结改动，使用 production 补丁及太阳系 v4 的已验证 Waveshare 板级配置；包含七个 Native App 的当前源码，其中 IMU/HID 仍明确不可用，遥控仍有本文与 07 列出的实现缺口。

| 项目 | 结果 |
|---|---|
| Input fingerprint | `b0266f7d0313e5bfb9523ea75e23b18df0776df46398eabba133e21dea21df03` |
| espocket.bin | 12,445,008 bytes，比太阳系 v4 增加 23,552 bytes |
| SHA-256 | `9f9a02c530d20f88e4afce310d4441ee0d98ba5406a10d0272f02f61e16e8f21` |
| App 分区余量 | 2,235,056 bytes（15%） |
| 归档复核 | 115 artifacts 的大小/hash 全部匹配，完整冻结输入复核通过 |
| 源码复核 | 147 个 Native App、IMU/HID 与 System 注册文件和 checkout 匹配；核查的原始 HAL 文件 hash 保持不变 |
| Bluetooth 配置 | `CONFIG_BT_ENABLED`、BLE Adaptor 仍关闭，不证明 HID backend 已编译接入 |
| 部署/物理验收 | `deployed=false`、`physical_validation=false` |

候选保存镜像、ELF、配置、精确 lock、补丁字节与输入证明；LittleFS 为 fresh filesystem，不是已有设备的迁移镜像。未访问设备、未刷写、未配对、未发送实际 HID。IMU/HID backend、遥控缺失交互与 [09](../issues/09-device-acceptance.md) 物理验收保持未完成，08 不因阶段候选成功而关闭。

最终原始日志为 `/private/tmp/espocket-028-hid-build-v3.log`、`/private/tmp/espocket-028-hid-checks-final.log`；归档与源码复核摘要为 `/private/tmp/espocket-028-hid-final-verification.json`。这些本地产物不提交源码仓库。
