# 05 — 收敛源码、构建与生成目录

**What to build:** 将 ESPocket Native/Runtime App、构建元数据与可配置生成输入放入已确认的位置，同时保留 ESP-IDF 和工具固定目录。

**Blocked by:** 04 — 拆分 System 并收回 PWR Owner。

**Status:** resolved

- [x] Hello Native 移到 `firmware/native_apps/hello/`，Hello Runtime 移到 `firmware/runtime_apps/hello/`，manifest ID 与正式可见 Reference App 行为不变。
- [x] Native App 作为 ESP-IDF component 由 `EXTRA_COMPONENT_DIRS` 发现，并自有 `CMakeLists.txt`；System 继续显式安装它。
- [x] LittleFS 镜像根目录迁入 `firmware/build/littlefs-root/`，设备路径仍为 `/littlefs`，Runtime App 仍从 `/littlefs/apps` 加载。
- [x] `managed_components/` 与 `components/gen_bmgr_codes/` 保持工具原位且只读/生成语义明确；Runtime App 本地产物保持在各 App 内。
- [x] `Kconfig.projbuild` 收敛为 component `Kconfig`，公开依赖使用 `REQUIRES`，实现依赖使用 `PRIV_REQUIRES`。
- [x] `-Wno-error=attributes` 只作用于需要兼容的 target；固件版本来自 `PROJECT_VER`。
- [x] 每个 `compat/` 文件记录受影响版本、上游问题与删除条件。
- [x] Host checks 与固件 build 通过，旧目录和旧配置入口不再被引用。

## Resolution

2026-10-02：源码、构建元数据、依赖和 staging 目录收敛完成，源码与 manifest 比对、Host checks、完整重编译和链接通过。04 的集中 smoke 仍待最终镜像结果，没有据此关闭硬件条件。详见 [阶段记录](../records/2026-10-02-layout-build.md)。
