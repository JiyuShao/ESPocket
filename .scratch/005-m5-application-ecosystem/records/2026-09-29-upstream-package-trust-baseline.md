# Runtime package trust local baseline — 2026-09-29

> 文档类型：锁定依赖源码事实快照。它不定义产品契约，也不证明 M5 已通过。

本页从 Brookesia System Core 0.8.4、App Store 0.8.2 和当前依赖锁中抽出影响远程 Runtime 包信任的事实。实施前必须按届时锁定版本重新核对。

## 已有机制

- System Core 提供 `verify_app_package_release()`，要求 `META-INF/hash.json` 与 `META-INF/signature.sig`，验证 RSA-PSS-SHA256 签名和成员 SHA-256。
- Core 验证 manifest identity、系统兼容性、Service 要求和解压路径。
- 包可以 staging 到 `.installing` 目录，激活前验证 manifest 与 resource。
- Runtime storage 与 App code root 分离。

这些能力存在不代表公共安装路径已经强制调用它们。

## 公共路径缺口

锁定版本中的以下入口没有形成一个统一强制信任门：

- App Store 下载与安装；
- `SystemApi::install_runtime_app_package()`；
- System Core 的 Runtime package install；
- 启动时扫描已解压 App 目录；
- 可选 USB `InstallBpk` bridge。

Store 会解析 Catalog `hash_sha256`，但在 cache rename 和安装前不计算并比较完整下载字节。安装后的 hook 也无法补救：Core 解包时排除 `META-INF/`，原始签名材料已经不在安装目录。

## 重启发现缺口

启用 package App 扫描后，Core 会从配置的 App roots 接受兼容的已解压 manifest，不要求签名或 Core-owned trust receipt。仅在 Store 验证一次不能防止重启后绕过信任来源。

Build-staged Hello Runtime 属于固件构建供应链，可以作为内置样例；它不能证明任意已解压目录可信。

## 更新事务缺口

当前更新流程在 staging 新包后先卸载旧 Runtime App，再 rename 并安装新记录。旧目录移除后若 rename、GUI preparation、lifecycle hook 或新 Runtime 安装失败，Core 没有恢复旧版本的完整事务。

密码学验证必须先于此过程，但验证成功本身不提供回滚。

## Cache 与发布缺口

- Store 把完成的 partial download rename 为最终 cache `.bpk`；Core 安装失败不会自动删除该文件。
- Core 卸载已解压 App 时不会删除 Store cache。
- 核查时已知官方 Catalog 包未提供 ESPocket 所需的签名和 `systems: ["espocket"]` compatibility。
- 本仓库没有执行私钥生成或签名操作。

## 产品影响

在统一 Core 信任门、不可变 verify-to-unpack、事务更新、可信重启发现和兼容签名发布路径同时存在以前，动态安装与动态 Launcher 必须保持关闭。

产品契约见 [Runtime 包信任](../../../docs/design/product/05-runtime-package-trust.md)，当前任务与结果见 [Application Ecosystem Spec](../spec.md)。
