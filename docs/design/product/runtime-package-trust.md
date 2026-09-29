# Runtime 包信任契约

> 文档类型：长期产品安全契约。实施状态和证据由 [M5](../../milestones/m5/acceptance.md) 判定。

本契约定义远程 Runtime 包何时可以从下载产物变成 ESPocket 可启动 App。它不规定某个 Brookesia 版本的具体接口。

## 适用边界

- 远程 Catalog、Store、文件导入及未来网络入口取得的 `.bpk` 都属于不可信输入。
- 固件构建时随镜像生成并校验的 build-staged 样例属于构建供应链，不用它证明远程分发安全。
- 调试包、解包目录和“下载成功”都不等同于已安装 App。

## 信任不变量

1. 所有远程安装入口汇合到同一个 Core-owned 公共安装边界。
2. 验证读取完整、不可变的原始包，并在解包和执行任何成员之前完成。
3. Release signature 绑定 package identity、版本、目标系统和成员摘要。
4. 每个允许成员的路径、大小和哈希都受保护；缺失、额外、重复、逃逸或大小写冲突成员均失败。
5. `systems`、版本与所需 Runtime 必须与当前 ESPocket Platform Baseline 兼容。
6. 只有完整事务提交后的包才能进入 Core 已安装集合和 Launcher。
7. 重启扫描只接受具有可信安装收据且磁盘内容仍匹配的包。
8. 任一门槛无法执行时 fail closed；失败产物不能降级成“临时可用”。

## 生命周期

```text
Downloaded
  → Verified
  → Staged
  → Committed
  → Discoverable

任何失败
  → Rejected / Quarantined / Cleaned
```

### Downloaded

下载结果保存在不可执行临时位置，并记录下载过程中验证的外部 artifact digest。Catalog 提供的摘要是预期输入，不是最终信任结论。

### Verified

验证器使用同一包字节检查签名、manifest、成员列表、成员哈希和兼容性。验证完成前不把成员写入活动 App 根目录。

### Staged

已验证成员解包到新的事务目录。解包过程必须防止路径逃逸、链接跳转、重复成员和验证后替换。

### Committed

Core 原子地激活新版本并写入受信安装收据。更新失败时保留原活动版本；不允许活动目录同时混有两个版本的成员。

### Discoverable

Core 重启扫描重新核对安装收据与活动目录。只有仍满足信任条件的包才进入已安装集合。

## 安装收据

收据至少绑定以下产品事实：

- package identity 与版本；
- 原始 artifact digest；
- 签名 key identity 与验证策略版本；
- manifest digest；
- 已提交成员集合及摘要；
- 兼容 Platform Baseline；
- 提交事务 identity。

收据是重启发现的输入，不替代磁盘内容核对，也不能由 Store 或 Launcher 自行生成。

## 更新、卸载与清理

- 更新先验证并完整 staging，再切换活动版本。
- 切换失败保持原版本可用，并清理未提交事务。
- 卸载由 Core 移除活动引用、收据和包内容；Launcher 只观察提交结果。
- 启动时发现孤立 staging、无收据目录或内容不匹配时不得执行，并记录可诊断结果。
- 清理不能删除当前已提交的可信版本。

## 产品可见行为

- 用户看到“已下载”时，不暗示“已安装”或“可启动”。
- 验证失败必须给出稳定的失败类别，不继续安装。
- 未知结果不自动重试会产生副作用的提交步骤。
- 在统一信任门可用前，ESPocket 保持固定 Launcher，关闭远程动态安装与曝光。

## 设计依据

- [ADR-0004](../../adr/0004-core-owns-the-runtime-package-trust-gate.md) 决定信任门的所有权。
- [ADR-0001](../../adr/0001-espocket-is-a-product-layer-over-brookesia.md) 禁止用私有 Installer 绕过上游边界。
- 当前上游能力和阻塞事实见 [Upstream Tracking](../../upstream/README.md)。
- 实施步骤和测试矩阵属于 [M5 Spec](../../../.scratch/005-m5-application-ecosystem/spec.md)。
