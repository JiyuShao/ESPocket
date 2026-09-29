# M5 包信任门

## 状态

- 设计：已针对锁定的 Brookesia 0.8.x 基线完成
- 强制执行：受上游集成缺口阻塞
- 产品实现：有意暂不加入
- 私钥或签名操作：未执行
- M5 保持 `BLOCKED`

本文定义 ESPocket 安装远程提供的 Runtime App 之前必须满足的最小信任边界。它不引入私有包格式、Package Manager、Store backend，也不 fork managed component。

## 安全目标

远程提供的 Runtime App 只有同时满足以下条件，才能完成安装或在重启后被发现：

1. 下载的 `.bpk` 字节与 catalog 声明的 SHA-256 一致；
2. 包内包含完整的 Brookesia release signing 文件对；
3. Core 使用 ESPocket 固定的公钥验证 release signature；
4. 每个包成员都与已签名的 `META-INF/hash.json` 一致；
5. manifest 明确允许 `espocket` system type；
6. 包通过 Core 的 manifest、service、path 和 GUI 验证；
7. 激活以原子方式提交，在新版本可用前一直保留旧的已安装版本；
8. 重启发现只接受 built-in 包，或带有有效 Core-owned trust receipt 的安装。

TLS 仍然是必需的，但 TLS 传输验证不等于包发布者身份验证。

## 锁定版本 0.8.x 的事实

### 已有的可复用机制

System Core 0.8.4 已经提供：

```cpp
verify_app_package_release(package_path, {
    .public_key_pem_path = "...",
});
```

验证器同时要求 `META-INF/hash.json` 和 `META-INF/signature.sig`，验证 hash document 上的 RSA-PSS-SHA256 签名，并验证成员 SHA-256。相关 Kconfig 选项默认启用，但仅仅编译该函数并不代表安装路径强制调用了它。

Core 还提供以下有用的安装保护：

- 精确检查包的 `systems` 兼容性；
- 安全验证 manifest ID 和解压路径；
- 在 `apps/.installing/...` 下 staging；
- 激活前验证 staged manifest/resource；
- 激活前出错时清理 staging；
- 调用方拥有的 Runtime 存储路径与 App code root 分离。

这些机制必须复用，不能重新实现替代品。

### 缺失的强制执行

以下路径不会调用 `verify_app_package_release()`：

- App Store 下载与安装；
- `SystemApi::install_runtime_app_package()`；
- `System::install_runtime_app_package()`；
- 启动时扫描已解压的 `apps/<id>/manifest.json` 目录树；
- 可选 USB `InstallBpk` bridge。

App Store 0.8.2 会把 catalog 的 `hash_sha256` 解析到 `StoreEntry::sha256`，但在 cache rename 与安装前，并不会计算和比较下载包的字节哈希。

`SystemApi::install_runtime_app_package()` 会直接调用不可覆写的 Core 安装方法。ESPocket 无法在 `espocket::System` 中覆盖该调用，而安装后的 `on_app_installed()` hook 已经来不及认证原始 `.bpk`。Core 解压时会排除 `META-INF/`，因此 hook 也不能从已安装目录重建 release 验证。

### 重启绕过

ESPocket 当前为了构建预置的 Hello Runtime，需要：

```cpp
config.install_package_apps = true;
```

启动时，Core 扫描每个已配置的 `apps/` root，并安装所有兼容的已解压 manifest；不要求签名或可信安装记录。因此，仅在 Store 中做安装前检查不能形成持久信任边界：重启后，已解压目录会脱离产生它的 `.bpk` 而被独立接受。

### 更新回滚缺口

Core 当前先 staging 新包，把 private data 复制进 staging，然后对旧 Runtime App 调用 `uninstall_app()`。`uninstall_app()` 会删除旧 App 目录；之后 Core 才把 staged 目录 rename 到目标位置，并安装新的 Runtime App record。

如果旧 App 移除后发生 rename、GUI preparation、lifecycle hook 或新 Runtime 安装失败，旧版本不会恢复。密码学验证必须发生在此之前，但验证本身并不能使更新具备事务性。

### Cache 清理缺口

App Store 会把完成的 partial download rename 为最终缓存 `.bpk`，然后调度安装。Core 安装失败不会删除该最终缓存包；Core 卸载也只移除已解压 App 目录，不会删除 Store 缓存的 `.bpk`。

已知官方 catalog 包没有签名，并且只声明 `systems: ["super"]`，无法满足 ESPocket 信任门。

## 必需的统一 Core 契约

