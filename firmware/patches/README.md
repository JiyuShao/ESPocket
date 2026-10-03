# 上游源码补丁

本目录保存已经接受的上游源码修改。自有兼容头文件与编译适配放在[compat](../compat/README.md)；managed_components 是依赖解析产物，不手工修改。

## 当前清单

已接受 [Runtime JS 0.8.3 异步栈配置补丁](espressif__brookesia_runtime_js/0.8.3/001-configure-async-stack.patch)，由 [ADR-0015](../../docs/adr/0015-runtime-async-stack-patch-exception.md)限定授权。manifest 锁定完整原始源码与补丁 hash，上游问题尚未提交。构建与设备验收状态以 [008/04](../../.scratch/008-m8-app-contract/issues/04-resolve-runtime-async-stack-overflow.md)为准。

Core 0.8.4 的 failed-stop、键盘 Owner 与 queued event 补丁依据 [ADR-0016](../../docs/adr/0016-maintained-upstream-fixes.md)维护；源码回归、完整构建与尚待设备门槛见 [005/07](../../.scratch/005-m5-application-ecosystem/issues/07-isolate-runtime-keyboard-results.md)。

HAL 0.8.4 的 HTTP cooperative cancel 与 playback-only 差异当前属于候选，尚不在默认产品构建清单；状态分别见 [005/06](../../.scratch/005-m5-application-ecosystem/issues/06-adopt-online-store-stability-fix.md)与 [004/04](../../.scratch/004-m4-device-capabilities/issues/04-adopt-playback-only-audio.md)。

Core 的 embedded-theme GUI task seam 与 Settings 0.8.3 的当前圆屏内容布局候选见 [004/05](../../.scratch/004-m4-device-capabilities/issues/05-fix-settings-controls-rendering.md)。Settings 布局仅加入 audio-candidate，未采纳为默认生产补丁。

## 组织约定

```text
patches/
└── <registry-component>/
    └── <upstream-version>/
        ├── manifest.json
        ├── 001-<change>.patch
        └── 002-<change>.patch
```

例如 registry component 可使用 `espressif__brookesia_runtime_js`。采用上述布局。[独立副本准备工具](../../scripts/firmware/prepare_patched_component.py)已实现完整源码与补丁 hash 校验、准确应用及失败清理；独立构建入口为 [build_patched_firmware.py](../../scripts/firmware/build_patched_firmware.py)，使用工程副本及 Component Manager override_path，原始缓存和 lock 不参与写入。工具验证见[008 记录](../../.scratch/008-m8-app-contract/records/2026-10-03-patch-preparation-tool.md)。

manifest 记录原始组件版本、源码 commit/hash、按顺序排列的补丁文件及其 hash、上游问题/修复链接、负责验证的工作票和删除条件。未提交的问题应链接本地草稿并明确该状态。

正式应用工具应先验证上游身份，再复制到构建目录、准确应用补丁，并让构建使用该副本。版本/hash 不匹配或补丁不能准确应用时停止，不做模糊匹配；副本和中间产物不提交 Git。工具实现与 Component Manager override 的验证由实际接入工作票负责，不把这里的目标流程写成已实现。

依赖升级时一起审查版本锁、补丁适用性及对应测试/构建/真机证据；上游提供等价修复后移除本地补丁。源码差异持续扩大时，单独决定是否维护 fork，不在补丁目录内复制整套组件源码。
