# The-Badge Native App 迁移

Sequence: 028

Status: active
Blocked by: 无额外人工许可；按 tickets 完成公共接口核查与离线实现，物理验收等待设备。

## Problem Statement

用户希望将 The-Badge 的圆屏游戏、玩具与蓝牙遥控迁移到 ESPocket，保留原作玩法与视觉，同时不改变现有分层和设计。原项目的 C/LVGL 应用不是现有 JavaScript Runtime package，硬件与启动器职责必须按 ESPocket 契约适配。

## Solution

以七个独立可见 Native App 交付：泡泡纸、打砖块、弹球、水池、太阳系、重力迷宫、蓝牙遥控。蓝牙遥控包含触控板和空中鼠标两种模式。应用使用现有 System Core、导航和 GUI 生命周期，硬件能力保持真实 Service/HAL Owner；产品行为已确认，已完成来源锁定、自绘/受控输入接口与暂停/活动接入，泡泡纸已实现为首个独立 Native App；离线构建和设备证据分开记录。打砖块、弹球和水池触摸版随后已实现；其余两个游戏与蓝牙遥控尚未交付，倾斜控制待 IMU 能力。

## User Stories

1. 用户从现有 Launcher 启动各 App，获得中文界面及原作的圆屏玩法和视觉。
2. 用户在所有迁移 App 内仍可使用现有 PWR Home 和全局下拉 Quick Settings；App 不拥有系统导航或显示恢复状态。
3. 用户通过蓝牙遥控 App 使用触控板或空中鼠标；实际配对、连接、IMU 和鼠标体验需真机证明。

## Implementation Decisions

- 2026-10-09 第一轮用户答复“全部同意”：采用编译进固件的 Native App；六个游戏/玩具分别独立，触控板与空中鼠标组成一个蓝牙遥控 App；保留原作视觉和玩法，用户可见文字中文化，不强制统一系统主题配色。
- 独立应用源码和资源遵守现有 Native App 组织方式；不迁入原项目 Launcher、Settings、锁屏或电源策略，不复制 Core、导航或生命周期管理器。
- 使用 CONTEXT.md 既有 App、Owner、Service、HAL 等术语；本次未产生新领域词汇，也未重开既有 ADR。
- IMU 与 HID 的真实接口兼容性必须先核实，优先复用厂商驱动和官方实现。平台暴露能力，App 实现业务策略；所需具体缺口与接入方案仍须核查，不从缺接口推断硬件不支持。
- 当前暂停方向复用既有 Core on_pause/on_resume，由 System 接通 Quick Settings 与息屏触发，App 回调负责自身动画、采样和业务工作；不解释为系统冻结全部线程。暂停期间的平台 App 定时更新停止，正常运行仍须保持系统手势、GUI 调度和 PWR 响应，不能读取原始输入绕过系统仲裁。早期 Q5 允许不暂停的选择已被后续讨论替代，保留在记录中。
- 用户接受 Q6：Quick Settings 时蓝牙遥控停止输入并保留连接，返回丢弃积累移动；Home 或息屏释放按键并断开。策略由 App 执行，平台提供事实与能力，实际停止/失败资源清理由真实 Owner 保证。两种暂停原因对应不同连接策略，所需既有公共事实及最小接入缺口仍待核查。
- 用户接受 Q7：BLE 首批验收目标为 macOS、Windows；首次手动配对，之后打开遥控 App 尝试连接已配对电脑，开机不自动进入遥控；连接失败仍可操作页面。
- 用户接受 Q9：保留原作短音效，经现有 Audio Service 播放并遵守系统音量/静音；其他业务占用音频时跳过音效，游戏继续。
- 已核实既有 Core 提供 on_pause/on_resume，但当前 Quick Settings 覆盖和屏幕开关没有调用它；本次方案需补齐触发接入，不能以接口存在认定场景已实现。完整共同理解尚未最终确认。
- 生命周期方向及恢复行为已在后续问答中收敛为复用 pause/resume、暂停实际更新并自动继续同次进度；早期允许继续运行或建议独立交互通知的讨论仅保留为 records 中的历史，完整方案尚待最后确认。
- 该方向要求暂停只作用于真实被覆盖的普通 App；Quick Settings 与息屏两个原因都解除后才恢复同一个仍有效且未被其他前台取代的 Running Instance。隐藏 Shell、持续 Service 和 App Card 保持各自既有 Owner，不能调用旧 resume_app 复活停止实例或强抢新前台。
- 用户接受 Q11–Q13（“都同意”）：收起 Quick Settings/亮屏后自动继续同一次游戏进度，暂停时间不累计，恢复时清除旧触摸状态；Home 后重新打开仍从 Root 开始。息屏断开的遥控仅在返回同一次遥控 App 时尝试重连已配对电脑，连接完成前不发送输入，不补发暂停期间移动，失败提供重试入口。默认保留 Wi-Fi，由既有 HAL/Service 处理 BLE 共存，不由 App 擅自关闭系统网络；实测延迟不达标时再讨论产品取舍。
- 用户接受 Q14–Q17（“全部同意”）：IMU 失效时保留不依赖传感器的交互，受影响功能明确提示不可用并允许重试/退出，空中鼠标可切回触控板；生产版不使用模拟数据冒充硬件。遥控保留主机切换与按电脑记忆灵敏度；忘记配对采用明确的设备管理入口及确认，取消原作隐藏长按清空。有效遥控移动、点击与滚动算活动，沿用系统息屏超时，主动息屏立即生效，游戏动画不算用户活动。
- Exposure Decision：用户接受首版不增加这些 App 的 AI 操作接口，包括代玩、鼠标移动/点击及配对管理；不改变现有 Launcher 的能力或建立第二个 AI Owner。
- 不修改原始 managed_components；若确需上游补丁，遵守 ADR-0016 的隔离、版本/hash 与回归要求。本轮尚未授权或实施某个具体补丁。