权威信任门必须位于 System Core 公共的包安装边界，而不是某一个 Store UI 中。每个 `.bpk` 入口都必须汇聚到同一个操作。

兼容的上游 API 可以在概念上扩展如下安装选项；准确命名留给 Brookesia 决定：

```text
install_runtime_app_package(package_path, options)
    expected_package_sha256     可选的来源摘要
    require_release_signature   产品策略
    trusted_public_key(s)       产品固定的验证公钥
    replace_existing            更新策略
    source                      built-in / store / usb / developer
```

必需的操作顺序：

```text
复制或锁定不可变候选字节
    -> 如果提供了预期值，验证整个文件的 SHA-256
    -> 验证内嵌 release signature 和所有已签名成员
    -> 从同一个已验证候选中读取 manifest
    -> 验证精确 system type 和 service 要求
    -> 解压到新的 staging 目录
    -> 验证 staged resource
    -> 写入 pending Core-owned trust receipt
    -> 原子切换新旧目录
    -> 安装并验证新的 App record
    -> 提交 receipt 并删除备份
```

### 同一字节要求

包不能在一种文件状态下完成验证，然后从另一种状态解压。Core 应采用以下任一方案：

- 对同一个不可变 byte buffer 执行读取、验证和解压；或
- 先把候选复制或 rename 到 Core-owned staging 位置，再只验证和解压这份不可变副本。

在调用方可写路径上分别调用当前 verifier 和 unpacker，会留下 TOCTOU 窗口。

### 公钥策略

ESPocket 要求由固件或产品配置固定 public verification key。Private signing key 绝不能放入设备，也不能提交到本仓库。

V0.x 使用一个固定 release key 即可。将来轮换时可以使用小规模显式 key set 或已签名 key identifier，但在出现真实轮换需求前不需要通用 trust store。

签名缺失、签名 metadata 不完整、未知 key、无效签名、成员不匹配或 verifier 被禁用，都必须 fail closed。

## 可信重启发现

Core 必须区分两种信任来源。

### Built-in 来源

固件或 LittleFS 构建 staging 属于签名固件镜像和显式产品装配的一部分，因此可信。ESPocket 构建预置的 `espocket.app.hello_runtime` 仍然只是 built-in 验证 App；它不能证明任意已解压目录都可信。

Built-in allowlist 应由构建过程显式生成，不能从 `apps/` 下碰巧存在的目录推断。

### 动态安装来源

动态安装成功后，必须在 Runtime 可写 App storage 之外写入 Core-owned receipt。该 receipt 至少绑定：

- manifest ID 与版本；
- 已安装 volume 与标准化 App path；
- 整个 `.bpk` 的 digest；
- signer/key identity 或固定 key policy version；
- 已签名成员 hash 集合，或等价的已安装目录完整性绑定；
- 已提交的安装 generation/state。

启动扫描必须拒绝或隔离 receipt 缺失、pending、不匹配或无效的动态 App 目录。任意已解压 `manifest.json` 目录树不得被当作可信。

如果 Core 能保证任何不可信主体都无法修改已安装 code root，那么 committed receipt 可以为已验证安装事务背书；如果 code root 可能在 Core 之外被修改，启动时还必须把已安装成员与 receipt 中的签名 hash 对比。

## 事务更新与恢复

在新版本提交前，更新必须保留最后一个已知可用版本。

最小状态机：

```text
Downloaded
  -> Verified
  -> Staged
  -> PendingActivation
  -> Committed
```

失败行为：

- `PendingActivation` 之前失败：删除 staging，旧 App 保持不变；
- 切换期间失败：恢复旧目录和旧 App record；
- 新 App 安装、GUI preparation 或 hook 期间失败：移除新目录，恢复并重新安装旧版本；
- 存在 pending receipt 时掉电：下次启动确定性地回滚到 committed 版本；
- 只有成功激活后：删除备份并完成 receipt。

在提交前不得销毁保留的 `cache/`、`data/` 和 `files/`。现有的预复制行为可以复用，但在新版本被证明可用前，旧目录必须 rename 为备份，而不是直接删除。

版本策略默认还必须拒绝意外降级。显式 developer/recovery 操作可以选择允许降级；仅凭 Store metadata 不得用旧包静默替换较新的已安装版本。

## Store 职责

官方 Store 继续负责传输与 cache 生命周期，不负责 publisher key 策略。

在最终 cache rename 或安装前，Store 必须：

1. 要求可下载入口的 `hash_sha256` 是格式严格正确的 SHA-256；
2. 计算完整 partial file 的 hash，并以固定结果语义进行比较；
3. 拒绝 metadata 与包 manifest ID 或版本不一致的情况；
4. 把预期的完整文件 digest 传给 Core 安装操作；
5. 区分报告信任失败、网络失败和容量失败。

