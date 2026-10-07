# 官方小智能力与麦克风真机验证

2026-10-07。验收 Owner：[005/14](../issues/14-verify-official-microphone-capability.md)。用户要求验证此前关于“官方自带音频能力”的说明。本次只核实来源和硬件路径，未将产品从 playback-only 改为支持语音对话。

## 结论与边界

锁定的官方 Brookesia HAL 包含真实 Codec Recorder、Audio Encoder 和 Opus 配置转换；官方 XiaoZhi Agent 包含激活、音频通道建立、编码数据上传和回复音频接收实现。这些能力不需要从零开发，但存在不等于本项目已经完成板级装配或端到端验收。

真机 ES7210 与 ES8311 都响应 I2C；两个实际麦克风输入在临时 16 kHz、双通道、16 bit 诊断中连续采样，三轮扬声器 1000 Hz 短音引起稳定、明显的信号变化，没有削波。该结果支持本机麦克风／ADC／I2S 路径可用，不是语音识别、云端上传、回声消除、唤醒或完整小智对话的验收。

当前产品镜像 `0203fb1fc` 仍关闭 Codec Recorder 和 AFE。本次没有启用正式产品录音，也没有在云端操作账号。恢复后的实际小智请求返回 `No activation code or challenge found, activate successfully`，官方 Agent 已进入 Activated，说明当前设备已获服务器激活认可；不沿用此前“仍等待激活码”的旧状态，也不能据此推断具体账号身份。

## 官方来源核对

- `brookesia_hal_adaptor` 0.8.4：`src/audio/codec_recorder_impl.cpp` 通过 Board Manager 获取 `audio_adc`，调用 `esp_codec_dev_open/read`；`processor_impl.cpp` 实现 `AudioEncoderImpl`；`processor_type_converter.cpp` 支持 Opus 编码。
- `brookesia_agent_manager` 0.8.2：管理 `audio.encoder.0` Capture DataFlow 与编码数据回调。现有受维护补丁只将获取 Capture 推迟到会话启动，缺少真实输入时仍失败。
- `brookesia_agent_xiaozhi` 0.8.2：`on_activate` 执行激活；`on_encoder_data_ready` 调用 `esp_xiaozhi_chat_send_audio_data`；音频回调进入 decoder。Registry component hash 为 `ff4b086e501d92d1c21a55c17ab1f9f72fcea463213ed2b905ecccbf0ca0e30a`，官方仓库提交为 `e9f22576bb4d19ca190a8105134010d514574a6b`。
- `esp_xiaozhi` 0.1.2：锁定 component hash 为 `8e2e8a32abee72b29fd1833990a033f07bc6e468867ece1176513da467292e3f`。
- 诊断使用与产品一致的官方 `esp_codec_dev` 1.5.11，component hash 为 `df70f10af8d7b922add7b9d07372c9c97ab356e58d72b7a892050227c2d44348`。未修改 managed component。

