# 2026-10-03 — 官方 AudioPlayback 听感验证

Sound 页面本身没有 Play/test-tone；此前用户的 Volume 拖动已成功，但未证明 speaker 出声。锁定 Audio helper 提供 Play/Stop/GetVolume/GetMute、真实 PlayStateChanged；av_processor 使用官方 simple player，file 输入和 WAV 解码已启用。

使用 `prepare_audio_playback_probe.py` 在独立 audio-candidate 加入只用于设备测试的 Native fixture，不改 managed components，不复制播放器或创建新 USB/Assistant 能力。进入 Sound 的既有动作触发官方 AudioPlayback Play；波形是本地产生的 400 Hz sine，0.5 秒音+0.5 秒静音，30 次循环，配置 35 秒播放超时（非严格总时长保证）。

V1 最初设计在 LittleFS 上独占创建 `/littlefs/.espocket-audio-probe.wav`；O_EXCL 拒绝同名已存在文件；Back/Home 先由官方 Stop 清理播放，再删除自己的测试文件。Stop 失败保留文件并明确报错，不冒充清理成功。用户原 volume/mute 不由 probe 改写。

已验收无 probe 候选 image `e7c095d3d` ELF/BIN 保存在 `/private/tmp/espocket-settings-theme-accepted/`，听感后恢复。Fixture/header/WAV identity 存在 `/private/tmp/espocket-settings-theme-build/audio-probe-inputs.json`；构建、实际事件、听感和恢复证据分列下文。

Exposure Decision：此 fixture 仅为显式设备验收，不是正式 App 行为，也不对 Assistant 注册播放、Recorder 或 raw codec。Recorder/AFE 继续关闭。

## V1 failure and recovery

V1 full build、依赖与播放配置校验通过，ELF `590cb24898d5c158ab1c55f6a4623b4045e881c7bb835212abc18dc683ab03da`、BIN `ef382e0b6fb4b56abebfdd11961ee4efe5793b720ef96782fdb6dfd8998500c6`。App-only 刷入校验与启动通过；自动 Sound 入口失败，`/private/tmp/espocket-audio-probe-owner-result.log` FAIL，cleanup release timeout，不能算播放或 Home 清理通过。

`/private/tmp/espocket-audio-probe-owner.log` 捕获 `assert failed: spi_flash_disable_interrupts_caches_and_other_cpu ... esp_task_stack_is_sane_cache_disabled()` 并重启；addr2line 定位 audio_probe::start 的 open → vfs_littlefs_open → lfs_file_opencfg，调用者是 Core dispatch_action 的外部 RAM App 任务。断言发生在测试文件创建阶段，尚未提交 Play。此为 probe 直接 Flash IO 的错误，不把它误报为已证明的 Audio 解码/Renderer bug。

先按 App-only 恢复无 probe 的 `e7c095d3d`，写入校验与 `/private/tmp/espocket-audio-probe-recovery-boot.log` 启动 PASS。V1 输入单独保留 `audio-probe-v1-inputs.json`。可能未完成的 V1 文件不擅自删除；V2 使用明确不同的 fixture path。

## V2 Owner correction

替换直接 POSIX IO 为官方 Storage::fs_stat/fs_write/fs_remove，复用 Storage 的两个 stack_in_ext=false 工作线程。Flash 状态、副作用与执行位置留给真实 Storage Owner，不让 Adapter 新建一个私有存储线程。V2 path `/littlefs/.espocket-audio-probe-v2.wav`；串行 fixture 检查不存在后再写，拒绝未知现存文件，不对通用并发创建声称原子性。Probe 不改写原 volume/mute，Play/Stop 继续官方 AudioPlayback。

新增实际 C++ fixture 公共接口 seam 回归：现有数据拒绝、成功写入和播放、Stop 失败不删除、部分写入清理、Play 失败清理、删除失败保留所有权并重试。该回归不证明物理 Flash cache-safe 或扬声器听感；设备门槛仍开放。

## V2 device result

80 项 host tests 与 Markdown 检查通过；完整构建 `/private/tmp/espocket-audio-probe-v2-build.log` 通过，依赖和 playback-only 配置再次验证。ELF `54da1b8e3260d49dcbc01d4cb5d71fa746ef3d4578ed32b0824692a8689af5bc`、BIN `6cea34875265b5878e5a43e4d56141a8d181f7e001ed9b67df8747d4d8c9db31`、hello `54da1b8e3`。App-only 刷入校验及 `/private/tmp/espocket-audio-probe-v2-boot.log` 启动 PASS。

