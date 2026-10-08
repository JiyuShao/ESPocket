# 2026-10-08 — 剩余启动同步路径检查与配置读取修复

## 范围与结论

按 023/04 继续检查服务绑定、本地配置读取、Runtime 加载与 GUI 准备。本轮修复位于本地 Chat Runtime App 0.1.5；未新增平台 API 或修改 managed_components。此前 Core 分阶段启动与诊断保持有效。

AppData 中的 openai.json、coze.json 和 Coze 私钥补读改用现有 Core StorageRead 异步桥，避免文件服务慢读占住 App 执行链。配置验证函数只负责验证，不再同步读取私钥。读取使用捕获的 service handle，并在每个 await 后检查 Running Instance epoch、所选 Agent 与 handle；过期结果不能继续补读、配置或启动 Agent，也不能错误地锁住新实例。

## 失败复现与回归

命令：`python3 -B -m unittest discover -s firmware/runtime_apps/ai_chatbot/test -p test_startup_responsiveness.py -k config_file`。

修复前真实 maybeStartAgent → configureSelectedAgent → loadSelectedAgentConfig → StorageRead 链路，在平台边界注入虚拟 500ms 慢读后失败：`slow config-file read must not occupy the App Owner`，actual 500、expected 0。修复后绿灯。虚拟占用是确定性同步调用检测，不是硬件时延，也不能证明 250ms 真机响应。

Chat 9 项回归通过：除前轮路径外，新覆盖配置读取 single-flight、停止／重启旧读失效、OpenAI 新实例配置、Coze 私钥补读、首次读取结束前停止、私钥补读期间停止和格式错误不触发 Agent。

StorageRead 的公开 schema 要求 scheduler，ServiceBase::call_function_async 将 handler 投递到 Service Owner task group，而非在 JS 调用处直接执行。继续走原 Core caller 身份与 AppData 路径验证，没有绕过权限或文件解析。异步完成返回 Runtime 原 Promise completion pump。

## 剩余路径审计

| 路径 | 代码事实 | 当前结论与后续方向 |
|---|---|---|
| 服务绑定 | Core host_bridge 的 start_service 同步 manager.bind；ServiceManager::bind 递归绑定依赖、等待 Starting/Stopping 条件变量，冷启动同步 service.start | 仍可能占住 App 执行链。下一步应在 Host Bridge 与 Service Owner 内设计异步 bind，覆盖实例结束时 pending bind、晚到 binding 的释放及引用计数；不能只把 JS 函数标 async，也不能让旧绑定泄漏 |
| Runtime load | Core ensure_runtime_loaded 同步 runtime.load_app，backend mutex 内创建 QuickJS runtime/context 与 native modules | 尚无真机时长。先采集 runtime_load phase；若超过预算，再在真实 Runtime Owner 设计 prepare/commit 与取消清理，避免多个线程同时操作 QuickJS context |
| Runtime start | backend 同步入口文件读取和 JS_Eval，加载模块并 drain microtasks | 尚无真机时长。runtime_start phase 仍同步；任意 JS/Native callback 不可安全强制抢占 |
| GUI prepare | SYSTEM_GUI_TASK_GROUP 的 pre-execute 持有 GUI runtime gate 与 GUI thread guard；resource registration、root load、screen flow mount 在任务内完成 | App Owner 的 future 等待已非阻塞，但 GUI 锁依然可能阻碍 QS 绘制。先使用既有分步骤 profile 测量；解析可否分离、节点是否需分批创建要在 GUI Owner 内处理，不得简单解锁后调用 LVGL |
| JSON 解析与 GUI 更新 | 异步读返回后 JSON.parse 与 GUI 调用仍同步执行 | 文件等待已移除；超大配置解析与实际 GUI 锁耗时没有硬件证明，仍不能认定全链路有界 |

另使用真实 on_start 的同一 stand-in 夹具，仅在 Device 的 start_service 注入 500ms 慢绑定：`node /private/tmp/repro-startup-service-binding.js firmware/runtime_apps/ai_chatbot/src/app/chatbot/lifecycle.js` 仍报 `on_start occupies App Owner for 500ms with slow service binding; PWR/QS cannot run`。这是未解决路径的离线反馈，保存在临时 debug artifact；不能将配置回归绿灯解释为全部启动阻塞消失。

## 验收边界

未部署、未连接设备、未提交或推送。250ms、真实 PWR／全局 QS 与取消／回滚门槛继续开放。候选的 AEC 开关仍关闭，不宣称声学或打断效果。

## 构建与产物

隔离 ESP-IDF 完整产品构建通过；81 个产品组件输入、完整 Chat 源码和已 staging 的 lifecycle 与工作区一致。原始 Core inventory 仍匹配 source_files，隔离 patched Core 匹配 patched_files。没有修改原始 managed_components。

官方锁定 packager 0.1.7 输出 Chat 0.1.5 BPK，31 个成员与维护源码逐字节一致；开发包未签名，设备未验收。

保存于 `/private/tmp/espocket-startup-storage-release/`，含 App、ELF、LittleFS 镜像、sdkconfig、lock、依赖 overrides、Core manifest、BPK 和 source-inputs/release JSON；此前候选保留。Core profile 与 render profile 开启，软件 AEC 关闭。

| 产物 | 字节数 | SHA-256 |
|---|---:|---|
| espocket.bin | 11,235,920 | `7df335e1780cb43f6860b8c80f74f97735bffc17bbb6bcdfc5127865157d76bb` |
| littlefs_data.bin | 18,481,152 | `9ee6b5954222ddc9dacb46f65559b0d8ab0e5feb557d8494f678523145675a2d` |
| Chat 0.1.5 BPK | 87,391 | `722cd405736b1367b3844c0ed41c5d4919a92f0af40a46da365b3f508fa45eb0` |

## 最终检查

- `python3 scripts/check.py`：执行 220 项主机测试，218 项通过、2 项跳过，Lifecycle parser self-test 通过。
- `python3 scripts/docs/check.py --markdown`：319 个 Markdown 文件通过。
- `git diff --check`：通过。
- 完整固件构建与 BPK 成员核对通过；真实 on_start 的慢服务绑定 stand-in 夹具仍失败，作为开放阻塞路径保留，不计为已通过回归。
