# Store 签名测试产物

`python3 scripts/firmware/prepare_store_release_fixture.py --output /private/tmp/espocket-store-release-fixture` 用 Hello Runtime 的维护资源和项目锁定的官方 `@brookesia/packager` 生成独立 App `espocket.test.store_hello` 的 0.1.0、0.2.0。两者声明支持 `espocket`，通过 SDK 的内嵌 META-INF 发行签名与成员摘要验证。

输出必须是仓库外的新目录，包含产物 identity 报告及临时测试密钥；不提交私钥，不自动发布或安装，不修改维护样例。使用前先按 Firmware README 安装锁定 SDK，Node 需 20 或更新版本。`--node` 可指定运行时。

这只准备测试输入。Core 的统一 trust gate、不可变验证输入、receipt、故障回滚与可信重启发现仍需独立证明；正式 publisher/key identity 和 catalog publication 仍按 005/08 验收。不得把该临时密钥加入正式固件信任根，或把 SDK verify 结果当作安装成功。
