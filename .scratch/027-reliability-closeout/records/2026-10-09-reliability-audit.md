# 2026-10-09 — 旧票核对与离线可靠性

## 核对基线

Git HEAD `2511be4`，开始核对时工作区干净。当前已包含 021–026 的源码、测试与工作记录。最新前置候选是 026 的 Chat 0.1.6，229 tests 通过、2 skip，327 Markdown 通过，完整隔离构建成功；该候选未部署。历史设备证据仍有效，但不自动迁移到当前源码。

## 收尾矩阵

| 原票 | 当前源码与离线证据 | 剩余性质与唯一归属 |
|---|---|---|
| 017/01 | 已 resolved；主题迁移与对比度门槛存在 | 不重做；最终画面由 017/02 持有 |
| 017/02 | 普通态 schema、系统配色修复已实施并有历史刷写 | 只差当前候选的 light/dark 配色及按钮像素确认；024 覆盖态共同观察 |
| 017/03 | check_glyphs、18sp chevron、实际字体门槛已进入构建；历史完整构建与刷写有证据 | 只差箭头像素确认；不重复静态字体工作 |
| 019/01 | Display 获取失败 guard、Shell start guard、Core partial init/GUI teardown 在真实 Owner；对应 cleanup suites 存在 | 真实 callback/GUI 竞争、失败诊断与显式重启未验；普通候选不含逐失败点注入夹具，补齐测试入口后才能做完整验收；fake scheduler 不能写成硬件通过 |
| 019/02 | System stop 遍历受管实例并先撤销入口、Shell 最后停止；Core 三轮模拟生命周期与 scope 回归已有 | 本轮发现系统 Dialog 在 stop 后残留；修复后仍需完整产品 stop→start / deinit→init 各三轮、后台与在途回调资源证据。现有 USB Adapter 会在 stop 时关闭，缺外部生命周期协调夹具，不等同只差连设备 |
| 019/03 | 024 已集中实际 Shell interface，并覆盖重叠／过期／草稿／PWR／锁失败连续路径；Core 原请求有效性仍为事实源 | 只差物理触摸、显示与停止竞争；与 024/01 同轮验收，不再抽取第二套仲裁模块 |
| 019/04 | Loading hook、022 样式、023 分阶段启动、025 请求归属均已实施 | **缺代码**：Super Startup / Shell launch/icon 动画尚未迁移；单阶段 binding/Runtime/GUI 阻塞仍未治理。250ms 也未测，不能归为只差真机 |
| 019/05 | init_product_theme / restore_product_theme 在 Surface 前执行；Core 保存抑制；unknown/Light fail/Dark fail 实际方法回归 | 有效主题保存／恢复差实际存储和重启证据；unknown/apply-failure 和默认不可用路径还缺故障注入夹具，不能只归为设备等待；不是 017 配色或即时切换新功能 |
| 019/08 | 014-refresh-staged-package、main/check_resources.py 与真实 CMake/LittleFS edit/add/delete 门槛已整合；025 自动绑定副本输入和全部镜像 | 本轮统一检查／完整构建通过，已关闭离线核查；视觉留原功能票 |
| 014/03 Card 更新迁移 | 005 Core replacement 事务 hooks、System snapshot/commit/rollback、Registry RemovedByUpdate 与 AppUninstalled 已存在；原 needs-info 接口 blocker 过时 | 更新未删除 Card 保留、删除原因和 rollback 源码已满足；真实安装/断电/NVS 由 005/03 持有，不新建同义迁移票 |
| 025/01–02、026/01 | 实例恢复与候选归档已 resolved，Chat 旧 Promise 归属已 resolved | 不重复实现；025 投影的物理恢复由 024/021，Chat 声学／恢复由 020 持有 |

## 生产方法核对

