# 03 — 稳定 shared worker baseline

**What to build:** 一套 firmware worker configuration，能通过 clean boot 与联合 App 使用，同时保留已测量余量。

**Blocked by:** 02 — 证明 Runtime lifecycle 与 Native 共存。

**Status:** retrospective-resolved

- [x] System worker overflow 与 secondary-buffer failure 作为 failed canary 保留。
- [x] 根据实际观察推导稳定 System 与 Service worker 值。
- [x] 记录 project owner 对独立 file-install evidence 的例外，不虚构日志。

## Resolution

M3 于 2026-09-28 通过，acceptance 中明确记录 evidence exception。
