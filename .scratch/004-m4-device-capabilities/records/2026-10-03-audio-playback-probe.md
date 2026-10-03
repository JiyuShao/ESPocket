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
