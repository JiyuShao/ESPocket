# 02 — 隔离构建候选流程

**What to build:** 深化现有隔离构建入口，在成功构建与复核后自动保存完整候选和输入证明。

**Blocked by:** None.

**Status:** resolved

## Acceptance

- [x] stage 记录实际副本的产品源码、patched inventory、原始配置/lock 与输入 fingerprint。
- [x] 复核 staged immutable inputs、Registry lock 和被编译的 patched 路径；不从变化中的 checkout 重新声明输入身份。
- [x] 归档 flasher_args 全部镜像、ELF、配置、lock、补丁字节与产物 hash/bytes。
- [x] 缺失镜像、路径越界、输入漂移、prepare-only、失败不发布候选的回归通过。
- [x] 全新目录的完整 ESP-IDF 构建与自动归档通过。
- [x] 统一 host checks 与 Markdown 通过。

## Comments

候选 manifest 明确 deployed=false、physical_validation=false。LittleFS 是新文件系统产物，不能替代设备备份迁移；本票不执行刷机。

## Resolution

实现、统一 host 回归与全新隔离完整构建通过。[结果与候选 identity](../records/2026-10-08-offline-verification.md)。没有执行刷机或真机验收。
