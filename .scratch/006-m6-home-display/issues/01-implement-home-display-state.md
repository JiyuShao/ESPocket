# 01 — 实现 Watch Face Home 与 Display State

**What to build:** Watch Face Home、PWR Home/Off/Wake、auto-off 与 valid-page resume 的完整源码路径。

**Blocked by:** [002/02 Home 与 cleanup](../../002-m2-native-app/issues/02-close-the-home-and-cleanup-loop.md)（已完成）。

**Status:** resolved

- [x] Host build 与 static contract gate 通过。
- [x] Screen Off 与导航保持正交。
- [x] PWR 与 BOOT ownership 符合产品契约。

## Resolution

源码实现与隔离 build evidence 已存在；hardware acceptance 单独执行。

## 已验证的源码与构建条件

| 检查项 | PASS 条件 | 状态 |
|---|---|---|
| Interaction contract | 实现与主交互规范一致 | PASS（STATIC，2026-09-28） |
| Current-vs-target wording | 文档和 UI 不把 M1–M5 的 Launcher Home 误称为 Watch Face 实现 | PASS（STATIC，2026-09-28） |
| Existing Launcher reuse | 使用当前固定入口 Launcher；不把动态同步带入 M6 | PASS（STATIC，2026-09-28） |
| PWR integration | 短按只执行已定义的 Home/Off/Wake；长按不被系统层重定义 | PASS（HOST BUILD + 真机，2026-10-01） |
| Display/navigation separation | 息屏不清空或改写有效导航位置 | PASS（STATIC，2026-09-28） |
| Resume fallback | 目标失效时只回 Watch Face | PASS（STATIC，2026-09-28） |
| Touch while off | Screen Off 时页面动作不可被触摸触发 | PASS（STATIC + 真机，2026-10-01） |
| BOOT | 不产生日常导航动作 | PASS（STATIC + 真机，2026-10-01） |
| Build | 正常固件 clean build/link 成功 | PASS（2026-10-01，测试开关关闭的隔离构建；[记录](../records/2026-10-01-reclaim-test-image.md)） |
| Static checks | JSON、脚本或项目既有检查全部通过 | PASS（JSON parse + `git diff --check`） |
