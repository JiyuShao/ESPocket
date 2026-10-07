# 上游源码补丁

本目录保存已经接受的上游源码修改。自有兼容头文件与编译适配放在[compat](../compat/README.md)；managed_components 是依赖解析产物，不手工修改。

GUI Interface 0.8.2 的[预加载资源归属补丁](espressif__brookesia_gui_interface/0.8.2/001-preserve-declared-image-preloads.patch)已纳入默认 `production`，`gui-candidate`／`scheduler-candidate` 保留为兼容入口。动画切帧保留文档声明的 `preload: true` 资源，普通自动加载资源仍按引用释放，文档卸载仍释放全部资源。真实资源更新／释放方法的主机回归验证 200 次切帧无重复加载、非声明资源释放和失败回滚；构建及真机联合门槛见 [005/10](../../.scratch/005-m5-application-ecosystem/issues/10-reduce-runtime-startup-blocking.md)，原包联合回归与默认构建采纳结果见该工作票。

## 当前清单

Agent Manager 0.8.2 的[会话阶段录音初始化补丁](espressif__brookesia_agent_manager/0.8.2/001-defer-capture-until-conversation.patch)将 capture DataFlow 的获取从服务启动移到会话启动。账号激活可以在 playback-only 产品上运行；实际会话仍要求真实录音接口，不伪造输入或吞掉缺少接口的错误。默认 production 精确选择该补丁；验收由 [005/13](../../.scratch/005-m5-application-ecosystem/issues/13-xiaozhi-and-launcher-performance.md)持有。

同一 Owner 的[音频队列所有权补丁](espressif__brookesia_agent_manager/0.8.2/002-own-queued-agent-audio-packets.patch)通过官方 DataFlow `write_copy` 将 Opus 包交给现有有界 Decoder 队列。旧同步借用路径把 200 ms 消费延迟误判为流故障并重置 Decoder；复制后调用者可安全归还输入，实际消费仍由 Audio Owner 管理。保留原队列容量和 20 ms 入队超时，满队列、关闭和写入失败继续报告，不增加另一套音频队列。真实 ingress 方法回归覆盖延迟消费、输入复用、Home 清理、准入失败及半双工条件；完整播放与退出门槛由 [005/15](../../.scratch/005-m5-application-ecosystem/issues/15-enable-xiaozhi-voice-conversation.md)持有。

2026-10-07 的正式产品语音装配由 [005/15](../../.scratch/005-m5-application-ecosystem/issues/15-enable-xiaozhi-voice-conversation.md)持有：独立构建启用官方 Recorder／AFE，准确选择 ES7210 MIC1/MIC2 的双通道配置，既有 playback-only 与会话阶段 capture 补丁仍保留。该装配使用官方 Opus／Agent DataFlow，不另建录音或云协议实现。

XiaoZhi 0.1.2 的[动态音频任务释放补丁](espressif__esp_xiaozhi/0.1.2/001-release-dynamic-audio-task-stacks.patch)修复官方动态／PSRAM 任务创建后仍调用普通 `vTaskDelete` 的不匹配。正常退出和无效参数退出统一匹配 `vTaskDeleteWithCaps`；静态模式仍使用原 API。真实退出函数的 host 回归覆盖 32 次释放、空参数和静态模式；同一 [005/15](../../.scratch/005-m5-application-ecosystem/issues/15-enable-xiaozhi-voice-conversation.md)持有真机会话及反复 Home 门槛。

Lib Utils 0.8.2 的[定时器生命周期补丁](espressif__brookesia_lib_utils/0.8.2/003-serialize-timer-scheduling-and-cancellation.patch)修复周期回调决定再次排队后，取消／移除任务并释放 timer 导致的 LoadProhibited。每个任务拥有短时 timer 锁，统一保护排队、取消、暂停／恢复、restart 和 shutdown；回调运行时不持该锁。timer／promise 完成初始化后才发布 task handle，已取消或关闭中的任务不重新排队。执行真实 delayed／periodic／cancel／remove 方法的并发回归，在 expiry 与 async_wait 之间强制取消，原版失败、修复通过；普通镜像联合 App／语音退出由 [005/15](../../.scratch/005-m5-application-ecosystem/issues/15-enable-xiaozhi-voice-conversation.md)持有。

