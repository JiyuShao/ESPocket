# 2026-10-03 — 自主续跑结果与晨间 frontier

## 已完成的可执行工作

- 用户确认 Runtime 栈配置补丁的限定例外，记录 ADR-0015；版本化三文件小补丁、完整源码/补丁 hash 校验、独立工程 override 构建、精确传递依赖约束及 drift 拒绝、CI 与操作说明完成。
- 三个配置完整构建：普通、Native-only reclaim/resource、Runtime-only reclaim/resource。原始 managed_components 与 registry lock 未改动，没有 push。
- 普通真实 Runtime 最小 7 步和完整 Native/Runtime 57 步 PASS；两个独立回收套件各 17 步 PASS，未选中模型保留 Detail，选中模型重启 Root 并清除旧确认状态。
- 有限资源路径两次各 45 步 PASS；有效 heap checkpoint 无持续下降，largest block 不变；16 KiB 异步栈剩余最小 7400 bytes。日志缺项仍存在，quiet window 改善采集但未证明根因；不补造采样或声称长期稳定。
- 63 项 host unittest、M2 parser 通过；Markdown 与空白检查通过。失败、镜像 hash 和独立 attempt 均见[详细验证](2026-10-03-runtime-stack-patch-validation.md)。

## 当前设备

已恢复普通 `c8d56e5e2`，应用分区写入校验通过，LittleFS/NVS 未写。最终只读快照为表盘亮屏、App/Page 空、Back pending/inputBusy false，release=ok。普通保存配置 Card fixture、所有 reclaim 和 resource trace 均关闭。没有遗留串口采集或刺激序列。

诊断产物保留 `/private/tmp/espocket-runtime-native-reclaim-preserved` 与 `/private/tmp/espocket-runtime-runtime-reclaim-preserved`；普通产物保留 `/private/tmp/espocket-runtime-patched-normal-preserved`。原始日志/报告均是临时产物，关键判定已进入版本化记录。

## 晨间最小介入

休息期间不重复发送操作问题，不重做已接受的 Native 常规导航、013 smoke、亮度/Wi-Fi 或十轮人工资源测试。按现有 ticket，只集中完成缺失路径各一次：

1. 普通镜像的 Runtime 视觉与物理路径：Root 没有 Back；进入 Detail，普通横滑不返回；点 Confirm Back，看到 On；Edge Back 后看到 pending 提示，Cancel 留在 Detail；等待一次自动息屏，PWR 恢复 Detail；允许 Back 回 Root，PWR Home 回表盘。可在这次集中路径检查确认反馈，没有重启/黑屏。
2. Native-only 镜像一次：Native Detail 自动息屏后 PWR 回表盘，重开 Native 从 Root；另一模型保留页面已自动验证。助手负责切换镜像和采集，不要求用户自己烧录。
3. Runtime-only 镜像一次：Runtime Detail 自动息屏后 PWR 回表盘，重开 Runtime 从 Root；完成后助手恢复普通镜像。

当前自动结果不能证明显示文字、触摸硬件或 GPIO，故 008/03、008/04 保持 ready-for-human，不冒充完成。确认后按真实依赖进入 009/01。

## 其余未完成 issues 的依赖审计

| 工作票 | 当前真实依赖 | 后续动作 |
|---|---|---|
| 004/03 | 官方 Settings Storage/Developer 页的物理显示与真实控制效果 | 另一次集中观察；Quick Settings Developer Mode On 不替代官方 Debug 页验收 |
| 004/04 | 官方 playback-only HAL/Audio seam，且不能启用 Recorder | 等受支持的能力/版本；本次 Runtime 例外不授权 Audio 补丁 |
| 005/03、08 | Core 的完整信任事务、兼容签名包与受支持发布路径 | 上游或外部候选，不创建第二个 Installer，不冒充其他 System |
| 005/04、05 | 005/03 可信安装、替换、重启 discovery 事务 | 保留源码 projection；真实 package lifecycle 等前置 |
| 005/06 | 官方 HTTP/Store cancellation 同步修复 | 不重跑已知不安全的 Refresh/TLS 崩溃 |
| 005/07 | Core owner-scoped keyboard result / failed-stop cleanup | 保留 keyboard containment，不能用产品层绕过框架隔离缺口 |
| 011/01 | Launcher 滚动、阈值反馈、画面等视觉/触摸观察 | 一次样机观察；不将系统合成导航 PASS 当成手感通过 |
| 014/03、05 | 005/03 的实际 replacement/迁移事务 | Card 样例已接受，剩余事务不能用内存 fixture 代替 |
| 009/01–08 | 008/03 验收是 Spec 明确的产品实施顺序；后续还有授权、声音、provider 等依赖 | 不绕过依赖提前实施第二套 AI framework；前置解除后按 ticket 顺序推进 |

013、012、015、016 及 007 已 resolved，不重复检查或重新制造工作。当前没有满足真实前置、能独立关闭的其他源码 ticket；剩余人工与外部条件集中留在此清单。

## 本轮上游读取边界

打开的官方版本页支持当前已锁定的 [Core 0.8.4](https://components.espressif.com/components/espressif/brookesia_system_core/versions/0.8.4/readme?language=en)、[HAL Adaptor 0.8.4](https://components.espressif.com/components/espressif/brookesia_hal_adaptor/versions/0.8.4/readme?language=en) 与 [Audio 0.8.2](https://components.espressif.com/components/espressif/brookesia_service_audio/versions/0.8.2/readme)。Store 页面读取失败，HAL 根入口还返回过旧缓存 0.7.4；不能据此降级、声称穷尽所有修复或断言 master 没有修复。本轮未获得可直接采用、覆盖上述事务/隔离门槛的新修复证据，保留锁定版本。
