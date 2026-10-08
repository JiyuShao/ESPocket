# 2026-10-07 — 本地 Runtime App 包与迁移准备

## 来源与归属

AI Chatbot 0.2.1 与 Calculator 0.3.0 原包来源及 SHA256 保存在各 App 的 `upstream.json`。导入包内可读 JavaScript、图片、配置示例和小智激活提示音，未取得上游完整 Git 项目，未确认原包未附带的 LICENSE；本轮不公开再发行。

使用 `espocket.app.ai_chatbot`、`espocket.app.calculator`，初版 `0.1.0`。圆屏 GUI、业务代码与导航声明属于各自 App；删除 System 的专用资源、嵌入代码、官方 ID／版本布局分支和 Core 024 GUI document override patch。通用 viewport 保留。

聊天通过既有 Navigation seam 管理唯一页面栈，Back 后同步业务状态，stop/restart 撤销旧 async completion，轮询与用户操作并行时拒绝过期页面。计算器保留原真实按键与运算逻辑。

## 本地 BPK

锁定 `@brookesia/packager` 0.1.7 构建；ZIP CRC、成员唯一性、逐文件内容与完整源码比较通过。独立 unsigned debug 包安装仍需开发者模式；内置 staging 使用显式清单与编译时不可变成员摘要，不放宽 Core gate。

| Identity | Version | Bytes | SHA256 |
|---|---|---|---|
| `espocket.app.ai_chatbot` | 0.1.0 | 86489 | `b058b0475393f071c7f4be77612f3058c24ff297d4acaf537ffda3f1ee4ced2f` |
| `espocket.app.calculator` | 0.1.0 | 12524 | `e3ad924d5194ec15fd69795d4afa3c609628aef6773e02e4e40f53a13bce4078` |

产物和逐成员验证报告位于各 App 的 `dist/`，不提交生成 BPK／node_modules。种子 AppData/AppFiles 与不可变代码分开验证；用户配置通过迁移保留。

## 验证

- 最终统一 `scripts/check.py` 全部 PASS：跨模块套件 159 项、1 项既有 skip，耗时 179.141 秒；两个 App Owner 回归及其他 Owner suites 均 PASS。两轮完整检查与最新轮询修订后的最终复验分别保留日志。Markdown 291 文件和 `git diff --check` PASS。
- 实际 GUI parser、Controller 目标和圆屏边界 PASS；计算器真实 JavaScript 动作覆盖加法、删除、除法、百分比、除零与恢复。
- 聊天真实 JavaScript 回归覆盖 push、Back、resetToRoot、重复目标、呈现失败、轮询与用户操作并行及 stale completion。
- 字形检查 PASS；实际 CMake Core allowlist、三 App staging 字节与声明资源符合源码。两个新 App 构建副本与工作区逐文件摘要一致。
- 真实 LittleFS 模拟设备验证：保留原安装、其他 App、主题与所有旧文件；旧版 data/files 同内容复制到新身份，序列化后重新挂载核对 PASS。
- 完整产品构建 PASS，镜像 identity `ad8326c75`，App 11180656 bytes。BIN SHA256 `a9595de690ddf8a30396333766af30ba383db25d7fb3c5c9006755e379e454eb`；ELF SHA256 `ad8326c7583b1d0f4b3e847335abdddba14bb905a1a37e2e0494ac78d56b2ed8`。精确补丁选择与依赖版本/hash 核对 PASS；新生成的空白 LittleFS 镜像不用于覆盖既有设备，设备部署须使用保留现有文件的迁移镜像。

## 环境失败与设备状态

首次构建因沙箱进程查询权限失败；旧仓库 sdkconfig 缺少板级配置，改用上一轮已验收完整配置。磁盘满时只清理本轮失败副本，保留旧镜像。当前独立构建为 `/private/tmp/espocket-local-runtime-20261007-v4`。

完整 Flash 读取未成功：约 6.5 MB 处数据包长度错误；重试曾因磁盘满终止，另一次约 6 MB 处设备断开。没有有效完整备份，没有改写 Flash，也未卸载旧 App。随后只读发现其他 Python 打开串口，另一个 active 聊天正在做音频修复设备测试。

用户已授权直接部署替换旧版；消息工具要求明确授权跨聊天通知，已异步询问协调或等待。部署在设备交接前不执行，避免覆盖另一线测试镜像。

## 下一步

交接串口和当前镜像身份后，完成有效备份，用 `stage_local_runtime_apps.py` 生成保留旧文件的镜像。先验证本地版，再通过 Core 卸载两个旧 Store 安装。其他 App 和远程 Catalog 保留。验收由 [02](../issues/02-device-replacement.md)持有。
