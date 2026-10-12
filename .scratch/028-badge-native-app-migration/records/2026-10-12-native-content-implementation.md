# 2026-10-12 Native App 自绘与多点输入实现记录

028/10 完成首版生产 seam。变更由三个真实 Owner 持有：GUI Interface 定义 App document/container 约束、opaque mount token 和 pointer delivery；GUI LVGL 在 backend thread guard 中创建/裁剪/销毁自绘 root，并从既有 MultiTouchPointerManager 缓存投影坐标；System Core 验证 Native App、当前 document、Running/foreground 资格和产品仲裁回调。CircularShell 只发布输入取消 epoch，不新增 Input Manager。

挂载失败（分配失败、attach 返回错误、attach 抛异常）、重复挂载、旧 token、跨 Runtime/document、重复卸载和父树销毁均有 host 回归。预加载 DOM 在 App 停止时保留解析文档，但 Core 先清理 native mounts；下次 Running Instance 需重新挂载。指针在初次挂载、权限变化、Quick Settings、键盘/Dialog、系统手势、息屏和无效快照后等待新的全释放帧；旧触点不会恢复。

验证：

- `python3 -m unittest discover -s firmware/test/host -p 'test_native_*.py'`：3 passed。
- `python3 -m unittest discover -s firmware/test/host -p 'test_core_native_content.py'`：2 passed。
- 8 个实际生产源文件使用 ESP-IDF v6.0.1/目标编译数据库单独编译通过。
- 完整隔离产品构建：`/private/tmp/espocket-028-native-build-v4/candidate`，App `0xab8c70` bytes，分区余量 `0x347390`（23%）。候选 `deployed=false`、`physical_validation=false`。
- `python3 scripts/check.py`：184 tests passed，2 skipped；Markdown 349 files passed。

限制：尚未迁移七个 The-Badge App；未做真实 LVGL 画面、触摸手感、并发 worker、IMU、BLE HID 或设备验收。028/03 的 Quick Settings/息屏 on_pause/on_resume 仍是后续票；本票只提供输入撤销和 App-owned mount seam。
