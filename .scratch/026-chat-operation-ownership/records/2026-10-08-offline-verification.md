# 2026-10-08 — Chat 异步归属离线验证

## 已确认

实际 App 回归在修改前复现：旧 Activate 失败把新 Agent 的 status.starting_agent 覆盖为 status.activate_failed。修复后 Chat 的 11 项测试通过，包含实际 lifecycle 与 operations 模块；不是只验证重复实现的替身。

本轮修改位于 Chat App 源码、测试、版本与文档。原有 021–025 工作保留，没有添加平台补丁。

## 本地包

- 路径：`/private/tmp/espocket-026-packages/ai_chatbot/espocket.app.ai_chatbot.debug.0.1.6.bpk`
- SHA-256：`eda8ba8d896a9ba7952ea00526c0d7aa509f0fd0c876dc3752f98ff5c3510926`
- 大小：88,199 bytes；32 个成员逐项与源码一致。
- 官方 packager 0.1.7，开发未签名包；deviceAccepted=false。

## 验证边界

全部 host 测试与完整隔离构建已完成。没有部署、串口测试或提交代码。失效归属只抑制旧回调发布，不取消已提交的服务副作用；无请求身份的服务事件仍由现有真实事件处理。声音、回音、触控和时延未进行真机验收。

## 统一验证

- `python3 scripts/check.py` 执行 231 项测试，229 通过、2 跳过；Lifecycle parser self-test 通过。
- 首次统一入口仅 Markdown 子项失败：本工作票误用了 in-progress。改为规范状态后单独重跑 `python3 scripts/docs/check.py --markdown`，327 份文档通过；没有代码测试失败，也没有重复执行已通过测试。
- 提交前暂存检查覆盖了新增文件；修正一处测试脚本行尾空格。补丁文件内空白上下文行是 unified diff 格式，保留已验证字节与 manifest hash；排除补丁载体后 `git diff --cached --check` 通过。
- 完整隔离 ESP-IDF 构建退出码 0，构建后不可变输入、selected component 路径与补丁校验通过。

## 固件候选

- 目录：`/private/tmp/espocket-026-candidate/candidate`
- 状态：built_candidate；deployed=false；physical_validation=false。
- 输入 fingerprint：`fdb567a6fd4a50bd680d18c7b806ce2c1ba6baad0909f37813448c8c82ae205f`
- Chat App 0.1.6 内置源码包含 operations.js；保留既有 021–025 改动。
- 软件 AEC 候选开关关闭；Runtime render / Core profile 保留开启。
- LittleFS 是全新文件系统镜像，不是设备用户数据迁移镜像。

| 镜像 | bytes | SHA-256 |
|---|---:|---|
| `bootloader/bootloader.bin` | 22528 | `c22803958b088eb049c47d1eb5eed6c8e5de5820d6c2734d5dfa01e04eb27682` |
| `partition_table/partition-table.bin` | 3072 | `a36fc76cb99ebb23c40b352afc9434aa8d760ee9f76ed9f6feb4a41b539e286d` |
| `srmodels/srmodels.bin` | 125951 | `72447db11fd5bc683507ddd6727bea458473873019bf919858ed520a87429894` |
| `littlefs_data.bin` | 18481152 | `17208092f947e4b0b938c80920267ce709cd4414516a147dfd17705fed617a5f` |
| `espocket.bin` | 11233088 | `a7634fb63581493f0e03738e0fec886c850f949f5e93e93707782ff78ff61936` |

候选还归档 ELF、flash 参数、配置、lock、补丁和输入 inventory；本次再次逐项核对全部归档文件的大小和 SHA-256。App 镜像 11,233,088 bytes，App 分区余量约 23%。构建包含上游 Kconfig 警告，没有构建错误。
