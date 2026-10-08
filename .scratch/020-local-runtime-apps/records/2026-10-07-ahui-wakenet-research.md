# “啊灰啊灰”官方 WakeNet 获取与适配边界

## 本轮范围与结论

2026-10-07 托管指令将目标唤醒词明确为“啊灰啊灰”，Reset 指实体硬件 Reset，禁止新增界面 Reset 按钮。本会话仅在 chat-audio-distortion worktree 做只读源码／官方资料核查和文档更新；不打开串口、不部署、不修改 main、不合并、不清理 worktree。当前任务与未满足条件由[托管票 04](../issues/04-chat-wake-hardware-reset.md)持有。

锁定 ESP-SR 2.4.4 的 75 个模型目录中，没有“啊灰啊灰”或名称含 `ahui` 的模型。`wn9_customword/_MODEL_INFO_` 实际内容为 `WakeNet9_v1h24_小爱同学_3_0.620_0.627`，因此这个目录是已有系数的示例，不是输入任意文本即可识别的通用模型。修改目录、显示文案或 `_MODEL_INFO_` 不能把“小爱同学”变成目标词。

WakeNet 接口公开模型创建、音频 detect、阈值和状态清理，未提供文字到新模型的训练接口；`mn_language="cn"` 也只是配置中的语言项，不是自定义唤醒词。必须取得针对目标读音训练的真实系数，然后验证锁定引擎兼容性和实际检测。不能把云端 STT 识别文字当作本地 WakeNet。

来源：锁定组件 `firmware/managed_components/espressif__esp-sr/idf_component.yml`、`model/wakenet_model/*/_MODEL_INFO_`、`include/esp32s3/esp_wn_iface.h`、`include/esp32s3/esp_wn_models.h` 与 HAL `include/brookesia/hal_adaptor/audio/device.hpp`。

## 官方取得方式：申请训练，不是现场填词

