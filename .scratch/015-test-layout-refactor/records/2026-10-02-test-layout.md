# 测试目录与设备测试执行职责迁移

Date: 2026-10-02

## 实施

- 局部组件/Native App 测试保持原 Owner；Runtime JS 样例测试迁到 runtime_apps/hello/test。
- 跨模块与工具主机测试迁到 firmware/test/host；scripts/check.py 显式发现 Runtime App 与 host，不发现 device。
- 从原 interaction_driver 分离 UsbTestClient、DeviceTestRunner、navigation/cards 用例，device/profiles 保存唯一坐标配置。
- 新 CLI run_device_tests.py 保留原参数、suite 默认值、报告与失败清理；旧入口转发，旧 profile 为指向新文件的符号链接。
- Firmware README、脚本说明与交互协议更新。未修改 managed_components、固件实现、App 资源或构建配置，没有新增人工轮次。

## 检查

迁移前后 navigation/cards 函数体 AST 一致，仅 self 更名为 runner。完整 scripts/check.py 通过，46 项 host unittest、M2 parser 与 Markdown；日志 /private/tmp/espocket-test-layout-final-host.log。Runtime 样例同一 JS realm 再启动/旧异步结果回归继续通过。新增两项实际 CLI 主机测试覆盖仓库外 help、受控 transport 失败报告与旧入口行为，不接真实串口。

初次检查发现搬迁后的旧 profile 链接缺失，已以唯一配置的兼容符号链接解决；Runner 更名后的主机错误字符串断言同步更新，未放宽协议判定。最终检查重新通过。

新 CLI 实际设备 attempt 20261002T141004Z-f9671ee5-43f5-43ea-87de-e39e76c240b7：navigation PASS，35 步（含初始唤醒），设备 ESPocket-Waveshare-A0F262E30B68、当前普通镜像 71567f599。目录 /private/tmp/espocket-test-layout-device-attempts/<attempt>/ 保存 report.json 与 serial.log。最终 release=ok、seq=711、Watch Face/display=true，前台 App/Page 为空，canBack/backPending/inputBusy=false。physicalInputVerified/visualVerified 均 false，不增加物理验收声明。

只有测试工具与文档变化，不要求重编译/刷写固件；未重新运行 Card fixture 设备套件，保持用户当前普通镜像。两张 Card 用例的 AST/执行器主机门槛通过，但既有 Card 物理结果仍由 014 原记录持有。
