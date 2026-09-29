# 系统上下文

这张图回答：ESPocket 运行在什么环境中，哪些主体会向它提供输入或接收输出？

![ESPocket 系统上下文](assets/system-context.svg)

## 上下文说明

- 用户只与 Shell、应用和物理按键交互，不直接接触 ESP-Brookesia 或硬件 Adapter。
- 构建系统把固件与内置 Runtime App 一起装入设备；Hello Runtime 当前走这条可信的 build-staged 路径。
- 官方 Settings 和 App Store 是 ESP-Brookesia 提供、由 ESPocket 显式安装的 Native App。
- 网络 Catalog 与动态 Runtime 包属于系统上下文，但远程安装只有通过包信任门后才能成为产品基线。
- 串口日志和验收工具是外部诊断关系，不属于设备运行时架构。

## AI Native 关系

Assistant 是用户目标进入产品语义的统一入口，不是设备外部状态 Owner。它通过 Owner 注册的 Context、Action 和 Event 使用 System、Shell、Service 或 App 能力；权限仍与实际调用者、User Intent 和框架准入求交集。

AI Native 不改变图中的设备边界，也不增加第二套 Runtime 或 Service plane。跨模块规则见 [AI Native 架构](07-ai-native.md)。

## 源码锚点

- firmware/main/app_main.cpp
- firmware/main/CMakeLists.txt
- firmware/components/espocket_system/src/system.cpp
- firmware/main/idf_component.yml
