# Runtime 包发行输入

正式发行包必须声明支持 `espocket`，包含官方 SDK 生成的 `META-INF/hash.json` 和 `META-INF/signature.sig`。Catalog 的 package identity、版本、下载大小和 SHA-256 必须与实际 BPK 一致。开发者模式接受的 unsigned/super 例外不属于正式发行。

## 准备与验证

签名目录必须已有发布者的 `private.pem` 和 `public.pem`；私钥留在仓库和设备之外。使用锁定的官方 SDK：

```bash
python3 scripts/firmware/prepare_runtime_release.py \
  --source /path/to/app/source \
  --sign-dir /path/to/publisher-signing \
  --output /private/tmp/new-release \
  --artifact-url https://your-distribution.example/app/version/download
```

入口校验目标系统和 identity，用已存在的 key 生成包并执行 SDK 验签，保存 BPK、metadata.json 与输入报告；不自动生成发行密钥或上传。报告中的 public key 摘要应与设备配置的信任公钥摘要核对。两版本更新验收分别生成独立目录，不覆盖旧版本。

## 设备与发布门槛

设备 Core 必须配置相同公钥，经真实安装路径完成验签、成员完整性、兼容性、receipt、更新回滚和重启发现。SDK 验签通过只证明产物符合该 key，不能证明 key 所属发布者可信或设备已接受。

上传到实际分发端之前，需要确认发布者身份、受支持的 Catalog 写入权限、版本更新规则和下载 URL。上传后重新下载实际 artifact，严格核对 metadata 摘要与 BPK，再执行设备验收。当前测试 key 及本地测试包不作为正式 trust root；当前没有已经验收的官方 ESPocket 签名包或 Catalog 发布权限。

产品准入规则见[Runtime 包信任](../design/product/05-runtime-package-trust.md)。

## 隔离真机验收输入

`prepare_package_acceptance.py` 只复制公开测试公钥和两个固定 `espocket.test.store_hello` 签名版本，拒绝其他 identity；私钥不进入设备或生成 header。准备外部输入后，在隔离构建的 sdkconfig 中显式开启 `CONFIG_ESPOCKET_PACKAGE_ACCEPTANCE_TEST` 并指定 `CONFIG_ESPOCKET_PACKAGE_ACCEPTANCE_INPUTS`。两项默认关闭，普通镜像没有测试 trust root。

测试在已有 App Owner tick 中调用真实 Core install/start/update/uninstall、Storage 和 Developer Mode API，注入一次新版本激活失败，核对旧版本与 private data，在 pending activation 内重启以验证旧版本恢复，再执行提交后的受控重启，再核对 discovery 和清理。Flappy Bird 必须已安装；模式关闭期间 USB 自然被拒绝，内部测试恢复初始模式后才可继续读取。它不扩展 USB 命令，也不替代 Store 的触屏确认验收。串口 `ESPocket.PackageTest` 的逐项 PASS 与最终 COMPLETE 才构成完成证据；FAIL 和中断必须保留。

```bash
python3 scripts/firmware/prepare_package_acceptance.py \
  --inputs /path/to/isolated-signed-test-fixtures \
  --output /private/tmp/package-acceptance-inputs
```
