# 07 — AI Native 架构

## 目的

定义 AI Native 如何横向连接 System、Shell、Brookesia Service 与 App 的稳定产品语义，同时保持真实 Owner、实际调用者、授权和生命周期。

## 支撑的产品要求

- [OVR-004、OVR-007–OVR-010](../product/01-overview.md)
- [AIN-001–AIN-014](../product/02-ai-native.md)
- [APP-011–APP-015](../product/04-app-contract.md)
- [TRU-011–TRU-014](../product/05-runtime-package-trust.md)
- [DSC-011–DSC-014](../product/06-application-discovery.md)

## 结构

![ESPocket AI Native 架构](assets/ai-native-architecture.svg)

```text
User Intent / Scoped Grant
            ↓
        Assistant
            ↓
 Permission + Action Risk
            ↓
 Semantic Registration
            ↓
 System | Shell | Service | App
          real Owners
            ↓
 Brookesia public seams / HAL adapters
```

每项 Semantic Registration 包含稳定 identity、Owner、Context / Action / Event、Permission、Action Risk、生命周期、取消边界以及结果语义。

## 架构不变量

| ID | Invariant |
|---|---|
| AIA-001 | Assistant 组合用户目标，但不拥有目标状态、副作用、资源或生命周期。 |
| AIA-002 | Semantic Registration 位于真实 Owner Seam，不集中到第二套全局 AI Manager。 |
| AIA-003 | 每次访问都绑定实际调用者，并依次应用 User Intent、Scoped Grant、风险规则和 Owner admission。 |
| AIA-004 | Context、Action 与 Event 只表达稳定产品语义，不暴露 GUI 控件、任意方法、HAL handle 或对象转储。 |
| AIA-005 | Action 结果来自 Owner 可观察事实；未知结果不得报告为成功或自动重试副作用。 |
| AIA-006 | 取消只阻止尚未越过提交边界的工作；提交后的结果遵守 Owner 契约。 |
| AIA-007 | App registration 绑定单次 Running Instance；跨 App 生命周期能力由 Brookesia Service 拥有。 |
| AIA-008 | Capability Discovery 只描述可用能力，不授予 Context 读取或 Action 执行权限。 |

## AI Native

每个系统设计都必须作 Exposure Decision：开放稳定语义、明确不开放，或延期并保持能力不可发现。UI 可用不自动意味着 Assistant 可用，Assistant 可发现也不自动意味着获权。

能力 Adapter 是具体语义与 Owner Interface 的防腐层。它应该保持小 Interface，把授权后的调用、结果观察和生命周期绑定集中在一个 Seam；只有出现第二个真实 Adapter 后才提取共同结构。

## Code Anchors

- [system.cpp](../../../firmware/components/espocket_system/src/system.cpp)
- [circular_shell.cpp](../../../firmware/components/shell_circular/src/circular_shell.cpp)
- [Display lifecycle](../../../firmware/managed_components/espressif__brookesia_service_display/src/display_lifecycle.cpp)
- [Display backlight](../../../firmware/managed_components/espressif__brookesia_service_display/src/display_backlight.cpp)

## 相关决策

- [ADR-0006](../../adr/0006-ai-semantic-access-stays-with-real-owners.md)
- [ADR-0007](../../adr/0007-ai-authority-comes-from-user-goals.md)
- [ADR-0008](../../adr/0008-app-ai-capabilities-follow-the-running-instance.md)
- [ADR-0009](../../adr/0009-ai-native-is-a-foundational-design-dimension.md)

## 非目标

- 指定模型、Assistant UI、语音供应商或传输协议。
- 建立第二套状态、生命周期、权限数据库或 Service plane。
- 让 App prompt、package manifest 或 Capability Discovery 自动产生用户授权。
