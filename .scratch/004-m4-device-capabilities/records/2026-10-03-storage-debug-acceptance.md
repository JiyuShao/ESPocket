# 2026-10-03 — Settings Storage 与 Debug 验收

## 当前镜像

普通无 fixture Audio 修正镜像 hello `b9b4a413f`；App-only 恢复、启动与最终表盘快照证据见 [App 验收记录](../../008-m8-app-contract/records/2026-10-03-current-firmware-acceptance.md)。未新刷镜像或修改数据分区。

## Storage 页面结果

用户对 Settings → My device → Storage 信息回复“file system key value”，确认两种接口可见。锁定 Settings 的 `refresh_my_device_state` 调用真实 Device `GetCapabilities`，按接口类型分组显示；该位置是能力清单，不显示容量/剩余空间，因此不把本次观察记为容量测试。

当前独立构建配置显式启用 Storage FileSystem/LittleFS（`/littlefs`、`littlefs_data`）与 KeyValue。锁定 HAL `StorageDevice::get_interface_specs` 依据这两个开关声明相应接口，实际 KeyValue 实现为 NVS。此前真实 Runtime 从 LittleFS 加载及 Audio fixture 通过 Storage Owner 写入/删除已有独立设备证据，Developer Mode 持久存储已有验收；这些事实与本次可见接口一致，不推论未测试的任意文件/键值操作或容量。

对应采集 `/private/tmp/espocket-settings-capabilities-physical.log` 已在有限窗口后结束，只包含精确 hello/snapshot，未抓到用户查看页面，不补造串口页面结果。物理显示依据用户直接反馈。

## Debug

已请求在 My device 连点 Device name 三次进入官方 Debug，打开/关闭 GUI debug，观察布局边框，再 Edge Back 回 My device、PWR Home。结果仍待用户。新的有限监听 `/private/tmp/espocket-settings-debug-physical.log` 只读，不注入触摸/按键或开启设置；不以 Quick Settings Developer Mode 代替这项验收。
