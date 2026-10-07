# Application Ecosystem

Sequence: 005

Status: retrospective-active
Blocked by: [003/02 Runtime lifecycle 与共存](../003-m3-runtime-app/issues/02-prove-runtime-lifecycle-coexistence.md)（已完成）；上游及分发依赖见各 ticket。
Historical basis: 2026-09-29 根据已接受 Store 工作、真机失败和未解决 distribution gate 重建。

## Problem Statement

ESPocket 需要官方 Store 与远程 Runtime distribution path，但锁定的上游栈尚未提供稳定 cancellation、统一 package trust boundary、兼容 signed package 或可信 dynamic Launcher source。

## Solution

保留官方 Store 与 Service；当前在线路径不稳定时 fail closed；要求 Core 持有 trust gate；只有安全与稳定性 gate 通过后，Launcher 才投影 Core committed state。

## User Stories

1. 作为用户，我希望 Store browse 与 refresh 不导致设备崩溃或重启。
2. 作为用户，我希望下载的 App 在可执行前完成验证。
3. 作为 maintainer，我希望 Core 持有唯一 installation truth。
4. 作为 Launcher，我希望只显示可信且已提交的 App。
5. 作为 Runtime App 用户，我希望 keyboard 与 Service result 隔离到对应 owner App。
6. 作为 release owner，我希望获得可审计 signed package 与兼容 publication path。

## Implementation Decisions

- 使用官方 Store、HTTP、Storage、Runtime 与 System Core path。
- 1/1 cancellation failure 完成 symbolization 后，online Store 保持 blocked。
- 在 Core 公开 install boundary 执行 Runtime trust contract。
- Dynamic Launcher projection 使用完整 Core snapshot。
- 所有前置 gate 通过前，dynamic installation 与 exposure 保持禁用。

## Testing Decisions

- 分别保留 offline、cached 与 online Store 结果。
- 不为增加一次样本而重复已知不安全 crash。
- 进入 package lifecycle 前，先使用 non-download Refresh 重新验证官方 HTTP fix。
- 端到端测试 verification、transaction rollback、reboot discovery、update、uninstall 与 Launcher reconciliation。
- 上游源码事实与产品 acceptance 分开记录。

## Out of Scope

私有 Store backend、私有 downloader、私有 package format、产品自有 Installer，以及把 debug 或 build-staged package 当作 remote release 信任。

## Tickets

- [01 — 集成官方 Store](issues/01-integrate-official-store.md)
- [02 — 诊断 online Store failure](issues/02-diagnose-online-store-failure.md)
- [03 — 执行 Core 持有的 package trust gate](issues/03-enforce-core-package-trust.md)
- [04 — 从 Core 投影 dynamic Launcher entry](issues/04-project-dynamic-launcher-from-core.md)
- [05 — 验证 remote package lifecycle](issues/05-validate-package-lifecycle.md)
- [06 — 采用并复验在线 Store 修复](issues/06-adopt-online-store-stability-fix.md)
- [07 — 隔离 Runtime keyboard result](issues/07-isolate-runtime-keyboard-results.md)
- [08 — 取得兼容签名包与发布路径](issues/08-publish-compatible-signed-package.md)
- [09 — 开发者模式包准入与 Super 兼容运行](issues/09-allow-unsigned-developer-installation.md)
- [10 — 降低 Runtime 启动阻塞并准确测量](issues/10-reduce-runtime-startup-blocking.md)
- [11 — Runtime 图标、Weather、Store 安装与手势误点击](issues/11-runtime-store-gesture-regressions.md)
- [12 — 存储、圆屏适配与 Runtime 可用性](issues/12-storage-round-display-and-runtime-usability.md)

## Further Notes

长期规则见 [Runtime package trust](../../docs/design/product/05-runtime-package-trust.md)与 [App discovery](../../docs/design/product/06-application-discovery.md)。

## 已接受结果

| Gate | Result |
|---|---|
| Official Store integration | Store 0.8.2、HTTP 0.8.2、TLS policy、resources 和 clean build 通过 |
| Offline lifecycle | clean image Store startup/Home 与 cached 1/1 containment lifecycle 通过 |
| Network transfer | 远程 index 和部分 metadata 曾成功写入 cache |
| Containment image | 1 worker / 1 request app-only write、hash、90-second boot、Wi-Fi 与 SNTP 通过 |
| Static analysis | 包信任、catalog compatibility 与 Runtime keyboard isolation 缺口已经识别 |

## 剩余工作与完成条件

