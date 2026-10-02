# 上游文档与兼容目录整理

Sequence: 016

Status: resolved
Blocked by: None.

## Problem Statement

compat 与源码补丁容易混淆；upstream 根目录混合有日期快照和问题入口，最新核查未完整列出，issues 命名又像 .scratch 的工作票。

## Solution

明确 compat/patches 的文件职责；全部日期上游核查、故障报告与提交草稿归对应 Effort 的 records，移除 docs/upstream。工作状态继续由 .scratch 持有。

## Implementation Decisions

- firmware/compat 保存自有兼容实现，firmware/patches 保存已接受的上游源码修改。
- 本次只建立 patches 管理说明，不正式接入待决 Runtime 补丁。
- 五份版本/源码核查、两份故障材料移入对应 .scratch Effort 的 records；同步所有本地链接，移除独立 docs/upstream。
- 保留故障、历史判定和版本事实；报告只记录上游提交事实，不复制工作票依赖或验收状态。

## Testing Decisions

Markdown 结构与链接检查、统一 host checks、Git 空白检查通过。没有生产源码/资源或构建配置修改，不需要新的固件构建或物理验收。

## Out of Scope

补丁应用工具、Runtime 补丁采用决策、依赖升级、官方组件修改、上游问题提交。

## Tickets

- [01 — 整理上游材料与兼容目录职责](issues/01-organize-upstream-materials.md)

## 记录

- [2026-10-03 迁移与验证](records/2026-10-03-upstream-materials-migration.md)

## Resolution

01 全部完成；上游核查与故障材料以对应 Effort records 为权威，compat 与 patches 各有管理说明。未正式接入 Runtime 补丁或修改依赖。
