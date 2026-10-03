# 2026-10-03 — I2S playback 退出清理

## 失败与归属

旧设备 Home 退出日志中 `i2s_channel_disable: the channel has not been enabled yet` 已见听感记录。最小主机回归提取并执行锁定 Board Manager 0.5.15 的真实 periph_i2s_deinit：初始化标记 out_en=true，但 Codec close 已把驱动通道停用，再释放即触发重复 disable 断言。直接运行 run_teardown(original) SIGABRT，旧源码负例测试验证此具体断言，未以其他失败代替。

实际顺序为 HAL player close → esp_codec_dev_close 停数据通道 → Board Manager device deinit 删除 codec/data interface → periph_i2s_deinit。Board Manager 的 in_en/out_en 是初始化标记，不能代表被 Codec 调用后驱动实时状态。其他候选为 Codec 自身重复 close 或共享通道仍在运行；当前负例与驱动状态差分把修正限定在 Board Manager peripheral release。

## 修正

受维护补丁 espressif__esp_board_manager/0.5.15 在 IDF 6 使用公开 i2s_channel_get_info.is_enabled 查询实时状态，仅关闭正在运行的通道。查询/关闭/删除失败时返回失败并保留句柄以供重试；空闲 peer 的释放同样检查失败。旧 IDF 保留原初始化标记策略，不声称修复未支持版本。

完整 registry source inventory/hash 与 patch hash 保存于 manifest；组件包未公开 source commit，明确记录为未知，绑定 Registry 0.5.15 与完整源码 hash，不虚构提交身份。原始 managed_components 未改，上游问题未提交。

主机回归覆盖 TX/RX、Codec 已停用/仍在运行、peer 真实停用/运行与查询/关闭/删除失败保留后重试。实际驱动调用由测试 sink 验证；完整固件与 Play→Home→replay 设备门槛待后续结果，不把主机通过当作设备验收。

## 2026-10-04 设备准备失败与保留

第一份 fixture 54b8e7a21 未进入 Playing：Storage 发现设备旧 `.espocket-audio-probe-v2.wav`，按契约拒绝替换。此为测试前置失败，不是 I2S 修复回归通过或失败；原报告 `/private/tmp/espocket-audio-teardown-final/20261003T155630Z-a9baa5fe-eb51-414c-a6eb-04a8aaf92bdd/report.json` FAIL 保留。未删除旧文件，也未声称 Home 已停止尚未启动的音频。

准备工具改为每次生成 UUID 绑定的测试路径及对应 file URI，并把实际路径/header hash 写入 probe manifest；两个装配路径不同、路径与 URI 一致、模板不变及非法 token 拒绝有主机回归。重新构建只更换临时 fixture 的文件身份，真实 Board Manager 修复和生产固件不变。

## 设备验收

唯一 fixture 474d7dc30 降低波特率后的独立写入校验、启动通过。audio-playback 两轮 PASS：每轮真实 Owner Playing，PWR Home 后停止并删除本次拥有的 WAV，再次进入 Sound 成功播放；没有 `the channel has not been enabled yet` 或 codec deinit 错误。旧 V2 文件未删除。报告 `/private/tmp/espocket-audio-teardown-unique/20261003T161144Z-a4ec85e0-eea7-4789-b045-9b10074d9c5d/report.json`，最终 Watch Face、display=true、无前台 App、inputBusy=false、release=ok。004/07 关闭。

输入是 synthetic，未以事件代替听感；004/04 原物理出声/音量/停止验收继续有效，本次只改实际释放路径，无需重复人工听音。普通 production 不包含自动播放 fixture，测试后恢复其镜像。

最终恢复普通 production 74b1b55ce 的写入、启动与表盘快照通过，无 Audio probe 或 Card sample。所有主机门槛与 68 个 host tests 通过，完整最终证据见 [默认构建收尾](2026-10-03-production-followup.md)。
