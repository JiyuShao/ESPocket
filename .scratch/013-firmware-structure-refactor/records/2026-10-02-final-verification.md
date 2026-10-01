# 结构重构最终验证

- 日期：2026-10-02
- 范围：013/04、013/06
- 初始功能基线：`43159fb`

## 自动验证与边界复核

- 统一 host 入口通过：15 项 component／跨 component unittest、离线 M2 parser 和 Markdown 检查。测试从各 Owner 的 test/ 发现；C++ 行为测试执行实际源码。
- 最终完整重编译、链接和镜像大小门槛通过，镜像与 hash 见 [05 记录](2026-10-02-layout-build.md)。普通配置保持 30 秒自动息屏，M2 stress、M6 reclaim/resource 诊断关闭。
- System 26 个原有方法逐段比对一致；差异限定为组合式 ShellHost 装配、固件版本来源及新增 System 输入消费方法。Shell 26 个方法除 callback 字段名称外一致；构造、启动和 tick 的差异限定为 Host 装配与 PWR 消费位置。
- Native 与 Runtime Reference App 的源码、资源和 manifest 比对一致；保留同一 Root、Home、Display State 与 lifecycle 语义，没有新增 Semantic Registration 或第二套 Owner。内部 Host tick 保持 unexposed。
- 两个 workflow YAML 解析通过。Host CI 以同一 scripts/check.py 编排检查，显式加 --diagrams；完整 ESP-IDF build 使用独立 workflow。远端 GitHub Actions 尚未运行，不能把配置验证写成远端 CI 通过。
- Host 依赖准备与检查分开；使用 IDF Component Manager 3.0.3 读取锁定 Settings 并校验 hash。已有依赖与临时空目录的准备路径均通过，统一检查不隐式下载或改写工作区。
- 此阶段没有修改架构 SVG，未本地运行 Chrome 图检查；CI 仍保留该检查。

## 设备与待决人工检查

只写 App 分区 0x60000，写入 hash 校验通过；没有改写 NVS、LittleFS 或分区表。USB hello 返回 ok:true、image_identity:e8bbe74ff，与最终 ELF SHA-256 前九位一致。

已发出一次集中 smoke 请求：Native Detail Edge Back；自动息屏唤醒保留 Detail；PWR Home → 息屏 → Watch Face；Quick Settings 与 Launcher 的反向返回。当前尚待用户结果，不提前标记 04/06 硬件条件通过。
