# The-Badge migration inputs

[028](../../../.scratch/028-badge-native-app-migration/spec.md) 的七个 Native App 迁移工作区。本目录只保存精确上游参考源码、素材和来源锁，不编译、不安装、不注册应用。迁移实现位于独立的 [泡泡纸](../bubble_wrap/README.md) 与 [打砖块](../brick_breaker/README.md) App 目录；其余进度由 028 持有。

`upstream.lock.json` 固定仓库、完整 commit、所选文件大小及 SHA-256；`upstream/` 保持原字节，后续适配代码另写，禁止把未修改来源和适配版本混记。上游完整仓库包含其他产品入口，本目录只保存审计/迁移需要的输入。

来源为 [The-Badge](https://github.com/curisama/The-Badge/tree/76172dfaf0fa0ffedee91a61da3261afdde56ce3)，commit `76172dfaf0fa0ffedee91a61da3261afdde56ce3`。保留 `upstream/LICENSE` 的 MIT 版权及授权全文、`upstream/NOTICE` 的第三方与 NASA 图像来源说明。官方 GAP 示例另保留其文件头的 Unlicense OR CC0-1.0 标识；不能将它改标为项目 MIT。驱动依赖的许可证不由这一 MIT 许可替代。

选取的 `port_esp.c`、`app.h`、BLE 和 keypad 文件用于核查真实依赖，不直接编入 ESPocket：原作自行管理 BSP、全局 screen、音频、无线和 NVS，不能绕过既有 Owner。游戏/玩具源码仍有静态全局、LVGL timer、模拟触摸回退与直接活动报告，迁移需要逐项适配。详细结论见 [来源和边界核查](../../../.scratch/028-badge-native-app-migration/records/2026-10-12-source-and-boundaries.md)。

原作 planet map 的 NASA 来源/作者在 NOTICE 中逐项保留；四份材质已由独立 [太阳系 App](../solar_system/README.md) 按锁定原字节发布，参考目录本身仍不编译。QMI8658 的 `^2.0.0` 只是上游依赖范围，上游没有提交 dependencies.lock，本地生产依赖未因此升级。真机传感器、无线连接和玩法不以源码存在判定通过。
