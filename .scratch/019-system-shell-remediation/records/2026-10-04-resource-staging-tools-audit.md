# 2026-10-04 — 隔离资源 staging 与工具核查

## 输入与边界

本线快照位于 `/private/tmp/espocket-019-resources-6nwoxorm`。baseline 包含捕获时当前未提交、未跟踪源码和文档，不是已提交 HEAD；working 从该 baseline 复制。原 checkout 未修改，未使用串口、刷写、重启或设备查询。首次磁盘可用 40 GiB，后续 37 GiB。只读进程检查发现 Store 正在构建，待其退出后才配置本线唯一 product-build。

## 当前资源来源、目标与依赖矩阵

| Owner / 输入 | 目标 | 更新与失败约束 |
|---|---|---|
| Circular Shell resources/gui.json | build/esp-idf/shell_circular/shell_gui.json → 固件 embed | configure_file COPYONLY 自动配置依赖；缺失源文件配置失败 |
| System light/dark_theme.json | build/esp-idf/espocket_system/espocket_*_theme.json → 固件 embed | 同上，实际主题保持集中资源 |
| Hello Native gui.json/card.json | build/esp-idf/hello/hello_gui.json、hello_card.json → 固件 embed | 同上，唯一 basename 防止符号冲突 |
| Hello Runtime src（manifest、JS、res root/screens/flows/profile/navigation/cards） | build/littlefs-root/apps/espocket.app.hello_runtime | Core runtime_app_stage target；产品 built-in hash header 由 CONFIGURE_DEPENDS/GLOB 跟踪，资源字节同时受准入约束 |
| Settings 0.8.3（实际选中的补丁组件 package/res） | build/littlefs-root/apps/brookesia.general.settings | Settings esp_platform 调用同一 Core staging；adapter 配置兼容检查；含 inline 466px assets |
| Store 0.8.2（实际选中的补丁组件 package/res） | build/littlefs-root/apps/brookesia.general.app_store | Store esp_platform 调用同一 Core staging；远程 Store 缓存/安装文件不是构建输入 |
| 三个 package staging targets | build/littlefs_data.bin | main 收集全局 staging target，LittleFS always target 原本每次重建镜像；新增完整性 target 排在 staging 后、镜像前 |
| 未来语言、文件字体、Files、动画资源 | 无当前 staging | 依赖各功能设计，未提前引入 |

System project_include 使用 Core 公开路径接口指定 CMAKE_BINARY_DIR/littlefs-root；设备挂载仍 /littlefs，App 根 /littlefs/apps。Native Settings/Store package 没有 Runtime manifest，不要求不存在的文件。

## 真实失败、修复与镜像实验

真实锁定 Core CMake + Ninja 最小工程：修改文件内容能更新；删除 obsolete.txt 后旧文件仍在 stage；将输入目录清空后 build 返回 0 且旧文件保留。这是 copy_directory 增量不删除目标多余成员导致的真实缺口。

修复在真实 Core staging Owner：新增 006-refresh-staged-package.patch，每次 copy_directory 前只删除本 target 独占的 package stage_dir。原 managed source 不改；manifest 精确补丁 hash 与 related issue 更新。未改变包信任或安装状态。

main/check_resources.py 在配置时检查源资源，在镜像 target 前检查全部实际 staged bytes。覆盖 root 声明与全部 variants 的文件资产、inline assets 的 imageSet 路径、imageSet 图片、Runtime entry 与 profile/navigation/cards；缺失或越界路径失败，源/目标多余、缺少或不同字节失败。它是当前产品构建门槛，不是通用 GUI schema 校验器，不证明动态文本、外部 App 或物理面板。

三个回归通过：真实 CMake Owner 删除与修改、关键页面/entry/navigation/图片缺失、stage 残留和错误字节。额外真实 LittleFS 4 MiB 镜像实验 clean/edit/add/delete 均成功（0.262/0.304/0.249/0.258 秒）；edit/add 镜像 SHA 改变，delete 恢复原始 SHA，目标无 obsolete。缺少关键 screens/main.json 返回 1（0.124 秒），镜像步骤未运行；此前镜像文件仍存在，仅有成功构建退出码才可当作有效新产物。

