# Loading 呈现与全仓分层审查

Sequence: 022

Status: active
Blocked by: Loading 真机视觉验收需设备返回

## Problem Statement

用户认为 Loading 样式不佳，并要求使用 code-review 检查所有代码是否破坏分层或存在硬编码。

## Solution

Loading 改为主题配色的紧凑圆角提示与小型 spinner，继续保持非模态、最低优先级和真实 Owner 的等待生命周期。并行检查 Standards 与 Spec，覆盖第一方代码及维护补丁，分别记录可复核问题。

## User Stories

1. Loading 在浅色／深色页面上有清晰的反馈，不占用触摸或改变导航。
2. 开发者获得带规范、源码位置和影响说明的分层／硬编码审查结果。

## Implementation Decisions

- 保留 Shell 原生 Overlay seam；颜色引用已注册产品主题，几何由 Circular Shell 持有。
- 圆角提示位于屏高 10% 的底部安全位置；使用内容尺寸，不固定宽度。
- Review 覆盖全仓第一方实现；近期基线为 `5e0e246`，使用 `git diff 5e0e246` 包含未提交修改，并检查未跟踪文件。提交列表为 `f9271ae`。
- 第三方原始 managed_components、生成代码与二进制不作为自有代码逐文件审查；涉及边界时核对锁定上游接口。

## Testing Decisions

- 保留真实 Loading 生命周期回归，增加子控件创建失败时完整清理的回归。
- 统一 firmware checks、Markdown 和隔离产品构建；真机视觉不以主机替代。

## Out of Scope

- 本轮不部署，不连接设备，不自动提交或推送。
- 审查发现的跨模块迁移不混入 Loading 样式修改。

## Tickets

- [01 — Loading 呈现](issues/01-loading-presentation.md)
- [02 — 全仓分层与硬编码审查](issues/02-code-audit.md)

## Further Notes

- [主题规范](../../docs/development/app-navigation-card-api.md#主题开发规范)
- [Overlay Owner](../../docs/adr/0017-overlay-arbitration-preserves-request-ownership.md)

Loading 离线实现与检查通过，真机待设备返回；双轴审查完成，剩余分层／配色及启动响应问题见[记录](records/2026-10-08-review.md)。
