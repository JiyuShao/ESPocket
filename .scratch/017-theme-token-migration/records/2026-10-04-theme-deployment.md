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
