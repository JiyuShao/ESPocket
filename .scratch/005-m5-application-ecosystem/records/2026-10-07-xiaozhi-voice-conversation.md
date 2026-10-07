# 完整小智语音对话修复

日期：2026-10-07。范围由 [15](../issues/15-enable-xiaozhi-voice-conversation.md)持有；用户明确要求完整修复，正式录音、真实上传与回复播放纳入范围。此前的[官方硬件验证](2026-10-07-official-microphone-verification.md)是已完成前置。

## 可重复故障与修正

原普通镜像 `0203fb1fc` 的服务器激活已被接受，实际 Start 失败于 `Failed to get audio encoder interface`，继而无法打开 capture DataFlow。`/private/tmp/espocket-xiaozhi-conversation-ready.py /private/tmp/espocket-xiaozhi-voice-baseline` 返回失败，不能将激活成功称为语音对话成功。

独立产品构建启用官方 HAL Recorder、AudioEncoder0 与 AFE，ES7210 实际采集 MIC1/MIC2，mask `0x3`，16 kHz／双通道／16 bit／`MM`，30 dB 增益且无逐通道 0 dB 覆盖。生成配置先准确转换，reconfigure 后复核；意外 ADC 芯片、通道 mask 或音频格式漂移拒绝构建。已有 Player／Agent DataFlow、Opus 与小智协议 Owner 保留，不创建另一套录音或云端实现。CodecRecorder 编译沿用已有 IDF/Picolibc `noreturn` 兼容头，不放宽 warnings。

首个普通候选 `f354b42ba` 完整构建和 app-only 烧录／hash 验证／启动成功，但 AFE 引入内部静态数据后，旧 Wi-Fi 配置只能分配 7/10 个静态 RX 缓冲，真实驱动初始化失败；进入 AI Chatbot 没有建立音频通道。此镜像不作为修复通过证据。BIN SHA-256 为 `cd678d3e1b517ca3032c57adffebc88c8524a84caeb3e4944a25e6750c3a288b`，ELF SHA-256 为 `f354b42bae52040429ba256103eb1ebbacb9725613af5987640ef193dcff23d8`，启动与 readiness 失败分别保留在 `/private/tmp/espocket-xiaozhi-voice-flash1.boot.log`、`/private/tmp/espocket-xiaozhi-voice-ready1.log`。

正式语音预算改用官方小智动态音频任务／PSRAM 配置，保留 8 KiB 栈大小，避免常驻内部栈；Wi-Fi 静态 TX 从 16 调为 8，每个约 1.6 KiB，仍高于 TX BA window 6；静态 RX 保持 10。没有缩小线程栈或关闭网络错误。

源码核对同时发现 XiaoZhi 0.1.2 创建动态任务使用 `xTaskCreatePinnedToCoreWithCaps`，正常和异常参数退出却调用普通 `vTaskDelete`。IDF 要求匹配 `vTaskDeleteWithCaps`；新增精确补丁匹配动态退出 API，静态模式保持原释放。真实退出函数的 host harness 在原版积累 34 个 8 KiB 未释放栈，修复后 32 次正常退出及两个异常参数路径全部回收；静态模式同样通过。原始 managed_components 不修改，manifest 锁定完整文件库存、补丁 hash、上游 commit 和移除条件。

## 当前验证

最初完整 `scripts/check.py` 通过：152 个跨模块 host tests，1 个已有 skip，其它组件／样例检查通过。新增配置回归为 22 项；音频任务释放回归单独通过。最终普通镜像、完整声学对话、反复退出、联合 App 回归与最终合并仍待本轮后续证据，不以这些主机结果关闭设备门槛。

加入小智任务释放后，完整 `scripts/check.py` 再次通过：153 个跨模块测试，1 项原有 skip；随后补强 Opus／栈与 Wi-Fi 预算配置约束的 22 项回归通过，282 份 Markdown 检查通过。日志分别为 `/private/tmp/espocket-xiaozhi-voice-final-checks.log`、`/private/tmp/espocket-xiaozhi-voice-stage-final.log`、`/private/tmp/espocket-xiaozhi-voice-docs-final.log`。

