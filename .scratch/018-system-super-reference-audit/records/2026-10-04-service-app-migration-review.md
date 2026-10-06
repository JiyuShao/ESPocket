# Service 与 App 迁移参考核查 — 2026-10-04

本记录保存当前官方固定源码与 ESPocket 的只读比较，建议不是新任务、已接受产品决定或功能验收。未改 firmware/依赖、未构建、未操作设备。

## 来源与当前边界

官方上游：`espressif/esp-brookesia` `e937455b0db1a3e873b1da61d6d13652f3dcc7e2`，本地只读副本 `/tmp/espocket-brookesia-review-20261004`。所有上游源码链接固定提交；GitHub Web 读取该 SHA 的源码页返回 cache miss，源码结论以已克隆的官方提交逐行读取为依据。官方在线 [Files 文档](https://docs.espressif.com/projects/esp-brookesia/zh_CN/latest/app/files.html)及 [Wi-Fi 文档](https://docs.espressif.com/projects/esp-brookesia/zh_CN/latest/service/wifi.html)可访问，仅补充公开组件职责，不用 latest 文档推断锁定版本兼容。此前全 examples 调查见[记录](../../009-ai-native-foundation/records/2026-10-04-brookesia-examples-review.md)。本轮核查五个 Service examples、Settings/Store/Files Native App 与 Chatbot 的分层借鉴价值；不将示例的 `0.8.*` 源码 override 直接视为当前 Registry 精确版本兼容。

本项目已有官方 Service Manager/Helper、Settings/Store、Wi-Fi NVS 重连和 SNTP、Storage filesystem、production playback-only；[004/02](../../004-m4-device-capabilities/issues/02-prove-keyboard-wifi-and-status.md)、[004/04](../../004-m4-device-capabilities/issues/04-adopt-playback-only-audio.md)、[004/07](../../004-m4-device-capabilities/issues/07-fix-audio-playback-teardown.md) 已完成。[005/07](../../005-m5-application-ecosystem/issues/07-isolate-runtime-keyboard-results.md) 也已 resolved，不再作为本轮新增工作。[005/09](../../005-m5-application-ecosystem/issues/09-allow-unsigned-developer-installation.md) 当前为 needs-info；developer package policy 正由其他工作维护，本记录不改其 scope/条件。

## Service：值得提取的具体候选

| 候选 | 已有覆盖与具体增量 | 谁持有事实与执行 | 现有工作归属 |
|---|---|---|---|
| 手机 SoftAP 配网 | 已有 Settings Wi-Fi键盘/扫描及NVS重连；新增从设备发起手机配网，显示SSID/连接入口，成功退出、主动取消和超时 | Wi-Fi Service 持有STA/AP、凭据和配网执行；产品持有何时进入、屏幕反馈和退出决策 | 尚无单独配网票；作为独立产品扩展先设计，不把已完成004/02重开 |
| HTTP request终态与取消观察 | 已有Store与HTTP；提取request_id关联的state/event collector、取消后GetRequestState及Canceled event双检查、retry/failure和BodyTooLarge/file-size验证 | HTTP Owner持有request状态、取消实现和TLS worker；Store只持有其请求并呈现结果 | [005/06](../../005-m5-application-ecosystem/issues/06-adopt-online-store-stability-fix.md)，不另立同义稳定性票 |
| Audio队列与中断边界 | 已有真实播放/音量/Home停止和I2S清理；新增 append、立即interrupt、延时interrupt、loop、pause/resume的场景参考 | AudioPlayback Owner持有player/queue；App或Assistant持有自己的播放意图和退出范围 | 未来播放/Assistant实际需求的独立增量；不重复已完成004/04、07 |
| 麦克风loopback→AFE前置 | playback-only仍不覆盖录音；参考先录10秒PCM/OPUS再decode、随后VAD/WakeNet事件，确认Recorder和model资源 | Audio/Board/Codec Owner持有硬件、format、录音和AFE；Assistant仅消费会话音频 | [009 Assistant](../../009-ai-native-foundation/spec.md)的语音集成前置，尚未独立分配录音验收票 |
| Storage typed配置与兼容迁移 | 已有Storage service及filesystem读取；Card仍直接raw NVS，可评估type-safe配置与namespace/type/error回归 | Storage Owner持久化；CardConfigurationStore/未来Assistant配置Owner持有schema、默认值和迁移规则 | 后续配置维护候选，暂无Storage重构票；不能因有helper自动全量迁移 |
| 开发诊断的有限订阅 | 已有USB开发模式及MemoryProfiler；可提取service/function/event introspection和受控事件订阅，补thread/time snapshot | 诊断session持有binding/SignalConnection/采集预算；真实Service仍持有状态 | [019/07](../../019-system-shell-remediation/issues/07-design-development-diagnostics.md)与[019/13](../../019-system-shell-remediation/issues/13-evaluate-build-and-profiler-tools.md) |

### Wi-Fi：提取流程而不是完整 demo 启动序列

[main.cpp:474](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/wifi/main/main.cpp#L474) 创建 SoftAP 和 general event monitors，启动配网并读取SSID/password，等待连接，最后TriggerSoftApProvisionStop；[main.cpp:592](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/wifi/main/main.cpp#L592) 另有 ResetData 演示。前者能成为产品入口参考，后者会清凭据，不能自动跟在生产启动流程后。Wi-Fi事件订阅以SignalConnection维持，成功/取消/超时都应由产品入口释放其订阅并停止自己的配网。

[wifi_provisioning.cpp:49](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/agent/chatbot/main/modules/wifi_provisioning.cpp#L49) 根据GetConnectedAps决定重连或SoftAP，Connected后停止配网；它也将STA Disconnected直接切成SoftAP。移植时需先定义短暂断网/自动重连/首次未配置/用户主动配网的不同路径，避免原有断网触发新配网界面。现有Settings设备上手路径已获验收，不能以新候选否定既有覆盖。

### HTTP：真正取消在 HTTP Owner 内

[main.cpp:543](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/http/main/main.cpp#L543) 提交RequestAsync得到request_id，再调用HTTP CancelRequest，等待RequestState::Canceled，同时按同一ID观察RequestCanceled及ErrorCode::Canceled。它能验证“已提交取消”与“实际终态”的区别，不能将Helper提交成功、UI关闭或同步等待超时当成已取消。

[main.cpp:675](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/http/main/main.cpp#L675) 设置HTTP500/retry_count=2/timeout，按最终response.error选择Completed或Failed事件校验。[main.cpp:811](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/http/main/main.cpp#L811) 验证下载大小限制。迁移价值主要是测试场景与观察方式；需要005/06继续覆盖活动TLS handshake并发边界、无重复终态及具体锁定修复。本例依赖外部Echo服务、含测试级网络重试；“retry demo通过”不足以证明产品请求没有重复副作用，CancelRequest与自然完成存在竞争，不能要求所有快请求必定Canceled。TLS Skip演示不能成为生产默认。

### Audio：queue、录音与生命周期分开评价

[main.cpp:167](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/audio/main/main.cpp#L167) 以interrupt=false追加播放且loop_count=5，再立即中断；源码显式检查立即interrupt不产生短暂Idle。[main.cpp:226](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/audio/main/main.cpp#L226) 测多URL/缺失文件与延时interrupt，后者允许第一段结束到新段开始出现Idle。[main.cpp:295](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/audio/main/main.cpp#L295) 测pause/resume/stop。这些边界比只展示Play按钮更有参考价值，但只有需求用到时才新增验收。

[main.cpp:350](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/audio/main/main.cpp#L350) 测PCM/OPUS/G711A encode→decode，录不到数据会跳过播放；跳过不能当成麦克风通过。[main.cpp:506](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/audio/main/main.cpp#L506) 测AFE事件，需要Recorder支持和唤醒模型。不能直接启用样例encoder/decoder/AFE完整配置覆盖production的playback-only约束，也不能重跑004/07已接受的I2S结论冒充新工作。

### Storage：type-safe API 不保证 raw NVS 字节兼容

[main.cpp:343](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/storage/main/main.cpp#L343) 用save_key_value/get_key_value测试基础类型、string/vector/struct；后续namespace隔离、缺key及错误类型检查值得复用。

本项目[system_cards.cpp](../../../firmware/components/espocket_system/src/system_cards.cpp) 直接nvs_set_str/commit写 `espocket/cards_v1`，读取缺key返回空、限制大小16385，错误与成功分开。锁定[Storage helper](../../../firmware/managed_components/espressif__brookesia_service_helper/include/brookesia/service_helper/system/storage.hpp) 对std::string也做JSON serialization/deserialization；因此不能在同一个raw JSON key上直接替换为typed string getter/setter。迁移需先验证旧数据读取、字符串编码、namespace/key、缺失/损坏/写失败语义，并选择兼容读或版本迁移方案。helper也不构成App私有数据授权或Provider秘密安全方案。

### Console：参考订阅管理，重设session边界

[cmd_service.cpp:27](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/console/components/cmd_service/cmd_service.cpp#L27) 用全局SubscriptionInfo保存service/event/SignalConnection；[cmd_service.cpp:364](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/console/components/cmd_service/cmd_service.cpp#L364) 防重复并清无效订阅，取消时erase销毁连接。[cmd_service.cpp:323](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/console/components/cmd_service/cmd_service.cpp#L323) 的svc_stop只release/erase binding，没有在该函数显式清理同Service的subscription集合。因此移植时需要诊断session拥有连接、退出/关闭开发模式完整清理，不照搬常驻全局订阅。

样例callback逐项打印全部event参数，可能泄露输入/网络/凭据类内容，也会与USB合成输入协议争用stdout。产品需要允许的事件/字段、频率预算与脱敏；不能因采用只读诊断把通用svc_call、延迟/周期写操作或命令历史开放到普通模式，也不能修改现有USB命令范围。这里不是重新解决005/07，Runtime原隔离已经完成。

## 取舍

优先是HTTP稳定性票中的观察/回归参考，以及有明确用户价值的手机配网。维护增量是有限诊断和配置兼容方案；Audio队列按使用需求推进，录音/AFE按Assistant语音前置推进。所有Service功能沿真实Owner执行，不通过复制示例另建一套Wi-Fi、音频或配置事实。

## App：现有组件、新增组件与实现参考

| 对象 | 固定源码确认的可借鉴内容 | 本项目的实际增量与归属 |
|---|---|---|
| Files | 从 Core StorageLayout 构建内/外卷，目录列表和容量、rename/delete 的键盘/确认流程，首次刷新延后与退出清理 | **新增官方 App 候选**；归 [019/11](../../019-system-shell-remediation/issues/11-design-files-integration.md)。依赖尚未进入产品；先确定可见目录、只读/修改、Page/Back 和圆屏资源范围；用户内容预览并非已有能力 |
| Settings | Service 可用性/binding 检查、禁用不可用页面、异步结果 generation、偏好保存失败后的恢复、语言资源与生命周期释放 | **官方 App 已集成**；这些 generation/binding 模式在锁定 Settings 0.8.3 也已存在，不是整包待迁移。新语言/主题产品能力分别归 019/09、10；真实缺陷在 Owner 内修复 |
| Store | 缓存启动、延后加载、异步 generation、request_id 终态关联、停止下载/刷新与释放图标和 binding | **官方 App 已集成**；稳定性与安装闭环继续归 005/03、06、08、09。值得核对/提取回归和 App 开发参考，不复制 downloader/Installer，也不将缓存视为 installed truth |
| Chatbot example | general_services、wifi_provisioning、ai_agents、display 的模块划分；Agent Manager 的 activate/start/stop、会话文本/语音事件与 MCP tool callback | **Assistant 的实现参考**，不是现成 ESPocket App；归 009。可复用 provider 接法与事件映射，产品入口、授权、PWR 和 UI lifetime 仍沿 ESPocket 契约 |

### Files 是可接入的组件，仍需产品适配

[lifecycle.ipp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/app/brookesia_app_files/src/app/lifecycle.ipp)声明 Native App、语言名称与 GUI 资源，读取 Core StorageLayout，延后首次刷新；stop 使容量 generation 失效，停止 timer、取消文件操作并释放 UI/Storage binding。[volumes.ipp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/app/brookesia_app_files/src/storage/volumes.ipp)列出可用内/外卷并检查操作目标是否位于当前卷根内；[operations/file.ipp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/app/brookesia_app_files/src/operations/file.ipp)用键盘重命名、确认删除，延后提交实际操作。文本读取见 [files_app.cpp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/app/brookesia_app_files/src/files_app.cpp)。

这些代码降低接入成本，但挂载卷可见与 ESPocket 用户可见目录不是同一决定，卷内路径检查也不替代 App 私有数据/包目录的产品边界。目录上一级操作、Browser/Operations 页面 Back、Root 无 Back 和 PWR 需要明确适配；同步目录读取/文件操作不自动满足慢操作期间的 PWR 目标。文件类型图标不证明已有完整音视频播放器。当前不批准开放内部数据或默认启用写操作。

### Settings / Store 的价值还包括 App 编写方式

[Settings service/services.ipp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/app/brookesia_app_settings/src/service/services.ipp)在 release_wifi_service 时推进 generation；后续异步偏好/连接结果检查 generation 和当前状态。[Store lifecycle.ipp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/app/brookesia_app_store/src/app/lifecycle.ipp)在 start/stop 改变 async_generation，延后 startup load，stop 取消操作、请求、timer、事件、UI 和各 Service binding。项目锁定的 [Settings services](../../../firmware/managed_components/espressif__brookesia_app_settings/src/service/services.ipp)与 [Store lifecycle](../../../firmware/managed_components/espressif__brookesia_app_store/src/app/lifecycle.ipp)已有这些路径。

可在后续真实 App 的开发参考中提炼如下规则，而不是再建统一 App manager：

1. 生命周期持有自己的 Service binding、订阅、timer 与临时 UI；释放 binding 不自动证明全部在途 callback 安全。
2. 区分操作 identity/generation 与 Running Instance，过滤旧结果；generation 检查不能单独证明捕获裸 this 的 callback 没有释放后访问。
3. 先给出初始可见反馈，再分批处理实际 I/O；延后到 timer 不等于变为非阻塞 I/O。
4. 请求、失败、已提交和终态分开呈现；App 退出后的业务结果由实际 Owner 确认。
5. GUI template、资源、i18n 与业务处理分开组织；方屏默认尺寸仍需圆屏适配，语言资源存在仍需字体覆盖。

官方 Settings 导航继续按 [ADR-0012](../../../docs/adr/0012-official-settings-keeps-its-navigation-owner.md)适配其真实事实源。中文资源与即时主题不因上游有代码就自动扩大现有验收范围。上游部分 Service 回调直接操作 GUI，不能将所有官方 App 归纳成「回调统一转 App task」。

## 补充后的推荐顺序与范围边界

- 继续现有 HTTP/Store 稳定性及 009 Assistant 工作，分别提取 HTTP 场景与 Chatbot provider/事件参考，不另立同义任务。
- 新的独立产品设计优先考虑手机配网与 Files；两者分别解决圆屏输入 Wi-Fi 凭据和文件操作的真实使用成本。
- 麦克风/codec loopback 再到 AFE 是语音接入的新增设备前置；播放 queue 按 TTS/提示音等具体需求定义，不重开已完成 playback/I2S 验收。
- 有限 Console/Profiler 已有 019/07、13 归属；Storage typed 迁移是维护候选，先证明兼容收益再扩大范围。

019 现有票没有承诺手机配网、录音输入或 Card Storage 迁移；本轮将其作为有证据的候选列出，没有在用户未确认功能行为时自动改为已接受实施范围。018 原 System/Shell 审计完成状态保持，本记录是后续 Service/App 补充调查。

## 后续更细核查的修正

2026-10-04 用户启动新一轮计划访谈后，确认上述「文本读取」仅指辅助代码，Files 的非目录点击实际进入 Operations，不能概括为用户可用内容预览。另确认 Files 缺公开 root allowlist/read-only/目录导航快照 seam，默认全卷可见；手机配网在锁定 HAL 已有网页，但会断开原网络且不保证取消回滚。后续具体事实与访谈见 [019 计划记录](../../019-system-shell-remediation/records/2026-10-04-service-app-extension-plan.md)，新配网计划归 [019/14](../../019-system-shell-remediation/issues/14-design-phone-wifi-provisioning.md)。
