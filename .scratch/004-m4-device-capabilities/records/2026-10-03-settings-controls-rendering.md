# 2026-10-03 — Settings 控件缺失诊断

用户在 image `a39b76776` Sound 页报告无滑块，照片仅能看到 Sound、Sound options 与 Mute 文本，Volume 标题、slider 与 toggle 不见。本次不算 UI 验收通过。

串口 `/private/tmp/espocket-audio-user-volume.log` 确认 Screen Flow 转入 sound；AudioPlayback、DAC、audio manager 与 playback open 已成功，无本次初始化失败。GUI 告警 theme dark 未注册，app.page/card/cardTitle/slider/switch 等 named style 找不到。LVGL backend 缺 bgColor 时将 main 背景设为透明。

已排除错误 opacity 单位假设：Settings enabled=255/disabled=96，backend 按 0–255 应用。主题缺失与几何裁切仍需区分。独立候选中使用公开 AppGuiRuntime::get_view_frame 查询 page/card/row/title/slider/toggle，临时标记 DEBUG-sound-frame，不新增 USB API、不访问 LVGL 私有对象。探针结果见下；诊断不进入正式源代码。

Exposure Decision：布局、主题与 frame 诊断均为内部 UI 装配，不对 Assistant 暴露控件树或 private handle。

## Geometry probe result

诊断 image `4812fed37` 启动通过，脚本 `/private/tmp/espocket_sound_frame_probe.py` 自动进入 Sound 再回表盘，release 完成。原始日志 `/private/tmp/espocket-sound-frame-probe.log` 的公开 get_view_frame 结果：page 450×404；volume card 450×122；row 422×94；Volume title 48×9；slider 422×28；toggle 58×30。宽高不为零，排除 collapsed-layout 假设。app.slider 命名样式缺失仍复现。

页面矩形从 (8,54) 延伸至 (458,458)，未处于圆屏安全区域；标题处在左上裁切区，而滑块轨道/旋钮因主题未加载而无正确外观。

## Implementation

ESPocket System 嵌入并在 App 启动前加载 dark/light 主题，覆盖当前 Settings/Store 消费的 named styles、颜色 token 与 slider/switch part styles。GUI Runtime 仍是唯一 theme Owner，不新增主题 registry 或写入用户文件。Core SystemGuiAccess 增加 load_theme_json，复制输入后在原 GUI task 中调用已有 Runtime::load_theme_json；与既有 load_theme_file 共享所有权，不为 Runtime App 或 USB 新增入口。补丁 004 按锁定 Core 0.8.4 manifest 维护。

Settings 0.8.3 的 root 资源追加仅当前 466×466 目标的 inline constant variant：内容矩形 (70,70,326,326)，四角处于圆屏内；其他尺寸继续原 variants。source patch 不改 Flow、动作、导航或设备调用，仅在 audio-candidate 启用，待视觉验收再决定纳入普通产品集合。此方案是当前板级适配，不把 466×466 自动泛化成所有圆屏规格。

回归：主题覆盖真实官方资源 styleRefs、可见控件 part 与动态颜色 token；原矩形圆屏边界失败、准确补丁矩形通过；实际 Core 方法验证 GUI task、调用输入复制、缺失 System/Runtime、调度拒绝及解析错误。统一 host checks 通过（Owner 22、cross-component 57），不把这些检查冒充像素或触摸验收。

Exposure Decision：Core embedded-theme 方法仅供可信 Native System 组合使用，无新的 Assistant action、App 服务或测试协议能力。临时尺寸探针只存在独立诊断工程；最终构建从正式 checkout 复制，包含未加探针的 Adapter。

## Candidate gates

统一检查 `/private/tmp/espocket-settings-theme-final-host.log`：79 项 host tests 通过；Markdown 检查 `/private/tmp/espocket-settings-theme-final-docs.log`：198 文件通过。Settings 原有 registry-only 门槛拒绝了本地补丁，已扩展为严格验证锁定版、实际组件路径与完整 patched_files hash；替换 root 资源的负例验证拒绝未知源码。完整构建及真实启动、导航证据见下；真机视觉/操作门槛已由用户确认。

完整构建 `/private/tmp/espocket-settings-theme-repaired-build.log` 通过；ELF SHA256 `8b69429a123f9aa50c996013f781e92663d5ba1bb80f21057125018e6f14292c`，BIN SHA256 `62d68af692b4db3ab1f9168ebeb8944b39183b97a403fd3a57ad7bfcbe997fda`，hello `8b69429a1`。应用分区 0x60000 写入校验通过，未写 NVS/LittleFS/models。原始 managed components 全部锁定 inventory 未变；初始 patch-inputs 保留，兼容门槛修订后的 manifest hash 单列 `/private/tmp/espocket-settings-theme-build/final-build-inputs.json`，不重写初始输入历史。

真实启动 `/private/tmp/espocket-settings-theme-boot.log` PASS。导航 attempt `20261003T014118Z-61d20d68-98fe-4184-94c8-ed5e3f66de80` 34 步 PASS；自动触摸进入 Settings Root → Sound 并回表盘，`/private/tmp/espocket-settings-theme-sound-result.log` PASS；Sound 期间没有 missing named style 告警，没有诊断 probe。AudioPlayback 启动/停止与设置 volume 成功。自动输入不证明像素可见、真实触摸或实际听感；用户随后确认“都可见，拖动正常”，完成一次真实 Volume 操作；未声称 Mute 点击或播放听感验收。

用户确认候选 image `8b69429a1` 的 Volume 与 Mute 可见，拖动正常。004/05 按候选控件渲染边界关闭，004/04 的实际播放听感保持未完成；Settings 圆屏资源仍在 audio-candidate patch set，普通构建的采用须单独构建验证。

实际拖动日志 `/private/tmp/espocket-settings-theme-user-capture.log` 显示 AudioPlayback Set volume 从 49 调到 23 再到 37，与用户观察一致。附带观察其他 Settings 页缺 primary.soft/on 等颜色与 settings.display.light 缺系统确认弹窗；颜色已扩展到真实 Settings/Store 资源的全部 color refs，并增强覆盖回归；弹窗另开 [004/06](../issues/06-support-settings-message-dialog.md)，未声称修复。

## Final color follow-up

仅补充真实 App 消费的 bg.base/overlay、primary.soft/on、info.soft、warning.soft，Sound 已接受的 slider/switch 样式与布局不变。加强颜色 token 回归后，`/private/tmp/espocket-settings-theme-accepted-check.log` 统一检查通过（79 host tests、199 Markdown）；第一次 resolved 文档缺少 Resolution 被检查拦下，补齐后重跑通过。

增量完整构建 `/private/tmp/espocket-settings-theme-colors-build.log` 通过，原有锁定依赖、4 个 patched component 路径及播放候选配置再次验证通过。最终 ELF `e7c095d3d9698b33e484cef16440471e02013582bf6b963d193caccc30536932`、BIN `5c53d3c67a79a453377230033ebb7d29162cb27e3702da85918c51dc7ae057c6`、hello `e7c095d3d`。App 分区刷入校验通过；`/private/tmp/espocket-settings-theme-colors-boot.log` 启动 PASS，`/private/tmp/espocket-settings-theme-colors-sound-result.log` 自动进入 Sound 并回表盘 PASS，无 missing style 告警，无临时 probe。

用户可见/真实拖动证据属于此前 image `8b69429a1`；最终 image 的自动检查不冒充新一轮人工验收。最终设备停在表盘，普通 image `5e79e3a82` 的既有 rollback 仍独立保存。无需重复用户已通过的一次控件操作。