## 统一检查与集成限制

新回归通过。scripts/check.py 实际执行，但捕获的 baseline 中 Card rollback test fixture 未声明 launcher_generation_，Launcher projection test 缺少 algorithm 导入，因此两个 Owner 的 host 编译失败。本线未修改 Store 所属源码或弱化断言。无 .git 的源码快照导致 repository-layout 的 git ls-files 失败；以 GIT_DIR 指向原只读 Git index、GIT_WORK_TREE 指向快照单独执行四项布局检查通过，此检查只证明当时原 index 的生成目录边界，不能把快照称为 HEAD。

完整配置首次失败：checker 未处理现有 Settings 补丁 inline asset，已按真实 GUI root 格式修复并加入回归。build-patched 复制的 gen_bmgr_codes 包含原 checkout 的绝对 board override 路径；完整构建前需在本线目录重生成或重定位，并核对实际 selected HAL 路径。完整构建结果另追加，未完成前不关闭 08。

## 工具事实与建议

固定 Super commit e937455b0db1a3e873b1da61d6d13652f3dcc7e2；analyze_build.py SHA-256 1587b7a0ed44bba9e23ad22a7303bf77d9f35b8668ad65f83b794c01b8fbe7e6；compile_tuning.cmake SHA-256 950ecd425890acb14ba295b969e7b86be26e5b0275346d382195a78ab092665b。

对已有 production-final 的元数据做独立复制，原目录不写。分析器在副本上完整运行，包括复制的 .ninja_deps、build.ninja/rules：0.365 秒，204 components、2,103 translation units、2,345 latest output edges、200 Boost consumers；skip-deps 0.107 秒。GUI interface 累计 edge 462,946 ms、Core 405,207 ms、Settings 247,877 ms，是最新输出的累计 edge 耗时，不能等同 clean wall time 或各组件可节省的时间。报告位于隔离根 analysis/。

分析器建议作为手动 artifact 工具；开销低且无需固件变更。暂不复制到产品或每次 build 自动运行，实际采用可另开范围明确的工具票。

compile_tuning 已存在锁定 lib_utils，但 helper 是 passive。历史 CMakeCache 中 CXX_JOBS=6、FAST_COMPILE=OFF、CCACHE_ENABLE=False；build.ninja 没有 brookesia_cxx pool assignment，缓存值不证明策略已生效。helper 选 brookesia/esp-boost/main，不自动覆盖 ESPocket 自有 System/Shell/Hello targets；GNU 还会改变 IPA 优化，FAST_COMPILE 会降低 debug 信息，不只是并发工具。当前 PATH 无 ccache。未测量 cache cold/warm 或不同 pool 参数的收益，不自动采用固定并行数、-g1 或 IPA flags，也不放宽 warning policy。建议先稳定 correctness baseline，再用独立配置比较 wall time、峰值 RSS、对象/ELF 尺寸及调试质量。

UtilsService 已提供 GetDebugCapabilities/Config/State/Snapshot、GetMemorySnapshot；memory snapshot 是即时采样，thread debug snapshot 来自已开启的共享采集。Memory 提供 internal/external heap free/min/largest/fragmentation；Thread 提供 CPU、priority/core、stack high-water、task state，需要 trace/runtime-stats。当前生产配置关闭 BROOKESIA_UTILS_THREAD_PROFILER_ENABLE_FREERTOS_CONFIG、FREERTOS_USE_TRACE_FACILITY、FREERTOS_GENERATE_RUN_TIME_STATS，不能报告 CPU 数据可用。Thread 默认 1,000 ms window、5,000 ms interval，两次 task-status 分配及采样；Memory 默认采集由真实 scheduler 与 singleton 持有。源码成本不是实测设备开销。

现有 USB console 配置是 USB Serial/JTAG 日志端口，不等于已装配通用 Brookesia Console REPL。ESPocket 只有既有开发模式 Adapter 读入；只读指标导出应复用该协议，不新增第二个 reader。不开采集、不改变设备，也不能测得 Profiler runtime/RSS/帧延迟开销。Memory 有条件建议复用现有 Utils 查询；Thread 与设备 overlay 性能在 019/07 的设计/设备票验收，不在本票擅自实现或宣称通过。

