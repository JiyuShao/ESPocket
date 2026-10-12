# Native App 自绘与多点输入

此接口用于需要 LVGL 自绘的可信 Native App；普通文字、按钮和 Runtime App 继续使用既有 JSON/binding。App 保留自己的 App Root、Screen Flow 和 Page，不接管全局 screen、顶层 layer 或显示来源。实现和验收归 [028/10](../../.scratch/028-badge-native-app-migration/issues/10-native-content-and-pointer-seam.md)。

## 所有权与接口

App 的 JSON 声明一个 `Container`。App 通过 `AppContext::gui()` 使用：

- `mount_native_content(path, shared_ptr<gui::NativeContent>)`：挂载到本 App 当前 document 的已有 Container，返回不透明 `NativeContentToken`。不接受调用者指定另一个 document。
- `invoke_native_content(token, callback)`：在 GUI 调度和 backend thread guard 内访问挂载内容。失败会返回错误，不执行旧 token 的回调。
- `unmount_native_content(token)`：撤销本次挂载；重复卸载返回 false。
- `read_native_pointer_frame(token)`：读取本挂载允许接收的多点帧；App 不能自行指定准入或取消代次。

LVGL App 实现 `gui::lvgl::NativeContent`，覆盖 `attach(lv_obj_t *root)` 与 `detach() noexcept`。backend 创建、裁剪并拥有 root；App 只在 root 下创建内容，不能删除、重挂 root 或保存其地址至卸载之后。backend key 是可信 Native C++ 扩展的 ABI 约定，不是运行不可信插件的安全沙箱；首版不增加 JS 绑定。

GUI Runtime 验证当前 document、节点与 Runtime 身份，LVGL backend 持有真实挂载。token 不公开 backend handle，也不延长挂载寿命。一个内容对象只能有一份挂载，包含跨 Runtime 的重复挂载；卸载后可以重新挂载，但旧 token 不会恢复有效。

## 清理与调度

父节点销毁、document 更新或卸载沿原 GUI 生命周期清理：先移除挂载身份，再调用 detach，最后删除自绘 root 和父树。失败的 attach（包括抛出异常）也会调用 detach，释放部分创建的内容。

attach、invoke、detach 不得重入 document、节点或挂载的结构生命周期操作。detach 必须同步、幂等且不抛异常，能处理部分 attach；App 在此断开自己的事件、取消 timer，停止使用 root 的工作。需要 GUI 锁的 worker 应在 App 生命周期中先停止，不能在持有 GUI 锁的 detach 中等待它获取同一把锁。资源无法安全停止时，App 必须报告生命周期失败，不能先释放 worker 仍在使用的缓冲。

App 负责在已有 on_pause/on_resume 中暂停和恢复动画、物理工作及输入。自绘挂载不自动冻结线程；Quick Settings/息屏的生命周期接通由 [028/03](../../.scratch/028-badge-native-app-migration/issues/03-system-lifecycle-and-activity.md)持有。

## 输入语义

多点帧复用 DisplaySource 的 `MultiTouchPointerManager` 已分配的触点，不从 App 二次读取硬件，也不读取 driver_data。帧包含 `sequence`、`updated_at_ms`、`valid`、`cancelled` 与带 `track_id` 的触点；坐标相对于自绘 root，并裁掉 root 范围外的点。

Core 仅允许 Running 的当前前台 Native App 申请输入；产品的 Shell 仲裁还要求屏幕点亮、无 Quick Settings/键盘/Dialog 覆盖、无已消费系统手势或待取消输入。没有产品仲裁回调时默认拒绝。

收到取消或无效帧时，App 清空按压、拖动和待发送移动，不能把空列表当成可补发的点击。暂停期间即使 App 没有轮询，取消代次变化也会阻止旧触点恢复；重新获准后，必须观察到更新序号的全部松开帧，才接收下一次触摸。初次挂载也执行此规则。

玩法和 HID 输入使用该受控帧；不得改读原始设备快照绕过仲裁。App 自己跳过重复 sequence，动画不计为用户活动。实际 HID 发送仍需在其 Owner 核实连接、暂停和实例身份；此接口不授予后台遥控权限。

## 验证边界

Host 测试执行生产 Runtime/Core/backend 方法和输入过滤，替换 LVGL 分配、节点及调度边界；它不证明真实 LVGL 绘制、线程并发、触摸手感或 HID 行为。完整构建和真机验收分别记录，设备门槛归 [028/09](../../.scratch/028-badge-native-app-migration/issues/09-device-acceptance.md)。