第二个普通候选 `a5c32e607` 完成。BIN SHA-256 `e31297d356093322b54818fe5a4d7188356f6969d6c23e2e8f1c1877c9accff5`，ELF SHA-256 `a5c32e607850ecd9ddc0cc4e5d7dd3f169a1d3222d1860ab17697b1f86276f1b`，精确 patch-inputs SHA-256 `af492b3a9d661eb3a1715d8e1d825d7419f392d631cac4426e82ff37610d87db`。16 个受维护组件从原始源与 Git 中补丁重新准确准备，文件库存与实际选中副本完全相同；110 个产品源码／资源／生成配置文件逐文件摘要一致，main 的精确 pin／override manifest 亦重建匹配。Registry 版本/hash、存储、性能、语音、字形预算与关闭的诊断 profile 复核通过。独立工程为 `/private/tmp/espocket-xiaozhi-voice-candidate-20261007`，该候选构建日志为 `/private/tmp/espocket-xiaozhi-voice-final-build.log`。该候选后来在模型加载阶段失败，详见后文，不作为语音成功或最终镜像证据。

## 模型加载真机故障

`a5c32e607` 是第二个普通候选，后续不作为最终成功镜像：app-only 写入／hash 校验／启动通过，Wi-Fi 正常，启动内部 heap free/largest 为 25,091/14,848 bytes，PSRAM 为 6,299,204/6,291,456 bytes。但进入 AI 后在 `recorder_setup_afe_config → esp_srmodel_init → srmodel_mmap_init → srmodel_load:138` 发生 StoreProhibited，真实 readiness 失败，不能宣称语音可用。该回溯由匹配 ELF 的 addr2line 解码。

只读 `0x10000` 的 4 字节分区头得到 `e9 06 02 5f`：模型分区残留了旧 App 镜像头，而非假设的全零模型头。ESP-SR 把这些字节作为模型数量使用，巨大分配失败后写入空指针。新增 ESP-SR 2.4.4 精确补丁在分配／mmap 前检查头部读取、零数量和分区头预算，不增加失败初始化的引用计数；有效模型复用保持原语义。官方 AFE 未请求 WakeNet／命令检测时允许模型为空，本修复不伪造模型或刷写空模型以掩盖解析缺陷。

真实 mmap／init 方法的 host 回归覆盖 7 类无效头／分区各 4 次，以及有效模型和复用，原版失败、补丁后通过。首次 harness 的有效模型样本忘记清空上一无效头的剩余字节而失败，修正 fixture 后重跑成功；未把那次 fixture 失败当成产品缺陷。日志为 `/private/tmp/espocket-xiaozhi-model-{red,green}.log`，物理头只读证据为 `/private/tmp/espocket-xiaozhi-model-header.bin` 与对应读取日志。新镜像与完整对话仍待后续验收。

## TLS 真机内存故障

第三个普通候选 `6fea93d9b` 完整构建、17 个组件／110 个产品文件的精确 proof、app-only 写入／hash 校验和启动通过。BIN SHA-256 为 `8dd37efbd290aebfcfaf7b830b083b8dc361c32072a2c6c4f0add1e158e5a015`，ELF 为 `6fea93d9b217410e18b33835467a38337ce0823ee93e8018fd2de5da9e228127`，当时 proof 为 `447868f6215f35d4f98460e31aede99b1b1a3519d06732373ae1549fa1678084`。完整主机检查通过 154 项（1 项原有 skip），日志为 `/private/tmp/espocket-xiaozhi-voice-model-checks.log`。

实际 AFE 双麦克风 16 kHz 前端成功创建，Recorder 和 Opus encoder 均启动成功，退出时 Recorder 正常关闭，没有再次发生模型解析 panic。但随后的 MQTT TLS 连接在 `mbedtls_ssl_setup` 返回 `-0x008D`，对应 IDF 的 PSA_ERROR_INSUFFICIENT_MEMORY（-141）；此镜像仍没有建立音频通道，不作为完整对话成功证据。旧 `CONFIG_MBEDTLS_INTERNAL_MEM_ALLOC` 明确强制分配内部 RAM，SSL 16 KiB 入站／4 KiB 出站缓冲与采集竞争。

