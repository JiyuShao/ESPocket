# 2026-10-08 — 启动阻塞治理离线证据

## 结论与范围

真实 Chat 生命周期中的 Agent discovery、网络探测和启动前 Agent 配置改为现有 Runtime async bridge。Core 仍独占启动 phase、取消与回滚；没有增加第二套生命周期管理器。App on_start 保持同步 bool 返回，完成表示 UI 实例启动，不表示远端 Agent 就绪。

此轮离线完成；没有连接设备、部署、提交或推送。总体 250ms 响应门槛保持开放。

## 可复现反馈

命令：`python3 -B -m unittest discover -s firmware/runtime_apps/ai_chatbot/test -p test_startup_responsiveness.py`。

测试执行完整 JS on_start 与真实业务函数，在平台调用 stand-in 中注入虚拟 500ms 同步占用。修复前 discovery 报错 `on_start occupies App Owner for 500ms with slow discovery; PWR/QS cannot run`；配置路径独立失败，Owner 占用 actual 500、expected 0。这里是确定性阻塞模式复现，不是硬件延迟测量，也不证明触摸、PWR 或 GUI 锁的实际响应时间。

修复后，以上查询与配置不再使用同步调用。回归同时覆盖 discovery 原子发布、网络 single-flight、停止／重启撤销旧结果、配置 single-flight、停止／切页／切换 Agent 后禁止旧配置链触发 Activate/Start，以及正常配置启动。Chat 全套 7 项通过。

## Owner 边界与诊断

异步完成携带 Running Instance epoch 和 service handle；Agent 配置另外验证选择身份与页面。停止／重启会重置当前实例 flags，旧完成不能清除新实例状态。异步服务请求已经发出的副作用不能靠 JS guard 撤回，guard 只禁止后续调用及状态写回。

Core 原 profile 开关下记录启动 phase 的 Owner 占用，长期等待 future 的短轮询不重复输出。GUI prepare 复用既有步骤 profile。此日志用于识别剩余慢阶段，没有改变调度或生命周期语义。

## 尚未验证与剩余路径

服务绑定、本地配置读取、包准入、Runtime 加载、GUI 持锁解析与任意同步 Native/Runtime callback 仍不能安全强制抢占；用户主动切换 Agent 的同步 SetTargetAgent 不在本轮启动路径修复范围。真机仍需测量启动期间全局 Quick Settings、PWR、取消／回滚与对话就绪表现。

## 最终离线验证

- `python3 scripts/check.py`：执行 218 项主机测试，216 项通过、2 项跳过；Lifecycle parser self-test 通过。
- `python3 scripts/docs/check.py --markdown`：318 个 Markdown 文件通过。
- `git diff --check`：通过。
- 隔离 ESP-IDF 完整产品构建通过，Core profile 开启的代码分支已编译；最终资源 staging 与 Chat 源码逐字节一致。
- 原始 Core inventory 与 manifest source_files 一致；隔离 Core 与 patched_files 一致。81 个产品组件输入与工作区一致。生成板级 CMake 仅隔离目录绝对路径不同。
- 官方锁定 packager 0.1.7 生成 Chat 0.1.4 BPK，31 个成员逐字节匹配维护源码；未签名、设备未验收。

## 产物

保存于 `/private/tmp/espocket-startup-responsiveness-release/`，包含 App、ELF、LittleFS 资源镜像、sdkconfig、lock、依赖 overrides、Core manifest、BPK、source-inputs 与 release JSON。此前候选保留。

| 产物 | 字节数 | SHA-256 |
|---|---:|---|
| espocket.bin | 11,235,920 | `a7e59554f9e9f4f85982e9897f46963531339ce51f44dc759121751c985fefa4` |
| littlefs_data.bin | 18,481,152 | `15015b15d83f9e48924027c079f3ed720f4cdc270b2b9d6a0bd047aed0a76518` |
| Chat 0.1.4 BPK | 87,298 | `7261e260662870a2ec7b184b225e807eafea23bf781ffa5bccef91c903b230f1` |

此候选 Core profile 与 render profile 开启，软件 AEC 关闭；用于启动耗时诊断，不能据此认定防回音或真机打断验收通过。
