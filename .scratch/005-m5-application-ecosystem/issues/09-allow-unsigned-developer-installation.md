# 09 — 开发者模式包准入与 Super 兼容运行

**What to build:** 将设备的 Developer Mode 准入传给 Core 的同一安装边界，允许开发路径安装完全未签名的 Runtime 包，显式记录发布者未验证身份；允许声明 super 的旧包通过目标系统匹配，提供不要求页面导航契约的兼容运行。

**Blocked by:** [03 Core 统一 install/discovery gate](03-enforce-core-package-trust.md)。

**Status:** ready-for-agent

- [ ] 普通模式拒绝未签名包；开发者模式仅允许完全未签名包例外，半套和签名验证失败不自动降级。
- [ ] Store、其他正式安装入口使用同一 Core policy；不扩展 USB 合成输入协议的命令范围。
- [ ] 保留 artifact/member/path/compatibility 检查、不可变 candidate、事务提交、回滚和重启验证；receipt 记录未验证发布者身份。
- [ ] 关闭和重新开启开发者模式的已安装 App 行为按用户确认实施并验证，不提升为 trusted release。
- [ ] 主机准入矩阵及必要完整构建／设备证据通过；开发验证与正式发行验收分开记录。

## Comments

2026-10-04 用户已接受仅开发者模式允许未签名安装；见 [ADR-0018](../../../docs/adr/0018-developer-mode-allows-unsigned-packages.md)。super 兼容是独立检查；Flappy Bird 的当前可行性事实见 [设备兼容核查](../records/2026-10-04-developer-package-policy.md)。尚未实现或刷入该策略。

## 已确认的实施门槛

- [ ] 所有声明 super 的 Runtime 包在开发模式进入同一 Core 校验；不改设备系统身份或原包，不跳过其他兼容／安全要求。
- [ ] Receipt 分别记录签名例外和目标系统例外，安装、启动、重启发现、更新与 Store 本地扫描使用同一准入判断。
- [ ] 关闭开发模式保留安装但禁止启动依赖例外的 App，并停止运行中实例返回表盘；再次开启重新准入。
- [ ] 缺少导航声明的外部旧包可兼容运行；不伪造 Page／Root／canBack，不支持系统指定 Page 打开或统一页面 Back；内部返回归 App，PWR Home 及异常退出清理仍验证。
- [ ] 安装前采用产品契约中的确认提示；未签名追加发布者说明，取消无安装副作用，不在提示中展示导航接入术语。
- [ ] 主机矩阵覆盖 normal/developer、espocket/super/其他系统、signed/unsigned/损坏签名、导航已接入/缺失以及关闭模式和重启；实际安装、退出和保留旧版本证据独立记录。

2026-10-04 追加：用户共同理解确认已完成，关闭模式行为与 super 范围不再待问。前述未实现事实保留。实施仍依赖 03 的 Core 统一事务门槛，不用 Shell 私有 installer 绕过；平台兼容能力按具体故障逐项评估。
