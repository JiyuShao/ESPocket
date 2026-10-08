# 聊天与计算器本地 Runtime App 包

Sequence: 020

Status: active
Blocked by: 补充语音听感确认，详见 02；部署替换已完成

## Problem Statement

聊天与计算器的圆屏资源嵌入 System，平台按官方 App ID 和版本覆盖 GUI。App 升级会使产品代码依赖旧 Controller 路径，修改界面也要求刷固件。

## Solution

建立本地维护的 Runtime App 源码与 BPK，将圆屏资源迁入各自 App，平台仅保留通用 viewport。用户要求本地版可替代 Store 安装版；设备替换前保留配置与其他安装内容。

## User Stories

1. 开发者在 App 目录修改业务与界面，生成独立 BPK。
2. 设备使用本地版聊天和计算器，导航、语音与运算保留真实 Owner。

## Implementation Decisions

- 使用新身份 `espocket.app.ai_chatbot`、`espocket.app.calculator`，本地初版 `0.1.0`，支持 `espocket`。
- 原包来源、版本和摘要记录在各 App 的 `upstream.json`；许可证未在原包提供，本轮不公开再发行。
- 内置包通过显式源码清单和 Core 编译时摘要验证；独立 unsigned BPK 仍要求开发者模式，不放宽统一 trust gate。
- 聊天使用现有 Runtime Navigation seam；平台不保留 App 专用 GUI 文档覆盖。
- 设备替换保留旧 App 的 data/files 并迁给新身份；先验证新 App，再移除旧安装副本，不改变远程 Catalog。

## Testing Decisions

- BPK 与源码逐成员匹配、真实 GUI parser、Controller 动作及异步导航生命周期检查。
- 统一 host/Markdown checks 和精确补丁产品构建。
- 若本轮部署，保留当前 Flash 区域备份，核对其他安装及用户数据；真机验证两 App、Back/Home、重启发现与语音。

## Out of Scope

- 改写远程官方 Store Catalog、上传或正式签名发行。
- 重写其他 Store App 或新建第二套 Installer／导航栈。

## Tickets

- [01 — 本地 App 源码、资源与 BPK](issues/01-local-app-packages.md)
- [02 — 部署与替换 Store 安装版](issues/02-device-replacement.md)
- [03 — 连续聊天卡顿与回复尾音自触发](issues/03-conversation-stutter-echo.md)
- [04 — 唤醒与实体 Reset 恢复](issues/04-chat-wake-hardware-reset.md)
- [05 — 离线 AEC 与打断候选](issues/05-aec-interruption-candidate.md)

## Further Notes

- [Core trust gate](../../docs/adr/0004-core-owns-the-runtime-package-trust-gate.md)
- [开发者模式 unsigned 例外](../../docs/adr/0018-developer-mode-allows-unsigned-packages.md)
- [共同生命周期与导航契约](../../docs/adr/0003-native-and-runtime-share-the-system-core-contract.md)

- [本地包、验证与迁移准备记录](records/2026-10-07-local-packages.md)

## 当前结果

本地源码、圆屏资源归属、独立 BPK、内置 staging 与产品固件完成；最终 host checks 与构建通过，已部署镜像 `b7d076a00`。完整备份、315 个旧文件的保留迁移和新 App 真机启动／运算／导航通过；两个旧版已通过 Store 卸载，硬件复位后的发现与唯一 Launcher 条目通过。小智账号连接、回复解码与 Home 清理已有证据；用户已明确授权后续声学测试；完整连续听感仍由 03 持有。最新证据见[部署记录](records/2026-10-07-device-deployment.md)。

用户报告连续对话声音／页面卡顿及静音时尾句自触发；主机已复现回复结束与实际播放完成的门禁缺口，已部署 `7094a19a4` 的 PCM 防护与实体 Reset 恢复；连续卡顿仍在诊断。连续对话验收由 03 持有，不能视为既有部署验证已覆盖。

[防回音与实体 Reset 恢复部署证据](records/2026-10-07-echo-reset-deployment.md)。


离线软件 AEC 与 Chat 0.1.2 已准备，完整候选镜像 `ae90157d1` 未部署；输入、构建、回退和物理门槛见[离线记录](records/2026-10-08-offline-aec-candidate.md)。正式设备仍为 `c60a29d3b`，物理回音／打断／滚动验收保持开放。
