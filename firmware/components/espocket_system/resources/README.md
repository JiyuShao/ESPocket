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

## 内置字体与图标检查

维护资源的 literal label 使用的字符必须存在于实际选择的字体中。字号不是“最近大小”：锁定 GUI 先选择不大于请求字号的已启用 Montserrat，没有时使用 LV_FONT_DEFAULT。当前默认 UNSCII 8 不包含 FontAwesome 图标；图标 label 应使用已启用的 18sp/20sp/32sp 或显式支持它的字体。

`python3 scripts/firmware/check_glyphs.py` 检查 Shell 与维护 Native/Runtime JSON，按两种主题的 styleRefs、内联样式与继承字号解析，用真实 LVGL cmap 验证字符。错误包含文件、节点、U+ 码点和实际字体。`python3 scripts/check.py` 包含对应主机门槛；独立补丁构建用生成后的 sdkconfig 再校验，避免本地 defaults 与构建配置不同。单独检查有效配置可用 `--sdkconfig <path>`。

此门槛只证明这些 literal label 的内置字体码点覆盖；动态输入、翻译绑定、第三方 App、文件/image font 和实际排版像素需各自验证，不能据此宣称所有文本都能正确渲染。

## 中文字体资源

System 为 Runtime App 提供全局 `zh_CN` 字体资源。`fonts/espocket_cjk.otf` 嵌入 App 镜像，来自锁定 LVGL 中的 Source Han Sans SC，派生字体名为 ESPocket CJK；许可见 [OFL.txt](fonts/OFL.txt)，来源、生成器版本和内容摘要见 [manifest.json](fonts/manifest.json)。字符集为 GB2312、可打印 Latin-1 与 en dash，涵盖原 Weather 包的静态文字；不宣称完整 Unicode CJK 覆盖。

Tiny TTF 直接读取嵌入数据，按注册字号解码字形，每个字号使用四项缓存。System 持有原生字体，Core 先清理使用字体的 GUI，再释放字体和 Display。第三方包的未声明字体引用仍需解析为已存在的真实字体资源。

构建使用已生成资产，不依赖 fontTools。需要更新资产时，在独立 Python 环境安装 `fonttools==4.66.1`，运行 `python scripts/firmware/prepare_product_font.py`；输入 SHA 不匹配会停止。主机测试用实际 Tiny TTF outline decoder 核对全部字符和小／大字号，生成器不会修改上游字体。
