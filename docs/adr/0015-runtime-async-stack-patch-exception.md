# ADR-0015: Runtime 异步栈配置补丁的限定例外

- Status: `accepted`
- Recorded: 2026-10-03
- Origin: 用户确认 ADR-0001 限定例外，并授权休息期间继续所有可执行工作

## Context

Runtime JS 0.8.3 的异步完成任务固定使用 8 KiB 栈。真实 Promise continuation 调用 GUI 更新发生栈溢出；删掉确认与待决反馈不能满足产品契约。上游锁定版没有预算配置能力，故障与提案见 [008/04](../../.scratch/008-m8-app-contract/issues/04-resolve-runtime-async-stack-overflow.md)。

## Decision

仅为 Runtime JS 0.8.3 增加异步任务栈配置，作为 [ADR-0001](0001-espocket-is-a-product-layer-over-brookesia.md) 对源码补丁基线限制的限定例外。上游默认 8 KiB 保持不变，ESPocket 首先验证 16 KiB；配置范围 8–64 KiB。不改变任务分配策略、优先级、调度、导航 API 或生命周期事实源。

补丁保存于 firmware/patches 的组件与版本目录，manifest 保存完整原始文件及补丁 hash、上游身份、顺序、工作票和删除条件。工具在独立构建副本准确应用补丁，版本/hash 或上下文不匹配时停止。原始 managed_components 不修改，不复制全套组件源码到 Git。

构建使用 Component Manager 的 override_path 指向副本。依赖解析在独立工程副本执行，避免覆盖或清理原始缓存及版本锁。生成的版本锁和选中的组件路径作为构建证据保留；原始 registry lock 与 patch manifest 共同定义输入基线。

正式验收依次要求主机检查、完整构建、最小真实 Runtime 回归、完整 App 套件及 ticket 的物理/资源门槛。上游提供等价能力后，同次审查移除补丁、更新依赖并复验。不将此例外推广为任意组件补丁授权，Settings 仍遵循 ADR-0012。

## Consequences

维护方承担一个小型源码差异及构建准备成本。额外栈内存必须通过资源门槛，构建成功不证明预算充足。若差异继续扩大，需另行决定维护策略。

补丁授权范围于 2026-10-03 被 [ADR-0016](0016-maintained-upstream-fixes.md) 更新；本记录保留原始决定。
