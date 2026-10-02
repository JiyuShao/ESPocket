# Card Owner、持久配置与 Native 呈现接入

Date: 2026-10-02
Scope: 014/03 source slice；Native Card 参考提供者属于 014/05 的部分实现。

## 实现事实

- System 在真实 Native/Runtime 安装时登记同一 CardRegistry，真实卸载时移除并记录原因。停止后的 Native 声明更新保留稳定 ID/顺序，只删除消失的 Card。
- 配置 codec/schema v1 和 NVS Store 完整验证身份、重复、未知字段及大小。用户提交完整左右候选；先保存再发布，失败保留现有配置。启动在 package 安装后恢复；未知身份或坏存储保留原 NVS 并报告。
- System 的 CardSession 接 Shell 左右序列；Card 横滑由 Home Space 处理，纵向交互保留内容。离屏/息屏取消 GUI 订阅并暂停，再次显示重新订阅和请求数据；打开完整 App 前暂停。
- CardDocument 使用官方 SystemGuiAccess 加载并挂载独立文档。原始 GUI 回调只入有期限/代际约束的队列，Owner 校验可见状态、前台身份和代际后执行模型动作。迟到点击不能操作新槽位。
- Native Hello 声明 summary→Root、detail→Detail，内容由自己的 manifest 提供。目标 Page 通过同一 Navigator 建立在 Root 之上；目标不可提交时记录错误，不伪报 GUI 已经回 Root。
- C++ CardModel/CardUi/Factory 与 configure_cards 开发边界已记录。没有 Card 编辑器，没有自动覆盖用户 NVS 或自动配置全部声明。

## 自动验证

- 全仓 host checks：42 项 unittest、M2 parser 与 Markdown 通过。新增覆盖存储失败原子性、坏编码/未知身份、模型动作、重入拒绝、暂停拒绝、文档释放、订阅释放、GUI 只入队及每次 show 的新代际。
- ESP-IDF 6.0.1 完整编译/链接通过，普通配置所有 reclaim 开关关闭。大小 0x5ef090，App partition 42% 空闲。
- BIN SHA256：d7d0b7c124bd3af8dcea9d2c36c9aa1139daa3105a3f02fd0bcdf782c4b278e6。
- ELF SHA256：49f6807287802dd35b58192e7da9ee0510287c99cd707fab8f92c3a4b23c5dc5。
- 原始日志：本地主机 /private/tmp/espocket-card-reclaim-host-check.log、espocket-card-reclaim-final-build.log。与 008/02 共用本次未刷写镜像。

## 真实剩余项

Runtime package update 在 Core 0.8.4 中调用 uninstall/install；AppInfo 不带 replacement 原因或事务 ID。因此目前只能处理普通卸载，不能保证替换保留仍存在的 Card 配置或把卸载原因伪报为 RemovedByUpdate。Native 显式声明更新已覆盖。统一可信安装/更新入口仍受 005/03 的上游 seam 约束，不能修改 managed_components 或推测两次相邻事件就是更新。

Runtime Card 尚无提供者。检查锁定版 Runtime::init/deinit 和 JS Backend 后确认：注册表返回共享 backend；JS Backend 构造私有且 get_instance 为单例。另建 Runtime 会配置相同 backend，deinit 也会清理它。不能以“独立 Runtime 对象”声称已隔离 Card。Core 未公开供未启动 App 的专用 Card JS 实例调用接口。后续可以评估声明式 Card 内容入口，但它不自动等价于可执行 JS Card 生命周期/轻量业务动作，不能未经明确接口定义就声称已完成。

未刷写设备、未执行实际显示/触控/恢复/目标打开；014/05 的硬件项、013 smoke 和 008/03 不因本记录勾选。
