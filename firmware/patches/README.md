# 上游源码补丁

本目录保存已经接受的上游源码修改。自有兼容头文件与编译适配放在[compat](../compat/README.md)；managed_components 是依赖解析产物，不手工修改。

## 当前清单

已接受 [Runtime JS 0.8.3 异步栈配置补丁](espressif__brookesia_runtime_js/0.8.3/001-configure-async-stack.patch)，由 [ADR-0015](../../docs/adr/0015-runtime-async-stack-patch-exception.md)限定授权。manifest 锁定完整原始源码与补丁 hash，上游问题尚未提交。构建与设备验收状态以 [008/04](../../.scratch/008-m8-app-contract/issues/04-resolve-runtime-async-stack-overflow.md)为准。

Core 0.8.4 的 failed-stop、键盘 Owner 与 queued event 补丁依据 [ADR-0016](../../docs/adr/0016-maintained-upstream-fixes.md)维护；源码回归、完整构建与尚待设备门槛见 [005/07](../../.scratch/005-m5-application-ecosystem/issues/07-isolate-runtime-keyboard-results.md)。

Lib utils 0.8.2 的 [worker dispatch 公平性补丁](espressif__brookesia_lib_utils/0.8.2/001-bound-worker-dispatch.patch)限制连续 ready queue 的单轮调度并给 Idle 留运行窗口；源码与补丁 hash 由 manifest 固定。真实 worker block 的主机回归已通过，Store 安装无 watchdog 的设备门槛仍由 [005/06](../../.scratch/005-m5-application-ecosystem/issues/06-adopt-online-store-stability-fix.md)持有，证据见[生命周期记录](../../.scratch/005-m5-application-ecosystem/records/2026-10-04-launcher-and-lifecycle-acceptance.md)。

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

Display 0.8.2 的同一输出背光与刷屏 IO 串行化补丁属于 `display-candidate`，实际 API 并发回归、完整构建和 100 次纯滑块自动设备压力验证已通过，剩余实体触摸观察由 [004/08](../../.scratch/004-m4-device-capabilities/issues/08-fix-settings-brightness-freeze.md)持有；不得因主机通过宣布设备修复。

## 默认组合合入

2026-10-03 用户授权将已验收候选纳入默认产品构建。默认 `production` 组合包含 Runtime/Core、HAL HTTP 与 playback-only、Settings 圆屏布局、Display IO 串行化，以及 Board Manager I2S teardown 修复。`baseline` 保留此前 Runtime/Core 组合，其他显式 candidate 为诊断子集。Audio 补充依赖仍准确绑定相邻清单中的版本/hash，原 registry lock 不改写；生产构建同样校验 Recorder/AFE 关闭与 DAC 输出格式。此次完整构建、设备与视觉结果见 [收尾记录](../../.scratch/004-m4-device-capabilities/records/2026-10-03-production-followup.md)，未通过的门槛不能因默认值已切换而关闭。

### Store Service completion 的 App Owner 边界

Store 0.8.2 的 `004-owner-service-completions.patch` 将 Storage/Device/HTTP 异步返回与 HTTP events 的 App 状态处理移到 App timer。每个 Running Instance 持有独立 mailbox，退出先关闭并丢弃结果；重进创建新 mailbox，旧 Service callback 不能访问已停止会话。真实 cached-index 回调主机回归验证旧版 worker 访问失败、候选 Owner 交接、停止丢弃与重进隔离。移除条件为锁定上游提供等价 Owner delivery 并通过相同主机与快速 Store 退出设备回归。故障与设备判定见[应用生态验收记录](../../.scratch/005-m5-application-ecosystem/records/2026-10-04-launcher-and-lifecycle-acceptance.md)。

Store `005-avoid-local-scan-during-remote-refresh.patch` 保留 startup/Local 的扫描，远程 index Refresh 不启动重复本地扫描；真实 deferred-refresh 方法回归覆盖三个 tab。Core `006-bound-recursive-package-removal.patch` 仅将递归目录删除的等待期限设为 30 秒，stat/read 保留 5 秒，并继续核对删除后目录不存在。主机真实 filesystem helper 覆盖慢后端、超出上限、目录仍存在与空路径拒绝；设备完整删除仍需独立门槛，不把延长期限等同成功。上游提供等价边界并通过相同回归后移除。

Storage 0.8.3 的 [单次元数据读取补丁](espressif__brookesia_service_storage/0.8.3/001-read-file-metadata-once.patch) 将每条类型／时间／大小查询合并到同一次 VFS lookup，保留 file-clock 和软链接语义；Core `007-count-package-admission-in-startup.patch` 将包校验纳入真实启动计时。完整校验保留，性能设备门槛由 [005/10](../../.scratch/005-m5-application-ecosystem/issues/10-reduce-runtime-startup-blocking.md) 持有。移除条件为上游等价实现通过相同元数据语义、包信任和设备性能回归。