## 板级副本隔离修复

在真实 build_patched_firmware.stage Owner 中增加已知 board generated paths 的重定位：只处理 gen_bmgr_codes 的 CMakeLists.txt、idf_component.yml、board_manager.defaults，将输入工程路径改为独立 firmware 路径；未知 checkout 的绝对 override 拒绝并要求重新生成。输入文件保持不变。13 项 stage host 回归通过，包含原始路径拼写与 canonical 路径、源文件不变、未知 override fail-closed。本线完整构建实际执行官方 gen-bmgr-config 并核对 brookesia_hal_custom selected dir 在本线 product-build 内；重生成目录不作为 patch 输入提交。

## 最终主机检查

最终 scripts/check.py 使用原 Git 的只读 index 仅供布局检查，工作文件均来自 working：87 项跨模块 host tests 通过，新增 resource gate 三项与 stage 13 项通过；统一入口仍返回失败，失败仅为 baseline 的 Card rollback fixture 未声明 launcher_generation_ 与 Launcher projection fixture 缺少 algorithm。两处失败文件与 baseline SHA 完全相同。本线不替 Store 修复这些测试，也不将局部 PASS 写成统一门槛 PASS。257 个 Markdown 检查通过。

## 完整构建与增量观测

同一唯一 product-build、ESP-IDF 6.0.1、Xtensa esp-15.2.0_20251204、Ninja 1.12.1、esp32s3/466px board；不改变 idf.py 默认并行参数，不启用 ccache/pool/FAST_COMPILE。配置与生成依赖在 clean build 计时前已准备。命令是加载 IDF export.sh 后 `/usr/bin/time -l idf.py -C /private/tmp/espocket-019-resources-6nwoxorm/product-build/firmware build`；连续两次执行，第一次没有编译对象，第二次输入不变。

| 观测 | clean | 未改输入 incremental |
|---|---|---|
| wall seconds | 486.35 | 2.88 |
| user/system seconds | 1150.77 / 286.03 | 1.52 / 0.58 |
| time -l maximum resident set bytes | 1,944,141,824 | 86,343,680 |
| 构建结果 | 完整链接/镜像/尺寸检查通过 | 三个 packages 重新 staging、完整性 gate、LittleFS 重建通过 |

这是单次会话观测，clean 期间并行运行过轻量 host checks；不作为隔离性能基准，也不能证明调优收益。time -l 的进程 accounting 值不等于全部并发进程 RSS 的同时总和。编译器/依赖已经物化，文件系统缓存未清空；incremental 并非 ccache warm build。完整 build 目录约 2.0 GiB；结束磁盘可用约 30 GiB。无并发第二个重型固件 build。

- ELF SHA-256 29d48a6652339b88300fe7208b05f3f3728817d494692385e60e5194f4257a8b（246,461,064 bytes）。
- BIN SHA-256 d5c46e30faeede2d2afab6876ba10c18c744d7761b3704a0265841158d9df2f7（7,720,864 bytes，应用分区剩余 28%）。
- LittleFS SHA-256 82aaa00fc9bf758ff53bdebc3b1690f71e17b1285454d2b66c9a6b3144b0c7ba（5,120,000 bytes）。
- 增量后 ELF/BIN/LittleFS 摘要与 clean 相同；post-build 精确 registry lock、production Audio 与有效配置字形门槛复核通过。
- 本线实际新元数据运行完整分析器 3.538 秒，2,107 translation units、201 Boost consumers；结果位于 product-build/firmware/build/brookesia_build_analysis.*。与历史复制报告不同输入，耗时不作直接对比或缓存收益推断。

本线实际完成源码与独立构建；统一 host check 尚有两项 baseline fixture 失败，未合入原 checkout、未部署、更没有物理/视觉验收。08 不关闭；13 的 ccache/并行策略参数比较与 Profiler 设备开销未测量且没有实际采用。后续完整集成可引用 build-identity.json、pre-build-verification.json、patch-inputs.json 和源快照 inventory，但必须重新核对 Store 后续变更。