自动实际 Sound→PWR Home `/private/tmp/espocket-audio-probe-v2-owner-result.log` PASS：提交官方 Play、连续收到 Owner Playing/Idle、底层 simple player Running/Finished；PWR 后 STOPPED，Storage 成功删除自己的 fixture，并停止/释放 AudioPlayback。没有 V1 的 Flash cache-safe 断言或重启。输入 synthetic，不声称 speaker 实際听感。原 volume=37、mute=false 从 Storage 加载，probe 未改写。听感请求已发出，只需一次实际播放、调音量及 Home 停止观察。

附带现存 Audio teardown 诊断：释放 audio_dac 的 i2s_audio_out 时，esp_board_manager 输出 `i2s_channel_disable: the channel has not been enabled yet`，随后释放 TX/RX 并返回正常表盘。不隐瞒这条重复停用错误，不把 Owner Playing 当作全部板级清理无问题；与 V1 probe 文件创建断言是不同路径，后续在真实 peripheral Owner 单独处理。

## Human hearing gate failed

用户确认“完全没声音，Mute 已关闭”；不得关闭 004/04。`/private/tmp/espocket-audio-probe-v2-user-capture.log` 显示 Mute=false、Playing/Finished 循环，实际 Volume 从 37 调至 93 再调低；PWR 后 STOPPED 并删除 fixture。App/Volume/Home 路径可运行不等于 speaker 出声。

排查顺序：是否非零 PCM 到真实 DAC；codec channel/PA；板级供电与 speaker。独立 HAL CodecPlayer write_data 中加入只读 DEBUG-audio-dac 采样，记录调用数、PCM peak/nonzero、真实 esp_codec_dev_write 返回值与 Owner PA/volume。仅修改临时候选，不提交到 HAL patch，不把 instrumented output 冒充 manifest 的精确补丁源码；身份单列 `/private/tmp/espocket-audio-dac-probe-inputs.json`。此次无需用户重复听，先自动定位输出边界。

[Waveshare 官方板卡说明](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75C) 确认当前 C 型号包含 ES8311 与内置 speaker；该产品信息不能证明本机 speaker 硬件健康。

## PCM boundary result

只读 PCM 诊断候选完整构建通过；ELF `8ddd7b9488c59808ea1a7916b4850ce9c4d066223f46214e2e6fe88d00da3d96`、BIN `9f76c4c646a9eb4648a51b826ec6025ffacf337ba017f7ea77fac54cfd868b2b`、hello `8ddd7b948`。App-only 写入校验与启动通过。首次启动诊断因刷写仍占用串口而失败（串口独占锁阻止冲突），等刷写退出后重跑启动检查通过；不把首次失败当成设备启动失败。

`/private/tmp/espocket-audio-dac-probe-owner-result.log` PASS，仅表示实际 Owner Play 和 Home cleanup。`DEBUG-audio-dac` 第 1/2/3/64/128 次写入均 bytes=1536、peak=4096、nonzero>0、esp_codec_dev_write 返回 0；PA Owner=true、volume=36。已排除此次输入未解码或全零 PCM；成功写入软件 codec 不证明 I2S 波形、功放电压或 speaker 出声。物理听感仍 FAILED。

下一只读诊断检查官方 codec register dump 与 GPIO 配置。GPIO46 的 gpio_get_level 是输入采样，若 input 未开启不能据此声称输出低电平，更不能当作实际电压测量。

## Codec boundary result

第二份只读诊断完整构建通过；ELF `7b973cbb4237fb2e2c598c4106fd46e6268c84f942548b15115203f63efe924e`、BIN `690ba6fa27ae63f026e814b31170bc1cc5b86b668634cfeda5b52ee4791ba51c`、hello `7b973cbb4`。身份与临时源码 hash 单列 `/private/tmp/espocket-audio-codec-probe-inputs.json`；App-only 写入和启动通过。实际 Play→Home cleanup `/private/tmp/espocket-audio-codec-probe-owner-result.log` PASS。

