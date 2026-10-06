# 019 生命周期隔离候选 — 2026-10-04

本记录对应 [01](../issues/01-close-initialization-cleanup-gaps.md)、[02](../issues/02-complete-stop-and-normal-restart.md)、[05](../issues/05-fallback-unavailable-saved-theme.md)。结果属于隔离源码候选，不表示原 checkout 已合入或设备已验收。原 checkout 与 Store 设备均未修改。

## 输入与隔离

输入为当天有未提交、已暂存和未跟踪改动的工作树，不能称为 Git HEAD。baseline 与 working 位于 `/private/tmp/espocket-019-lifecycle-7dgk8h2g/`；排除 `.git`、build、dist、node_modules、managed_components、gen_bmgr_codes、虚拟环境和 Python cache。锁定依赖只复制到 working；Core 原始完整 inventory 验证后，在额外的 core-baseline/core-working 副本应用当前 001–005 补丁，再生成 006 顺序补丁。

独立产品构建为 `/private/tmp/espocket-019-lifecycle-7dgk8h2g-build-3/`。源码快照不含原生成板目录，在此构建工程以同版本 Board Manager 重新生成 Waveshare 1.75C 配置。Component Manager 使用专用 `/private/tmp/espocket-019-lifecycle-7dgk8h2g/component-cache`；原 managed_components、SDK 配置与 registry lock 未写入。

## 实施内容

- Display 自有失败 guard 在 binding 获得后覆盖 outputs、解析、touch、背光、source.start 和 SetActiveSourceRole；只停止成功取得的 source，成功路径移交寿命给 System。
- Native Circular Shell 的 on_start 自有 guard 释放 Display binding/gesture/timer 与启动状态；Core 不调用失败 on_start 的正常 on_stop，因此不能依赖正常退出清理。
- Core 006 补丁区分 initializing 与 initialized，所有 init 错误自动 deinit；只移除本次成功注册的三项 Core Service；进入产品 on_init 后才匹配产品 on_deinit。正常 start 失败也执行产品 on_stop 与 Core deinit。
- Core GUI cleanup post 被拒绝时，stop_app 返回错误并保留业务与清理错误，不能报告 Stopped。deinit 的最终 GUI cleanup post 失败时先停止/join scheduler，再保留 backend guard 执行 GUI teardown；不在 workers 尚使用 guard 时 reset。
- System 析构在派生成员销毁前调用 Core deinit，随后释放可能专为关键失败画面保留的 Display source。
- app_main 在 init/start 返回失败后调用 System 的静态错误画面入口；显示可用时仅保留诊断 source/binding 并显示英文显式重启提示，source/GUI lock/分配失败保留日志并释放新取得资源。该入口不恢复 Core、Shell 或 App，不包含 Overlay/Loading。关键失败 latch 阻止 System init 原地重试。
- System stop 先撤销测试/Runtime/Card/PWR 执行入口，再停止全部 Running/Paused/Error 受管 App，Shell 最后停止；一个 App 的 stop 失败不跳过其他 App。deinit 释放旧 test Adapter、DeveloperMode、Launcher admission 和快照队列。Core 清除旧请求、pending timers/bindings、active App 与 preference restore 状态，identity 分配器不重置。
- 保存主题 unknown 或非默认 apply 失败时，本次 set_theme dark；完整尝试期间维持 Core preference restore suppression，成功才 mark restored。保存值保留，Dark apply 失败为关键错误。本票不交付运行时主题切换。

## 回归与验证范围

新增 host tests 执行产品或准确应用补丁后的实际 C++ 方法/分支，依赖 stub 只持有资源、失败点与结果。源码不复制到测试中的替代实现。实际 ESP-IDF ABI 与依赖另由完整构建核对。

- Display：八个 acquisition/activation 失败点与正常路径；baseline 在 binding 未释放的断言上失败，候选通过。
- Native Shell：主题、11 个 action 注册、gesture 与 Home timer 共 14 个失败点；baseline 残留状态/binding，候选通过。
- Core：完整 init/deinit 方法的 16 个获取失败点、重复 deinit、最终 GUI cleanup post rejection；原 registry 方法失败，全部顺序补丁候选通过。fake scheduler 证明回收和 rejection 分支，不证明真实线程竞争或 backend lock 成功。
- Core stop GUI 结果：business on_stop 与 GUI post rejection 的四种组合；原方法把 cleanup-only failure 报成成功，候选均传播正确错误。
- System stop：Native/Runtime/后台/Paused/Error 与 Installed/Stopped 混合清单，Shell 最后停止；失败后继续其他 Owner，先撤销外部入口；baseline 失败，候选通过。此用例不是三轮真实 stop→start/deinit→init 验收。
- Fatal diagnostic：新建/已有 Display source、source 不可用、1000 ms GUI lock 失败、screen/label 分配失败；仅成功画面持有诊断资源，锁失败不从持锁区 stop source。
- Theme：unknown、Light apply failure、Dark failure、正常 Light/default、同保存值再次恢复，以及原保存值不改写。

最终统一 `scripts/check.py` 通过，共 117 个 host tests；此后扩展 Core harness 纳入真实 start/stop 方法的三轮正常循环，单独回归通过。Markdown 检查通过（256 文件）。三轮 Core harness 使用 fake scheduler/backend，不是完整产品或设备三轮结果。

