# 现有界面主题变量迁移

Sequence: 017

Status: active
Blocked by: None.

## Problem Statement

Shell 用旧色值命名主题样式，浅色模式丢失 Card 的颜色语义；Hello 完整页面与系统原生 Overlay 仍有固定颜色，不能默认适配主题。

## Solution

按[主题开发规范](../../docs/development/app-navigation-card-api.md#主题开发规范)迁移产品维护的界面；两份产品主题集中持有语义颜色。

## Implementation Decisions

- Shell Surface 使用语义 styleRefs；Battery 与 Brightness Card 分别保留 success/warning 颜色语义。
- Hello Native/Runtime App Page 与既有 App Card 共享 app 样式。
- System 提供已注册的不可变产品主题资源；Shell 启动时按 GUI 当前主题解析原生控件所需颜色，不另存主题偏好，不在 LVGL 锁内查询 GUI。
- 普通按钮使用成对 primary.fill/on 与 pressed 状态；破坏性操作使用 danger.fill/on。

## Testing Decisions

检查全部维护资源的引用覆盖、固定颜色及常用文字对比度；运行统一 host checks、Runtime package build 和独立补丁固件构建。设备两种模式的视觉验收独立记录。

## Out of Scope

上游 managed_components 修改、依赖升级、即时主题切换、第三方 App 配色与真机刷写。

## Tickets

- [01 — 迁移现有界面并验证主题契约](issues/01-migrate-maintained-surfaces.md)
- [02 — 部署与普通态修复](issues/02-deploy-and-fix-default-control-colors.md)
- [03 — 字体字形静态检查](issues/03-check-built-in-glyph-coverage.md)

## 记录

- [2026-10-03 迁移与验证](records/2026-10-03-theme-migration.md)

## Resolution

01 全部完成；维护界面迁移到同一产品主题，源码、资源、主机与完整固件构建检查通过。未刷写设备，light/dark 真机视觉结果仍未验证。

2026-10-04：新增 02，设备部署后发现普通态样式格式缺陷；修复与系统配色的最终设备门槛由 02 持有。

- [2026-10-04 主题部署与普通态修复](records/2026-10-04-theme-deployment.md)
