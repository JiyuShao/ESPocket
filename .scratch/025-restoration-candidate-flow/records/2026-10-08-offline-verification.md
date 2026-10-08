# 2026-10-08：前台恢复投影与隔离候选离线验证

## 实现范围

System 产品层集中恢复意图，Core 继续拥有生命周期；本 Effort 未新增上游 Core 补丁。有效 Running Instance 由 Core active App 的 Running/visible 状态及 System 已提交的 App ID/代次共同投影。QS 显示返回绑定实例和 Display 注册身份；Home、stop/deinit 清理目标。没有有效实例时不恢复非 GUI 来源；息屏失败不提交唤醒目标。Page 栈没有复制，投影没有重启 App 的调用。

隔离构建入口 stage 后保存 product/patched/evidence inventory 与 fingerprint，构建前后复核不可变输入、lock 和 patched 路径。成功才将 candidate.pending 原子改名为 candidate。镜像从实际 flasher_args.json 获取，按相对目录归档全部镜像；缺失、路径越界、输入漂移或 IDF 失败均不发布成功候选。

## 执行过程与失败证据

- `/private/tmp/espocket-025-candidate`：Component Manager 的 psutil 进程查询被 sandbox 禁止，reconfigure 失败；没有 candidate。日志 `/private/tmp/espocket-025-build.log`。
- `/private/tmp/espocket-025-candidate-v2`：补齐无效实例与息屏事务边界后取消该旧输入构建，保留副本，不把它当作最终候选。
- 最终源码在全新 `/private/tmp/espocket-025-candidate-v3` 中重新 stage，使用 ESP-IDF 6.0.1。日志 `/private/tmp/espocket-025-build-v3.log`。

## 验证边界

没有访问设备、串口或执行刷写。普通讲话打断、AEC 声学效果、真实触摸/视觉、250ms 响应及原始声音/页面卡顿仍未由本次离线验证证明。物理验收继续由 021／023／024 对应票持有；候选 LittleFS 是全新文件系统产物，不是设备数据迁移镜像。

## 原始上游保护

完整构建期间再次核对 production 所选的 17 个原始 managed_components 目录：全部 inventory 与各版本 patch manifest 的 source_files 完全相同。构建使用 workspace 内 patched_components，不改写原始上游源码。

## 完整构建与自动归档结果

ESP-IDF 6.0.1 完整构建成功，自动生成 `/private/tmp/espocket-025-candidate-v3/candidate/`；没有手工设置构建成功状态。构建后 product/patched/evidence inventory 与 stage snapshot 一致，Registry lock 与选中 patched 路径复核通过。

输入 fingerprint：`a61ef9bdf701dbd2064e52f5a09353378265938d8af23b10b2019182b9959bb3`。Manifest 保存 107 个归档文件的 bytes/hash，以及实际配置、配置生成前的原始 lock/sdkconfig、补丁字节和全部镜像。

| 镜像 | bytes | SHA-256 |
|---|---:|---|
| `bootloader/bootloader.bin` | 22528 | `f7a72d47571ae45c0c10c6698661ad7d668493d7568037eab425cd6a8d062577` |
| `partition_table/partition-table.bin` | 3072 | `a36fc76cb99ebb23c40b352afc9434aa8d760ee9f76ed9f6feb4a41b539e286d` |
| `srmodels/srmodels.bin` | 125951 | `72447db11fd5bc683507ddd6727bea458473873019bf919858ed520a87429894` |
| `littlefs_data.bin` | 18481152 | `4cfbdd61580aef943526de42307fc571e280426813a5dd2bc5bd85d0f64baa39` |
| `espocket.bin` | 11233456 | `31936034fef6070616d941fdcdc3552d307d14b0e1c6f835d5de33ed5ad6e360` |

候选使用原有 Core/Runtime render profile 配置，软件 AEC 候选关闭。`deployed=false`、`physical_validation=false`。

## Host 回归

最终 `python3 scripts/check.py` 全部通过：执行 229 项测试，227 项通过、2 项跳过。日志 `/private/tmp/espocket-025-check-final.log`。其中候选构建测试主动模拟 IDF nonzero，日志中的对应失败消息是通过的失败路径回归，不是最终固件构建失败。

真实 projection interface、Core 状态采样、System QS/Display guard、启动请求归属、PWR 取消与停止作用域回归通过。Markdown 在完成结果记录后另行复核。
