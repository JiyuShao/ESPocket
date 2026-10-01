# 08 — 取得兼容签名包与发布更新路径

**What to build:** 一个可供端到端验证的 ESPocket-compatible signed release package，以及受支持的 catalog publication/update 路径。

**Blocked by:** 官方兼容包和受支持的 publication/update route。

**Status:** needs-info

- [ ] Package 的 system compatibility 接受 `espocket`，不通过冒充其他 System 绕过检查。
- [ ] Release signature、member integrity、publisher/key identity 与版本信息满足 [Runtime package trust](../../../docs/design/product/05-runtime-package-trust.md)。
- [ ] 提供可验证的初始版本和更新版本；catalog metadata 与下载 artifact identity 一致。
- [ ] 记录可复现的发布更新步骤或官方支持依据；unsigned debug/build-staged package 不冒充 remote release。

## 证据边界

[2026-09-28 报告](../records/2026-09-28-acceptance-report.md#known-official-packages)中检查的官方 Calculator 包只声明 `super`，且缺少 release signature；该历史事实不代表后续包已经核查。本 ticket 关闭前需重新检查实际候选。
