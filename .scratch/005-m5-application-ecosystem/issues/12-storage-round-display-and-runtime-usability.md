# 12 — 存储、圆屏适配与 Runtime 可用性

Sequence: 12

**Status:** resolved
**Blocked by:** 无；Store 已有开发者准入、事务安装与用户授权。
Origin: 2026-10-06 用户要求修复缓存与容量、Launcher/Weather 卡顿、系统侧圆屏显示，并安装除 Camera 外的 Store 应用；沿用验证后合并 main、清理任务分支的授权。

## Scope

在独立 worktree 中启用设备实测的 32 MiB Flash，迁移现有 LittleFS 文件，保留 NVS、安装版本及用户 data/files。Store 缓存回收由 Store Owner 管理；Core 保持不可变安装原包、完整验证与回滚。圆屏兼容在系统 GUI Owner 实施，原始包不重写。优化必须以同机 Launcher 滚动和原 Weather 操作为对照。安装全部非 Camera Catalog App；缺少真实 Service 或外部凭据时记录准确结果，不绕过准入。

## Acceptance Criteria

- [x] 芯片容量、分区和现有文件清单有可审计备份；32 MiB 分区迁移保留所有非可回收内容，逐文件摘要核对，设备重启发现通过。
- [x] Store 安装成功回收自有重复下载包；缓存容量有界、旧版本／空间压力回收不删除正在使用的包、安装原包和用户文件。
- [x] 下载／安装空间预算覆盖候选原包、解包成员、更新保留内容及文件系统开销；不足提前返回稳定错误，失败保持旧版本。
- [x] Launcher 与原 Weather 建立无截图干扰的基线，候选使用相同操作序列测量；保留失败与限制，不把响应成功等同流畅。
- [x] 系统侧圆屏兼容使 Calculator 四角控件可见且可点，Weather 可滚动；原包摘要不变，Native/Shell/Overlay 生命周期及输入坐标回归通过。
- [x] 非 Camera Catalog App 逐个完整验证、安装、启动、Home 与重启发现；缺少真实能力或凭据的结果逐项说明，不伪装安装成功。
- [x] 全部 host checks、Markdown、精确补丁输入与完整固件构建通过，最终设备镜像身份与证据一致。
- [x] 按已有授权提交并合并本地 main，清理本任务 worktree／分支，保留其它工作，不自动 push。

## Comments

2026-10-06 容量盘点：esptool 实测 GD Flash 32 MB，当前配置 16 MB；LittleFS 总量 5,120,000 bytes，allocated 4,800,512、free 319,488，201 个文件。Store 九份下载原包合计 1,009,023 bytes，其中四份与已安装原包完全相同。纯内存备份模拟清理四份重复缓存后 free 1,007,616；清理全部九份下载包后 free 1,351,680。尚未对设备执行清理。PSRAM 为 8 MB。原始备份、清单和读盘日志保存在本地临时 artifact，长期事实进入本票 records。

## Resolution

存储迁移、缓存策略、安装预算、圆屏代码与性能对照完成；所有非 Camera App 已安装，最终普通镜像 `69edbcc15` 的八个 App 启动／Home、Calculator 四角运算、Weather 实际滚动、Native/Runtime apps／navigation／surfaces 全部通过。安装后 LittleFS 剩余 11.58 MiB，193 个原文件摘要未变，八个删除项全部为 Store 下载副本。148 个跨模块 host tests、各 Owner suites、Markdown、精确输入与完整构建通过。已按授权纳入本地 main 并清理任务 worktree；证据、外部凭据条件与准确性能限制见[验收记录](../records/2026-10-06-storage-round-runtime.md)。
