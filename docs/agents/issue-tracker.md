# Issue tracker：本地 Markdown

本仓库的 Spec 与 ticket 以版本化 Markdown 保存在 `.scratch/`。

## 约定

- 每个 Effort 使用一个目录：`.scratch/<NNN>-<effort>/`。
- `<NNN>` 是按提出顺序单调分配的不可变 Sequence。标题变化时保留原号，永不复用。
- Spec 位于 `.scratch/<NNN>-<effort>/spec.md`，分别记录 `Sequence:`、`Status:` 与 `Blocked by:`。
- 每个可独立执行的 ticket 位于 `.scratch/<NNN>-<effort>/issues/<NN>-<slug>.md`。
- 每个 Spec 按不可变 ticket Sequence 链接全部 tickets，用于替代本地 Markdown 缺少的 issue list UI。
- Effort `Status:` 只能是 `planned`、`active`、`blocked`、`resolved`、`retrospective-active` 或 `retrospective-resolved`。
- Ticket `Status:` 使用规范 triage role，或终态记录 `resolved`/`retrospective-resolved`；依赖只写在 `Blocked by:`，仓库内前置工作链接到具体 ticket，外部 blocker 说明缺少的接口、版本或人工输入。
- 回溯材料必须说明它是在实现后重建，并链接历史证据。
- 后续讨论追加到 `## Comments`，保留此前决定。

## 创建 Effort

使用脚手架分配下一个全局 Sequence、创建 Spec，并更新 `.scratch/README.md`：

```bash
python3 scripts/tracker/new-effort.py <slug> "<title>" \
  --blocked-by "<dependency>" \
  --provenance "<proposal source>"
```

创建后补全 Spec，再在 `issues/` 下增加 ticket 并按 Sequence 链回 Spec。

## 操作语义

- 发布 Spec 或 issue，表示写入对应 Markdown 文件。
- 获取工作，表示完整读取被引用文件。
- 工作 frontier 是第一个 `Blocked by` 已全部解决、且状态为 `ready-for-agent` 的 ticket。Sequence 记录来源顺序，不覆盖 blocker。
- 解决 ticket，表示将状态设为 `Status: resolved`、勾选 acceptance criteria，并在 `## Resolution` 下记录结果。

## 验收与记录


- Spec 定义范围、整体状态和完成条件；ticket 持有可执行步骤、具体 acceptance checklist 和结果。
- 代码完成、构建通过和真机通过分别记录。只有 ticket 的全部条件满足时才关闭；Spec 在范围内工作全部完成时关闭。
- 真机固定次数、单次路径与证据规则放在负责验收的 ticket；已接受结果继续有效，缺少证据的路径保持未完成。
- 同一实现或验收条件由一张 ticket 持有，其他票通过依赖或链接引用。
- 有日期的长期事实放在同一 Effort 的 `records/`；保留镜像 identity、测量值、失败、豁免与未验证项，由 Spec 或 ticket 链接。
- records 只保存可读 Markdown。原始日志和中间产物保存在本地、CI 或 Release artifact；影响判定的事实先提炼，再删除临时产物。
- 历史记录中的旧阶段名称与当时状态保留为事实；当前执行顺序由具体 ticket 依赖决定。
