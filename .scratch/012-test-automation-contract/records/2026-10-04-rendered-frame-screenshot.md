# 2026-10-04 — 最终渲染画面截图

用户授权增加 USB 截图并导出实际设备画面。LVGL FLUSH_START 公共事件在 HAL 字节交换之前读取 RGB565 部分刷新块，逐像素覆盖检查通过后提供固定缓存；没有替换显示回调或新增上游补丁。

## 源码与主机

- 截图组件用例通过完整/重复/缺失覆盖、stride、截断、越界、RGB565 字节顺序、开发者模式、ID、分块边界、超时、idle 清理、release 和断连清理。
- 主机用例通过颜色转换、传输摘要、截断、ID 与 offset 校验。
- `python3 scripts/check.py` 全部通过，其中跨模块主机用例 82 项；Markdown 254 个文件通过。截图组件另跑 2 项通过。
- 完整构建通过。ELF identity `adc85a22e`，SHA-256 `adc85a22e7510c904d1f7859eb01c9ae34659fb55b8208272b58c33ede53f362`；BIN SHA-256 `ba14e79d9df045547034d389144588775d13a54cf93577925d997f6f36452e00`，7,698,256 字节，应用分区约 28% 剩余。
- 构建输入验证覆盖 lock、七套精确补丁 inventory、板级 HAL/PSRAM、Audio、字形、源码 checkpoint、九个与既有 LittleFS 相同的 built-in 文件摘要及 BIN 内嵌 ELF 摘要。

## 设备

`adc85a22e` 完成 app-only 写入，但首次启动超过脚本 35 秒窗口，保留 startup incomplete。独立 USB attempt 随后严格验证同一 identity、两项截图 capability、Store Root/亮屏/空闲状态通过。首次截图因息屏返回 invalid_state；显式唤醒后真实捕获触发 `espocket_test_u` 栈溢出并重启，故此镜像截图验收失败。

修复将调用同步 renderer 的 USB worker 从 8 KiB 扩为 32 KiB PSRAM 栈，并记录成功捕获的最低剩余栈。新的构建与设备验收待完成；不能把原镜像 capability 或 Store 状态通过当成截图通过。启动日志还发现 Flappy Bird 被 Core 加载，尚未用 receipt 证实此前安装行为。原始产物保存在 `/private/tmp/espocket-m5-reviewed-adc85a22e`，不进入 records；缓存帧仅为 rendered-frame，不证明实体面板或 GPIO。

## 栈修复构建

修复镜像 `3cd0a2324` 完整构建和统一检查全部通过；ELF SHA-256 `3cd0a2324c8b895c8fee00bc9a5e377690d19f3b5ebd52cff11380e0af6e511a`，BIN SHA-256 `73889e087c87eaf4ef4ed26114f85b8a6beb9cb0d80ef8ab871155aa66972d3a`，7,698,448 字节。沿用同一配置、补丁与 built-in 摘要，重新核对源码 checkpoint 和所有输入；app-only 刷写与实际捕获待完成。

## 首帧设备证据

`3cd0a2324` app-only 写入、启动 marker、hello identity/capabilities 和 Store Root 合成输入通过。同步捕获成功，最低剩余调用栈 20,828 字节；512-byte read 的响应超过原 512-byte TX ring，记录 response write failed。临时采用 128-byte read 的独立 attempt `ea6b7db7-d99c-42f5-a1cd-00ce6e9a67ae` 实际导出 466×466 RGB565/PNG，434,312 字节，原始像素 SHA-256 `19e363778d289b2162537ec4eb517baa2b4f6722f2ba9c4d79f658de1aa7d476`，release 和最终亮屏 Store Root/inputBusy=false 通过。PNG 显示 Store 首屏、NES Emulator 和 Music Player，不含弹窗。

修复将 TX ring 扩为 2048 字节，保持整个响应一次入队，避免与普通控制台日志交错；最大 512-byte 分块的最终设备门槛待新镜像。后续 128-byte 滚动截图 attempt 于 offset 51,328 返回 invalid_state，保留失败且不导出 PNG；不把部分像素作为截图。

## 最终设备结果

最终镜像 `f3fdd7e82`：ELF SHA-256 `f3fdd7e8294825aa0ef68d5132df39c2acb99b7875b8d78161cc58f6d48d37b2`；BIN SHA-256 `4e5d8f30788bd5871b6674c68d97a13cbeef0f653e2aea303c5ed55a7360e424`，7,698,448 字节。完整构建、统一检查、精确输入核对通过；仅写应用分区 0x60000，Flash hash、启动 marker、hello 与 Store 输入路径通过。LittleFS 与 NVS 没有被构建产物覆盖。

默认 512-byte read 成功导出三个独立实际设备 PNG，并校验全部 434,312 字节及整帧摘要，release 和最终快照均通过。最低剩余 USB 调用栈 20,828 字节：

| attempt | 内容 | 耗时 | RGB565 SHA-256 |
|---|---|---|---|
| `434b6260-458b-419c-b49e-690160f684fc` | Store 滚动列表，AI Chatbot 与 Camera | 6.85 秒 | `9bc30735220d12e297652f4cdf6e84eba28a8ed6089056d543307289c3c17615` |
| `b891530b-c35a-4d5e-8cba-6d796d48d9dd` | Local 页及 Loading local packages 提示 | 10.35 秒 | `bf2a4ea069a2dc8dbef503bd4093fd5aea64d2573ef743c69d1dfb65f3ff404d` |
| `f980e66c-fd86-454b-a834-0fe4f54f4d17` | Local 扫描完成，NES Install、Flappy Bird Installed | 6.81 秒 | `2569c0ea1bda7469e83ca4f2aaa5408686ba8d990a12a45685aa2ac8b4cce02c` |

PNG 与原始 attempt 位于 `/private/tmp/espocket-m5-reviewed-f3fdd7e82/screenshots/`。另有两次默认块读取于中途返回 invalid_state，未产生 PNG，保留失败；当时设备未重启，缓存失效原因尚未细分，不将失败改记通过。当前入口会明确拒绝不完整传输，而非静默生成画面；后续捕获仍应保留独立 attempt。

实际画面表明此前推算 `[360,276]` 在当前滚动位置是 AI Chatbot 的 Install，不能作为 Flappy Bird 按钮校准。Flappy Bird 在 Local 中已经显示 Installed，Core 启动也发现该包；这些只证明当前可观察状态，不证明之前 Cancel/Continue 的流程或 receipt。005/03、09 的设备条件仍独立开放。本票完成软件渲染帧导出，不证明实体面板或输入硬件。