Catalog digest 可以发现损坏或下载内容不匹配，但不能代替 signed release 检查，因为 catalog metadata 本身不能证明包发布者身份。

## 清理策略

ESPocket 存储受限，失败时必须保持关闭并回收无效产物：

| 失败场景 | Partial download | 最终缓存 BPK | Staging | 现有 App |
|---|---|---|---|---|
| 网络错误或下载不完整 | 删除 | 不变 | 无 | 不变 |
| Catalog SHA 不匹配 | 删除 | 删除候选 | 无 | 不变 |
| 签名缺失或无效 | 删除 | 删除候选 | 删除 | 不变 |
| Manifest/system/service 拒绝 | 删除 | 删除候选 | 删除 | 不变 |
| 新安装激活失败 | 删除 | 删除候选 | 删除 | 无 |
| 更新激活失败 | 删除 | 删除候选 | 删除 | 恢复旧版本 |
| 安装或更新成功 | 删除 | 按产品 cache 策略处理 | 删除 | 提交新版本 |
| 卸载 | 无 | 删除匹配的 Store cache | 无 | 删除 App 与 receipt |

在出现明确的支持流程前，没有必要增加诊断 quarantine；直接删除是更小、更安全的 V0.x 策略。

## ESPocket 临时策略

在没有上游 Core/Store 变更的情况下，锁定的 0.8.x API 无法提供统一信任门。因此 ESPocket 必须：

- 保持 M5 `BLOCKED`；
- 只把当前 Store 当作集成与传输验证，不当作生产分发边界；
- 不安装任意下载或本地 `.bpk`；
- 不声称 `CONFIG_BROOKESIA_SYSTEM_CORE_ENABLE_PACKAGE_RELEASE_VERIFY=y` 等于验证已被强制执行；
- 不修改 `managed_components/`，也不增加替代 Store 或 package framework；
- 继续只允许显式构建预置的产品 Runtime App；
- 在启用动态安装前要求上游 hook/API。

在产品侧包装 `verify_app_package_release()` 并不足够，因为官方 Store 和 USB 路径可以绕过它，启动过程会扫描已解压目录，而 post-install hook 已经拿不到签名包 metadata。最诚实的本地 containment 是彻底禁用动态安装；项目明确拒绝仅为绕过 0.8.x 而实现第二套 installer。

## 验收矩阵

主机与单元测试必须覆盖：

- 有效包、正确 catalog digest、正确 key：安装成功；
- catalog digest 不匹配：解压前拒绝并删除；
- 未签名包：拒绝；
- `hash.json` 与 `signature.sig` 只存在其一：拒绝；
- key 错误或 signature 损坏：拒绝；
- 签名后修改 manifest、Runtime code 或 resource：拒绝；
- 存在额外或缺失的 signed member：按 release format 规则拒绝；
- 验证与解压之间尝试修改包：拒绝；
- ESPocket 上的 `systems: ["super"]`：拒绝；
- service 缺失或不兼容：拒绝，且旧 App 保持不变；
- 更新激活失败：恢复旧版本和 private data；
- 未显式授权的降级：拒绝；
- 卸载：删除 App 目录和 trust receipt，并删除匹配的 Store cache；
- 带有效 committed receipt 启动：能够发现；
- receipt 缺失、不匹配或 pending 时启动：不安装；
- 在每个事务状态模拟掉电：确定性回滚或提交；
- Store、USB 和未来任何 developer installer 都经过同一个 Core gate。

上游实现存在后，真机验收还必须增加：

- 安装、启动、Home、重启并重新启动签名且兼容 ESPocket 的包；
- 签名更新后 private data 得以保留；
- 人为触发更新失败后恢复旧版本；
- 卸载后重启，不得重新发现；
- 重复安装、更新、卸载，不得持续增长 cache 或 staging；
- 完整流程中不得出现 TLS、panic、reboot 或 Runtime isolation 失败。

## 必需的上游解锁条件

只有官方 Brookesia 提供以下全部能力或等价公共契约后，M5 包信任才能继续：

1. 每个 Core `.bpk` 安装路径都强制执行完整包 digest 与 release 验证；
2. 不可变的 verify-to-unpack 边界；
3. 可信重启发现，而不是无条件接受已解压目录；
4. 事务化更新回滚；
5. Store 对信任失败的清理与错误传播；
6. 至少一个官方支持、签名且 `systems` 允许 `espocket` 的包，以及受支持的发布与更新路径。
