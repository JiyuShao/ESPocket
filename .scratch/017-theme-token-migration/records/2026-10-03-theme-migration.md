# 2026-10-03 主题变量迁移验证

## 范围

Shell Watch Face、Battery/Brightness Card、Quick Settings、Launcher 与 App Card 容器改用语义 styleRefs。Hello Native 与 Runtime 的完整页面移除固定颜色；既有 Card 继续复用 app 样式。系统键盘、消息弹窗、默认 Back 与 Card hint 读取同一产品主题资源。

light/dark 集中定义 bg、surface、text、border、primary、info、success、warning、danger 与 control.knob。Battery Card 使用 success.soft/fill，Brightness Card 使用 warning.soft/fill；两种模式保留颜色含义。按钮文字配合 primary.on 或 danger.on，键盘按下状态明确使用 primary.fill/on。

## 原生控件边界

锁定 GUI Runtime 的 get_constant_value 读取文档自身 constants，而已注册 ThemeAsset 只保留颜色与样式映射，不能把该查询当作主题颜色读取接口。System 因此提供注册时使用的不可变产品主题 JSON，Shell 依据 Core GUI 当前主题选择同一资源，在启动时严格校验并缓存所需色值。不另建主题偏好或固定配色表，不在 LVGL 锁内同步查询 GUI。缓存随 Shell 启动重建，匹配当前重启生效的主题行为。

## 已通过检查

- `python3 scripts/check.py`：全部 host checks 通过。
- `npm run build`（Runtime Hello）：GUI 资源校验、打包通过。
- 新增资源契约检查覆盖所有维护页面与 Card 的 styleRefs、主题内颜色引用以及原生控件 token；普通颜色不能回退为固定色值。
- light/dark 的正文、辅助文字与背景、主按钮、破坏性按钮及 Card 标题配色对比度均至少 4.5:1。
- 主机执行真实原生颜色加载方法，核对两份实际产品主题；缺失资源、缺失颜色与非法色值失败，失败保留旧完整快照。
- Xtensa 编译器使用已有生产构建的 include/config 对六个修改的 C++ translation units 进行 `-fsyntax-only` 校验，通过。

## 固件构建

首次直接构建被沙箱中的 psutil 进程枚举权限阻断。独立补丁构建使用工作区 sdkconfig 时在 Kconfig 阶段失败（Missing required kconfig option after retry）；该配置包含实验 Audio 设置。

改用已有生产构建的 sdkconfig，在 `/private/tmp/espocket-theme-production-build` 独立生产补丁构建，通过 reconfigure、全部源码编译、最终链接、分区尺寸检查与补丁组件路径核对。原生键盘 selector 的枚举转换修复同步进入此独立副本，再完成最终构建。不修改生产 lock、managed components 或用户配置。

- 配置输入：`/private/tmp/espocket-production-final/firmware/sdkconfig`。
- 产物：`/private/tmp/espocket-theme-production-build/firmware/build/espocket.bin`。
- 固件大小：7587200 bytes。
- 固件 SHA-256：`fe7e8879612607128580bf4b8d249ac0d86b1e5994f1496f96d04edd75418861`。
- 构建输入 identity：临时目录中的 `patch-inputs.json` 与构建生成的 `project_description.json`。
- 完整构建日志：`/private/tmp/espocket-theme-production-build.log`（本地临时证据）。

## 未验证

未刷写设备，未验收 light/dark 的实际像素、圆屏可读性及交互状态。完整切换仍需保存主题后重启；本次不增加即时主题重套能力。计算对比度和资源校验不代替真机视觉验收。
