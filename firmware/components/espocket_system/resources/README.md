# Product GUI themes

ESPocket System 加载 dark/light 主题，再启动 App。主题集中定义背景、表面、文字、边框、主色、状态色与控件颜色，样式通过 `${color.<语义路径>}` 引用；覆盖官方 Settings/Store、Circular Shell 与 Hello App 的 named style token；Brookesia GUI Runtime 持有注册和解析事实。资源嵌入固件，不写 NVS 或用户文件，不为 App 复制 GUI runtime。

slider/switch 的 main、indicator、knob 样式必须明确可见；官方资源升级新增 styleRefs 时，host contract check 应失败，不能忽略缺少的样式。圆屏页面几何仍由 App 资源负责。

本次修复与候选视觉门槛见 [004/05](../../../../.scratch/004-m4-device-capabilities/issues/05-fix-settings-controls-rendering.md)。

开发与扩展遵循[主题开发规范](../../../../docs/development/app-navigation-card-api.md#主题开发规范)。Shell 原生键盘、消息弹窗和 Back 控件在启动时从 System 提供的同一份已注册产品主题资源读取颜色；GUI Runtime 仍持有当前主题偏好，原生控件不另设配色表。当前主题切换在重启后生效。

## 默认与交互状态的格式

Theme `styles.<name>` 的普通属性直接写在样式对象上，例如 `{"bgColor":"${color.primary.fill}","stateStyles":{"pressed":{"bgColor":"${color.primary.hover}"}}}`。不要将普通属性再包进 `style`：锁定 GUI parser 会忽略这层内容，造成按钮只有按下时填色正确。View asset 的局部 `style` 与 `partStyles` 的格式分别按各自 schema 使用。

## Home Space 配色

| Surface / 控件 | 浅色与深色共用的语义 |
| --- | --- |
| Watch Face | 基础背景、强对比时间、蓝色主色点缀 |
| Launcher | 基础背景、凸起列表项、默认文字、按下时主色弱底 |
| Quick Settings | 轻微蓝色背景、亮度黄色弱底、Wi-Fi 蓝色弱底，其余中性凸起控件 |
| Battery Card | 绿色弱底与绿色标题 |
| Brightness Card | 黄色弱底与黄色标题 |

颜色只在两份产品主题中定义；Shell 资源引用对应语义样式，App 的主要操作继续使用 primary.fill/on。语义弱底按钮按下时加强边框，保持文字对比度。