- 初始化／失败：System display/startup diagnostic、CircularShell on_start guard；test_display_initialization_cleanup、test_start_failure_cleanup、test_core_initialization_cleanup、test_core_partial_gui_initialization、test_core_gui_cleanup_result。
- 停止／旧请求：System on_stop / on_deinit；test_stop_scope；Core monotonic request IDs 与 stop/drain；Chat test_operation_ownership、test_chat_operations；Shell test_overlay_presentation 使用实际声明和 implementation。现有 System/Core 部分 harness 抽取真实完整方法并替换外围类型，不宣称等价完整产品 ABI 或线程调度。
- Card：System on_app_replacement_prepared/replaced/committed/rolled_back 和 restore_replaced_card_state；CardRegistry update/uninstall prune；test_card_replacement_rollback 编译生产方法与真实 Registry/Store。已有用例覆盖成功删除、receipt commit 后存储失败、回滚恢复、无旧声明；并非真实掉电结果。
- staging：真实 Core CMake 的独占 stage 目录刷新、main/check_resources.py、test_resource_staging 与 test_patched_firmware_stage；没有发现需要新建资源管理器的缺口。

## 新发现与红绿回归

命令：`python3 -m unittest discover -s firmware/test/host -p 'test_core_stop_requests.py'`。

修复前准确应用现有 001–025 补丁后的实际 stop/enqueue/has_message_dialog_request 方法编译通过，执行失败：`stop retained old system dialog handlers`。active、queued system 请求在正常 stop 后仍存在，旧 handler 捕获的 Owner 也仍被保留；原 stop 只调用产品 on_stop 和 startup drain，deinit 才清空这些请求。

新增 026-revoke-input-requests-on-system-stop.patch 在原 stop 的 App Owner drain lambda 内清除 keyboard、Dialog map、queued 与 active identity；不调用已停止 Owner 的 handler，不重置请求 ID，不改变业务提交／取消语义。调度失败记录错误并保留 Core 内 stop_cleanup_failed 故障事实；start 与旧输入结果 fail closed，deinit 清理后才复位。void stop 不提供新的全量成功返回契约。测试三轮请求／停止与下一次成功启动的请求身份；同步 scheduler 不证明 rejection 后已释放或真实 GUI callback 已 drain；在拒绝分支明确保留请求但阻止直接重启和迟到结果，等待显式 deinit。

修复后同命令通过。初次测试夹具缺 MessageDialogRequestRecord 类型别名，先修正夹具使生产方法正常编译，再取得上述运行期红灯；不把编译错误当故障复现。

补丁按 ADR-0016 维护：原始组件完整 inventory 不变，精确追加补丁、hash、patched lifecycle hash、019/02 issue 和上游等价行为移除条件。无临时生产日志，无新平台管理器。

## 验证状态

最终统一检查通过：232 项测试中 230 通过、2 skip；新隔离完整构建、不可变输入与归档校验通过。未访问设备，声音、回音、打断、触摸、最终配色与完整重复生命周期均未新增真机证据。

调度拒绝的附加红灯：仅清空成功路径后，注入 App task rejection，实际 start 仍成功，违反不得携旧请求直接重启的断言。加入故障门槛后重启拒绝、旧 Dialog result/validity 拒绝；完整实际 deinit harness 验证故障标记复位。

同一拒绝分支扩展到实际 complete_app_keyboard / hide_app_keyboard：先复现旧键盘结果仍可交付 handler，再补相同故障门槛。故障标记使用 atomic_bool，避免外部 stop 与 Owner／同步 Service validity 读取竞争。未改变请求 map 的原 Owner 调度。

## 构建与检查收敛过程

初版清理成功路径后开始构建，在补充调度拒绝及键盘迟到结果回归时发现剩余缺口；旧 `/private/tmp/espocket-027-candidate` 和 `candidate-v2` 构建主动终止，目录／日志保留，未发布可验收候选。最终使用新目录 `candidate-v3`，不修改旧输入证明或冒用中间构建。

此前统一检查暴露测试 fixture 未声明新增私有故障字段；已同步 fixture 依赖声明并保留原断言，不能把 fixture 编译错误当作故障红灯。最终统一检查与完整构建以 v3 日志为准。

[最终候选与精确 identity](2026-10-09-unified-candidate.md)。本记录与候选票引用原物理条件，不新增同义验收票。