首批非零 PCM 成功写入时，公开 esp_codec_dev_dump_reg 读取 ES8311：0x09=0x0c、0x0d=0x01、0x0e=0x02、0x12=0x00、0x31=0x00、0x32=0x7a、0x37=0x08；dump 返回 0。对照当前驱动 start/set_mute，DAC 路径启用、0x31 静音位未置位。以上仅缩小软件假设，不能证明 MCLK/I2S 引脚波形、模拟电源和 speaker。

日志标签 `actual_gpio46=0` 的命名不准确：实际调用是 gpio_get_level，板配置 GPIO_MODE_OUTPUT，IDF 文档明确未启用输入时返回恒 0。因此此值不构成 PA 输出低电平证据，也不据此修改极性。最终二次候选未包含 gpio_dump_io_configuration；GPIO 配置结论取自锁定板配置，不冒充设备读回。

[官方原理图](https://files.waveshare.com/wiki/ESP32-S3-Touch-AMOLED-1.75C/ESP32-S3-Touch-AMOLED-1.75C-schematic.pdf) 的 ES8311→NS4150B→speaker 路径和 GPIO46 PA_CTRL 与锁定板配置吻合。物理波形、电压和本机 speaker 健康尚未测量。后续优先确认本机是否曾有已知成功音频，再决定播放配置差分或独立板级验证；不直接归咎硬件，不盲改 codec 寄存器。

测试后 Play STOPPED，自己的 V2 文件已由 Storage 删除；未认领 V1 的可能残留文件仍保留。临时 HAL DEBUG instrumentation 已恢复至备份原文，不提交诊断补丁。恢复无 probe 的已验收候选 `e7c095d3d`，写入校验与启动结果另补录。

恢复结果：`/private/tmp/espocket-audio-probe-final-restore-flash.log` 写入校验通过，`/private/tmp/espocket-audio-probe-final-restore-boot.log` 启动 PASS。当前设备为无 probe 的 `e7c095d3d` 候选；Recorder/AFE 仍关闭。最终 80 项 host checks 与 200 Markdown 文档检查通过。此 slice 提交测试工具与失败证据，不声称修复扬声器无声，也不关闭 004/04。

## Follow-up: no known successful speaker baseline

用户说明此前“没确认过”本机出声；不是确认硬件损坏，也不能以官方型号内置 speaker 推断本机正常。

对照 [Waveshare 官方 ES8311 示例](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75C/blob/main/examples/arduino/examples/07_ES8311/15_ES8311.ino)，当前 MCLK/BCLK/WS/DOUT 引脚、16 kHz/16 bit、256 倍 MCLK、非反相时钟、PA 高有效配置一致；实际 codec 输出配置为 stereo，与示例一致。其示例后续包含 microphone echo，不直接刷入，不据此启用本项目 Recorder。官方 driver 初始化主要 DAC power/format 寄存器亦与此次设备 dump 相符；旧驱动 DAC OSR 为 0x10，当前 esp_codec_dev 为 0x20，这一差异尚未判定为故障原因，不盲改。

补查实际 I2S 写入：esp_codec_dev 的 data_if 写入在 out_reconfig 分支可能不调用 driver 而返回成功。现有 No paired data 日志不能完全代替真实 driver 写入证据。在独立 HAL 源码/CMake 加入临时 linker wrap，转发原 i2s_channel_write 不改参数或返回值，采集 requested/written/ret；同时只读 PA output latch/enable 和 GPIO 配置。它不改变输出电平、音频内容或产品 API，也不手改任何 managed_components。GPIO output latch 仍不是电压测量。

### Actual I2S and PA result

独立诊断完整构建、App-only 写入校验与启动通过；ELF `4c0ec9ab42099efcc6920c4d8373a2d99f77b8bafdc25514873ccbabdce9afb8`、BIN `3e2da5b866fc842426ea8689c740e684f88ad4f5468a200a2a2ab6e8861f0569`、hello `4c0ec9ab4`。额外源码与 CMake hash 保存 `/private/tmp/espocket-audio-i2s-probe-inputs.json`，不冒充已批准 manifest 的原样源码。

`/private/tmp/espocket-audio-i2s-probe-owner-result.log` 的实际 i2s_channel_write 第 1/2/3/64/128 次调用全部 requested=1536、written=1536、ret=0；同时 PA output latch=1、output enable=1。实际 GPIO dump 显示 GPIO46 FuncSel=GPIO、SigOut ID=256/simple GPIO、InputEn=0，支持上轮 input sample 恒零不能代表 output 的解释。实际发送和 GPIO 配置已确认，物理波形、电压与出声仍未确认。Home 后官方 Stop 与 Storage 清理 PASS，临时 HAL cpp/CMake 已恢复。

准备独立参考诊断：基于本地 ESP-IDF 6.0.1 官方 i2s_es8311 示例接口，保留当前锁定 esp_codec_dev 1.5.11，在 checkout 外只创建 TX、DAC/OUT codec，以同样 16 kHz/16 bit stereo、256 倍 MCLK 播放 10 秒 400 Hz 间歇音。临时 volume=85，不访问 NVS/文件系统，不打开 RX/Recorder，不写 AXP，仅读取原 power 状态；结束关闭 codec/PA。此诊断用来区分 Brookesia/Board Manager 与更低层路径，不等于厂商出厂镜像，也不能单独判定硬件损坏。未将其作为产品实现或新增 USB 能力。

参考候选完整构建 `/private/tmp/espocket-audio-reference-build.log` PASS；ELF `529e046fcaa2327e08299bba8184620f37b70fc37328cf691269748be753cfbc`、BIN `484ac6ba3afbed85149ab2e006d9814e9c2e3c7e2bf275b7f6beb9f0b9a091d4`，输入 hash 单列 `/private/tmp/espocket-audio-reference/inputs.json`。源码与产物仅存 checkout 外，不采用为产品架构；设备启动、10 秒发送、关闭与物理听感尚未执行，不称为已知可出声镜像。已请求用户准备好后再开始这唯一一次听感，等待期间不刷参考镜像。

I2S 诊断后的 `/private/tmp/espocket-audio-i2s-restore-flash.log` 校验 PASS，`/private/tmp/espocket-audio-i2s-restore-boot.log` 启动 PASS。当前设备已恢复无 probe `e7c095d3d`，参考候选尚未刷入。临时 linker wrap 和 cpp/CMake 改动均已清除。

### Reference device run

用户回复“准备好了”后才 App-only 刷入已构建参考候选。`/private/tmp/espocket-audio-reference-device.log` 写入 hash 校验 PASS；实际 codec open OK，首笔真实 I2S 写入 3200 字节，约 10 秒后 STOPPED、codec closed/PA disabled，app_main 正常返回，没有崩溃或持续播放。完整发送检查使用实际 i2s_channel_write 返回与 bytes_written，每笔断言完整发送，当前 sdkconfig assertion level=2。日志附着时已错过最初 AXP 读取输出，因此不把未抓到的电源值报为实际证据；电源读取错误会由源码 ESP_ERROR_CHECK 中止，而本次已进入播放。

本次没有 GUI 或 PWR Home 实现，是 checkout 外的临时板级参考诊断；只使用 OUT/DAC 与 TX，无 RX、Recorder、NVS/文件系统或 AXP 写入，volume=85 不持久化。已请求一次实际听感，结果尚待用户；软件发送通过不等于听感通过。结束后立即恢复无 probe 表盘镜像，恢复结果待补录。

### User-requested repeat with explicit start

用户请求“再来一次”，第一轮不判定听感。先完成上一轮恢复写入校验，再将同一参考 BIN App-only 刷入并以 --after no-reset 留在 bootloader，`/private/tmp/espocket-audio-reference-repeat-flash.log` 校验 PASS。明确提示“几秒后开始”后才 reset 触发，以避免自动刷入启动的听音时机不清晰。

`/private/tmp/espocket-audio-reference-repeat-device.log` 再次记录 codec open OK、首笔 3200 字节发送、约 10 秒后 STOPPED/codec closed/PA disabled、app_main 正常返回。此次重复由用户直接要求，未因软件日志自动要求多轮听感。结果待用户；随后恢复表盘固件。

### Reference hearing passed; real format mismatch found

用户对明确提示后的第二次参考播放确认“听到了短音”。因此本机在当前独立 TX/DAC 参考路径可出声；不是所有 product Audio 路径已验收，也不关闭 004/04。参考镜像无 AXP/NVS 写入，实际 product volume 仍由此前用户保存值控制。

复查旧 `/private/tmp/espocket-audio-probe-v2-user-capture.log`：HAL 实际 Set volume 到 93，并维持约 3.6 秒，期间继续 Playing；不能把 service text 或后来 volume=36 的 dump 当作 93 时的实际寄存器证据。旧实际播放器日志每轮 Get info, rate:48000, channels:1, bits:16；同时 I2S/DAC 是 16000/2/16。非零 PCM 统计及每轮约 1.5 秒发送时长支持格式不匹配，但声称其为完全无声的唯一原因仍需物理确认。

锁定 AudioProcessorPlaybackConfig 的 player 默认为 16000/2/16，audio_manager_config 使用它；simple-player 默认启用重采样至 48000，未启用 channel/bit converter，av_processor 读取 compile-time destination 配置，导致未将 WAV 转为相同硬件格式。候选 staging 现在显式启用重采样至 16000、channel converter 到 2、bit converter 到 16。普通 production 配置与 managed_components 不改。CONFIG 选择只适用于当前锁定 playback candidate，不声称覆盖自定义 DAC format。

新增实际 staging/verification seam 回归，旧实现 `/private/tmp/espocket-audio-format-red.log` FAIL（缺少输出约束）；修正后 `/private/tmp/espocket-audio-format-green.log` 9 tests PASS，并拒绝 48000/mono/禁用转换/32bit 输出。该回归锁住已实测的不匹配，不把它当扬声器听感回归。完整构建、真实 Get info 一致性与听感仍待验证。

### Format candidate build

81 项 host checks 和 200 Markdown 检查 PASS；完整 `/private/tmp/espocket-audio-format-build.log` 构建 PASS，SDK 与精确依赖校验 PASS。修正后的现有听感 fixture 候选 ELF `7a72035bddd0c55e8c25e410b73b5e01bc1884f55971d7be1c655fe83b4f0190`、BIN `5ee745c264152f4300d52e8febdffb238866a1e8c731095f79a8acf6b0038474`、hello `7a72035bd`，保存在 `/private/tmp/espocket-audio-format-preserved/`。配置 hash 单列 `/private/tmp/espocket-audio-format-inputs.json`。App-only 写入校验 PASS；该候选不再包含 PCM/register/I2S instrumentation。实际格式/听感待设备检查。

同时已从隔离项目移除 fixture source、WAV 与 Adapter/CMake 注入，准备同样修正格式但无自动测试音的恢复候选；原始 checkout 的 App/资源不改。

### Actual corrected output passed

`/private/tmp/espocket-audio-format-boot.log` 启动 PASS；`/private/tmp/espocket-audio-format-owner-result.log` 自动门槛 PASS：实际连续 Get info, rate:16000, channels:2, bits:16，不再出现旧的 48000/mono；Owner Playing 正常、Home 后 STOPPED/Storage 删除自己的 fixture。每轮 WAV 发送恢复到约 1 秒，符合目标格式。此为格式、生命周期门槛，不代替 speaker 物理听感。现存重复 i2s_channel_disable 的 teardown 诊断仍存在，与格式修正分开跟踪。

请求用户一次产品路径听感：Settings Sound 中将实际 Volume 调至约 85，听后降低音量，再 PWR Home；由用户通过真实 Settings Owner 调整，不由 fixture 更改或恢复其偏好。Serial 捕获 `/private/tmp/espocket-audio-format-user-capture.log`；听感尚待回应。

无 fixture 的修正恢复候选 `/private/tmp/espocket-audio-format-clean-build.log` 完整构建 PASS，SDK/精确依赖校验 PASS，Adapter/CMake 与 checkout 原文相同。ELF `b9b4a413f7017313214a6b3f29a7f171201d4455f918c2a0a22e2a9ca0edd40c`、BIN `1be447353b882a636636b5358abf39b316ac6eb5d8a14c1b846741f126aa14d9`，保存在 `/private/tmp/espocket-audio-format-clean-preserved/`。尚未刷入，避免提前移除等待用户观察的 test tone。当前设备仍为修正 fixture `7a72035bd`，自动测试后处于 Watch Face，fixture 文件已清理；用户进入 Sound 才重新触发。120 秒串口监听窗口内未见本次人工操作，因此不补造听感/音量证据，保持问题 pending。该 slice 只提交配置修正与已验证的真实格式回归，不提前采用生产 Audio 依赖或关闭 004/04。
