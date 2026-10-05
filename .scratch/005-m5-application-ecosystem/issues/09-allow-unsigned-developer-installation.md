# 09 — 开发者模式包准入与 Super 兼容运行

**What to build:** 将设备的 Developer Mode 准入传给 Core 的同一安装边界，允许开发路径安装完全未签名的 Runtime 包，显式记录发布者未验证身份；允许声明 super 的旧包通过目标系统匹配，提供不要求页面导航契约的兼容运行。

**Blocked by:** [03 Core 统一 install/discovery gate](03-enforce-core-package-trust.md)。

**Status:** ready-for-agent

- [x] 普通模式拒绝未签名包；开发者模式仅允许完全未签名包例外，半套和签名验证失败不自动降级。
- [x] Store、其他正式安装入口使用同一 Core policy；不扩展 USB 合成输入协议的命令范围。
- [x] 保留 artifact/member/path/compatibility 检查、不可变 candidate、事务提交、回滚和重启验证；receipt 记录未验证发布者身份。
- [x] 关闭和重新开启开发者模式的已安装 App 行为通过 host policy 和隔离真机矩阵；运行中停止、保留安装、拒绝启动与重新开启后的准入/启动通过，不提升为 trusted release。
- [x] 主机准入矩阵与最终完整构建通过；开发验证与正式发行验收分开记录，见 [最终构建证据](../records/2026-10-04-package-final-build.md)。
- [ ] 实际 Store 安装、外部 App 运行和开发模式切换的设备证据完整；不以主机或构建结果代替。

## Comments

2026-10-04 用户已接受仅开发者模式允许未签名安装；见 [ADR-0018](../../../docs/adr/0018-developer-mode-allows-unsigned-packages.md)。super 兼容是独立检查；Flappy Bird 的当前可行性事实见 [设备兼容核查](../records/2026-10-04-developer-package-policy.md)。尚未实现或刷入该策略。

## 已确认的实施门槛

- [x] 所有声明 super 的 Runtime 包在开发模式进入同一 Core 校验；不改设备系统身份或原包，不跳过其他兼容／安全要求。
- [x] Receipt 分别记录签名例外和目标系统例外，安装、启动、重启发现、更新与 Store 本地扫描使用同一准入判断。
- [x] 关闭开发模式保留安装但禁止启动依赖例外的 App，并停止运行中实例返回表盘；再次开启重新准入。隔离真机矩阵已通过。
- [x] 缺少导航声明的外部 Flappy 包实际兼容运行；快照明确导航不可用，不伪造 Page／Root／canBack，实际 start 与 PWR Home 通过。
- [ ] 安装前采用产品契约中的确认提示；未签名追加发布者说明，Cancel/dialog replacement/show failure 无安装调度副作用。实际触屏确认仍待真机验收。
- [x] 主机矩阵覆盖 normal/developer、espocket/super/其他系统、signed/unsigned/损坏签名、关闭模式、receipt、update 与重启恢复；实际安装、退出和保留旧版本证据独立保留为设备门槛。

2026-10-04 追加：用户共同理解确认已完成，关闭模式行为与 super 范围不再待问。前述未实现事实保留。实施仍依赖 03 的 Core 统一事务门槛，不用 Shell 私有 installer 绕过；平台兼容能力按具体故障逐项评估。

2026-10-04 实施结果：Core/Store/product 全链路代码与 host matrix 已通过，见 [package implementation evidence](../records/2026-10-04-package-implementation-evidence.md)。完整构建受磁盘空间阻塞，未刷机；实际 Store Cancel/install/launch/PWR/reboot/mode-off/re-enable 因无最终镜像且当前动态启动入口属于 04 范围，保持未验收；下一步需要构建空间、物理设备与启动入口，状态为 `ready-for-human`。

2026-10-04 后续检查：当前完整主机检查和候选 `f6cb09bbd` 完整构建通过，磁盘 blocker 已解除；停止重试、Card rollback 与删除失败门槛已核对。未刷机，下一步为明确授权 app/LittleFS 本地备份后执行 app-only 设备验收。锁定 Store 的 Installed 页面没有启动入口，launch 等门槛仍依赖适用入口；详情见 [最终构建记录](../records/2026-10-04-package-final-build.md)。


2026-10-04 设备推进：用户已授权并完成 app/LittleFS 本地备份。首个 app-only 候选 `86558ce79` 因旧板级配置关闭 HAL 而启动失败；恢复原设备已验收的完整 sdkconfig 后，最终 `f2791ea1b` 构建、输入校验、Flash hash 与启动通过，Native/Runtime 样例合成输入回归通过。Store 点击包操作后打开了真实弹窗，但计算 Cancel 点击未关闭，尚待用户核对屏幕标题／按钮；未提交安装，未验收 receipt 与安装后 discovery。该人工信息及适用外部启动入口仍限制剩余设备验收，票不关闭；详见 [最终构建与设备记录](../records/2026-10-04-package-final-build.md)。

2026-10-04 截图推进：当前镜像 f3fdd7e82 的构建、检查、app-only 写入、启动和默认 512-byte 分块截图通过，已能直接读取实际屏幕。Local 扫描完成后 Flappy Bird 显示 Installed，Core 启动也发现该包；此前“尚未安装”只代表当时未取得正向证据，不能继续作为当前设备状态。计算坐标在当前滚动位置指向 AI Chatbot，先前弹窗不算 Flappy Bird Cancel/Continue 证据。receipt、准确安装过程和外部启动条件仍未满足，票保持开放；见[截图设备证据](../../012-test-automation-contract/records/2026-10-04-rendered-frame-screenshot.md)。

2026-10-04 全部执行：用户已授权其余实现与真机验收，不再存在备份或启动入口的人工 blocker。正式发行输入尚未准备，按用户回复保留 08 的外部发布阻塞；本轮 Launcher、Store、signed test lifecycle 与模式切换证据见[自动验收记录](../records/2026-10-04-launcher-and-lifecycle-acceptance.md)。

2026-10-04 隔离镜像 `a2f85c1a1` 的完整 lifecycle fixture 获得 PASS COMPLETE，真实 mode off/on 与外部 Flappy start/PWR 已通过。正常 `a963c55b8` 的 Store 安装/卸载全链路仍在验收，06 发现快速退出栈溢出；本票保留开放，详见[自动验收记录](../records/2026-10-04-launcher-and-lifecycle-acceptance.md)。
