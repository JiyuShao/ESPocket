# App 发现与 Launcher 契约

> 文档类型：长期产品契约。实施状态和证据由 [M5](../../milestones/m5/acceptance.md) 判定。

本契约定义固定产品入口与动态 App 如何成为 Launcher 中的可启动项。它不规定刷新 timer、generation counter 或 UI 子树更新算法。

## 两类入口

### 固定产品入口

由 ESPocket 产品装配明确提供，包括首版所需的内置 Native、Runtime 和官方 System App。固定入口可以使用产品排序与专用呈现，但启动时仍由 Core 解析当前 App identity。

### 动态 App

由 Core 已提交安装状态产生。动态 App 必须同时满足：

- 已通过 Runtime 包信任契约；
- 当前仍在 Core 已安装集合；
- 与 ESPocket 兼容；
- 具有 Launcher 所需的最小展示信息；
- 未被产品策略隐藏。

Store Catalog、下载记录、缓存目录和未提交事件都不具备动态曝光资格。

## 唯一事实来源

`Core::list_apps()` 是动态 Launcher 的实时事实来源。Launcher 是该集合的显示投影，不保存第二份安装数据库。

```text
Core committed Apps
  → eligibility filter
  → stable presentation model
  → Launcher projection
```

安装、更新或卸载通知只表示投影可能过期。Shell 随后读取完整 Core 快照，并从该快照恢复一致状态。

## Identity

- Manifest ID 是展示和产品引用的稳定 identity。
- 运行期 `AppId` 属于当前 Core 状态，必须在实际启动时解析。
- Launcher 不跨重启持久化旧 `AppId`。
- 同一 Manifest ID 的重复或冲突记录 fail closed，不猜测目标。

## 对账规则

每次成功对账产生一个完整、确定的结果：

1. 保留固定产品入口。
2. 读取 Core 完整 App 快照。
3. 过滤不可信、不兼容、隐藏或信息不完整的项。
4. 按稳定 identity 去重并排序。
5. 原子替换动态展示投影。

读取失败或快照不完整时保留最后一次完整视图。Launcher 不根据单个事件局部猜测安装结果。

## 启动行为

- 用户选择条目后，System 使用 Manifest ID 在当前 Core 状态中解析 App。
- 目标不存在、不可启动或 identity 冲突时不调用过期 `AppId`。
- 启动失败保持当前 Surface，并提供可诊断结果。
- 成功启动后遵守统一 App 交互契约和直接 Launch Source 规则。

## 更新与卸载

- 更新只有在 Core 提交新版本后才改变 Launcher 投影。
- 卸载只有在 Core 移除提交状态后才移除条目。
- 下载失败、回滚或孤立目录不应造成图标闪现。
- Launcher 不负责清理包文件或修复安装状态。

## 安全边界

动态曝光同时依赖包信任和在线 Store 稳定性。在两个门槛通过以前，固定入口是产品的 fail-closed 行为。

## 设计依据

- [ADR-0005](../../adr/0005-launcher-projects-core-committed-app-state.md) 决定事实来源与投影关系。
- [Runtime 包信任契约](runtime-package-trust.md) 决定动态 App 的准入条件。
- 具体刷新机制和验收步骤属于 [M5 Spec](../../../.scratch/005-m5-application-ecosystem/spec.md)。
