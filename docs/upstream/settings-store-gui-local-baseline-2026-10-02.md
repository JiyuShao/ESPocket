# Settings 与 Store GUI 本地源码快照 — 2026-10-02

本页是对当前锁定依赖和本地源码的一次只读核对，不是升级建议，也不代表 ESPocket 已实现官方 App 的统一 Page 适配。长期产品契约见 [App 契约](../design/product/04-app-contract.md)，当前实施状态见 [014/01](../../.scratch/014-app-navigation-card-contract/issues/01-page-declaration-navigator.md)。

## 锁定版本与提交边界

[`firmware/main/idf_component.yml`](../../firmware/main/idf_component.yml) 声明 Settings `0.8.3`、Store `0.8.2` 以及 Brookesia GUI 和 System Core 依赖；[`firmware/dependencies.lock`](../../firmware/dependencies.lock) 保存解析后的组件版本与 hash。`firmware/managed_components/` 是生成依赖且被 Git 忽略；本地修改不是可提交的产品源码。ESPocket 的产品代码、测试和文档保存在本仓库，只有变更依赖时才更新 manifest 与 lock。

## 当前 GUI 路径

| 组件 | 已核对事实 | 源码 |
|---|---|---|
| ESPocket System | 选择 Brookesia GUI LVGL Backend。 | [`system.cpp`](../../firmware/components/espocket_system/src/system.cpp) |
| Circular Shell 与 Hello Native | 都提供 Brookesia `AppGuiDescriptor`，使用 JSON GUI 文档和 Screen Flow。 | [`circular_shell.cpp`](../../firmware/components/shell_circular/src/circular_shell.cpp)、[`hello_app.cpp`](../../firmware/native_apps/hello/src/hello_app.cpp) |
| 官方 Settings | 提供 Brookesia GUI 资源与 `settings_content` Screen Flow；该 Flow 的初始屏为 `settings_home`，包含多个设置页面。Settings 的 `current_page_`、页面动作和 `settings.header.back` 处理在组件内部。 | [`settings_app.cpp`](../../firmware/managed_components/espressif__brookesia_app_settings/src/settings_app.cpp)、[`content.json`](../../firmware/managed_components/espressif__brookesia_app_settings/package/res/flows/content.json)、[`lifecycle.ipp`](../../firmware/managed_components/espressif__brookesia_app_settings/src/app/lifecycle.ipp) |
| 官方 Store | 也提供 Brookesia GUI；当前 `app_store` Screen Flow 只有一屏。Store／Installed／Local 标签、列表翻页和弹窗是这屏内的状态。 | [`app_store.json`](../../firmware/managed_components/espressif__brookesia_app_store/package/res/flows/app_store.json)、[`catalog.ipp`](../../firmware/managed_components/espressif__brookesia_app_store/src/screen/catalog.ipp) |

Brookesia 的 `IApp` 要求 Native App 提供 manifest，GUI descriptor 可选；生命周期、动作与计时器回调有默认实现。不能由 Settings 和 Store 的实现推断所有 App 都有 GUI 或 Screen Flow。[`IApp`](../../firmware/managed_components/espressif__brookesia_system_core/include/brookesia/system_core/app/iapp.hpp) 与 [`AppGuiDescriptor`](../../firmware/managed_components/espressif__brookesia_system_core/include/brookesia/system_core/app/types.hpp) 是此结论的接口依据。

## 可用接口与适配风险

System Core 公开 `gui_get_screen_flow_state(appId, flow)`，可读取某个 App 已加载 Flow 的当前屏；它没有 Settings 专用的 Page／Back API。[`system.hpp`](../../firmware/managed_components/espressif__brookesia_system_core/include/brookesia/system_core/system/system.hpp) 中可以核对这一边界。Settings 的 Back 动作会在 `SettingsApp::on_action` 中先根据当前页面解析，再执行页面转移及 Wi-Fi、键盘等关联处理。直接触发 GUI Flow 不能据此认定会执行这些 App 处理。

`settings_content`、`settings_home` 和 `settings.header.back` 在锁定版组件中可见，但不属于 Settings 专用公开契约。未来升级若使用这些名称，需要先核对新锁定源码与行为，不能把未知屏静默解释为 Root。Store 目前的一屏事实同样只适用于锁定版 0.8.2；若官方 Store 新增详情屏，应重新判断其 App Page 语义。

本次核对没有修改 Brookesia 依赖、运行构建或真机测试。
