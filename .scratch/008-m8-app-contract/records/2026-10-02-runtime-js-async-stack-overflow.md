# Runtime JS 异步 GUI 调用栈溢出

Date: 2026-10-02
Status: 本地复现，未提交上游
Locked backend: espressif/brookesia_runtime_js 0.8.3
Device: Waveshare ESP32-S3 AMOLED 1.75C

## 实际故障

普通 ELF identity 71567f599，Hello Runtime entry SHA-256 d7e27a802f1575934348b2d91821bd70ce5fae32c8f2e855f5caf48838063130。在 Runtime Root 打开 Detail，点击 Confirm Back，导航异步完成后更新文字时出现：

```text
***ERROR*** A stack overflow in task RuntimeJsAsync has been detected.
Backtrace: 0x4038500d 0x40384fd5 0x4240f672 0x403862db 0x40385888
ELF file SHA256: 71567f599
Rebooting...
```

对应保存的原 ELF 符号化为 panic_abort、esp_system_abort、vApplicationStackOverflowHook、vTaskSwitchContext、_frxt_dispatch。原始栈已损坏，不能从这些帧断言溢出函数的完整调用链。无需息屏：最小路径也复现相同错误。

## 可执行复现

设备启用 Developer Mode、普通镜像启动完成后运行：

```bash
python scripts/firmware/run_device_tests.py --suite runtime-confirm \
  --port /dev/cu.usbmodem101 \
  --device-id ESPocket-Waveshare-A0F262E30B68 \
  --expected-image 71567f599 \
  --output /private/tmp/espocket-runtime-confirm-regression
```

该套件通过真实 Launcher、Runtime 页面按钮和 Edge Back；遇到设备错误立即失败，保留 report、串口原文和 cleanup 结果，不重试掩盖故障。

## 锁定版源码事实

- `brookesia_runtime_js/src/backend.cpp` 的 Backend::init 为 RuntimeJsAsync 明确设置 `stack_size = 8 * 1024`，Kconfig 没有这个任务的栈配置；公开 Backend 接口未提供修改其私有 scheduler 的入口。
- enqueue_async_completion 将完成任务投递到该 scheduler；flush_async_completions 进入 flush_app_async_completions 并 drain_microtasks，JS 的 await 后续逻辑在此执行。
- 本项目 sample 的 toggle_confirm 在 await 导航完成后调用 SystemGui SetText；on_timer 的 await 后续也会更新待决提示。

这些是只读源码事实。栈预算不足与同步 GUI 服务调用嵌套是当前支持度最高的解释，未通过调整上游栈大小实验确定最小预算，也未排除更深的 backend 调度缺陷。

## 单变量诊断

保持 ELF 不变，仅对临时 LittleFS 资源进行隔离；正式 sample 与 managed_components 均未修改。

| 资源 | 结果 |
|---|---|
| 原始资源 | Confirm Back 点击处 RuntimeJsAsync 栈溢出 |
| 仅省略确认开关文字更新 | 开关步骤通过；后续待决提示文字更新处同一任务栈溢出 |
| 再省略待决提示更新 | 相同确认、待决 Back 与 PWR Home 路径通过 |

后一结果只证明触发边界，不是正式修复，也不证明通用异步 GUI API 安全。两次启动 hello 超时也保留为独立失败，均未发送刺激；设备最终快照就绪后新 attempt 才执行无 GUI 的路径。

## 需要上游提供的能力

请求可配置的异步完成任务栈预算及分配策略，或让微任务/同步 Service 调用安全地在有足够栈预算的执行上下文运行。还需相同最小复现和完整 apps 套件验证，不以隐藏确认 UI 或取消契约作为通过条件。本地不修改 managed_components，不私自维护 backend fork。

产品验收与 attempt 清单见 [008 设备记录](2026-10-02-app-device-frontier.md)。

## 2026-10-03 版本勘误与补丁提案

此前把 Runtime Manager 0.8.2 误记为 Runtime JS 版本。重新核对 main/idf_component.yml、dependencies.lock、组件 metadata、原镜像 compile_commands 后确认 Runtime JS 为 0.8.3，Manager 为 0.8.2；原故障 ELF 和资源 hash 不变。Registry 当前最新稳定 JS 版本仍是 [0.8.3](https://components.espressif.com/components/espressif/brookesia_runtime_js/versions/0.8.3/readme?language=en)。本地 0.8.3 changelog 只记载 Storage loader 修复，不是本故障修复。

已准备[最小公开配置补丁提案](2026-10-03-runtime-stack-proposal.md)。它尚未接入产品、未刷写、未向上游发消息；是否维护受版本锁约束的组件补丁需用户决定。
