# Reliability fixture

只供独立测试候选，普通构建不启用。协调入口在 `app_main`，不依赖停止时会关闭的 USB Adapter，也不从 System Owner 的回调里等待自己停止。使用与产品相同的公开 System API，没有新增生产命令或生命周期 Manager。

```sh
python3 scripts/firmware/build_patched_firmware.py \
  --workspace /private/tmp/new-reliability-lifecycle \
  --sdkconfig firmware/sdkconfig --reliability-fixture lifecycle
```

先加载 Firmware README 要求的 ESP-IDF 环境。每种模式使用新的目录；测试注入在输入冻结前完成，模式写入 `patch-inputs.json` 和候选 manifest，注入后的源码进入输入 inventory。禁止将测试候选当普通固件发布；LittleFS 仍是 fresh filesystem，不可覆盖用户数据。

| 模式 | 实际边界与观察 |
|---|---|
| `lifecycle` | 同一 System 对象 stop→start、deinit→init 各三轮；每轮启动 Native/Runtime Hello，生成键盘及 active/queued 系统 Dialog；停机后旧结果必须拒绝，不能交付 handler；记录 App 状态及 internal/PSRAM free/largest |
| `init-after-theme` / `init-after-cards` / `init-after-shell` | 在所列产品初始化资源获得后注入失败，经真实 Core init 失败清理和产品 guard 返回；观察诊断及显式硬件重启 |
| `start-after-shell` / `start-after-power` | Shell 或 PWR 成功启动后注入失败；观察真实 startup failure 清理、显示诊断及显式硬件重启 |
| `theme-unknown` | 仅替换启动时读到的主题 ID，走真实默认回退；不修改 NVS |
| `theme-apply-failure` | 测试副本选择 light 并拒绝第一次 apply，默认 dark 仍由真实 backend 应用 |
| `theme-default-failure` | 测试副本同时拒绝 light 和 dark，必须进入关键启动失败 |

这些是可编译、可执行的测试入口，不是设备通过证明。注入失败的返回值不能证明真实驱动/backend 的全部失败机制。主题测试不写坏真实偏好，实际保存/重启持久化仍须单独比较。lifecycle 输出 `SEQUENCE_COMPLETE` 仅表示断言通过；heap 的变化、后台持续工作和真实 callback/GUI 锁竞争需审阅串口与资源证据。默认回退故障需要分别构建，普通产品镜像不能覆盖所有注入条件。

当前不注入 Core 内每个分配点、调度拒绝或 GUI 锁失败；对应生产方法 host 回归仍有效，完整故障矩阵保持开放。测试候选不得与包验收、M2 自动压力或其他自动协调夹具同时开启。执行前保留用户数据和实际 image identity，执行后恢复普通候选并核对 Home/Reset；无设备时不运行这些步骤。