产品改用 ESP-IDF 已支持的 `CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC`，保留缓冲长度、密码与证书验证，配置回归拒绝退回无效的内部分配。证据为 `/private/tmp/espocket-xiaozhi-voice-ready-model1.log`；修正版完整对话与监听／播放中退出仍待下文验收。

## 语音通过与中文显示故障

第四个普通候选 `599f33666` 修复 TLS 后，真实小智音频通道、Recorder 打开／关闭及 Listening Home readiness 通过，用户明确确认设备语音正常。BIN SHA-256 为 `d8723f8e75d5ea9570bde34dc1b878c4bd0b2d199879704ec999736dc46b58f0`，ELF 为 `599f336666c06679ff9cfbe0c3d2ff9b7e4c2094bee413eead744ff12f1865d2`，精确 proof 为 `2d496491691df7a5a5e2de8590c4d18796c427d220323517868e9a507fd4eb5c`。启动 internal free/largest 为 27,247/18,432 bytes，PSRAM 为 6,297,260/6,291,456 bytes。readiness 证据为 `/private/tmp/espocket-xiaozhi-voice-ready-tls1.log`。

`/private/tmp/espocket-xiaozhi-acoustic-final1.log` 在真实声源后收到服务端 emoji 和 Opus，随后两次借用音频写入完成等待超时并重置 decoder；用户仍确认实际语音正常。该次截图 keepalive 收到 `stimulus.touch: invalid_state` 中断，随后单独重启结束会话；不能把失败截图或超时标记误报为通过的稳定性验收。固定有效声源为 Tingting 的“你好，请简短回答，一加一等于几。”，时长 3.9286 秒，173 KiB。旧零长度音频 fixture 不作证据。

用户继而报告文字均为空白方块。实际产品只注册 `zh_CN` 资源，而界面语言默认为 `en`，动态中文文本走 `default` → 内置 Montserrat，未连接 CJK 字体。GB2312 字库本身覆盖这些汉字。增强 `test_product_fonts.py` 执行真实 Runtime `resolve_style` 和产品字体 Owner；原版在英文界面的默认字体解析断言失败，修复后显式／隐式默认字体、英文／中文环境及反复创建／销毁通过。字库轮廓解码验证增加 10 px 和真实测试问句汉字，日志为 `/private/tmp/espocket-xiaozhi-font-red.log`。

产品注册自己拥有的 Montserrat 字体副本作为 `default`，只在原字形缺失时转到同字号 TinyTTF 中文字体；不修改 LVGL 内置常量、不扩充／复制 1,558,520 bytes 字库，不改变 App BPK 或用户语言设置。原英文字体与符号继续使用编译字形，中文共用原有有界缓存。候选 `d3e83715b` 完整构建通过，17 个组件、110 个产品输入精确复核通过；最终真机文字／退出和合并结果追加如下。

## 字体候选镜像与文字验收

`d3e83715b` 的 BIN SHA-256 为 `059d4c68bdd4fc034917b20afaa69b58177b4cf35bab455cc4e614277816c0e0`，ELF 为 `d3e83715bc3a8f827f45e86a6687332bc3b0dac1d86984ac2f221c4ffc50a061`，构建结束后的精确 patch-inputs proof 为 `c759da24a9038cedb8922795e949e49f9f99db568c66dd3e34172df7d0eec70f`。App-only 写入、设备 hash 校验、启动和 hello 身份全部通过。启动 internal free/largest 为 27,147/18,432 bytes，PSRAM 为 6,288,504/6,160,384 bytes；中文字库大小和原包均未改变。构建、输入、烧录证据分别为 `/private/tmp/espocket-xiaozhi-font-build.log`、`/private/tmp/espocket-xiaozhi-font-proof-final.json`、`/private/tmp/espocket-xiaozhi-font-flash.{flash.log,boot.log,json}`。

字体候选 host checks 全通过：154 个跨模块测试，1 项已有 skip，其它组件／样例通过；282 份 Markdown 检查通过，日志为 `/private/tmp/espocket-xiaozhi-font-checks.log` 与 `/private/tmp/espocket-xiaozhi-font-docs.log`。已实现字体解析的失败回归与字库轮廓解码，不以静态 `check_glyphs.py` 代替动态对话验证。

