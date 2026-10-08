# 01 — Loading 呈现

**What to build:** 用主题配色圆角提示与小型 spinner 替换裸露文字，不改变等待身份、触摸与 Overlay 优先级。

**Blocked by:** 设备不在身边，真机浅色／深色与触摸验收待返回。

**Status:** ready-for-agent

## Acceptance

- [x] 内容自适应、主题配色、底部相对安全位置；无整页遮罩和输入控件。
- [x] 保留 startup／app_wait 身份与清理；子控件创建失败删除整个提示。
- [x] 统一 checks、Markdown 与完整构建通过。
- [ ] 真机两主题、App／键盘／Dialog／Quick Settings 场景视觉与触摸通过。

## Comments

审查发现的其他分层问题由 02 记录，不混入此视觉调整。

主机与构建证据见[记录](../records/2026-10-08-review.md)；真机条件保持未完成。
