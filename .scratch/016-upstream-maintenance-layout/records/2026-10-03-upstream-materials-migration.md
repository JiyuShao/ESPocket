# 上游材料与兼容目录迁移

Date: 2026-10-03
Scope: 016/01

## 最终选择

用户选择 compat 与 patches 分开，并明确全部现有 upstream 材料归 .scratch。实际材料都是日期核查、故障分析或上游提交草稿，不需要独立 docs/upstream 文档类别。工作票引用证据，长期开发契约和架构决定继续保留在 development、design 与 ADR。

中间曾考虑 snapshots/reports 子目录，未作为最终布局提交。原文中的历史版本、故障和判定保留；搬移只调整相对链接及文档职责说明。

## 迁移清单

| 原 docs/upstream 文件 | 对应 Effort records |
|---|---|
| status-2026-09-28.md | [005：综合上游核查](../../005-m5-application-ecosystem/records/2026-09-28-upstream-status.md) |
| package-trust-local-baseline-2026-09-29.md | [005：package trust 核查](../../005-m5-application-ecosystem/records/2026-09-29-upstream-package-trust-baseline.md) |
| issues/http-cancel-race.md | [005：HTTP 故障与上游草稿](../../005-m5-application-ecosystem/records/2026-09-28-http-cancel-race.md) |
| ai-native-local-baseline-2026-09-29.md | [009：AI Native 能力核查](../../009-ai-native-foundation/records/2026-09-29-upstream-ai-native-baseline.md) |
| settings-store-gui-local-baseline-2026-10-02.md | [014：Settings/Store GUI 核查](../../014-app-navigation-card-contract/records/2026-10-02-upstream-settings-store-gui-baseline.md) |
| status-2026-10-02.md | [014：发布与 Card/更新能力核查](../../014-app-navigation-card-contract/records/2026-10-02-upstream-status.md) |
| issues/runtime-js-async-stack-overflow.md | [008：Runtime 故障与上游草稿](../../008-m8-app-contract/records/2026-10-02-runtime-js-async-stack-overflow.md) |

较早综合核查含多个 Effort 的限制，以 005 的 records 保存一份，其他领域通过链接引用，不复制历史事实。新材料仍按实际所属任务存放，不集中到 016。

## Firmware 职责

firmware/compat/README.md 列出现有两项兼容实现及适用版本/删除条件。firmware/patches/README.md 定义正式源码补丁的版本、顺序、hash、验证和移除约定。目前没有正式接入补丁，Runtime 提案仍在 008 records；应用工具与组件 override 未实施。

没有改动生产源码、资源、CMake、官方依赖或设备内容；本次不新增固件构建或真机通过判定。

## 验证

统一主机入口 scripts/check.py 通过：47 项 unittest、M2 parser 和当时的 Markdown；日志 /private/tmp/espocket-upstream-layout-host.log。最终归属调整只修改 Markdown 及链接，最终 scripts/docs/check.py --markdown 再次通过 185 份文档，git diff --check 通过。

七份原 docs/upstream 文件与迁移后文件逐份对比：除 Markdown 相对链接目标外，全文相同。没有丢失版本、日期、未提交声明、失败、未验证项或历史结论。