实际 AI Chatbot 英文界面截图 `/private/tmp/espocket-xiaozhi-font-conversation1-conversation.png` 显示可读中文：麦克风识别“不对呀。”，小智回复“是我哪里说得不对吗？您跟我说说，我来帮您理一理。”。这是实际服务端文本，不是注入 GUI；现场声音与固定声源混合，不能将此结果称为固定“一加一”问句的识别准确率证明。英文标签仍保持可见，中文方块故障消失。

该次截图期间有一次 decoder 借用写入完成等待超时并重置；截图明确在性能窗口外，不将截图期间的串口／绘制压力当作普通对话性能通过。后续三轮真实回复开始后的 Home／重进均通过：Recorder 关闭、返回 Watch Face，继续观察 8 秒没有重开 capture／音频通道，也没有 panic 或 Stop timeout。证据为 `/private/tmp/espocket-xiaozhi-font-speaking-home-{0,1,2}.{log,summary.log}`；第 0 轮在 Home 竞争期间出现一次相同 decoder 重置，第 1／2 轮没有该超时。没有吞掉这些上游超时日志，也不承诺弱网 UDP 永不丢帧。

用户报告“闪退”并确认“直接回到表盘”；对应日志有明确的 `HOST_PHASE reply_started → HOST_PHASE home → stimulus.powerShort`，随后正常 `App stopped`，无重启／panic。此事件与自动 Home 退出测试一致，不作为真实崩溃或用户语音否定证据。后续自动打开 App／返回表盘已提前说明。

使用方法：打开 AI Chatbot 的 Chat 页面，等待 Listening 后直接说话，服务端提供识别、回复文字与语音；按 Home 返回 Watch Face 并停止录音。当前半双工会在小智回复时暂停采集；没有本地唤醒词模型，不能要求先说“小智”唤醒关闭中的 App。已有服务器激活被接受，无需将本轮成功误写成仍待绑定。

## 联合 App 回归发现的真实调度器崩溃

字体候选 `d3e83715b` 的七个其它 Store App 打开／Home 通过；2048 首次因测试器触摸前熄屏而未执行，补充点亮后重试，实际启动触发 Core 1 LoadProhibited。证据为 `/private/tmp/espocket-xiaozhi-font-apps-retry-2048.{log,summary.log}`；匹配 ELF 的回溯指向 Lib Utils `schedule_periodic:1067` 的 `handle->timer->async_wait`，从上一周期回调再次排队而来。这是后续独立捕获的真实 panic，不能因此前 Home 事件属自动测试而忽略，也不能将此候选作为完整稳定性通过镜像。

`remove_task_internal` 与 `stop` 在另一线程 cancel 并 reset timer，而再次排队的 callback 没有保护 timer；Running 检查与实际异步等待之间也存在取消窗口。host 回归执行真实调度方法，在 expiry／async_wait 边界用双线程强制 cancel／remove；checked timer seam 将空指针访问转为明确失败，原版与此前补丁版本均失败，增加每任务 timer 生命周期锁后通过 delayed／periodic 各 8 次。取消完成的 callback 不再执行或重新排队。日志为 `/private/tmp/espocket-xiaozhi-timer-{red,green}.log`。

新补丁维护在实际 Lib Utils Owner 内，同时序列化 suspend／resume／restart／shutdown 的 timer 操作，并在完整初始化 timer／promise 后发布 handle。锁不跨用户任务回调或音频采集；保留此前有界 worker dispatch／空闲唤醒修复。完整原始／补丁后文件库存与补丁摘要记录在同一版本 manifest，原始 managed_components 不手工修改。失败 BIN／ELF 及组件副本保存在 `/private/tmp/espocket-xiaozhi-font-failed-d3e83715b`。最终新镜像与设备联合回归追加如下。

## 调度器修复后的最终镜像

最终普通候选 `07fedabe1` 完整构建、精确 proof、app-only 写入／hash 校验、启动与 hello 身份通过。BIN SHA-256 为 `8382ef71ea65d0ea39ccdb262242277474adad7dd3817f7b9b59f0b967c3e9c1`，ELF 为 `07fedabe1e1e93b38747d055ec8aaee39395cf9e0093af6082007928d04bade6`，patch-inputs 为 `499b42267f46880ade7eea867a30b2d1fe07907a64a05b7e2b2a9132cc906593`。17 个受维护组件与 110 个产品文件、精确 pin／override manifest、生成麦克风／显示配置和运行配置复核通过。启动 internal free/largest 为 27,099/18,432 bytes，PSRAM 为 6,287,564/6,160,384 bytes。

