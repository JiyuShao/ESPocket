# 02 — 增加可控 reclaim fallback seam

**What to build:** 默认关闭的 test path，使当前 resume target 失效，让 hardware acceptance 能证明回退到 Watch Face。

**Blocked by:** 01 — 实现 Watch Face Home 与 Display State。

**Status:** resolved

- [x] Test seam 不会在普通产品使用中激活。
- [x] 使 target 失效时不引入通用 memory manager。
- [x] 下一次 wake 到达 Watch Face，不重启 App。

## Comments

- 2026-10-01：默认关闭的 `CONFIG_ESPOCKET_M6_RECLAIM_ON_TIMEOUT_TEST` 已实现；隔离镜像构建、烧录成功，证据见 [M6 reclaim 测试镜像记录](../../../docs/milestones/m6/records/2026-10-01-reclaim-test-image.md)。还需在前台 App 自动息屏后观察停止事件和 PWR Wake 的实际屏幕，才能勾选验收条件并关闭 ticket。

## Resolution

2026-10-01：测试镜像的固定五轮 Native Detail 自动息屏均记录 App 停止与回收标记；用户确认五次 PWR Wake 均显示表盘且无异常。串口记录 Wake 前没有 App 重启。详见 [M6 reclaim 测试镜像记录](../../../docs/milestones/m6/records/2026-10-01-reclaim-test-image.md)。
