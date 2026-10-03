# ESPocket 开发契约

本目录面向 Native App、Runtime App 和设备测试工具开发者，规定 ESPocket 产品框架额外提供的声明与协议语义。这里描述目标 API；实现完成情况和可执行工作以 [本地工作项](../../.scratch/README.md) 为准。

- [App Page、Card 与 Back 开发 API](app-navigation-card-api.md)：App 声明、导航、Back、Card 生命周期及错误处理；包含[主题开发规范](app-navigation-card-api.md#主题开发规范)，界面优先使用主题样式与颜色变量。
- [交互自动化测试协议](interaction-test-protocol.md)：开发者模式、USB 命令、快照和证据边界。

产品必须呈现的行为以[产品设计](../design/product/README.md)为准；模块所有权以[架构视图](../design/architecture/README.md)为准。本目录的示例名称与字段是接口设计草案，具体语言绑定及线缆格式需在对应实现工作项中确定并版本化。
