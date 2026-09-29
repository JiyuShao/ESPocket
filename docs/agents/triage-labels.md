# Triage labels

| Matt role | Local `Status:` | 含义 |
|---|---|---|
| `needs-triage` | `needs-triage` | 需要 maintainer 决定如何处理。 |
| `needs-info` | `needs-info` | 继续处理前需要补充信息。 |
| `ready-for-agent` | `ready-for-agent` | Agent 可以根据 acceptance criteria 直接执行。 |
| `ready-for-human` | `ready-for-human` | 下一步需要人或物理设备。 |
| `wontfix` | `wontfix` | 仓库决定不继续处理。 |

历史重建使用 `retrospective-resolved`；仍有当前工作的重建 Effort 使用 `retrospective-active`。二者是记录状态，不是 triage role。

当前 ticket 完成后使用 `resolved`。`resolved` 与 `retrospective-resolved` 都是终态记录，不是 triage role；已完成文件继续保留，使其 Sequence 与 blocking edge 可追溯。
