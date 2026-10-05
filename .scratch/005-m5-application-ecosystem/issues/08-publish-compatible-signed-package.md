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

## Comments

2026-10-04：当前设备缓存 Flappy Bird 0.3.0 由实际包扫描拒绝，错误为 `Package does not support system type: espocket`。本轮未发起下载／安装，不将这个缓存包的结果推广到全部最新官方包。见[当前可用性诊断](../records/2026-10-04-store-availability.md)。

2026-10-04：已用锁定官方 SDK 准备两个 espocket-compatible signed 测试版本，identity 与边界见[候选记录](../records/2026-10-04-store-icon-admission.md#签名输入准备)。测试 key 不作为正式 publisher；受支持的正式发布路线和 Core 端验收仍待完成。

2026-10-04 用户确认正式发行的发布者身份、签名目录和 Catalog 权限尚未准备，要求先完成其余验收并记录发布阻塞。本轮已准备 SDK 验签脚本和明确 test-only 的两个签名版本；不关闭本票，不上传或生成生产发布者身份。见[准备与官方文档核查](../records/2026-10-04-launcher-and-lifecycle-acceptance.md#签名准备与外部发布边界)。
