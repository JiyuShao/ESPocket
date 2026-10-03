# 2026-10-04 — 主题部署与普通态修复

## 首次部署

017/01 完成源码与构建而明确没有刷写。设备原为普通镜像 74b1b55ce，其 Hello Native/Runtime 完整页面仍带旧颜色。将已核对独立构建部署为 a732ae73b（设备协议身份），原 bin SHA-256 fe7e8879612607128580bf4b8d249ac0d86b1e5994f1496f96d04edd75418861。

LittleFS 先备份，再仅更新 Hello Runtime 的 res/screens/main.json 与 detail.json，全部其他文件 hash 保持。原始备份、更新镜像与逐文件 ledger 分别位于 /private/tmp/espocket-theme-before-littlefs.bin、espocket-theme-updated-littlefs.bin、espocket-theme-runtime-image-update.json。固件与文件系统刷写 hash 校验通过。此操作是设备开发资源更新，不宣称签名安装或线上发布。

用户确认浅色完整 App 背景正常；按钮仅在按下后正常。普通 App 合成输入回归通过，attempt 20261003T163806Z-e223933d-5113-425f-834d-0efd772d5bb6；不证明按钮像素正确。

## 普通态缺陷

锁定 GUI parse_style_set_object 直接将 Theme styles 中的每项交给 parse_style_object，不读取额外 style 包装；stateStyles 则单独解析。资源把 app.action/slider/switch 的普通态包在 style 中，导致普通态被忽略但 pressed 生效。partStyles 支持 style 包装，与 Theme 顶层不是同一 schema。

`python3 -m unittest discover -s firmware/test/host -p test_product_theme.py` 先得到 FAIL（普通态 style 被忽略），删除顶层包装后七项通过。修复所有同类控件。系统配色见 Product GUI themes 文档，未改变页面布局或导航规则。

统一主机检查通过（71 个跨模块 host tests）；完整独立 production 构建通过。普通产物独立保存在 /private/tmp/espocket-theme-controls-preserved，ELF identity 53fb55e37。临时 Native 键盘协调器不属于此产物。

## 待完成

最终普通固件的 light/dark 像素确认与系统交互结果待记录，不能以资源检查替代。

普通修复镜像 53fb55e37 与恢复的普通 Runtime 资源刷写 hash 校验通过。重启日志确认 light 恢复、Shell/Core 与 USB Adapter 正常启动。bin SHA-256 d65d1ba7153ed97e1936d70f22ef182b9dfb7466656bb5fa20cdcb657090165f；ELF SHA-256 53fb55e372c071873006469273044ba239b9617c6d1c8a66fe9c9d081f8f41ac。等待一次视觉确认。

用户确认：浅色 Native/Runtime 按钮未按下时已清楚可见，Watch Face、Launcher、Quick Settings 配色正常。深色最终配色仍未独立做像素确认。

深色已通过 Settings 保存，原自动确认点击关闭弹窗但未重启，因此没有宣称确认重启路径通过；随后显式复位，启动日志确认 Product GUI theme active: dark 与 ESPocket started。等待一次深色最终像素确认。

## 深色反馈与布局调整

用户确认深色其他控件基本正常，但 Brightness Card 按钮仍是蓝色，Quick Settings 与 Launcher 外观需调整。亮度卡主按钮改用 warning.fill/on，次按钮与按下边框使用 warning 语义；Quick Settings 采用两列四个紧凑控件，Launcher 改为 72dp 列表行与轻量箭头。动作、返回手势与页面身份不变；USB 测试坐标随布局调整，须重新验证。

新版普通镜像 fc107fb10：ELF SHA-256 fc107fb10eb211b9afab17b6f63b92ad7154a715976347c0187ab643dfa2c0b3，bin SHA-256 ac348ddca80e12cd1b3d49eea5e2de6133fe4913bbf0fd9e941f3d9cb5b20044，独立保存于 /private/tmp/espocket-compact-preserved。主机检查通过（跨模块 73 项，加各组件所有者测试）；新增圆屏控件边界和黄色按钮文字对比度约束。依赖锁、六个 production 补丁路径和 playback-only 配置核对通过。构建源码已移除临时键盘协调器。

紧凑布局首次 USB 回放发现实际缺陷：Launcher 下拉松手落在 Settings 行，Home 已提交后，GUI 排队的行 clicked 动作仍打开 Settings。报告 /private/tmp/espocket-compact-device-ready/report.json 判 FAIL，不记为通过。on_action 现在先检查 Launcher 动作仍来自当前 Launcher，避免导航后旧页面排队动作再次打开 App；保留原拉动阈值期间的点击抑制。须用同一路径重放。首次 boot window 报告捕获 SNTP 缺失配置警告，未开始场景，不作为有效门槛。

修复后的普通镜像 24acc698e：ELF SHA-256 24acc698efeea1e6738583f708404e4737e16cbf80f286430989f9dc521550f3，bin SHA-256 9d8de06b7072d28b2b3c813123876a975152fa891d519ba3471ff918b6b2d536。长期 surfaces 设备场景加入 Launcher 下拉后的前台 App 为空断言，22 项设备 Runner 主机测试通过。

修复重放 PASS：/private/tmp/espocket-compact-device-fixed/report.json。普通 Native/Runtime Root、Detail、Edge Back、PWR Home，圆屏两侧 Card，双列 Quick Settings 到 Settings 入口，以及 Launcher 下拉返回后没有前台 App 均通过。固件刷写 hash 通过（/private/tmp/espocket-compact-pull-flash.log）；设备保留普通固件、普通 Runtime 资源与深色主题，停在 Quick Settings 供单轮视觉确认。USB 合成输入只验证实际 Owner 语义，不代替新布局像素或实体触摸验证。用户的 light 控件、先前系统配色已通过；本次布局与黄色按钮的最终像素意见待补。