独立 ESP-IDF 6.0.1 / ESP32-S3 / Waveshare 1.75C 完整构建通过，最终日志 `/private/tmp/espocket-019-lifecycle-7dgk8h2g/build-3-board-corrected.log`。七组 production patch override 路径、构建前后 registry lock、Audio 配置与字形检查通过。最终 ELF 链接使用 CPU 持续推进约四分钟后完成，没有取消、改变优化项或跳过链接。

| 构建输入/产物 | SHA-256 |
|---|---|
| espocket.bin（7725232 bytes） | `62bbfa7e97e571cf6ca31db974fdcfb5889079292e9af8c912444780db1d5662` |
| espocket.elf | `1dd255860c101e871574a462e760f768b3b4189b67781d3fab7e2a40817a32c6` |
| 独立最终 sdkconfig | `7ca02f6ff7998285f0aa1a324923bb52b937338a1c3c7fcaff62c4a20bb91608` |
| 独立最终 dependencies.lock | `0d6467d0e010e7f1f323faecd25ad22050868fae93b74c49929fa4a6f75dbc40` |

初次构建的沙箱 psutil 进程查询失败后，独立构建获自动审查允许；后续共享组件 cache 冲突以专用 cache 解决。板配置生成会移走不匹配的 sdkconfig，重新生成后按准确 board_manager.defaults 合并板相关配置，并重新应用生产 Audio 约束；修改前配置保留为独立构建根下 `sdkconfig-before-board-correction`。上述失败日志均保留，不宣称最初未配置工程构建通过。源码配置不回写。初次 host check 发现快照中既有 Card replacement 测试 stub 缺 launcher_generation_；候选只补该测试字段与 atomic include，没有改 Store 源码。原 checkout 的 Store 线已独立出现同义 fixture 修正，集成时已有者不重复应用。

统一检查需要 Git tracked-file inventory。隔离副本没有 Git；执行时显式设置 GIT_DIR 指向原仓库只读对象库、GIT_WORK_TREE 指向 working、GIT_INDEX_FILE 指向 `/private/tmp/.../validation-index` 的 index 副本。没有 git init/add/commit/reset/clean，也不以 copied index 表示源码是已提交 HEAD。Markdown 旧链接指向 gen_bmgr_codes，working 只建空目录满足链接检查，生成内容只在构建工程。

## 尚未完成的条件

01、02、05 不关闭：候选未整合，设备归 Store，未打开串口、刷写、重启或改变 NVS。

- 01：还需真实 callback 在途停止、GUI 锁/等待竞争、关键失败画面/日志与显式重启证据；host rejection 测试不覆盖 LVGL/backend 实际锁失败。Core 的公开 deinit/stop 是 void，没有产品全量 stop 聚合返回值。
- 02：当前为 01 候选基础上的独立准备工作。Core stop 尚未专门撤销 System-owned pending dialog 队列（App-owned 请求沿实际 App stop 清理），不能把清除 deinit 队列等同 stop 全部请求已失效；与 Overlay 线整合时仍需在 Core Owner 内处理，并覆盖迟到 handler。需验证 Native/Runtime/后台 App、pending keyboard/dialog 和迟到 callback 的真实生命周期，连续三轮 stop→start 和三轮 deinit→init 资源/identity 记录。调用 Core deinit 的线程必须是 scheduler 外部 Owner；从 Core worker teardown 自身会触及 scheduler self-join，当前候选没有承诺这种调用上下文。
- 05：需默认回退视觉与重启后保存偏好、用户明确选择可用主题后的实际存储结果；017 配色与 019/10 即时主题均不重开。

GUI cleanup 错误不代表资源已全数释放；Core 在 App teardown GUI post 被拒绝时保留 Error，最终 deinit fallback 的真实 callback/GUI 竞争还需专项验证。不将失败后原地重试当成正常重复运行。

## 集成注意事项

按 baseline patch 审查，不覆盖整个源树。公共 System 增加 report_startup_failure，stop_display 为私有；Core 006 只增加 Impl 状态和修改内部生命周期，没有更改 Core public virtual signatures。

共同文件为 system.cpp/system.hpp/system_display.cpp/CMakeLists、circular_shell.cpp、Core manifest 与 manager/lifecycle 的顺序补丁。Overlay/Loading 线应保留本线 Native start guard，与自己的 on_stop/GUI userdata 安全修改合并；不要用本线 on_start guard 替换该线的 Overlay teardown。本线没有触及 Overlay 仲裁或 App loading hook。

Core 006 必须位于当前 005 后。Store 若重写 005 的行数或上下文，需在新 001–005 结果上重生 006 并刷新 SHA-256，不能模糊应用；原 source_files inventory 保持 registry 身份。Runtime failed-stop latch 不因正常生命周期清理解除，保留 005/07 异常后需显式重启的隔离规则。

补丁依据 [ADR-0016](../../../docs/adr/0016-maintained-upstream-fixes.md)，上游未提交；等价 partial init rollback、GUI failure propagation、callback/join 和资源回归通过后移除 006。现有 manifest 的原上游报告保留，本记录补充此次问题与回归，不混入 Store trust/签名证明。
