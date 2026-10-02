# 2026-10-03 — 独立组件补丁准备工具

## 范围

新增 `scripts/firmware/prepare_patched_component.py`。工具接受原始组件目录、manifest 和不存在的输出目录，在独立副本应用补丁。尚未接入生产构建，也未采用 Runtime 补丁。

ADR-0001 明确拒绝将 managed component patch 作为产品基线。目录维护方式的讨论不自动改写该决定；已向用户提出 Runtime JS 0.8.3 栈配置限定例外的确认。008/04 继续保留采用决策与真实设备回归门槛。

## 工具保证

- manifest schema 1；source_files 保存每个文件的相对路径与 SHA-256，包含上游 metadata 和 hash marker。不能只信任 marker。
- 完整文件清单匹配，源目录不允许符号链接；复制后再次验证，检测复制期间的源码变化。
- patches 按清单顺序应用，逐个验证 SHA-256。补丁仅支持文本文件修改；每个 hunk 的原始位置、上下文、长度及新位置必须准确匹配，不搜索偏移或模糊匹配。
- 禁止绝对路径、父目录逃逸、源目录嵌套输出、已有输出和 managed_components 内输出。
- 使用临时目录，全部成功后才发布副本；失败不留下半成品。

这只是准备能力，不包含 Component Manager override、正式版本锁或栈预算选择。准备成功不能等同完整构建或设备修复。

## 验证

8 个 host tests 覆盖成功副本、源文件改变/新增/缺失、补丁篡改、上下文错位、补丁顺序、路径/符号链接、已有输出、依赖缓存保护及失败清理。

在实际 Runtime JS 0.8.3 的 31 个文件上生成临时 manifest，应用现有栈配置提案；成功得到 `/private/tmp/espocket-runtime-stack-proposal-20261003/verified-copy`。应用前后原始组件全部文件 hash 相同。manifest 与副本仅为本地验证产物，未纳入正式补丁清单。

统一 host checks 与 Markdown 检查通过；没有改动生产 firmware 源码、资源或 CMake，也没有刷写设备。本轮不重复设备回归。
