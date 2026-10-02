# 2026-10-03 — Playback-only HAL candidate

用户明确允许采用 patch 修复上游，更新旧禁止补丁的工作边界，见 [ADR-0016](../../../docs/adr/0016-maintained-upstream-fixes.md)。Recorder 关闭要求继续有效。

## Red/green feedback

`python3 -m unittest discover -s firmware/test/host -p test_audio_playback_only.py` 最初执行真实锁定 HAL AudioProcessorCore::open_common，player 有效而 recorder 为空，输出 `FAIL: playback-only requires Recorder`。假设依次为配置耦合、open_common 强制 Recorder、底层 manager 不支持空输入回调。

[HAL 候选补丁](../../../firmware/patches/espressif__brookesia_hal_adaptor/0.8.4/002-playback-without-recorder.patch)保持同一 PlaybackIface/Audio Owner：Processor 配置只要求 Player，playback-only 默认不开启 Processor，避免改变普通镜像；没有 Recorder 时不注册 Encoder、不打开 ADC、不配置 rec_io。输出格式来自 player config；存在 Recorder 时继续已有双向格式归一化。直接 encoder 调用在没有 Recorder 时拒绝。

Host 回归执行原版预期失败与补丁版通过；另编译真实 get_interface_specs，证明 Recorder off 不暴露 recorder/encoder，仍具有 playback。真实音频、板级 Player 与完整 optional dependency 构建不由替身证明。

## Optional backend candidate

原生产 lock 未包含 av_processor，因为 Processor 关闭。阅读官方 [av_processor 0.6.6](https://components.espressif.com/components/jason-mao/av_processor/versions/0.6.6/readme)并下载该精确版本 archive，仅用于临时源码分析；ZIP SHA-256 `9408bcec1ffb8b763da3ba43e2fb20d2c98f8f866397a6519897ff3dc00912ed`。其实际 audio_manager_init 复制 config 后初始化 codec/manager，不要求 rec_io；audio_playback_open 兼容入口存在。此检查不证明全部 Brookesia TypeConverter 兼容。

独立实验 `/private/tmp/espocket-playback-only-experiment` 明确固定 av_processor=0.6.6，Audio/Player/Processor 开启，Codec Recorder、AFE、Media Dump 与 Video Processor 显式关闭。配置与 registry 解析/完整构建结果待补录。生产配置与 dependencies.lock 未更改；不把新增实验依赖冒充已接受生产 baseline，也不将候选页缓存当作最新版本断言。

## Remaining gates

必须验证新增依赖的精确身份及原有依赖无意外 drift、完整编译/链接和大小，再检查板级录音未打开，最后 Settings Sound/Volume 实际声音与音量观察一次。当前设备保持 Core/brightness 普通候选，Audio 实验不自动刷入，工作票不关闭。

独立实验 reconfigure 通过：新增 17 项 registry 依赖，精确 av_processor 0.6.6，component hash `67b9054b361f90c18bddf781bd934b735c63062217a25a53e59f4eff15f78c58`；除三项 source override 外，所有既有 registry version/hash 无 drift。生成配置复核 Processor=y，Recorder/AFE/Media Dump/Video Processor 无开启项。完整编译正在执行，尚不采纳新 lock 为生产配置。

第一次完整编译失败于 AudioDevice 与 CodecPlayer 编译单元的 IDF/Picolibc `__noreturn` 属性拼写，诊断与原 display 兼容问题相同。复用既有 compatibility header，精准应用到这两个实际失败编译单元，保留属性语义与告警门槛；源码改变记录于 firmware/CMakeLists.txt。原失败日志 `/private/tmp/espocket-playback-only-build.log` 保留，修复重编译结果待补录。

Exposure Decision：HAL 与编译兼容 seam 是内部实现，不对 Assistant 暴露原始播放器、Recorder 或 codec handle。现有 UI Sound/Volume 的 Owner 仍是 Brookesia Audio/Playback；新的 AI Playback Action 延后，不因修复而赋予 Assistant 音频访问。

修复 compatibility 后完整构建通过；ELF `bd0dd79704a58ed970bc049744fd7b924a86c2ae673fab9c050aff3ee2a40312`，BIN `b836a1621c1ac004a6c7896f66f1d84a21ee2e5161430b2db661906a579adf44`，App 7,539,216 bytes，srmodels 仅 4 bytes。精确 HAL source inventory/override、Recorder/AFE 配置再次通过复核；原始三个 managed component inventory 均未改变。依赖精确 snapshot 保存为 HAL patch 目录的 audio-candidate-dependencies.json。

新增可复现构建入口 `--patch-set audio-candidate`：自动固定这 17 项新增版本/hash，强制 playback-only 配置，在 reconfigure 后拒绝 Recorder/AFE/Dump/Video 被重新开启，并要求 registry lock 精确相等。普通 `production` 不采纳这些候选；`hal-candidate` 只应用 HAL 差异，不自动打开 Processor。默认与候选隔离、取消 Recorder 配置及其反向验证有主机回归。

## Candidate boot failure

App-only 写入并 hash 校验成功。一次 navigation attempt `20261002T213449Z-fe3e2a3e-88d9-449d-a0e7-9746a8a2bf63` 未收到 hello，报告 FAIL，不能算导航通过。随后 reset 抓取日志显示 LVGL secondary buffer 46,600 bytes 分配失败，GUI Display source 启动失败，System 输出 Fatal initialization failure 后 app_main 返回；未观察到 panic。证据 `/private/tmp/espocket-audio-candidate-boot.log`。仅凭该结果不能归因到具体 Audio 分配；下一步应在实际 Audio/GUI Owner 初始化边界记录 heap capability 与最大可用块，定位资源占用后再修改，不靠随意缩减栈或开启 Recorder 绕过。

候选不采纳为普通固件；已恢复并写入校验通过的 `5e79e3a82` 普通镜像。恢复后的第一次只读检查读到启动完成标记而中止，未观察到 panic；待启动完成后第二次 hello 精确身份核对、release、snapshot 均通过，最终 surface=watch_face。记录 `/private/tmp/espocket-audio-restored-readonly.json`。未做声音/音量验证，也未进行 Store 网络刷新。新构建入口 audio-candidate 的 prepare-only 实际执行通过。最终统一 host checks 通过（Owner 21 项、cross-component 53 项）。
