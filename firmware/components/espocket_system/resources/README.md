# Product GUI themes

ESPocket System 加载 dark/light 主题，再启动 App。主题保存当前官方 Settings/Store 使用的颜色与 named style token；Brookesia GUI Runtime 持有注册和解析事实。资源嵌入固件，不写 NVS 或用户文件，不为 App 复制 GUI runtime。

slider/switch 的 main、indicator、knob 样式必须明确可见；官方资源升级新增 styleRefs 时，host contract check 应失败，不能忽略缺少的样式。圆屏页面几何仍由 App 资源负责。

本次修复与候选视觉门槛见 [004/05](../../../../.scratch/004-m4-device-capabilities/issues/05-fix-settings-controls-rendering.md)。
