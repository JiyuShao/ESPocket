# 2026-10-03 — Audio、主题与默认产品构建收尾

用户授权完成 004/07、004/10 并将验收候选纳入默认构建，不推送。另一聊天正在实施 017 主题变量迁移；本轮固件、Runtime 包与隔离主机检查使用 ea5cebc 的已提交主题资源，不混入其未完成修改。

## 默认构建与部署

默认 production 组合包含 Runtime/Core/HAL/Settings/Display/Board Manager 六个准确应用的组件补丁；原 registry lock 与 Audio 补充依赖、实际 override_path、Recorder/AFE 关闭及 16000/stereo/16bit 配置均校验通过。完整构建通过，identity 74b1b55ce，ELF SHA256 `74b1b55ce945ffaedc734c494b9274959d63cccbecf67bd0d9c060bbe19cc133`，BIN SHA256 `f3d5b1f0f0eb8d69fcf6ba1977ff2003f2e88b877f86bbd28f44cf7aebfbfeaf`。

仅写 App 0x60000 和有完整备份的 LittleFS 0xaa1000，写入校验与启动通过；未写 NVS、bootloader、partition table 或 model。启动恢复 Light。原始 managed_components 未改。

## Runtime 资源部署

锁定 Toolkit 1.0.1 在隔离副本重新打包。设备旧文件系统完整备份 `/private/tmp/espocket-pre-production-littlefs.bin`；更新镜像只改参考 App manifest 与 res/cards.json，所有其他文件哈希保持一致，详细 ledger `/private/tmp/espocket-runtime-image-update.json`。属于当前开发设备离线资源更新，不声称完成正式签名安装事务。

## 主机与普通镜像回归

所有 component checks 与 67 个 host tests 在独立树通过，日志 `/private/tmp/espocket-final-isolated-host-verified.log`。该树首次缺少 Git/生成 Board 文档目标，补齐后源码检查通过、Markdown 209 文档另行通过；没有跳过门槛。共享工作树当时受 017 未完成改动影响的失败日志 `/private/tmp/espocket-final-host.log` 保留，未误报为本轮通过。后续 fixture 唯一路径和 peer 状态扩展回归另行通过。

74b1b55ce apps 套件 PASS（57 步），Native/Runtime 导航、待决 Back、息屏恢复与 Home 清理通过，最终 Watch Face、display=true、无前台 App、inputBusy=false。报告 `/private/tmp/espocket-production-apps/20261003T154311Z-2931dc96-dc18-46e7-89ea-697186f12c35/report.json`；输入 synthetic，不冒充视觉。

## 主题与视觉

普通镜像上 Later 关闭、Home 清理、确认重启恢复 Dark/Light 且 Settings 仍可导航均通过，日志 `/private/tmp/espocket-final-theme-cancel-result.log`、`/private/tmp/espocket-final-theme-dark-result.log`、`/private/tmp/espocket-final-theme-light-result.log`。

用户确认深色紧凑弹窗“基本正常”，浅色“正常，浅色按钮清楚”。用户指出问号看起来怪；源码确认它是 Question 图标的文本替代，不是报错或缺失字形，保留后续样式改进意见。

## 2026-10-04 Card 收尾

临时 Audio/Card fixture 54b8e7a21 单独完整构建，ELF SHA256 `54b8e7a21d48f643206d2afe9101219f4544e2f4810571f735aa87aae8c26f09`，BIN SHA256 `e839da88ae5359cb9ff753860da6a357d0731daa4637726cf9acf40f9f31018d`。Card sample 只在 RAM 中，不改用户 NVS；普通 production 无 sample 或播放 probe。

在 Dark/Light 分别验证 Native/Runtime summary 打开 Root、detail 打开 Detail、Back 回 Root、PWR Home，通过；日志 `/private/tmp/espocket-final-card-dark-result.log`、`/private/tmp/espocket-final-card-light-result.log`。用户确认已部署浅色 Runtime Card“正常，Card 显示清楚”；004/10 关闭。原始串口 `/private/tmp/espocket-final-card-54b8e7a21.log` 最后为 Light 路径。

## Audio 准备与恢复

第一份 fixture 发现旧 V2 WAV 后按规则拒绝覆盖，未进入 Playing，不算 Audio 修复验收。旧文件保持原样；详情见 [I2S 清理记录](2026-10-03-i2s-teardown.md)。

唯一文件路径 fixture 重构建完成：identity 474d7dc30，ELF SHA256 `474d7dc30da201d4b9388e9536fd0bd7f6d329f3595ef60b38916cf70228b636`，BIN SHA256 `4d74e763779705ce4b7240a6191091f93720cdcc546cc23f43fdd4ebe28c9c70`，owned_path `/littlefs/.espocket-audio-probe-423d1d363dc9411b94eab9c8bdff4a90.wav`。

首次写入该 fixture 时 USB 串口临时消失，写入未完成，尚未执行 Audio 测试；失败日志 `/private/tmp/espocket-final-unique-fixture-flash.log` 保留。保护性恢复普通 74b1b55ce 校验与启动成功。不会把串口失败算作播放或 I2S 失败/通过，准备以独立 attempt 重试。

## Audio 最终设备结果

独立低波特率重试写入 474d7dc30 校验、启动通过；两轮 audio-playback PASS，每轮实际 Playing、Home 停止与自有文件删除、重新播放成功，没有重复 I2S disable。报告 `/private/tmp/espocket-audio-teardown-unique/20261003T161144Z-a4ec85e0-eea7-4789-b045-9b10074d9c5d/report.json`，最终 Watch Face、无前台 App、inputBusy=false。004/07 关闭，先前两个准备/写入失败仍保留，不改写为成功。

## 最终恢复与检查

保护性最终恢复普通 production 74b1b55ce 写入 hash 校验与启动通过；日志 `/private/tmp/espocket-production-final-restore-retry-flash.log`、`/private/tmp/espocket-production-final-restore-retry-boot.log`。仅写 App，Runtime 新资源与其他文件保留，旧 V2 WAV 未删除。最终精确 hello identity 与 snapshot 核对通过：Watch Face、display=true、无前台 App、canBack=false、backPending=false、inputBusy=false；原始 `/private/tmp/espocket-production-final-snapshot.log`。普通镜像无 Audio probe 或 Card sample。

加入 UUID 工具回归与 peer 状态扩展后的隔离统一检查最终全部通过（所有 component checks、68 个 host tests 与 Markdown），日志 `/private/tmp/espocket-final-all-checks.log`；共享工作树最终 Markdown 214 文档通过、git diff --check 通过。不自动 push；其他聊天的 017 改动保留，由其独立提交/验收。