ESP-SR 2.4.4 的[模型头校验补丁](espressif__esp-sr/2.4.4/001-reject-empty-or-invalid-model-header.patch)在读取模型数量后、分配与 mmap 前拒绝空、读取失败或超出分区头预算的模型；失败不增加初始化引用计数。真实 mmap／init 方法的 host 回归覆盖零模型、擦除、短分区、读取失败、超预算、缺失分区、设备残留旧镜像头以及有效模型复用。不会写模型分区；未请求 WakeNet／命令检测的官方 AFE 可以继续无本地模型运行。故障回溯与真机门槛由同一 [005/15](../../.scratch/005-m5-application-ecosystem/issues/15-enable-xiaozhi-voice-conversation.md)持有。

HAL 0.8.4 的[活跃播放关闭回调补丁](espressif__brookesia_hal_adaptor/0.8.4/003-separate-playback-callback-from-close-lock.patch)把 playback callback 存储与 acquire／release 生命周期锁分开。关闭仍串行等待真实音频 worker；最终 STOPPED 回调可完成，不等待关闭线程持有的生命周期锁。真实 close／release／event 方法的并发主机回归和小智播报中 Home 真机回归由同一 [005/13](../../.scratch/005-m5-application-ecosystem/issues/13-xiaozhi-and-launcher-performance.md)持有。

已接受 [Runtime JS 0.8.3 异步栈配置补丁](espressif__brookesia_runtime_js/0.8.3/001-configure-async-stack.patch)，由 [ADR-0015](../../docs/adr/0015-runtime-async-stack-patch-exception.md)限定授权。manifest 锁定完整原始源码与补丁 hash，上游问题尚未提交。构建与设备验收状态以 [008/04](../../.scratch/008-m8-app-contract/issues/04-resolve-runtime-async-stack-overflow.md)为准。

Core 0.8.4 的 failed-stop、键盘 Owner 与 queued event 补丁依据 [ADR-0016](../../docs/adr/0016-maintained-upstream-fixes.md)维护；源码回归、完整构建与尚待设备门槛见 [005/07](../../.scratch/005-m5-application-ecosystem/issues/07-isolate-runtime-keyboard-results.md)。

Lib utils 0.8.2 的 [worker dispatch 公平性补丁](espressif__brookesia_lib_utils/0.8.2/001-bound-worker-dispatch.patch)限制连续 ready queue 的单轮调度并给 Idle 留运行窗口；源码与补丁 hash 由 manifest 固定。真实 worker block 的主机回归已通过，Store 安装无 watchdog 的设备门槛仍由 [005/06](../../.scratch/005-m5-application-ecosystem/issues/06-adopt-online-store-stability-fix.md)持有，证据见[生命周期记录](../../.scratch/005-m5-application-ecosystem/records/2026-10-04-launcher-and-lifecycle-acceptance.md)。

HAL 0.8.4 的 HTTP cooperative cancel 与 playback-only 差异当前属于候选，尚不在默认产品构建清单；状态分别见 [005/06](../../.scratch/005-m5-application-ecosystem/issues/06-adopt-online-store-stability-fix.md)与 [004/04](../../.scratch/004-m4-device-capabilities/issues/04-adopt-playback-only-audio.md)。

Core 的 embedded-theme GUI task seam 与 Settings 0.8.3 的当前圆屏内容布局候选见 [004/05](../../.scratch/004-m4-device-capabilities/issues/05-fix-settings-controls-rendering.md)。Settings 布局仅加入 audio-candidate，未采纳为默认生产补丁。

## 组织约定

```text
patches/
└── <registry-component>/
    └── <upstream-version>/
        ├── manifest.json
        ├── 001-<change>.patch
        └── 002-<change>.patch
```

例如 registry component 可使用 `espressif__brookesia_runtime_js`。采用上述布局。[独立副本准备工具](../../scripts/firmware/prepare_patched_component.py)已实现完整源码与补丁 hash 校验、准确应用及失败清理；独立构建入口为 [build_patched_firmware.py](../../scripts/firmware/build_patched_firmware.py)，使用工程副本及 Component Manager override_path，原始缓存和 lock 不参与写入。工具验证见[008 记录](../../.scratch/008-m8-app-contract/records/2026-10-03-patch-preparation-tool.md)。

manifest 记录原始组件版本、源码 commit/hash、按顺序排列的补丁文件及其 hash、上游问题/修复链接、负责验证的工作票和删除条件。未提交的问题应链接本地草稿并明确该状态。

正式应用工具应先验证上游身份，再复制到构建目录、准确应用补丁，并让构建使用该副本。版本/hash 不匹配或补丁不能准确应用时停止，不做模糊匹配；副本和中间产物不提交 Git。工具实现与 Component Manager override 的验证由实际接入工作票负责，不把这里的目标流程写成已实现。

