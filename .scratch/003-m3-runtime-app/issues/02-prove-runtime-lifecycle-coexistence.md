# 02 — 证明 Runtime lifecycle 与 Native 共存

**What to build:** 一个能发现 Hello Runtime，并与 Hello Native 一起验证可见 lifecycle 的 clean image。

**Blocked by:** 01 — 构建并 stage Hello Runtime。

**Status:** retrospective-resolved

- [x] Core 在 clean boot 时发现 Runtime。
- [x] Runtime 完成 render 并返回 Home。
- [x] `Runtime → Native → Runtime` 的 start 与 stop 匹配。

## Resolution

Clean combined physical record 已接受。
