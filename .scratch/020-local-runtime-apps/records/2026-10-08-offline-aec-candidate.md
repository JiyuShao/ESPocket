# 2026-10-08 — 离线 AEC 与 Chat 增量更新候选

本轮用户确认设备不在身边并授权离线准备。未连接串口、播放声学输入或部署。正式设备仍为 `c60a29d3b` 半双工防回音版本，目标“啊灰啊灰”模型仍未获取；请求草稿未向外部发送。

## 实现与验证边界

HAL 008 默认关闭；从真实 DAC 增益后 PCM 取左声道播放参考，保留录音第一通道，替换第二通道并设置 MR／AEC。参考环 500 ms，按时间戳估计关联，过期／缺失／写入失败归零，生命周期重建清空。只接受 16 kHz／双声道／16 bit；不能同时启用播放录音抑制或自定义 AFE backend。软件参考不是已确认的板级回采，也不是已校准的 DAC／ADC 同步。

Host 覆盖格式拒绝、通道保留、延迟／过期／环覆盖／失效／实例重建，以及真实录放回调、尾帧与 MR 初始化。MR 缺失曾使 open 回归失败，补齐实际条件后通过。Chat bindings 回归先证明旧源码重复提交，更新后覆盖去重、变化、失败重试与实例重建。离线断言不能证明声学消除率或触摸 timeout 已解决。

参考环当前约 128 KiB，启动前分配；AEC 还增加算法／内部 RAM 压力。旧固件启动内部 free／largest 曾仅为 25,807／17,408 bytes，必须把 AEC 初始化和内存作为第一真机门槛。HalfDuplex encoded mic 仍在播音时丢弃普通音频，候选只保留 WakeNet 的唤醒词打断链路。

Chat 包版本 0.1.2，86,779 bytes／31 成员，SHA-256 `4f239b3ee6a4ad620644bc8b4a4419b8ebc363a0bd264fff40e5d4f9e33239fe`。尚未部署；包含真实私有资源的包不公开再发行。

## 构建过程与回退

使用现有隔离副本 `/private/tmp/espocket-local-runtime-20261007-v4`，输入证明 `/private/tmp/espocket-aec-candidate-inputs-v2.json`。Registry 无法解析已锁定 usb 1.6.0；关闭 component manager 又使组件短名称无法解析，因此恢复原 CMake。改为 81 个本地精确缓存／批准补丁 override，版本不变；YAML 格式须保留 Settings 验证要求的带引号 version／override_path。完整离线组件 inventory 保存在 `/private/tmp/espocket-aec-offline-input-inventory.json`，81 个组件版本与原 lock 相同；最终 sdkconfig／lock／YAML hash 与记录一致。

旧 App 与 ELF 已核对部署记录并保存 `/private/tmp/espocket-c60-rollback/`：App SHA-256 `4fd7c657b22e0a4947993ba554319d426a25efa57860304aa347556d70828101`，ELF SHA-256 `c60a29d3b3bdb963cc459405139971f2fd91b5f8ec2d7b6978aadef102fc9889`。既有 0.1.1 LittleFS 是历史备份；下次部署前必须读取最新设备内容，不能把历史备份当作当前完整用户数据。部署与回退步骤由 [05](../issues/05-aec-interruption-candidate.md) 持有。

## 检查

首轮统一检查的 164 项 host tests 通过，2 项因 host littlefs 环境跳过，但当时 Markdown 因未链接请求草稿失败。修复链接后独立 Markdown 检查通过，最终 `python3 scripts/check.py` exit 0，164 项 host tests 通过（2 项因主机环境跳过），所有统一检查通过；原始结果 `/private/tmp/espocket-aec-final-check.log`。记录收尾后另重跑 Markdown。


## 完整候选构建结果

IDF 6.0.1 完整构建通过，镜像身份 `ae90157d1`，App 11,196,992 bytes／14 MiB，分区余量 24%。App SHA-256 `c7c976ba726ecffded17a0aba55abae36f7773edf82d02ffd11cd90d0980e157`；ELF SHA-256 `ae90157d18f3ef03796642345e5c6cb1028a985e807d20f9f22324ad80fa65e3`。构建日志 `/private/tmp/espocket-aec-candidate-build-v5.log`。交付目录 `/private/tmp/espocket-offline-aec-release/` 保存 App／ELF、Chat BPK、有效配置、依赖 YAML／lock、输入证明及 `release.json`。未生成可直接覆盖设备当前数据的候选部署镜像；下次必须从最新 LittleFS 备份保留更新并核对编译 allowlist，不执行整体 `idf.py flash`。

已有跳过的内置更新检查在 `build/littlefs_py_venv/bin/python` 中单独执行，1 项通过，覆盖已有私有数据、未知内容保留、动态安装拒绝。主机回归与完整构建只证明候选代码可编译及指定逻辑成立，真实声学、WakeNet 检出率、AEC 内存与物理触摸仍未验证。