依赖升级时一起审查版本锁、补丁适用性及对应测试/构建/真机证据；上游提供等价修复后移除本地补丁。源码差异持续扩大时，单独决定是否维护 fork，不在补丁目录内复制整套组件源码。

Display 0.8.2 的同一输出背光与刷屏 IO 串行化补丁属于 `display-candidate`，实际 API 并发回归、完整构建和 100 次纯滑块自动设备压力验证已通过，剩余实体触摸观察由 [004/08](../../.scratch/004-m4-device-capabilities/issues/08-fix-settings-brightness-freeze.md)持有；不得因主机通过宣布设备修复。

## 默认组合合入

2026-10-03 用户授权将已验收候选纳入默认产品构建。默认 `production` 组合包含 Runtime/Core、HAL HTTP 与 playback-only、Settings 圆屏布局、Display IO 串行化，以及 Board Manager I2S teardown 修复。`baseline` 保留此前 Runtime/Core 组合，其他显式 candidate 为诊断子集。Audio 补充依赖仍准确绑定相邻清单中的版本/hash，原 registry lock 不改写；生产构建同样校验 Recorder/AFE 关闭与 DAC 输出格式。此次完整构建、设备与视觉结果见 [收尾记录](../../.scratch/004-m4-device-capabilities/records/2026-10-03-production-followup.md)，未通过的门槛不能因默认值已切换而关闭。

### Store Service completion 的 App Owner 边界

Store 0.8.2 的 `004-owner-service-completions.patch` 将 Storage/Device/HTTP 异步返回与 HTTP events 的 App 状态处理移到 App timer。每个 Running Instance 持有独立 mailbox，退出先关闭并丢弃结果；重进创建新 mailbox，旧 Service callback 不能访问已停止会话。真实 cached-index 回调主机回归验证旧版 worker 访问失败、候选 Owner 交接、停止丢弃与重进隔离。移除条件为锁定上游提供等价 Owner delivery 并通过相同主机与快速 Store 退出设备回归。故障与设备判定见[应用生态验收记录](../../.scratch/005-m5-application-ecosystem/records/2026-10-04-launcher-and-lifecycle-acceptance.md)。

Store `005-avoid-local-scan-during-remote-refresh.patch` 保留 startup/Local 的扫描，远程 index Refresh 不启动重复本地扫描；真实 deferred-refresh 方法回归覆盖三个 tab。Core `006-bound-recursive-package-removal.patch` 仅将递归目录删除的等待期限设为 30 秒，stat/read 保留 5 秒，并继续核对删除后目录不存在。主机真实 filesystem helper 覆盖慢后端、超出上限、目录仍存在与空路径拒绝；设备完整删除仍需独立门槛，不把延长期限等同成功。上游提供等价边界并通过相同回归后移除。

Storage 0.8.3 的 [单次元数据读取补丁](espressif__brookesia_service_storage/0.8.3/001-read-file-metadata-once.patch) 将每条类型／时间／大小查询合并到同一次 VFS lookup，保留 file-clock 和软链接语义；Core `007-count-package-admission-in-startup.patch` 将包校验纳入真实启动计时。完整校验保留，性能设备门槛由 [005/10](../../.scratch/005-m5-application-ecosystem/issues/10-reduce-runtime-startup-blocking.md) 持有。移除条件为上游等价实现通过相同元数据语义、包信任和设备性能回归。

GUI LVGL 0.8.5 的 [图片内部滚动补丁](espressif__brookesia_gui_lvgl/0.8.5/001-skip-relative-layout-for-image-offsets.patch) 已纳入 `production`，`gui-candidate` 保留为同组合入口。仅 ImageOffsetX/Y 更新跳过相对布局重算，图片来源、文字、几何与混合更新保持原路径。真实 Backend 方法 host 回归覆盖两条路径；原包性能、截图和 Apps 真机联合门槛已通过；持续流畅性仍由工作票验收。结果由 [005/10](../../.scratch/005-m5-application-ecosystem/issues/10-reduce-runtime-startup-blocking.md) 持有。

Core [同域队列候选](espressif__brookesia_system_core/0.8.4/010-share-task-domain-strands.patch) 已纳入 canonical manifest，同目录 `scheduler-candidate.json` 保留相同补丁组合；显式 `--patch-set scheduler-candidate` 在 GUI 候选上使 App／App Input、GUI／GUI Input 各共用一个 strand，保留原 gate 和 callback context。真实 group callback 与 Boost strand 回归验证独立 timer 的进展；原包压力、截图和完整 Apps 回归通过后已纳入默认 manifest。显示缓冲实验另用 `--display-buffer-height 80 --display-single-buffer`，保持默认 40 行及原双缓冲选择；实验配置和源码身份随 patch-inputs 保存。两项状态由同一工作票持有。

