# 03 — 执行 Core 持有的 package trust gate

**What to build:** 一条公开 install path，对完整 remote package 执行验证和事务式提交，并在重启后重新验证 trusted state。

**Blocked by:** 实施无设计阻塞；普通模式发行验收依赖 [08 兼容签名包与发布路径](08-publish-compatible-signed-package.md)，开发者模式例外边界由 [09](09-allow-unsigned-developer-installation.md) 持有。

**Status:** ready-for-human

- [x] Signature、member integrity 与 compatibility 在 unpacking 前 fail closed。
- [x] Update rollback 与 cleanup 保留上一可信版本。
- [x] Reboot discovery 拒绝没有有效 receipt 的 package。

## Required transaction shape

公开 Core operation 必须锁定或复制一个不可变 candidate；基于同一字节验证可选 source digest、release signature 与 signed member；验证 compatibility；解包到新 staging directory；准备资源；写入 pending receipt；原子切换版本；验证新 App record；提交 receipt；最后才删除 backup。

Receipt 绑定 package/version identity、artifact 与 manifest digest、signing-key identity、policy version、committed member、Platform Baseline 与 transaction identity。Built-in package 使用显式 build allowlist，不以目录存在作为信任依据。

## Required matrix

- [x] Activation 前拒绝 digest mismatch、缺半边 signature、unknown key、member 被修改或多出，以及 incompatible system。
- [x] 拒绝 verify-to-unpack mutation 与 path escape。
- [x] 自动注入的 update failure 与 reboot recovery 状态保留旧 App、private data 与 Card 配置；完整掉电／真机矩阵待设备验收。
- [x] Core uninstall 移除 receipt 与 retained archive；清理 orphan staging 时不删除 committed version。Store 自有下载 cache 不由 Core 删除。
- [x] Store、USB 与任何 developer installer 都通过同一 gate；USB 不扩展确认命令，Developer exception 正常拒绝。

## Comments

2026-10-04：[ADR-0018](../../../docs/adr/0018-developer-mode-allows-unsigned-packages.md) 增加仅开发者模式可允许完全未签名包的例外。本票的签名拒绝矩阵按普通模式执行；开发模式仍拒绝半套／验证失败签名，记录未验证发布者身份，保留成员、路径、不可变输入、事务与重启检查。关闭开发者模式后的启动规则待确认；不把例外算作本票已完成。

2026-10-04 追加：09 已确认 super 系统匹配及关闭模式行为。03 的 incompatible-system 拒绝矩阵区分普通模式与明确开发者例外；统一 gate 必须提供持久准入事实供启动与 discovery 使用，不视为本票已完成。

2026-10-04 实施交接：采用 ADR-0016 的锁定版补丁机制，在 Core 真实 Owner 内补齐统一 gate，不再等待上游提供 seam。03 可先执行开发路径所需基础；08 仍阻塞正式签名发行验收，不阻塞 09 的开发路径实施。Receipt 的 signing-key identity 对未签名包明确记为未验证，signed 包绑定实际信任公钥摘要；transaction identity 必须显式持久化。失败更新不得丢失 App Card 配置，孤立 staging 清理不得删除有效 committed version。

2026-10-04 实施结果：Core gate、receipt identity、replacement rollback、reboot recovery 与 host 注入矩阵已通过；完整构建因工作盘空间不足未产生镜像，设备验收及 08 的正式签名成功路径仍未完成。证据见 [package implementation evidence](../records/2026-10-04-package-implementation-evidence.md)，因此下一步为释放构建空间并执行构建／设备门槛，状态转为 `ready-for-human`。