在线稳定性由 [06](issues/06-adopt-online-store-stability-fix.md) 关闭；包信任由 [03](issues/03-enforce-core-package-trust.md) 关闭；Runtime isolation 由 [07](issues/07-isolate-runtime-keyboard-results.md) 关闭；兼容签名包与发布路径由 [08](issues/08-publish-compatible-signed-package.md) 关闭。前置条件成立后，再完成 [04 动态 Launcher](issues/04-project-dynamic-launcher-from-core.md) 和 [05 包生命周期](issues/05-validate-package-lifecycle.md)。这些未完成项仍是当前产品范围内的发布条件。

## 记录

- [2026-09-28-acceptance-report](records/2026-09-28-acceptance-report.md)
- [2026-10-04 Package review follow-up](records/2026-10-04-package-review-followup.md)
- [2026-10-04 Package final build](records/2026-10-04-package-final-build.md)

## 当前功能优先级

2026-10-04 用户明确 Store 不能稳定请求或安装，先推进 06 的实际 HTTP／Store 调度回归，再解除 08、03 的兼容包和统一信任事务前置。页面打开、缓存列表和 Home 正常不构成 Store 可用；[当前诊断](records/2026-10-04-store-availability.md)记录普通设备的容量拒绝与包不兼容。07 键盘隔离已通过独立门槛，不再作为尚未完成的隔离项。

## 开发者安装策略修订

2026-10-04 用户选择仅开发者模式允许未签名安装，见 [09](issues/09-allow-unsigned-developer-installation.md) 与 [ADR-0018](../../docs/adr/0018-developer-mode-allows-unsigned-packages.md)。08 仍持有正式签名发行包和发布路线；开发路径不再以取得正式发行签名作为前置，但仍依赖 03 的统一 Core 事务和实际兼容性。用户后续确认开发者模式允许所有声明 super 的包进入正常校验，外部旧包暂不要求导航契约；关闭模式保留安装、禁止启动并停止运行中的例外 App。安装提示与实施范围由 09 和 ADR-0018 持有。2026-10-04 已完成代码与 host matrix；完整构建因磁盘空间不足失败，尚未刷入或进行设备验收，详见 [实施证据](records/2026-10-04-package-implementation-evidence.md)。

## 实施范围与验收

当前检查点：已完成真实 Store 安装／卸载、动态 Launcher、例外包模式切换与隔离测试签名矩阵的可执行部分，历史结果与未通过项见[生命周期记录](records/2026-10-04-launcher-and-lifecycle-acceptance.md)。持久验证在 2698534d2 完成首次迁移与受控重启复用，Hello Runtime 打开约 0.9–1.0 秒、Flappy admission 约 6 ms。后续原包优化修复声明预加载资源被切帧释放、source 异步任务积累和隐藏 Shell 查询；逐行截图避免连续整帧分配。512 KiB 缓存／GUI／Core 联合候选 fb7055e85 的性能、70 秒前台压力、五图和完整 Apps 回归通过，独立滚动样本约 25–33 FPS，预热后 PNG 解码为 0。已纳入默认构建，最终 canonical 输入复核通过且 ELF／BIN 与已验收 fb7055e85 完全相同；不承诺持续稳定 30 FPS。原 Store 1.5 秒退出与活动取消门槛仍未通过；正式发布身份、目录和 Catalog 权限尚缺，物理掉电仍未验。详见[分阶段优化记录](records/2026-10-05-runtime-optimization.md)与 03／04／06／08／09／10 的未完成条件。

硬件／软件隔离诊断已完成：同机原生小范围刷新 48–49 FPS、全屏 15 FPS；原包主要可见成本为 PNG 解码／绘制与负载下的锁等待、调度，未发现要求换硬件的故障证据，但当前全屏显示实现也有性能约束。该阶段诊断不等于可玩性修复；临时 overlay 已清理，当时恢复 a2df08485，后续普通优化镜像见上面的当前检查点，原包保持不改。详见[诊断记录](records/2026-10-05-runtime-bottleneck-diagnosis.md)，后续验收仍由 10 持有。

