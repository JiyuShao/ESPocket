# 2026-10-04 Package implementation handoff

## 状态与依据

用户确认开发者模式允许 unsigned 和显式 super Runtime 包，缺导航声明的外部旧包不伪造 Page 语义；取消无副作用，关闭模式停止实例并保留安装。设计提交为 8711179，ADR-0018 与 03/09 为权威。仓库新增 Codex design-only 规则后，后续实现、最终验证和提交交给 Claude Code。

目前代码为未提交 candidate；其他聊天有大量暂存及未提交改动，必须保留。未刷入设备，09 尚未验收。

## Candidate 与证据

- 产品接入位于 firmware/components/espocket_system 的 CMakeLists、system.hpp、system.cpp、system_power.cpp、system_runtime_navigation.cpp。
- Core 005-runtime-package-admission.patch、Store 002-developer-install-confirmation.patch 与各 manifest；Host test 为 firmware/test/host/test_runtime_package_admission.py。
- 原始上游不改；Core 工作副本 /private/tmp/espocket-core-admission-work，基线 espocket-core-admission-base；Store 同名 store 副本。临时发布脚本 /private/tmp/espocket_publish_policy_patch.py 可重建 diff 与 sha；不要重跑历史 edit 脚本。
- Host test 实际编译 patched package.cpp 与提取的 installer methods，覆盖准入、内容/路径完整性、pending/committed、mode-off、built-in exact inventory、更新失败及恢复；最新单测日志 /private/tmp/espocket-package-final-host.log 已通过。此前完整检查 /private/tmp/espocket-developer-all-host.log 为 80 项通过，但晚于此的修订必须重跑。
- 隔离构建 /private/tmp/espocket-developer-package-build，日志 /private/tmp/espocket-developer-package-final-build.log 通过，app 大小 0x6b4400，剩余 35%。最后的包路径/深度/receipt 限制尚未同步到此构建，不能将其作为最终镜像。
- 构建需 IDF6.0.1；board manager extension gen-bmgr-config 和 Audio candidate config 已补齐。scripts/firmware/build_patched_firmware.py 为核对入口；重同步最终 patch-inputs 与所有 manifest SHA，并核对 registry lock、Audio config、字体。

## 必须完成的缺口

1. Receipt 补显式 transaction identity、manifest digest、签名 key identity（unsigned 明确未验证），不能只有 artifact/member map。
2. 更新期间 product on_app_uninstalled 会剪除/持久化 Card 配置；保证失败回滚后旧版本、private data 与 Card 配置均保留。由正确 Owner 解决，不新增第二套 installer。
3. 首次安装掉电产生的无 backup pending、orphan .installing 清理需真实测试；不得删除已提交版本。
4. 核对 Store prompt 的 Cancel、代际隔离、捕获 SHA/ID/version 的实际行为；host signed verifier stub 只覆盖失败不降级，正式 RSA 验证仍需真实 verifier 证据。
5. product 尚未配置发行 key，signed external 包 fail closed；不得把开发路径算正式发行完成。Linux host CommonCrypto/OpenSSL 分支需声明 libssl-dev 依赖。
6. 最终全检查、全构建及实际安装未完成；更新 ticket 与证据之后仅提交本次明确路径，不夹带其他聊天改动。

## 设备与安装路径

- /dev/cu.usbmodem101，设备 A0:F2:62:E3:0B:68；当前普通镜像 5bb555ca5，开发者模式 On、深色。
- app offset 0x60000；LittleFS offset 0xaa1000、size 0x4e2000。安装前备份；只刷 app，禁止用构建 LittleFS 覆盖当前安装内容。
- 官方 Flappy Bird：brookesia.general.flappy_bird 0.3.0，super、unsigned、缺导航声明。/private/tmp/espocket-store-flappy-current.bpk，63837 bytes，SHA256 ffdf1250f6be38377fe46617b6e0cca196cad4a388f9009edcdf87045165297a；metadata 同目录 espocket-store-flappy-metadata.json。原包不可改。
- device/support/usb_test_client.py、e2e/store_online.py 与 profiles/circular-466.json 提供现有自动化。Store tap [233,378]、Refresh [376,72]；列表目标需要按真实顺序/布局校准。
- 外部旧包的 page snapshot 应返回 page_adapter_unavailable；自动化使用原始 stimulus.touch/PWR request 和实际 Core lifecycle 日志，回 Home 后再读取正常 snapshot，不伪造导航。
- Developer Mode Off 后 USB 自然不可用，不扩展协议绕过；需要人工重新开启时集中请求一次，或使用隔离且最终撤除的设备测试 fixture。未做物理验证明确保留。

## 派发回执

- 时间：2026-10-04 08:20 Asia/Shanghai。
- 显示名：espocket-005-impl。
- 完整 session ID：46079258-f54f-4a0e-8886-ea2d9f7ef64e。
- CLI 启动曾返回 backgrounded，但身份核对的 --all 元数据显示 state=failed，不能称为持续执行中。
- 读取启动诊断失败：ECONNREFUSED /tmp/cc-daemon-501/e0e13790/control.sock。这证明后台控制端不可连接，不足以判定实现是否曾执行；未读取实现输出、未新建重复 session。
- 同项目另一个 espocket-020-impl 也为 failed。由用户修复 Claude Code 后台服务后恢复已有 ID；不以 CLI 状态替代 ticket 验收。

## 2026-10-04 08:23 身份核对更正

用户要求继续后尝试恢复原 ID。CLI 提示原会话已运行并创建副本 17491730-1995-4db1-81b4-544779a1c437。经允许访问控制 socket 的沙箱外身份查询，原会话 46079258-f54f-4a0e-8886-ea2d9f7ef64e 实际为 working/busy；此前沙箱内 failed 与 ECONNREFUSED 为无法访问后台控制端导致的误判，不能视作后台服务失败。

为避免相同写入范围并发，已停止副本 17491730，CLI 返回 stopped；保留原 espocket-005-impl 继续授权 03/09。没有读取实现输出或验收结果，也没有宣称完成。后续 CLI 身份管理需要能够访问控制 socket 的执行环境。
