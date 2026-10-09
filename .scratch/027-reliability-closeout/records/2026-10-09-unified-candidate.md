# 2026-10-09 — 最终统一普通验收候选

## 输入与验证

- 构建目录：`/private/tmp/espocket-027-candidate-v3`
- 候选目录：`/private/tmp/espocket-027-candidate-v3/candidate`
- Git 基线：`2511be4707c2f87f3ae7edaa175874f7c0bad149`，加本轮未提交 Core 026 补丁及测试；不是仅由 HEAD 构建。
- 精确输入 fingerprint：`95336c7b76aa5e6dde4e77430d1896531395894b7c88870821db9cdc237be477`
- 以候选 `inputs/input-snapshot.json`、`inputs/patch-inputs.json` 和归档补丁字节作为实际源码／资源／补丁证明；checkout 后续文档状态更新不改编译输入。
- 全新独立目录完整 ESP-IDF 构建退出码 0；original registry lock、selected component 路径、有效配置与不可变输入校验通过。原始 managed_components 未修改。
- 最终 `python3 scripts/check.py` 全部通过，232 项测试执行、230 通过、2 跳过。日志 `/private/tmp/espocket-027-check-v3.log`。
- 修复的 stop／重启、Dialog／Keyboard 迟到结果和拒绝调度回归通过；实际 deinit 和 partial GUI teardown 回归通过。失败清理、Card commit／rollback、Chat ownership、Shell interface 和资源 staging 原回归通过。
- 完成归档后再次逐项核对 108 个文件的大小与 SHA-256；Core patch manifest 与当前冻结修复字节一致。

## 资源版本

| App | 版本 | staged manifest SHA-256 |
|---|---|---|
| `espocket.app.ai_chatbot` | 0.1.6 | `2e73896fd9375a9beffd97963d7a005f93e809b3f5bf1a9b890ccf42ca5ab42e` |
| `espocket.app.calculator` | 0.1.0 | `051b9094033711ecd663f4ecdd21e88aade48115e9918f78150df1983c11e6c7` |
| `espocket.app.hello_runtime` | 0.1.0 | `efc63a1bca7f933c5f4b1168c9957233e6027b6fe092d4d99d86c4082c6cbd6e` |

Shell、light/dark Theme、字库、Settings 与 Store 的每文件版本由实际输入 inventory 和锁定组件 manifest 记录，不使用 App 版本号代替这些资源身份。

## 有效配置

软件 AEC 关闭，保留普通半双工播放抑制策略；Runtime render 与 Core profile 开启。CJK font 开启，图像缓存预算 524,288 bytes，自动息屏 30 秒。M2 生命周期压力、M8 Card 样例、package acceptance fixture 均关闭。该候选不含逐失败点注入或外部 System 重复运行协调器，不能自动执行这些未准备的物理路径。

## 镜像

| 镜像 | bytes | SHA-256 |
|---|---:|---|
| `bootloader/bootloader.bin` | 22528 | `4a28433fac3b2cbb1e011e5349cdb9a59323e4d0a8b9e3ba87e13815f493a319` |
| `partition_table/partition-table.bin` | 3072 | `a36fc76cb99ebb23c40b352afc9434aa8d760ee9f76ed9f6feb4a41b539e286d` |
| `srmodels/srmodels.bin` | 125951 | `72447db11fd5bc683507ddd6727bea458473873019bf919858ed520a87429894` |
| `littlefs_data.bin` | 18481152 | `17208092f947e4b0b938c80920267ce709cd4414516a147dfd17705fed617a5f` |
| `espocket.bin` | 11234592 | `3adb238c4d7c5448953a7804b03fc7a310de61bae862aa7230ac7350925cf178` |

ELF：386588416 bytes，SHA-256 `9d4ae93e625d6379526c9302c95f41a6a3c60caef23d0157521c5e25e0a04c20`。App 分区余量约 23%；完整归档另含 flash 参数、config、lock、补丁与输入证明。

## 状态与边界

`built_candidate`，`deployed=false`，`physical_validation=false`。LittleFS 是 fresh filesystem，不是用户数据迁移产物。设备返回后先保存最新备份，再用完全相同的冻结 App 源码按[候选票步骤](../issues/02-unified-device-candidate.md)生成保留数据资源镜像。当前没有设备数据可用于制作真实迁移镜像。

本轮没有串口访问、设备 reset、部署、commit 或 push。安静误识别、声音卡顿、打断、实体触摸与最终配色都没有新增物理通过证据。缺代码／夹具项按[收尾矩阵](2026-10-09-reliability-audit.md)保留；AEC 需要另一个同基线实验配置，不把本普通候选称为 AEC 候选。

旧 candidate 与 candidate-v2 已被主动终止，未归档成功候选；保留其日志与源码目录作为收敛过程证据，不用于部署。
