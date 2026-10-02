# 声明式 Runtime Card 首版

Date: 2026-10-02
Scope: 014/05 声明式 Runtime Card source slice；用户已确认继续，ADR-0014 已接受。

## 实现事实

- cards.json v1 与 navigation.json 使用同一 App ID、Card ID 和目标 Page；安装前校验大小、版本、唯一身份、单个独立 Screen、绑定路径与动作范围。缺少声明、未知身份和任意 JS 业务动作均拒绝，不发布半套 Card 提供者。
- System 在真实 Core Runtime 安装回调读取声明并登记模型工厂。每次可见刷新读取当前安装 manifest 的名称/版本；身份变化、App 消失或 GUI 更新失败返回错误。Card 不启动完整 App，不创建 JS backend，不使用私有 Runtime ID。
- GUI、显示/暂停、订阅释放和打开目标 Page 复用现有 CardDocument/CardSession 与 Owner 队列；打开前暂停，完整 App 使用同一 Navigator，Detail 栈底为 Root。首版没有独立 JS 回调或通用业务数据绑定。
- Hello Runtime 提供 summary→Root、detail→Detail 两张 Card。Native 样例保留此前实现。公开 C++ 工厂、Runtime schema、错误边界与作者职责已写入开发 API。
- 默认关闭的 CONFIG_ESPOCKET_M8_CARD_SAMPLE_TEST 只在持久 Developer Mode On、成功恢复的 Card 配置为空时设置 RAM 样例序列；既有配置/坏存储不覆盖。卸载、声明更新及 System 重启不把样例写入 NVS；显式 configure_cards 成功后才成为用户配置。这不是 Card 编辑器。

## 自动验证

- 最终全仓主机检查：43 项 unittest、M2 parser 与 Markdown 通过；新增记录后的独立文档检查为 171 个 Markdown 文件。新增测试执行生产声明 codec、模型、CardSession、Registry 和 Navigator，并解析实际 Runtime 样例资源；覆盖身份/目标、错误声明、刷新失败、暂停、Root/Detail 与重新打开 Root。
- 官方 App Toolkit 1.0.1 的 npm run build 通过，输出 espocket.app.hello_runtime.debug.0.1.0.bpk，SHA256 为 5f89fd647c6523c47b79ad5ff8b86a588848afb175352a64676ac2b814e08f88。固件 LittleFS staging 从样例源码生成，navigation.json 与 cards.json 均已逐字节核对一致；不将 debug package 视为签名分发通过。
- 默认关闭样例入口的普通 ESP-IDF 6.0.1 完整编译/链接通过；显式 reconfigure 后再次构建通过，新开关已登记为关闭。App binary 0x5f2410，App partition 42% 空闲。
- 样例入口启用分支使用真实 build compile_commands 的 Xtensa 命令交叉编译 system_cards.cpp 通过；不是启用配置的整机链接或已刷写镜像。
- 原始日志保留本地 /private/tmp/espocket-card-final-check.log、espocket-declarative-card-package.log、espocket-declarative-card-latest-build.log、espocket-card-reconfigured-build.log、espocket-card-samples-enabled-compile.log。

## 设备与剩余条件

本轮未刷写，未执行真实显示、触控、息屏恢复或物理 PWR。设备仍保留既有 013 smoke 镜像；等待已有单次 smoke 回复，不重复要求十轮验证。

后续在明确的样例测试镜像上，每条 Native/Runtime 物理路径只做一次：summary 打开 Root；detail 打开 Detail 后 Back 回 Root、PWR 回表盘；Card 离屏/息屏再显示。合成输入报告不能替代视觉或 GPIO 条件，通用导航证据仍引用 008/03。

014/03 的真实 Runtime package replacement 仍缺 Core 更新事务/原因 seam，005/03 依赖保持。014/05 的更新迁移和设备条件未勾选，整票不关闭。本实现解除此前 Runtime Card 首版范围待答复，独立 JS 业务回调仅作为未来扩展。

- 未刷写产物 espocket.bin SHA256：8526873498ec11ef4746a142ecc8a520882887d3aa284d9c53f06ea43c97cfcf。

- 未刷写产物 espocket.elf SHA256：de1d41337910bce05925aef7594e96104e86e1a8cbf996d268c2d4365db7890c。

- 未刷写产物 littlefs_data.bin SHA256：1c8ae48c7d11e014e31656a66c27ae0925d604c3ac787895c4488a3380333aeb。