完整 host checks 再次全通过：155 个跨模块测试，1 项已有 skip；其它组件／样例与 282 份 Markdown 检查通过。证据为 `/private/tmp/espocket-xiaozhi-timer-{build.log,proof.json,checks.log,docs.log}` 与 `/private/tmp/espocket-xiaozhi-timer-flash.{flash.log,boot.log,json}`。真机重新完成此前真实失败的 2048 启动与 Home；完整联合 App、语音重进及导航结果继续追加，不以单项通过关闭整体门槛。

## 最终镜像的联合回归与完整播放补充

`07fedabe1` 的八个非 Camera Store App（2048、AI Chatbot、Calculator、Clock、Flappy Bird、Music Player、NES、Weather）启动／Home 全部通过，无 panic 或 Stop timeout。证据为 `/private/tmp/espocket-xiaozhi-final-apps.json` 和对应各 App 日志。实际回复开始后 Home／重进三轮通过：每轮收到服务端 Opus，Recorder 正常关闭，随后观察 8 秒没有重开 capture／音频通道，没有 decoder 重置。证据为 `/private/tmp/espocket-xiaozhi-final-speaking-home-{0,1,2}.{log,summary.log}`。

同镜像的 Native／Runtime apps、navigation、surfaces 套件分别通过 57、34、22 步，证据为 `/private/tmp/espocket-xiaozhi-timer-flash-device-suites/{apps,navigation,surfaces}.{json,log}`。这些输入为 USB synthetic input，不替代触摸硬件与 GPIO 的物理验收。

短数学声源的完整问答尝试 `/private/tmp/espocket-xiaozhi-final-conversation` 正常退出，但没有服务端回复，截图为空 Chat ready；不计作问答通过。改用已验证的较长声源并等待真实 Opus 后，`/private/tmp/espocket-xiaozhi-final-full-reply1-conversation.png` 显示可读中文数数回复，然而完整播放在截图开始前已经出现一次音频写入完成超时，截图过程中再出现两次。临时脚本首轮对重置日志的字符串大小写匹配错误而打印 PASS，已修正断言；此轮仅证明中文显示与真实回复，不作为稳定性通过或最终镜像。

旧 Agent Manager 同步借用每个 Opus 包，等待 Decoder 的异步消费最多 200 ms；超时后关闭／重开流，仍必须等待 callback 才能释放调用者栈。新增回归执行实际 `feed_audio_decoder_data`，将消费延后：原版和此前补丁均失败，错误为 `Deferred decoder consumption resets a healthy stream`。修正使用官方 DataFlow `write_copy`，由现有 Decoder 的 32 KiB 有界队列持有包；不保留调用者缓冲与栈回调，不扩大队列或 20 ms 入队超时，关闭／满队列等真实错误继续失败。输入复用、关闭清理、准入错误和半双工回归通过。红／绿日志为 `/private/tmp/espocket-xiaozhi-queue-{red,green}.log`；后续完整构建与真机结果追加如下。

## 有界回复队列镜像

普通候选 `bf237d3c7` 完整构建、17 个受维护组件与 110 个产品文件的精确 proof、app-only 写入／设备 hash 校验、启动和 hello 身份通过。BIN SHA-256 为 `6303b91aca374da425841ab6cdfd9e1194c8001ca8baf9b4235dca45295a699a`，ELF 为 `bf237d3c74ae8ff27aaa9dd009f338bc3c1692e509e5bb79cad56d2806f1979e`，patch-inputs 为 `6e1840528ea85cf2b425dea1df4a897860dd57fec03cee510cea15815aebf9d4`。启动 internal free/largest 为 27,211/18,432 bytes，PSRAM 为 6,287,316/6,160,384 bytes，App 镜像为 11,172,416 bytes，仍在 14 MiB 分区内。旧 `07fedabe1` 镜像与选中 Agent 组件另存于 `/private/tmp/espocket-xiaozhi-before-queue-07fedabe1`。