Core 图片来源背压候选 [011](espressif__brookesia_system_core/0.8.4/011-bound-image-source-dispatch.patch) 已纳入默认 manifest：`SetViewSrc` 通过既有同步 GUI Owner 队列按序完成，避免周期 App 在 GUI 变慢时持续创建任务／promise。真实 call site 和 run_task_sync 模板覆盖慢 Owner、有界任务、全序更新与错误传播；真机 mutex 分配 abort 回溯及候选状态仍由 005/10 持有，原包联合回归通过后已纳入默认 manifest。

Core 0.8.4 新增[Overlay 请求有效性查询](espressif__brookesia_system_core/0.8.4/013-overlay-request-validity.patch)，由 [019/03](../../.scratch/019-system-shell-remediation/issues/03-arbitrate-overlay-input-and-deadlines.md)持有。该隔离实施候选只读取真实请求 Owner，不复制队列；查询在恢复呈现或提交结果前执行，调用不得持有 GUI 锁。源码/构建证据与尚待集成和真机门槛见[实施记录](../../.scratch/019-system-shell-remediation/records/2026-10-04-overlay-isolated-implementation.md)，不以加入 manifest 代替设备验收。


Core 019 整合补丁 012–014 分别处理 partial initialization 清理、真实 Overlay 请求有效性与 staging 同步删除旧成员；前序性能补丁保留，准确应用/hash、源码回归及尚未完成门槛见[019 联合整合记录](../../.scratch/019-system-shell-remediation/records/2026-10-05-joint-integration.md)。

esp_lv_decoder 0.4.3 的[不透明 PNG 原生 RGB565](espressif__esp_lv_decoder/0.4.3/001-copy-opaque-png-as-rgb565.patch)只在首次解码确认所有 alpha=255 后转换，透明 PNG、非 RGB565 display 与分配失败保持原格式；同时按实际 stride 解码 padding 行。Lib utils 的[空闲 worker 即时唤醒](espressif__brookesia_lib_utils/0.8.2/002-wake-idle-worker-on-task.patch)保留逐项 dispatch 和 busy 后 1 ms 让步，空闲等待可被入队任务/到期 timer 唤醒。真实调用点回归、单变量真机测量与最终组合结果见[延迟优化记录](../../.scratch/005-m5-application-ecosystem/records/2026-10-05-runtime-timer-latency.md)，不得以 host 通过代替性能及 watchdog 门槛。


esp-boost 0.6.0 的[ESP 条件变量等待时钟补丁](espressif__esp-boost/0.6.0/001-match-esp-condition-wait-clock.patch)匹配该平台默认 CLOCK_REALTIME 的条件变量初始化，保留其他平台的原路径。它是即时唤醒候选在真机启动失败后定位的前置修复；原失败、真实等待方法 RED/GREEN、设备结果和采纳边界同见延迟优化记录。

Core 的[诊断输出降优先级](espressif__brookesia_system_core/0.8.4/017-lower-timer-diagnostic-priority.patch)在 ESP 上只在输出 timer 样本期间将当前 worker 降至最多 2，并通过作用域 guard 恢复原优先级。诊断仍保留有界发布与丢窗标记；真实输出调用点回归验证输出期间优先级及结束后恢复，性能收益仍须原包真机测量。

Decoder 的[二值 alpha PNG 原生绘制](espressif__esp_lv_decoder/0.4.3/002-copy-binary-alpha-png-as-rgb565a8.patch)只在 RGB565 display、alpha 全为 0/255 且 LVGL 支持 RGB565A8 时转换，alpha 平面保持半个 RGB stride；半透明、未启用目标格式和分配失败均保留 ARGB8888。原包无需改变，格式、padding、像素与 fallback 回归通过后仍须真机计时和截图验收。

Core 的[有界异步 source 队列](espressif__brookesia_system_core/0.8.4/018-bound-asynchronous-image-source-queue.patch)取代 011 的同步等待，恢复上游 SetViewSrc 的异步提交契约：返回值表示接受，实际 GUI source 失败仍由 GUI Owner 报告。每个 App/document 待处理批次最多 8 项、32 KiB，保留所有已接受 source 的 FIFO 顺序，不合并或静默丢弃换帧；最多一个批次执行、一个后继 GUI task 排队。队列满或调度失败立即拒绝；停止／卸载／重启（包括保留同一 DOM）撤销旧 buffer。旧实例不能把已排队内容应用到新实例。回归同时验证非阻塞、容量、顺序、失败和撤销，仍须原包计时与长期压力验收。
