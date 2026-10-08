# 2026-10-08 — Owner 整改离线结果

## 实现

- Chat 0.1.3 的普通界面颜色改为已注册语义主题 token；静态资源和实际 JS refresh 均留在 Runtime App 包内。动态颜色由真实 GUI Runtime 解析，不在平台写 Chat 配色。
- GUI LVGL 008 补丁持有 decoder/cache hook、容量预检、超预算绕过与 PSRAM 压力淘汰；System 只调用公开的预算与统计接口。release 保留后来替换 callback 的 Owner。
- Core 024 严格解析可选 bool `package.keep_screen_on`，默认 false，保留既有 package trust gate。System 仅对前台 Running 实例应用声明，不再特判 Chat ID。
- Core 025 将启动进度放入原 AppRecord，由原 App Owner tick 推进；GUI future 等待非阻塞。重复同实例请求幂等；第二实例拒绝不覆盖 Loading/source；取消与失败经原 stop/failure hooks 回滚。GUI 清理失败保留记录供下一节拍重试，stop/deinit 先 drain 后销毁。
- Card 目标保留到启动完成；实体 Reset 恢复走同一启动入口。PWR 取消未完成启动，同时停止原可见前台 App，防止返回 Home 后旧 App 继续运行。

## 验证

- `python3 scripts/check.py` 的所有 firmware 测试通过：9 个组件/App 目录共 50 tests，host 目录 167 tests，合计 217，2 skipped。完整日志 `/private/tmp/owner-remediation-final-check.log`。
- 该统一命令最初因架构文档引用工作票而非零退出；固件测试无失败。按文档权威位置规则移除架构中的工作票与状态描述后，独立重跑 `python3 scripts/docs/check.py --markdown` 通过（312 文件）。无需重复已通过的固件测试。
- 回归执行真实 GUI policy、Core 请求／推进实现、实际 package admission、实际 System launch/PWR/timeout 方法与 Chat JS refresh；覆盖两主题、拒绝/幂等、延迟 GUI、取消后不得提交 Running、启动各阶段失败、回滚重试与 stop 失败状态。
- 首次构建暴露 GUI 新实现缺少显式 `esp_timer` 依赖，已在 GUI 008 的 ESP CMake 补齐 `esp_timer heap`；首次 host 检查暴露两个 lifecycle harness 缺少任务组常量，已同步真实接口。
- ESP-IDF 6.0.1 隔离完整产品构建通过；最后 PWR 修改的增量编译及链接也通过。最终日志 `/private/tmp/owner-remediation-last-build.log`。App 为 11,225,424 bytes，应用分区剩余 24%。
- Core 与 GUI 的隔离 patched inventory 精确匹配维护 manifest；原 `firmware/managed_components` 对应 source inventory 完全未改。实际编译的产品源码与 checkout 匹配；隔离构建生成自己的 `gen_bmgr_codes`，使用本地依赖 overrides。
- Chat BPK 使用官方 packager 0.1.7 生成，31 个成员逐个与源码匹配；unsigned developer 候选，未安装。
- `git diff --check` 通过。

## 候选 identity

本地产物：`/private/tmp/espocket-owner-remediation-release/`。保存 App、ELF、sdkconfig、隔离 lock/main dependency overrides、两组件 manifest、Chat BPK，以及 source-inputs/release JSON。

| Artifact | SHA-256 |
|---|---|
| espocket.bin | `5625d4fe2456cd014e8689919d3543c160cf9a632ddaaef7a2da9c7416cd58b6` |
| espocket.elf | `d71747c6c0525fb1805ab2713e1c783562dd1e73771cc4c28726ecfd5f516cd8` |
| Chat 0.1.3 BPK | `2552362ef1f40c7edd4927c518ecefaf31bb0c9e9db32e2421ad5f46cb882705` |

此次配置 AEC 关闭、render profile 开启。不能将此次构建当作 AEC 或唤醒词真机证据。

## 开放条件

GUI future 等待已释放 App Owner，但每阶段内的同步包准入、Runtime load/start、Native/Runtime lifecycle callback 仍不能抢占，GUI parse 仍持 GUI 锁。长阶段耗时治理与启动期间顶部下拉／PWR 250ms 响应要求保持开放，不因分阶段关闭。

未接设备、未部署、未声学测试，视觉、内存压力、真实触摸、电源与取消路径需设备验收。未提交或 push 此批修改，既有 Quick Settings／Loading 未提交内容保留。