## Testing Decisions

- 源码、host 行为、完整隔离构建和真机验收分别记录；不能以模拟数据或成功编译认定实际 IMU/HID 可用。
- 设备不在用户身边，当前阶段只完成设计与允许的离线工作；不刷写、不配对电脑、不发送实际 HID 输入。
- 后续 ticket 明确游戏计时/碰撞、实例停止、迟到回调、资源回收、系统手势竞争及硬件失败路径；具体矩阵在共同理解确认后定版。

## Out of Scope

Excel 快捷键、录音机、原项目计算器/时钟/Settings/Launcher/锁屏、USB 导出、原项目分区和电源管理、新增 AI 操作接口。首版不新增 App Card 或后台遥控，不实现新通用框架或改变 ESPocket 现有分层。

## Tickets

1. [迁移契约、能力核查与实施拆分](issues/01-confirm-migration-contract.md)
2. [锁定上游来源与确认公共 GUI 接入](issues/02-source-and-gui-boundary.md)
3. [接通覆盖与息屏生命周期及活动语义](issues/03-system-lifecycle-and-activity.md)
4. [接入板级 IMU 能力](issues/04-imu-capability.md)
5. [接入 BLE HID 与配对资源所有权](issues/05-ble-hid-capability.md)
6. [迁移六个游戏与玩具 Native App](issues/06-native-games-and-toys.md)
7. [迁移蓝牙遥控 Native App](issues/07-native-ble-remote.md)
8. [离线回归与隔离构建候选](issues/08-offline-build-candidate.md)
9. [真机玩法与无线验收](issues/09-device-acceptance.md)
10. [App 所属自绘挂载与多点输入](issues/10-native-content-and-pointer-seam.md)

## Further Notes

- [上游项目](https://github.com/curisama/The-Badge)。
- [App 契约](../../docs/design/product/04-app-contract.md)、[分层架构](../../docs/design/architecture/02-layered-architecture.md)、[ADR-0003](../../docs/adr/0003-native-and-runtime-share-the-system-core-contract.md)、[ADR-0016](../../docs/adr/0016-maintained-upstream-fixes.md)。
- [第一轮决定与接口初查](records/2026-10-09-scope-and-capability-frontier.md)。

2026-10-12：用户要求无真机时先完成离线可靠性再继续 028，沿此前已接受方案实施，不再重复索取总体许可。[来源锁定与边界核查](records/2026-10-12-source-and-boundaries.md)记录当前输入、官方驱动和真实缺口；历史“待最后确认”保留为当时阶段描述。

2026-10-13：用户授权完整实现下一批 [03](issues/03-system-lifecycle-and-activity.md) 与首个泡泡纸 App 流程。实现、离线验证与候选见 [本批记录](records/2026-10-13-suspension-and-bubble-wrap.md)；泡泡纸使用说明见 [App README](../../firmware/native_apps/bubble_wrap/README.md)。六个游戏的总体票仍未关闭，IMU、BLE HID 和真机验收继续保持独立门槛。

2026-10-13：[App 接口与 IMU 提案审查](records/2026-10-13-app-interface-review.md)复现暂停原因回调重入后的恢复错误，[03](issues/03-system-lifecycle-and-activity.md)已重开，优先修复并补回归。现有命名优化与 IMU 契约缺口分别记录，尚未实施；v5 是初版候选，不能代表该错误已修复。

2026-10-13：用户授权的 [生命周期接口优化](records/2026-10-13-lifecycle-callback-contract.md)完成，统一原因回调命名/快照、保留旧入口兼容，修复原因回调重入恢复并通过生产回归与新的完整隔离构建；[03](issues/03-system-lifecycle-and-activity.md)再次 resolved。活动凭据、执行快照/策略参数和 IMU 的其他审查建议未由本批实施，04/06/07/08/09 的剩余条件保持。

2026-10-13：继续实施 [06](issues/06-native-games-and-toys.md) 的独立打砖块触摸版，复用既有 App 接口及共享短音效适配，本批未修改 Core；[打砖块使用说明](../../firmware/native_apps/brick_breaker/README.md)和[弹球使用说明](../../firmware/native_apps/pinball/README.md)记录触摸交互与边界；[实现与候选记录](records/2026-10-13-brick-breaker-touch.md)区分离线完成、倾斜控制待接入与真机待验。六游戏总票保持未关闭。

2026-10-13：完成 [06](issues/06-native-games-and-toys.md) 的弹球触摸版，保留原作碰撞球、目标、挡板与定步物理；[实现记录](records/2026-10-13-pinball-touch.md)区分离线完成、倾斜控制与真机待验。

2026-10-13：完成 [06](issues/06-native-games-and-toys.md) 的独立水池触摸版：原作 380 粒子流体、小船、RGB565 绘制和 App 所属有界工作线程；[实现与候选记录](records/2026-10-13-water-touch.md)同时记录弹球移植缺口修正。倾斜控制等待 04，太阳系/重力迷宫/蓝牙遥控与真机仍待完成。
