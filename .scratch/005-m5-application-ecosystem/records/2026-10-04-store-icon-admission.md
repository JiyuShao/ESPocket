# 2026-10-04 — Store 图标请求容量回归

普通 24acc698e 捕获 4 次图标请求被 HTTP 的 1-request 容量拒绝，证据见 [可用性诊断](2026-10-04-store-availability.md)。锁定 Store 实际版本是 0.8.2（component hash ad0bbb0e101e79c88cf1686fe7dc27c3428e8499451ae46b5cac744845eb5036），不是 Settings 0.8.3。

## 真实控制流回归

`python3 -m unittest discover -s firmware/test/host -p test_store_icon_admission.py` 抽取完整真实 process_refresh_icon_step，在异步提交失败回调处注入容量拒绝。原版 FAIL：transient HTTP capacity rejection permanently discarded the icon。随后容量恢复也没有机会重新提交同一个图标。

候选补丁在临时容量拒绝时保留 cursor，通过已有 Owner timer 延后同一图标，使用与 size metadata 相同的 retry delay。正常错误仍推进到下一个；context 已停止时不增加 timer。真实通用提交结果 callback 仍使用原 async_generation 检查；没有提高并发上限，也未更改安装或 trust gate。

补丁与完整 hash manifest 在 firmware/patches/espressif__brookesia_app_store/0.8.2；仅显式 store-candidate 使用，原始 managed_components 不修改。Host、完整构建与当前设备结果分别补录；这不是完整 Store 可用性验收。

## 当前官方包核对

本机 HTTPS 获取当前官方 index.json、Flappy Bird 0.3.0 metadata 和 download artifact；BPK SHA-256 ffdf1250f6be38377fe46617b6e0cca196cad4a388f9009edcdf87045165297a 与 metadata 完全一致，原始产物在 /private/tmp/espocket-store-flappy-current.bpk。包 manifest 的 systems 只有 super，ZIP 中没有 META-INF/hash.json 或 signature.sig。此实际产物无法满足 ESPocket 的兼容性与签名要求。

Core 0.8.4 已有 verify_app_package_release，但 install_runtime_app_package 在当前源码中直接读取 manifest、解包并提交，没有调用这个验证函数；当前更新还会先卸载旧 App，不能据此宣称事务回滚与可信重启发现成立。005/03 的签名、不可变候选、receipt 与事务要求继续有效，不能用放宽 systems 或 unsigned build-staged 包关闭安装票。

## 候选构建与真实在线结果

独立 store-candidate 全量编译、链接与 source/patch hash 校验完成，首个镜像 5d6de3fd8。应用分区 flash verify 和设备 hello 一致。启动实际先后提交 music_player、flappy_bird、ai_chatbot、camera 四个 icon；本次不再出现原有四次容量拒绝跳过。随后手动 Refresh 的 index HTTP 成功并真正写入 cache/index.json；cached startup 不被计算为在线成功。

第一次退出后重进 E2E 报 Synthetic input tick failed: internal，实际原因是已完成 release 打开 App 后，System 仍因 foreground token 改变执行 cancel，额外 reset LVGL 时 100 ms 锁等待失败。真实 System::tick_test_touch + TouchInputSequence 主机回归先 FAIL：completed release recancelled after launching App，修复后 PASS。未发送点的跨任务取消、显式硬件取消与 cleanup 失败仍保留原规则。

最终镜像 5bb555ca5 的在线 E2E PASS：本次 Refresh 正向证据、Home、停留和重进均通过，报告 /private/tmp/espocket-store-online-fixed-e2e/20261003T192145Z-f7dba95c-ff75-408d-a60b-a17ce8114bf7/report.json。前面的失败 attempt 全部保留：5d6de3fd8 两次触摸清理失败；5bb555ca5 第一次 Refresh 期间 snapshot mailbox 超时返回 invalid_state，未算 PASS。测试改用已有 quiet window 捕获长耗时 Refresh 日志，操作结束后查询快照，不忽略错误响应，也不把 ACK 作为成功。

新 suite 位于 firmware/test/device/e2e/store_online.py，命令 run_device_tests.py --suite store-online。不下载／安装，不覆盖 offline、全部 timeout/deinit 故障矩阵或可信重启；005/06 与 03/08 仍不因本次在线成功自动关闭。

## 签名输入准备

使用项目锁定的官方 @brookesia/packager 生成独立 espocket.test.store_hello 0.1.0、0.2.0，均声明 espocket，并通过官方 SDK 的 META-INF 签名和成员 SHA-256 验证。脚本 scripts/firmware/prepare_store_release_fixture.py；报告 /private/tmp/espocket-store-signed-fixture-20261004/report.json。临时测试 key、产物只在仓库外；没有发布、安装或配置为正式 trust root。这只解除测试输入准备工作，不代替 Core trust/transaction 或正式发布门槛。

活动 Refresh 取消另有正向证据：/private/tmp/espocket-store-cancel-direct-5bb555ca5/report.json PASS，监听到 index request 2 提交后立即发送 PWR；同一 id 记录 Canceled，随后 HTTP stopped，未写入该次在线 index，重进和 Home 正常。先前 Driver 在发送 PWR 前查询快照的 attempt 由于 mailbox deadline 失败，原记录保留，不能计算为活动请求取消通过。

经过真实在线与活动取消门槛，本次 Store 图标补丁加入 production 的七组件基线；显式 store-candidate 为同一 patch set。这只采用已验证的局部修复，不表示 005/03 的 trust gate、正式包和 catalog publication 已完成，亦不关闭全部 005/06 shutdown/offline 要求。