检索日期为 2026-10-07。锁定 ESP-SR 2.4.4 对应官方提交 `c7acefa591d130c7919e761f247dc64b9b8afe1a`；检索时最新文档／README 对应 `76581015af7075681814627a5bb03d2f3f328f8a`。前者的[README](https://github.com/espressif/esp-sr/blob/c7acefa591d130c7919e761f247dc64b9b8afe1a/README.md#wake-word-engine)已经明确提供客户定制与 TTS 社区申请两条渠道。

| 渠道 | 官方入口与条件 | 交付限制 |
|---|---|---|
| 付费客户定制 | [官方定制流程](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/wake_word_engine/ESP_Wake_Words_Customization.html)，联系 `sales@espressif.com`，说明目标词／数量、产品量产规模与语料来源 | 官方明确训练／调优收费，自采语料另计；金额未公开，语料准备后的训练通常 2–3 周，不是本项目时限承诺 |
| 免费社区 TTS 申请 | [官方 issue 88](https://github.com/espressif/esp-sr/issues/88#issue-2040833215)，附项目链接与简述，或获得超过五人的喜欢／赞同；正文要求阅读提交协议 | 不保证受理、排期、专属使用或指定家族；[维护者 2025-11-12](https://github.com/espressif/esp-sr/issues/88#issuecomment-3521477213)明确不会训练所有请求，只选最热门词 |

issue 正文称社区模型与 ESP-SR 同许可、免费商用，但还附提交协议和词语权利条件；本轮没有提交申请或接受协议，也没有发送邮件。取得渠道明确不等于“啊灰啊灰”已受理、训练或交付。

[官方 2025-07-24 答复](https://github.com/espressif/esp-sr/issues/88#issuecomment-3111752609)为 “The pipeline has not been open-sourced yet.” 所查当前 README／issue 仍提供申请渠道，没有公开的官方自助训练管线或填写词语就生成模型的 API。旧明确答复不能替代未检索渠道的现状，准确结论是本次官方来源未给出可本地运行的官方训练入口。

定制文档建议通常 3–6 音节，[锁定版中文源文](https://github.com/espressif/esp-sr/blob/c7acefa591d130c7919e761f247dc64b9b8afe1a/docs/zh_CN/wake_word_engine/ESP_Wake_Words_Customization.rst)确认这里指音节。普通话“啊·灰·啊·灰”拟为四音节，仍需确认具体声调、轻声、连读和停顿。[维护者 2025-10-21](https://github.com/espressif/esp-sr/issues/88#issuecomment-3425023069)建议提供拼音或音标；不把本轮暂记的无调 `a hui a hui` 当作用户确认的训练读音。人声语料定制页的超过 2 万条、16 kHz／16-bit／mono WAV 等要求不直接套用到社区 TTS 申请。

模型家族是关键外部依赖：[维护者 2026-09-07](https://github.com/espressif/esp-sr/issues/88#issuecomment-5564365968)明确 “We have started using WakeNet10 and the new TTS pipeline to generate the requested wake words.” 新的[2026-09-11 中文交付实例](https://github.com/espressif/esp-sr/issues/88#issuecomment-5633522500)为 `wn10_tu2tu2ni3hao3`。[最新固定 README](https://github.com/espressif/esp-sr/blob/76581015af7075681814627a5bb03d2f3f328f8a/README.md#news)也记录 WakeNet10；没有找到保证继续提供新 wn9s／wn9 定制且兼容 2.4.4 的承诺，亦不据此断言旧家族停止服务。

申请时应明确“啊灰啊灰”、确认后的读音、项目描述、ESP32-S3、ESP-SR 2.4.4、307200 bytes 模型分区、片内 RAM／PSRAM 预算，优先询问兼容当前链路的 WakeNet9s，备选 WakeNet9。若官方只能交付 WakeNet10，应由托管会话先设计组件升级、模型格式与资源验证；不能把 wn10 重命名为 wn9／wn9s。完整检索笔记暂存在 `/private/tmp/espocket-ahui-official-customization.md`，记录已核查的全部引用和申请边界。

## Flash 容量：已执行官方 packer

模型分区为 `0x10000`、307200 bytes（300 KiB），在 `0x5b000` 结束；App 分区从 `0x60000` 开始。该分区虽然 CSV subtype 为 littlefs，ESP-SR 当前直接 mmap 官方 `srmodels.bin` 打包格式；应交付准确模型镜像，不能按普通 App 资源目录写入。来源：`firmware/partitions_32m.csv`、锁定 ESP-SR `src/model_path.c` 的 `srmodel_mmap_init` 和 `CMakeLists.txt`。

本轮在临时目录执行锁定官方 `model/pack_model.py`，每次只打包一个官方目录，并核对模型数量为 1。报告保留在 `/private/tmp/espocket-ahui-pack-proof.json`；模型没有写入设备。

| 官方模型 | 打包 bytes | 300 KiB 剩余 bytes | 已训练词 |
|---|---|---|---|
| wn9s_nihaoxiaozhi | 125951 | 181249 | 你好小智 |
| wn9_customword | 291150 | 16050 | 小爱同学 |
| wn9_nihaoxiaozhi_tts | 291042 | 16158 | 你好小智 |

`wn9s_nihaoxiaozhi` 镜像 SHA-256 为 `72447db11fd5bc683507ddd6727bea458473873019bf919858ed520a87429894`，与此前真机候选一致。`wn9_customword` 为 `4aca88a71eef1749118d3d268e3e48091dbb30d63d27f32cda61e7edf41d7f9a`，标准小智为 `56990e6b97faeced7aeea48c89f15b0d0c579c012a8106b91e96141f490051a6`。

同型单词模型的尺寸说明本分区可能可容纳定制 WakeNet9s 或 WakeNet9，不能保证未交付的“啊灰啊灰”模型大小。标准模型加现有小模型的 payload 已超过 300 KiB，不应默认同时保留二者。收到交付后须按完整 header、索引、系数及元数据核对总 bytes；超限时先重新设计分区／迁移，不能侵入 App 分区。当前不需要也未实施分区变更。

## 内存与处理时间：不能用 Flash 大小推断

2026-10-07 获取的[官方 ESP32-S3 benchmark](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/benchmark/README.html)给出 Quantised WakeNet9 双通道：RAM 16 KB、PSRAM 324 KB、每 32 ms 帧平均运行 3.0 ms；三通道：RAM 20 KB、PSRAM 347 KB、每 32 ms 帧 4.3 ms。其 MR／SR／LOW_COST 完整 AFE 配置为 internal RAM 60.1 KB、PSRAM 739.7 KB，并包含额外算法。随后用[锁定 2.4.4 提交中的 benchmark](https://github.com/espressif/esp-sr/blob/c7acefa591d130c7919e761f247dc64b9b8afe1a/docs/en/benchmark/README.rst)核对上述 ESP32-S3 表数据一致。上述数据属于官方示例条件，不是本机 Chatbot 的实际峰值或可以直接相加的额外预算。

latest 页面已有锁定版本外的新型号，因此不把整页当作 2.4.4 保证；最初尝试 `v2.4.4` tag 原始源码地址返回 404，改用核实过的固定提交后成功取得版本化表，暂存 `/private/tmp/espocket-wakenet-benchmark-locked.rst`。所查资源表没有提供本次需要的 WakeNet9s 双麦、当前 AFE／Opus／GUI 并发实测值。

[官方 WakeNet 说明](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/wake_word_engine/README.html)要求输入 16 kHz、单声道 signed 16-bit PCM。集成 AFE 可从双麦输入组织模型数据：旧候选 `63039f6bf` 的日志实际显示 16 kHz、2 microphone／0 playback、`AFE Pipeline: [input] -> |WakeNet(wn9s_nihaoxiaozhi,)| -> [output]`。不能把裸模型单声道输入与板端双麦缓冲混用；模型块长和通道数应按官方接口查询。

锁定组件 README 将 WakeNet9s 描述为更少参数和计算的 cost-down 型号，将 WakeNet9l 的 CPU／内存描述为约 WakeNet9 的 1.3 倍。latest 说明主要把 9s 列给 C3／C5／C6；此前 2.4.4 的 S3 候选确实初始化过 9s，但没有通过目标词检测。定制交付仍必须要求官方明确 S3 与 2.4.4 兼容，不能仅按这个历史初始化结果承诺定制模型可用。来源：[锁定组件所指官方 README](https://github.com/espressif/esp-sr)、上述引擎说明与此前另一个 worktree 的设备记录（未视为本轮验收）。

此前 `63039f6bf` 启动 internal free／largest 为 27191／18432，PSRAM free／largest 为 6286772／6160384，约 26.6 KiB 片内空闲，最大片内块 18 KiB。这是启动后空闲量，不是聊天运行中的资源峰值。PSRAM 剩余较多并不能替代片内分配需求；不得把 Flash 上约 126 KB 的系数大小视为模型唯一 RAM 开销。最新交接镜像 `b7d076a00` 没有由本会话再次测量。

此前默认 Recorder 编码 priority 10，AFE fetcher priority 5；一次设备回溯落在 Opus 编码并伴随 FEED full／IDLE0 watchdog。单变量将 AFE fetcher 调到 11 后，该窗口未再观察到上述两项错误，仍有少量 AFE empty，且没有完成关键词恢复／真实回复验收。priority 11 应作为已交接候选保留，不是解决全部卡顿的结论；最终须测回音、空转、播放、网络与 GUI 并发以及 watchdog。来源同前述设备记录；本轮没有新增设备证据。

## 收到真实模型后的集成条件

1. 获取官方型号、模型名、实际读音、引擎／ABI 版本、所需组件版本、Flash／片内 RAM／PSRAM 与运行时间说明；目标文本为“啊灰啊灰”，暂记普通话四音节 `a hui a hui`，具体声调／“啊”的自然语气由训练方确认，不在本轮自行改变目标词。
2. 维护模型来源、交付 hash 和版本，在独立 staging 中打包；禁止修改原始 managed_components 系数或用当前已有模型重新贴标签。优先询问资源较小且兼容当前 S3 的定制型号，实际型号由官方能力与实测决定。
3. 当前 `model/movemodel.py` 按启用的 `CONFIG_SR_WN_*` 后缀转成目录名，并复制存在的目录；配置一个不存在的 `wn9s_ahui...` 不会生成模型。新模型需要明确目录、配置／staging 输入、精确打包成员及编译所选组件，不能只改 WakeNet 显示词或 HAL 的分区标签。
4. 托管会话部署前备份实际模型，验证整个镜像 ≤307200 bytes；只写预定分区并保留 NVS、用户配置、App 与 LittleFS。此前备份和模型 hash 仅代表历史设备状态，需以托管会话当前设备为准。
5. 真机在 Sleep 后准确说目标词，必须见到本地 WakeStart → Agent WakeUp → 云音频通道打开 → 真实回复；普通语音不应代替目标词触发。播放期间的自唤醒／回音、退出／Settings 暂停录音、连续开关引用与内存都由最终集成验收。

## 实体 Reset 与撤回的软件候选

此前 Core 025、产品 `restart_action="espocket.chat.reset"` 以及 GUI Reset 按钮实现 App stop／start；它们没有执行芯片硬件 Reset。旧测试只证明 Recorder 关闭／重开和连接恢复，不能满足最新实体 Reset 条件。上述候选仍在未合并 worktree 供审查，不继续实现或部署；最终集成不应把它们及 App 专用 Presentation opt-in 带回本地 App 方案。

实体 Reset 必须验证芯片实际重启、系统正常启动、NVS／账号及本地包保留，然后核对重新进入 `espocket.app.ai_chatbot` 和连接所需步骤。Reset 不等同 Home，也不能默认设备重启后自动进入聊天。按交接，最新两个本地包与旧 Store 包卸载、当前 `b7d076a00` 镜像及保留音频修复由托管会话持有；本轮只记录该信息，不反向修改它们。
