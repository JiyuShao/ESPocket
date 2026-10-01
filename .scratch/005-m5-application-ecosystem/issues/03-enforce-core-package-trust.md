# 03 — 执行 Core 持有的 package trust gate

**What to build:** 一条公开 install path，对完整 remote package 执行验证和事务式提交，并在重启后重新验证 trusted state。

**Blocked by:** 上游 Core/Store 的统一 install/discovery seam；[08 兼容签名包与发布路径](08-publish-compatible-signed-package.md)。

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