- 授权范围：先执行 [03](issues/03-enforce-core-package-trust.md) 的统一 Core gate、receipt、事务与恢复基础，再完成 [09](issues/09-allow-unsigned-developer-installation.md) 的开发准入与实际 Store 安装。03 的正式发行签名证据依赖 08，不虚报完成；后续用户已明确授权全部剩余工作，范围扩至 04/05/06/08/09；正式发行仍需真实发布者密钥和发布路线，测试签名不替代。
- 读取入口：本 Spec、03/09、ADR-0004、ADR-0016、ADR-0018、product/05-runtime-package-trust、product/07-developer-mode、development/app-navigation 与 [实现交接记录](records/2026-10-04-package-implementation-handoff.md)。
- 修改范围：ESPocket 产品 policy 接入、Core/Store 版本锁定补丁及 manifest、对应 host/device tests、相关接口文档与本 Effort 状态/证据。禁止修改 managed_components；保留其他聊天的暂存与未提交改动，不自动 push。
- 验证：最终完整 scripts/check.py 与 Markdown 检查；精确补丁输入、registry lock、Audio config 核对及完整固件构建；app-only 刷机前备份当前设备镜像与 LittleFS，实际 Store 取消/安装、启动、PWR 退出、重启发现、更新失败回滚、开发模式关闭/重新开启。已有有效证据不重复，视觉或物理门槛最多集中请求一次。
- 停止条件：09 全部验收通过，03 可执行基础完成且发行阻塞明确保留；或剩余工作确实需要人工/新设计/外部条件。设备未验证不得勾选通过。既定设计内修复持续执行，涉及契约或范围变化时同步修订设计与验收定义。

当前 [11 Runtime/Store 回归](issues/11-runtime-store-gesture-regressions.md)已完成图标、手势误点击、原 Weather 内存和字体、下载进度、私有初始文件及包写入超时修复；原 Music Store 安装／重启发现、原 Weather 联网／重开／Home、导航与 Native/Runtime 设备回归通过。普通活动下载取消及重试通过，带同步截图的 1 秒合成指令过期单独保留为失败证据。缺少 Service 的官方包继续准确拒绝，正式发行和其它票的性能／物理门槛保持开放。详细证据见[回归记录](records/2026-10-06-runtime-store-gestures.md)。

## 全部剩余工作授权

2026-10-07 用户明确要求完整修复小智语音，由 [15](issues/15-enable-xiaozhi-voice-conversation.md) 持有正式录音、编码、上传／回复及退出验收；此前 14 的临时硬件验证仅为已完成前置，不代表目标已经完成。

2026-10-07 新增 [14](issues/14-verify-official-microphone-capability.md)：用户要求验证官方音频能力与实际麦克风。官方实现和双麦克风三轮受控短音采样已验证，现有产品镜像已恢复。服务器现在认可设备激活，实际会话仍失败在录音关闭导致的 AudioEncoder0 缺失；未启用正式产品录音或宣称完整小智对话可用。来源、测量与恢复结果见[记录](records/2026-10-07-official-microphone-verification.md)。

2026-10-06 新增 [13](issues/13-xiaozhi-and-launcher-performance.md)：实际选择并验证小智，修复阻碍配置的显示入口，对照 Launcher 绘制并落实有效方案。沿用数据保护和完成后本地合并／清理授权。

2026-10-07：[13](issues/13-xiaozhi-and-launcher-performance.md) 完成并合并本地 main，任务 worktree 已清理。最终普通镜像 `0203fb1fc` 的小智激活码、播报中 Home、八 App 联合与导航回归通过；Launcher 改为四行 Release 翻页，warm 累计 draw 降低 55.25%。完整语音仍需要账号绑定和真实录音支持；未把激活等待当作云端对话通过。详见[验收记录](records/2026-10-07-xiaozhi-launcher.md)。

2026-10-06 用户进一步授权全部存储／缓存策略修复、Launcher／Weather 卡顿优化、系统侧矩形 Runtime 的圆屏兼容，以及安装除 Camera 外的 Store App；由 [12](issues/12-storage-round-display-and-runtime-usability.md) 持有具体验收。保留原包与用户数据，验证完成后合并本地 main 并清理任务 worktree／分支；真实 Service 或凭据缺失必须明确说明。

该票已完成：启用实测 32 MiB Flash 并保留数据，所有非 Camera App 安装／启动／Home 通过，Calculator 四角运算与 Weather 滚动通过；最终普通镜像 `69edbcc15` 的 apps/navigation/surfaces 与精确构建验证通过。Weather 首次启动 6.554 s，Chronos 12.289 s，Launcher 仍有软件绘制限制；不宣称全局 30 FPS。按授权合并本地 main，保留其它工作与原有发行／物理门槛。见[最终记录](records/2026-10-06-storage-round-runtime.md)。

2026-10-04：用户明确“可以，全部执行”。继续已有备份、app-only 刷写与真机输入授权，执行动态 Launcher、安装确认、外部运行、模式切换、在线稳定性及更新卸载矩阵；正式签名路径完成可执行准备和测试签名验收，缺少真实发行身份或外部发布权限时明确保留。保持 LittleFS 数据，不刷构建文件系统。
