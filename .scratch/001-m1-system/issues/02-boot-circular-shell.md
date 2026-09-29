# 02 — 通过 System Core 启动 Circular Shell

**What to build:** 一套产品 System，依次启动必需 Service、Core 与隐藏 Shell App，到达可用 Launcher，并让 fatal failure 可诊断。

**Blocked by:** 01 — 复现 Platform Baseline。

**Status:** retrospective-resolved

- [x] Shell 由隐藏 Native App 承载，不引入第二套 lifecycle manager。
- [x] Display 与 touch 到达可用 UI。
- [x] Fatal startup failure 停止并输出串口诊断。

## Resolution

M1 hardware smoke 已接受；成功启动的串口输出未单独保留为 raw file。
