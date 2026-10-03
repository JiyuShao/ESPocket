# 03 — 执行 Core 持有的 package trust gate

**What to build:** 一条公开 install path，对完整 remote package 执行验证和事务式提交，并在重启后重新验证 trusted state。

**Blocked by:** 上游 Core/Store 的统一 install/discovery seam；普通模式发行验收依赖 [08 兼容签名包与发布路径](08-publish-compatible-signed-package.md)，开发者模式例外边界由 [09](09-allow-unsigned-developer-installation.md) 持有。

**Status:** needs-info

- [ ] Signature、member integrity 与 compatibility 在 unpacking 前 fail closed。
- [ ] Update rollback 与 cleanup 保留上一可信版本。
- [ ] Reboot discovery 拒绝没有有效 receipt 的 package。

## Required transaction shape

公开 Core operation 必须锁定或复制一个不可变 candidate；基于同一字节验证可选 source digest、release signature 与 signed member；验证 compatibility；解包到新 staging directory；准备资源；写入 pending receipt；原子切换版本；验证新 App record；提交 receipt；最后才删除 backup。

Receipt 绑定 package/version identity、artifact 与 manifest digest、signing-key identity、policy version、committed member、Platform Baseline 与 transaction identity。Built-in package 使用显式 build allowlist，不以目录存在作为信任依据。

## Required matrix

- [ ] Activation 前拒绝 digest mismatch、缺半边 signature、unknown key、member 被修改或多出，以及 incompatible system。
- [ ] 拒绝 verify-to-unpack mutation 与 path escape。
- [ ] 每种注入的 update failure 或 power-loss state 都保留旧 App 与 private data。
- [ ] Uninstall 时移除 receipt 与对应 cache；清理 orphan staging 时不删除 committed version。
- [ ] Store、USB 与任何 developer installer 都通过同一 gate。

## Comments

2026-10-04：[ADR-0018](../../../docs/adr/0018-developer-mode-allows-unsigned-packages.md) 增加仅开发者模式可允许完全未签名包的例外。本票的签名拒绝矩阵按普通模式执行；开发模式仍拒绝半套／验证失败签名，记录未验证发布者身份，保留成员、路径、不可变输入、事务与重启检查。关闭开发者模式后的启动规则待确认；不把例外算作本票已完成。

2026-10-04 追加：09 已确认 super 系统匹配及关闭模式行为。03 的 incompatible-system 拒绝矩阵区分普通模式与明确开发者例外；统一 gate 必须提供持久准入事实供启动与 discovery 使用，不视为本票已完成。
