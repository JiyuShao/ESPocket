# 02 — 总体分层架构

## 目的

定义 ESPocket 产品代码、ESP-Brookesia Framework、平台 Adapter 与硬件之间的单向依赖，并把变化隔离在真实 Seam 上。

## 支撑的产品要求

- [OVR-001、OVR-003、OVR-004、OVR-005](../product/01-overview.md)
- [APP-010](../product/04-app-contract.md)
- [AIN-001、AIN-011、AIN-013](../product/02-ai-native.md)

## 结构

![ESPocket 总体分层架构](assets/layered-architecture.svg)

| Seam | Interface | Adapter |
|---|---|---|
| App 生命周期 | `IApp`、`AppContext` 与 System Core 生命周期操作 | Native App、Runtime JS backend |
| 产品 Shell | Shell 的 `IApp` Interface 与产品回调 | CircularShell |
| GUI | Brookesia GUI backend | GUI LVGL backend |
| 显示来源 | `DisplaySource` 与 Display Service | ESP LVGL Adapter |
| 板级能力 | Brookesia HAL 与 Board Manager Interface | Waveshare 1.75C board configuration |
| AI 语义访问 | Owner 注册的 Context、Action 与 Event | 能力专用 Adapter |

## 架构不变量

| ID | Invariant |
|---|---|
| LAY-001 | ESPocket 产品 Module 可以依赖 ESP-Brookesia 的公开 Interface，反向依赖禁止。 |
| LAY-002 | CircularShell 拥有圆屏交互 Implementation；`espocket::System` 拥有产品装配与跨 Module 编排。 |
| LAY-003 | App 通过 `AppContext`、GUI 与 Framework Service Interface 获得能力，不依赖 CircularShell Implementation。 |
| LAY-004 | App 安装、生命周期、GUI、Runtime 与 package 扫描复杂度保留在 System Core 深 Module 内。 |
| LAY-005 | 设备差异通过 HAL、Board Manager 和 Adapter Seam 隔离，ESPocket 不复制 Framework Implementation。 |
| LAY-006 | 一个 Adapter 不足以证明通用扩展 Interface；出现第二个真实 Adapter 后才提取共同结构。 |

## AI Native

AI Native 是横向语义访问维度。状态、副作用、资源和生命周期仍由原 Module 拥有；能力 Adapter 只把稳定语义映射到既有 Interface，不能形成第二套 Manager 或竞争状态。

Exposure Decision：每层只开放自己拥有的产品语义；Framework 与 HAL 的任意方法、对象和 handle 不自动成为 AI 能力。

## Code Anchors

- [ESPocket System CMakeLists.txt](../../../firmware/components/espocket_system/CMakeLists.txt)
- [CircularShell CMakeLists.txt](../../../firmware/components/shell_circular/CMakeLists.txt)
- [idf_component.yml](../../../firmware/main/idf_component.yml)
- [Board Manager generated interface](../../../firmware/components/gen_bmgr_codes)

## 非目标

- 预先建立 Shell Factory、Adapter Registry 或 Plugin system。
- 复制 System Core、ServiceManager、HAL 或 package format。
- 记录依赖版本或实现进度。
