# 09 — 开发者模式包准入与 Super 兼容运行

**What to build:** 将设备的 Developer Mode 准入传给 Core 的同一安装边界，允许开发路径安装完全未签名的 Runtime 包，显式记录发布者未验证身份；允许声明 super 的旧包通过目标系统匹配，提供不要求页面导航契约的兼容运行。

**Blocked by:** [03 Core 统一 install/discovery gate](03-enforce-core-package-trust.md)。

**Status:** ready-for-human

- [x] 普通模式拒绝未签名包；开发者模式仅允许完全未签名包例外，半套和签名验证失败不自动降级。
- [x] Store、其他正式安装入口使用同一 Core policy；不扩展 USB 合成输入协议的命令范围。
- [x] 保留 artifact/member/path/compatibility 检查、不可变 candidate、事务提交、回滚和重启验证；receipt 记录未验证发布者身份。
- [ ] 关闭和重新开启开发者模式的已安装 App 行为已实现并通过 host policy 验证；运行中停止、保留安装与重新启动仍待真机验收，不提升为 trusted release。
- [ ] 主机准入矩阵通过；完整构建因磁盘空间不足未产生镜像，设备证据待补。开发验证与正式发行验收已分开记录。

## Comments

2026-10-04 用户已接受仅开发者模式允许未签名安装；见 [ADR-0018](../../../docs/adr/0018-developer-mode-allows-unsigned-packages.md)。super 兼容是独立检查；Flappy Bird 的当前可行性事实见 [设备兼容核查](../records/2026-10-04-developer-package-policy.md)。尚未实现或刷入该策略。

## 已确认的实施门槛

- [x] 所有声明 super 的 Runtime 包在开发模式进入同一 Core 校验；不改设备系统身份或原包，不跳过其他兼容／安全要求。
- [x] Receipt 分别记录签名例外和目标系统例外，安装、启动、重启发现、更新与 Store 本地扫描使用同一准入判断。
- [ ] 关闭开发模式保留安装但禁止启动依赖例外的 App，并停止运行中实例返回表盘；再次开启重新准入。代码与 host gate 已完成，真机行为待验收。
- [ ] 缺少导航声明的外部旧包可兼容运行；不伪造 Page／Root／canBack。`page_adapter_unavailable` 与 PWR Home 路径已实现，实际外部 App 启动／异常退出待设备入口和验收。
- [ ] 安装前采用产品契约中的确认提示；未签名追加发布者说明，Cancel/dialog replacement/show failure 无安装调度副作用。实际触屏确认仍待真机验收。
- [x] 主机矩阵覆盖 normal/developer、espocket/super/其他系统、signed/unsigned/损坏签名、关闭模式、receipt、update 与重启恢复；实际安装、退出和保留旧版本证据独立保留为设备门槛。

2026-10-04 追加：用户共同理解确认已完成，关闭模式行为与 super 范围不再待问。前述未实现事实保留。实施仍依赖 03 的 Core 统一事务门槛，不用 Shell 私有 installer 绕过；平台兼容能力按具体故障逐项评估。

2026-10-04 实施结果：Core/Store/product 全链路代码与 host matrix 已通过，见 [package implementation evidence](../records/2026-10-04-package-implementation-evidence.md)。完整构建受磁盘空间阻塞，未刷机；实际 Store Cancel/install/launch/PWR/reboot/mode-off/re-enable 因无最终镜像且当前动态启动入口属于 04 范围，保持未验收；下一步需要构建空间、物理设备与启动入口，状态为 `ready-for-human`。
