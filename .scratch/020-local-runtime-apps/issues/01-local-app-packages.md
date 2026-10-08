# 01 — 本地 App 源码、资源与 BPK

**What to build:** 将聊天和计算器迁为有独立身份的本地 Runtime App，生成 BPK，接入内置 staging 并移除平台专用 GUI 覆盖。

**Blocked by:** 无

**Status:** resolved

## Acceptance

- [x] 完整导入原包业务、图片与所需音频／配置示例，保留来源和摘要。
- [x] 圆屏 GUI 与导航声明属于各自 App，平台不按官方 ID／版本替换文档。
- [x] 本地 BPK 由锁定 SDK 生成，逐成员核对源码。
- [x] 内置清单、资源检查、不可变成员摘要一致，不扩大 trust 例外。
- [x] 业务／导航／GUI parser 回归、统一 host checks 与完整产品构建通过。

## Comments

用户明确要求直接生成本地包，可替代 Store 安装版。原包内为可读 JavaScript 和 GUI JSON，未获取上游完整 Git 开发项目，也未确认公开再发行条款。

## Resolution

两 App 的本地源码、独立身份、圆屏资源、导航与 BPK 完成，System 专用 GUI 资源和 Core 024 文档覆盖已移除。锁定 SDK 逐成员包验证、真实 Controller／GUI parser／导航回归、两轮完整 host checks、字形、实际 staging 和编译时成员摘要、完整产品构建全部通过。固件 identity 为 `ad8326c75`，尚未部署；准确产物摘要、环境失败和设备边界见[记录](../records/2026-10-07-local-packages.md)。
