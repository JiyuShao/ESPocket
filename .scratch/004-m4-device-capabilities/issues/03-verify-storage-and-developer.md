# 03 — 验证 Storage 与 Developer control

**What to build:** 为剩余官方 Settings capability page 完成真机 acceptance。

**Blocked by:** 02 — 证明 keyboard、Wi-Fi 与 status capability。

**Status:** ready-for-human

- [x] 真机读取 Storage 信息并核对实际设备状态；记录页面可见结果、必要的串口证据和镜像 identity。
- [ ] 真机执行 Developer/debug control，核对实际控制效果、返回路径和 PWR Home；记录未验证项。
- [ ] 增加新 evidence，不修改此前已接受记录。

## Comments

2026-10-03：用户在当前 `b9b4a413f` 确认 My device Storage 显示 File system 与 Key value，已核对实际构建配置及锁定 Owner 的能力列表生成方式；此处不显示容量，不将能力清单验收冒充容量测试。官方 Debug 控件仍待观察，见[本次记录](../records/2026-10-03-storage-debug-acceptance.md)。