完整 host checks 通过 156 项（1 项已有 skip），其它组件／样例与 282 份 Markdown 检查通过。日志为 `/private/tmp/espocket-xiaozhi-queue-{build.log,proof.json,checks.log,docs.log}` 和 `/private/tmp/espocket-xiaozhi-queue-flash.{flash.log,boot.log,json}`。启动有两条瞬时 Touch0 读取失败日志，随后显示与 synthetic touch 正常；保留这一事实，不将 synthetic input 当作触摸硬件验收。后续设备结果追加如下。

`bf237d3c7` 的完整真实声学问答通过：服务端 Opus 回复开始后继续运行 15 秒，再完成实际 Chat 截图，最后正常 Home 并观察 8 秒。没有 decoder 重置、写入／feed 失败、panic 或 Stop timeout；Recorder 正常关闭，最终快照为 Watch Face。`/private/tmp/espocket-xiaozhi-queue-full-reply1-conversation.png` 显示英文 UI 内可读中文识别“还是内容。”以及回复“抱歉，我没太听清，您是想说‘还是内容’吗？能再说得具体一点吗？”。现场语音与固定声源混合，不称为固定数数问句识别准确率验证。完整证据为 `/private/tmp/espocket-xiaozhi-queue-full-reply1.{log,summary.log,json}`；这是修正版的稳定性结果，此前有重置的轮次继续保留为失败。

回复中 Home 的首轮 `/private/tmp/espocket-xiaozhi-queue-speaking-home-0` 通过；第二轮已打开 Recorder／音频通道，但固定声源后 25 秒没有回复，脚本失败于 `No real reply playback began`。日志无 panic、Stop timeout、写入失败或 Decoder 重置，随后 `/private/tmp/espocket-xiaozhi-queue-home-after-no-reply` 显式 Home 正常关闭录音并观察 8 秒。该轮不计为回复退出通过。

重试的测试条件为电脑输出音量 50、音频通道打开后等待 5 秒、最多三次实际扬声器重播同一问句、最多等待 45 秒。只有检测到真实服务端 Opus 解码才触发 Home；失败也在 finally 关闭 Recorder 并恢复电脑原音量。它验证实际回复与清理，不作为任意距离／噪声下识别率保证。

重试的第 0／1 轮成功取得真实 Opus 后 Home，关闭 Recorder、回到 Watch Face，继续观察 8 秒无 capture／音频通道重开，没有 Decoder 重置、panic 或 Stop timeout。第 2 轮最多三次播音后 45 秒仍无回复，测试脚本返回失败；finally Home 正常关闭录音。证据为 `/private/tmp/espocket-xiaozhi-queue-speaking-home-retry-{0,1,2}.{log,summary.log}` 和 `-cleanup.{log,json}`。包括首次第 0 轮在内，共有三次实际回复中的 Home／重进通过，两次未响应的声源尝试单独保留，不称为连续三轮全通过。电脑输出设备只读核对为内置 MacBook Pro Speakers；设备距离与现场声音未受控，未定位两次未响应的原因，不承诺固定声源识别准确率或弱网可靠性。

`bf237d3c7` 的八个非 Camera Store App 启动／Home 再次全部通过，报告为 `/private/tmp/espocket-xiaozhi-queue-final-apps.json`，对应各 App 日志没有 panic、stack overflow、Stop timeout 或 Decoder 重置。此前导致真实调度器崩溃的 2048 路径在该普通镜像也通过；原始包和用户文件保留。

最终 `bf237d3c7` 的 Native／Runtime apps、navigation、surfaces 套件全部通过，分别为 57、34、22 步，报告 identity 均准确匹配。证据为 `/private/tmp/espocket-xiaozhi-queue-flash-device-suites/{apps,navigation,surfaces}.{json,log}`，日志无 panic、stack overflow、Stop timeout 或 Decoder 重置。最终快照为 Watch Face，App 已停止；物理触摸／GPIO 与正式发行条件仍由各自原票持有，未借此全局关闭。

## 数据保留

本轮只向 App 地址 `0x60000` 写产品镜像，不写 LittleFS、NVS、model、分区表或 bootloader。旧普通镜像与已有备份保持可回滚，既有官方 BPK 与用户数据不改写；不 push。
