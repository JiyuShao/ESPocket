# 2026-10-08 — Core 启动操作共享与错误提示一致性

## 问题与范围

当前差异审查发现：分阶段启动和公开同步 start_app 虽共用 AppRecord，却各自维护准入、Runtime 启动、生命周期、Running 提交与清理操作；相同 developer_mode_required 错误的提示已经不同。用户批准仅收敛这个维护风险，不继续扩展异步 service binding、GUI parse 或 Runtime prepare。

## 实现

锁定 Core 025 内两种调度方式共用私有 admit_app_start、start_app_runtime、call_app_start、commit_app_start、release_app_start_runtime、rollback_app_start_gui 与失败报告。操作集中在原 manager.cpp；分阶段推进仍持有原 AppRecord pending phase。

失败分类使用私有枚举 Admission／Lifecycle，分阶段保留失败种类直到 rollback 完成。准入失败共用原 admission dialog，developer_mode_required 恢复原提示：Enable Developer Mode to run this app. Installed content is retained. 生命周期失败继续使用原 lifecycle dialog。

公开同步 API 的参数、launch transition、同步等待及已有状态／stop 行为保持；分阶段 API 保留非阻塞 future、取消后回滚、GUI 清理失败重试和 drain。这里共享真实操作，不把同步 API 强行包进另一个阻塞等待循环，也不新增 App manager。服务绑定与 GUI／Runtime 单阶段阻塞保持开放。

## 红灯与回归

命令：`python3 -B -m unittest discover -s firmware/test/host -p test_phased_app_start.py`。

扩展既有 Core harness，同一编译单元执行真实同步 start_app、真实 phase progression、真实共享操作及失败报告，外围 Runtime／Service／GUI 使用 stand-in。修复前同一个 developer_mode_required 在两条入口产生不同 dialog kind/detail，断言失败；修复后绿灯。

覆盖 developer-mode 提示、一般包准入、服务要求、Runtime load/start、lifecycle 失败提示和各一次回调；比较 Native／Runtime 正常启动状态与 active identity。原有慢 GUI future、取消、清理失败重试、stop 失败与 drain 连续场景继续运行；新增启动和 stop 同时失败时，last_error 保留 stop 错误、对话框保留原启动错误的断言。此夹具不验证真实对话框绘制或设备响应时间。

独立差异复查确认原 P2 已解决；保留的同步兼容行为与分阶段取消编排差异合理，未发现需要进一步合并的重复实际操作。

## 验收边界

未连接设备、未部署、未提交或推送。未改变 Chat 0.1.5 包；没有修改原始 managed_components。250ms、物理 PWR／QS 与原语音卡顿原因仍未验收。

## 最终验证与产物

- `python3 scripts/check.py`：执行 220 项主机测试，218 项通过、2 项跳过；Lifecycle parser self-test 通过。
- `python3 scripts/docs/check.py --markdown`：320 个 Markdown 文件通过。
- `git diff --check`：通过。
- 隔离完整固件构建通过，最终 manager 重新编译并链接，Core profile 开启的分支通过真实编译。
- Core 原始源码与 source_files 匹配；最终隔离源码与 patched_files 匹配。81 个产品输入和完整 Chat 源码匹配工作区，既有 Chat 0.1.5 BPK 仍逐成员匹配源码。

本轮仅改变 Core 的 manager.cpp、start_progress.cpp 与私有 impl.hpp 三个实现文件，在维护补丁 025 中保存；另更新 manifest、主机回归和文档。

保存于 `/private/tmp/espocket-core-start-sharing-release/`，含 App、ELF、LittleFS 镜像、sdkconfig、lock、依赖 overrides、Core manifest、既有 Chat BPK 和 source-inputs/release JSON。此前候选保留。Core profile 与 render profile 开启，软件 AEC 关闭。

| 产物 | 字节数 | SHA-256 |
|---|---:|---|

| espocket.bin | 11,235,296 | `b7c618965a33cdaca5ead6eecad033f46fafdcd4e8c3115bddc5757a78529578` |
| littlefs_data.bin | 18,481,152 | `9ee6b5954222ddc9dacb46f65559b0d8ab0e5feb557d8494f678523145675a2d` |
| espocket.app.ai_chatbot.debug.0.1.5.bpk | 87,391 | `722cd405736b1367b3844c0ed41c5d4919a92f0af40a46da365b3f508fa45eb0` |
