# 结构重构第二阶段：GUI 资源抽离

- 日期：2026-10-02
- 范围：013/02
- 阶段前基线：`7d8e17a`

## 变更

Circular Shell 与 Hello Native 的内嵌 GUI JSON 分别移入各自的 `resources/gui.json`，C++ 通过嵌入文本符号创建 GUI descriptor。每个 Owner 保留一个权威资源。

ESP-IDF 6.0.1 按文件 basename 生成符号；直接嵌入两个同名 gui.json 会冲突。CMake 在构建目录生成不同 basename 的文本副本，再通过 EMBED_TXTFILES 嵌入，源码没有第二份 JSON。

Owner 自有测试比较 GUI 事件声明、on_start 订阅和 on_action handler 集合，保留每个事件 action 只有一个 document Owner 的检查。共享解析工具在 `scripts/firmware/gui_actions.py`，跨 component 负例证明缺少订阅、缺少 handler、额外 action 或额外 GUI 事件会被拒绝。检查器只支持当前明确的注册与处理形式；结构形式变化时需同步更新检查器。

## 验证

- 与阶段前提交比对，两个 JSON 原始字节完全一致；两个 get_manifest 方法完全一致，manifest ID、版本、可见性及 Reference App 身份未改。
- Shell JSON SHA-256：`f9211b7d599f2477013ad003668c8c324a644dcd9780191a5b1b6641e40816f0`。
- Hello JSON SHA-256：`8f322c167951e4fc21da1ac2023d31a0d056b27f4f86707a4c029cf3b5be2984`。
- Host 检查通过：Markdown、离线 parser、Shell／Hello action contract、Navigator、Settings、USB protocol 与跨 component 检查。
- 首次 CMake 配置在依赖扫描阶段因相对资源路径失败；改为 CMAKE_CURRENT_LIST_DIR 的明确路径后，完整固件构建通过。
- 实际生成的两份嵌入汇编数据均等于权威 JSON 字节加一个 NUL；符号分别为 shell_gui_json 和 hello_gui_json，完整链接通过。
- 构建目录：`/private/tmp/espocket-m78-build`；日志临时保存在 `/private/tmp/espocket-refactor-02-build.log`。
- 未运行 Chrome，未刷机，未新增真机验收通过项。没有修改 action 名称、订阅和处理逻辑，产品交互与 AI Native Exposure Decision 未改变。

## 后续

013/03 拆分 Circular Shell 私有实现并收敛 ShellHost；PWR Owner 切换由 013/04 持有。
