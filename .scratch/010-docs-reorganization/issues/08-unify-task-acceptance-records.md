# 08 — 统一任务、验收与历史记录

**What to build:** 删除独立阶段管理层，将剩余任务、验收条件、具体依赖和历史记录统一到本地 tracker。

**Blocked by:** None；2026-10-02 项目所有者直接授权迁移。

**Status:** resolved

- [x] 原阶段目录已删除，文档入口、Agent 规则与脚手架统一使用 Spec/ticket/records。
- [x] 19 份历史记录归入对应 Effort；日期、镜像 identity、测量、失败、豁免和未验证事实保留。
- [x] Storage/Developer/Audio、Store、导航与 App 交互的未完成条件由明确 ticket 持有；已有通过结果不重开。
- [x] 补齐 online fix、Runtime isolation、签名包发布三张执行票，并分离导航绑定与 Card 样例。
- [x] 仓库内阶段阻塞改为具体 ticket；链接和重复任务归属核对通过。
- [x] 文档检查、迁移事实核对和 diff whitespace 检查通过。

## 迁移归属

| 原工作 | 当前 Owner |
|---|---|
| ESPocket System / Native / Runtime 已接受基线 | 001、002、003 的 Spec 与 records |
| Device capability 剩余检查 | 004/03、004/04 |
| Application ecosystem 剩余条件 | 005/03–08；005/02 只保留诊断终态 |
| Home 与显示已完成验收 | 006/03；构建条件归 006/01 |
| 系统 Surface 源码与真机路径 | 007/02、007/03 |
| Native/Runtime 新导航绑定与 API | 014/01、014/02、014/04 |
| App 回收与真实交互验证 | 008/02、008/03 |
| App Card 生命周期与样例/API | 014/03、014/05 |
| 阶段外 Home Space 样机记录 | 011 的 records |

## Comments

- 历史目录及 Sequence 保持不变，旧阶段编号仅用于追溯；执行顺序来自 ticket 依赖。此次迁移不执行 firmware build、刷写或真机操作。

## Resolution

2026-10-02：迁移完成，原阶段目录已删除。19 份 records 的正文完整性核对通过，除相对链接和当前状态入口外保持不变；83 行既有通过结果与硬件验收表项已迁入负责的 Spec/ticket。142 份 Markdown 从 README 全部可达，61 张 ticket 的显式依赖无循环。

新增 005/06–08 承接在线修复复验、Runtime keyboard isolation 和兼容签名包发布；014/04 收敛为导航绑定，Card 样例拆至 014/05。原有已接受结果与未验证状态分别保留。

验证：`python3 scripts/docs/check.py` 全部通过，包括架构图生成与布局；`git diff --check` 通过。新增检查已用临时 fixture 验证会拒绝旧阶段依赖、records 原始日志和恢复的旧目录。未执行固件构建、刷写或真机操作。