官方来源：[Brookesia XiaoZhi 文档](https://docs.espressif.com/projects/esp-brookesia/zh_CN/latest/service/agent/xiaozhi.html)；实际核对对象为锁定组件源码，未将最新文档当作当前固件行为证明。

## 板卡与引脚

核对 [Waveshare 官方原理图](https://files.waveshare.com/wiki/ESP32-S3-Touch-AMOLED-1.75C/ESP32-S3-Touch-AMOLED-1.75C-schematic.pdf) 第 1 页全部相关区域：ES8311 用于播放，ES7210 的 MIC1/MIC2 输入连接两个麦克风，MIC3 接扬声器模拟参考。原理图 SHA256 为 `7bcc0a3a9dc02893741e1e555b203a17055b5cc9cce3b5c548e160e21683900d`。

实际 I2C 7-bit 地址为 ES8311 `0x18`、ES7210 `0x40`；官方 codec 配置中的 `0x30`／`0x80` 使用 8-bit 表示，不是地址错误。SDA=15、SCL=14、MCLK=16、BCLK=9、WS=45、播放 DOUT=8、录音 DIN=10、PA=46。

厂商 [ES7210 示例](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75C/blob/main/examples/arduino/examples/06_ES7210/08_ES7210.ino) 也提供录音／VAD 路径，下载文件 SHA256 为 `2fffd4a37c5d2fe59d17f325cd51df0acddf8a098ff391f251eba471cb36bd7b`。先读到 ES8311 示例中带 echo 的代码，不能据此认定本板麦克风接 ES8311；原理图与 ES7210 示例纠正了这一初步疑点，本次未刷入错误芯片诊断。

现有上游板配置选择 `0111` 三路输入，启用产品录音前仍需统一真实麦克风、模拟参考、多通道格式、mic layout 与增益。临时诊断明确只选择 MIC1/MIC2，未证明三路 TDM 或 AFE 配置正确。

## 临时诊断与测量

独立工程位于 `/private/tmp/espocket-mic-verification-probe`，只使用官方 I2C／I2S／Codec API；不包含 Brookesia、Wi-Fi、Storage、NVS 或文件系统访问，不保存或上传原始音频。ADC 选择 MIC1/MIC2，16 kHz、双通道、16 bit、30 dB 输入增益。独立 worker 向 DAC 写入静音或 1000 Hz 正弦音，振幅 2048、临时输出音量 65。每阶段丢弃 1 秒稳定样本，再统计每通道 16000 个样本；共三轮静音／短音比较。

| 阶段 | 输出 | 通道 0 RMS | 通道 1 RMS | 通道 0 的 1000 Hz 幅度 | 通道 1 的 1000 Hz 幅度 |
|---|---|---:|---:|---:|---:|
| 0 | 静音 | 20.347 | 22.258 | 0.234 | 0.221 |
| 1 | 短音 | 1692.008 | 2057.877 | 2392.639 | 2910.066 |
| 2 | 静音 | 21.517 | 22.916 | 0.138 | 0.097 |
| 3 | 短音 | 1689.245 | 2056.115 | 2388.739 | 2907.581 |
| 4 | 静音 | 20.356 | 21.766 | 0.152 | 0.391 |
| 5 | 短音 | 1692.493 | 2059.566 | 2393.428 | 2912.554 |

12 组统计全部完成；每组削波计数均为 0。短音阶段每组非零样本 16000；静音阶段为 15652–15724。两个麦克风输入均明显响应受控声音；未做远场、主观听感、外部语音识别或声学耦合量化。

诊断构建通过，BIN SHA256 为 `e464b6e38172a57462837809ca9a18540f62665d9d97d56c7a497d77d8135bc1`，ELF SHA256 为 `ecd79dfe436003ceb698f02d2b3050b9962d7d6e41213744c3f2732a89f2ec49`，`main/main.c` SHA256 为 `4fff201d38487b73ba818d79dd04a59d3b4cefdb5a6977c28746b44a9e7bf34e`。诊断日志最终报告 Capture/Playback 都已关闭。

## 备份、失败与恢复

设备为 ESP32-S3，MAC `A0:F2:62:E3:0B:68`，串口 `/dev/cu.usbmodem101`。诊断前实际 `hello` 返回 `0203fb1fc`，与现有 canonical ELF 一致；对应 BIN SHA256 为 `f216d397758a92193e9429ecda53eb95ba69c1efa3deb26bcc90d6a81afe6385`。

第一次尝试备份整个 10666464-byte App 时，USB 在读取约 794624 bytes 后中断。尚未刷入诊断；异常清理仅重启原产品，`hello` 和 Watch Face 正常。没有把这次失败当作成功备份。

第二次只备份临时诊断会覆盖的 App 前 253952 bytes，从 `0x60000` 读取；SHA256 `5de06b07239e45867e3a896915c5e10491ded347d4dbc7d5356dba8e430dc1d6` 与 canonical 产品镜像同一范围完全相同。诊断只写 `0x60000` 的 253440-byte BIN；其擦除对齐范围完全包含在备份中。结束后写回原始 253952-byte 备份，esptool 校验通过；其他 App 区域、bootloader、分区表、NVS、model 和 LittleFS 未烧写。

恢复启动后 `hello` 仍为 `0203fb1fc`，Watch Face 无前台 App、无占用输入。Launcher 翻页、AI Chatbot 前台启动和 Home 退出通过，最后返回 Watch Face，`foregroundAppId` 为空且 `inputBusy=false`。此次检查同时观察到小智服务器认可激活，随后真实会话启动失败：`Failed to get audio encoder interface` → `Failed to start service: AudioEncoder0` → `Failed to open agent audio capture operation`。App 未崩溃，Home 正常释放 AudioPlayback、XiaoZhi 和 AgentManager。保留这个录音关闭下的预期失败，不将 UI／生命周期通过写成语音功能通过。证据为 `/private/tmp/espocket-mic-restored-ai-smoke-20261007.log` 与同名 JSON。

`python3 -m unittest discover -s firmware/test/host -p test_agent_activation_capture.py` 通过 1 项真实 Agent 方法回归：激活不需要 Capture，实际会话在缺少麦克风时拒绝，具备输入时才启动。该 host 结果不代替本次硬件测量。仓库只修改工作票、Spec 与证据文档，临时诊断源码未进入产品；280 份 Markdown 与 diff 检查通过。新 worktree 最初因未物化依赖而出现既有源码链接缺失，跨 checkout 符号链接也被正确拒绝；只复制现有文档引用的 29 个依赖／板级源码锚点到忽略目录后，原检查完整通过，未修改检查器或既有文档链接。

原始证据：`/private/tmp/espocket-mic-verification-device-prefix/result.json`、`probe-boot.log`、`original-read.log`、`original-restore.log`、`restored-boot.log`；第一次失败保留在 `/private/tmp/espocket-mic-verification-device`。诊断 runner 为 `/private/tmp/espocket-mic-verification-run.py`，包含自动恢复的 finally 路径。首次构建受沙箱进程读取限制失败，随后使用相同源码在允许的环境中构建通过；日志为 `/private/tmp/espocket-mic-probe-build-escalated.log`。

## 后续正式语音边界

本次证明官方实现存在且本机基本录音链路可用。正式接入仍需有意修订 [004/04 的 playback-only 范围](../../004-m4-device-capabilities/issues/04-adopt-playback-only-audio.md)、构建配置及验证契约，正确装配录音通道，再验证编码、Agent Capture、网络收发和退出释放。是否采用 AFE、回声消除和唤醒由具体产品方案决定，不能因源码支持就直接全部开启。

恢复后的激活认可已经由实际服务器响应证明。完整小智对话仍需要实际说话→编码→上传→回复→播放验证；本次没有完成这个链路，不改变 [005/13](../issues/13-xiaozhi-and-launcher-performance.md) 已接受的激活与播放范围。
