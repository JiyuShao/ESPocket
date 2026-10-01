# 官方 Settings 最小导航适配

- 日期：2026-10-02
- 范围：014/01 与 014/02 的官方 Settings 适配例外
- 决策：[ADR-0012](../../../docs/adr/0012-official-settings-keeps-its-navigation-owner.md)

## 源码与边界

ESPocket 的 `SettingsNavigationAdapter` 组合官方 SettingsApp，转发 manifest、GUI descriptor、安装、卸载、启动、暂停、恢复、停止、动作与计时器回调。官方 `settings_content` Flow 是唯一页面事实源；适配层映射十个稳定 Page ID，不维护栈。官方按钮与 Shell Edge Back 均委托 `settings.header.back`，Root 返回 `at_root`；不叠加默认可见 Back。

`System::foreground_page_snapshot()` 为 Navigator 与 Settings 提供相同的 PageSnapshot；前台任务改变或观察失败时返回错误。Settings 快照实时读 Flow；缓存仅用于 raw GUI 输入的 Back 可用标志，执行 Back 前再次读取页面。未知屏、无 Flow、未启动或停止后均不报告 Root、不执行委托 Back。普通 App 的唯一栈及待决 token 语义未改。官方 Settings 不提供通用 push/pop、待决 Back 或 Card 直达。

资源兼容检查绑定 Settings 0.8.3 的组件 hash、Flow、初始屏、页面集合和已知 Back 路由，已接入固件 CMake 配置。未来升级必须同次审查 lock、映射与测试。未修改 managed components。

## 验证

- 主机测试通过：执行真实 Adapter 源码与模拟 IApp/GUI 接口，覆盖回调转发、实时页变化、按钮与手势 Back 委托、Root 无 Back、未知屏／Flow 缺失、暂停恢复、停止重启和上游错误传播。
- 锁定资源兼容测试通过；它只能证明已知结构前提，不能证明官方 Wi-Fi／键盘清理在真机上的全部效果。
- Markdown 检查通过；未运行 Chrome 图布局检查。
- 最终整包构建通过，CMake 的锁定资源兼容门槛通过；普通配置关闭 M2 stress、M6 reclaim/resource 诊断，USB Service 自动注册仍关闭。
- 构建目录：`/private/tmp/espocket-m78-build`；镜像 SHA-256：`79f525cc0df4e3157211472e521b3c42e827867289681b4d98ab4f74a4fb3e86`，App 大小 `0x5d11c0`，App 分区剩余 43%。
- 真机仅写入 App 分区 `0x60000`，写入 hash 校验通过；没有重写 LittleFS 或 NVS。只读 `hello` 成功返回镜像 identity `c005fa14a`，与构建镜像的 ELF SHA-256 前九位一致。
- 用户完成一次 Settings → Display → Edge Back 检查，确认边缘返回正常，并明确报告没有可见 Back。资源中存在 Back 声明不能证明控件在当前设备上实际可见。
- 用户随后确认这种无可见 Back 的呈现可以接受，由 App 决定显示与样式；不为 Settings 补 Overlay Back。用户进一步确认所有 App 都可定制返回形式（边缘／上下滑动等）与返回 UI，不要求可见按钮；统一 Back 语义、Root 无 Back 与 PWR Home 保留。

## 尚未覆盖

Settings 深度 UI／业务定制、Runtime Page 绑定、App 更新稳定 ID 迁移以及全量 M7/M8 验收不属于本次通过项。

## Back 呈现契约后续修订

按 [ADR-0013](../../../docs/adr/0013-app-controls-back-presentation.md) 移除 `has_app_owned_back_control` 声明及多级 App 缺少可见 Back 时的安装拒绝。默认 Framework 呈现保留，AppOwned 关闭两种默认入口，App 自定义控件或手势使用同一 Back 请求。

主机 Navigator 测试通过，覆盖无按钮多级 App 安装、默认入口关闭与统一 Back 返回 Root；固件完整构建通过，Markdown 检查通过（147 文件）。此修订尚未刷入设备，当前设备仍是上述 Settings 适配镜像；没有新增真机通过项。
