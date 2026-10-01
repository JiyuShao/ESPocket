# Native 声明安装与生命周期收尾

- 日期：2026-10-02
- 范围：014/01 Native 安装边界、014/02 组件分发条件

## 实现

Hello 与 Store 共用 `System::install_navigated_app`，无 App 名称专用校验分支。先核对 Manifest/App 身份、校验 Root/Page/Card，才调用 Core 安装。失败不发布 Navigator；成功返回 Core App ID 与 Navigator，由 System 注册，App 只保存弱引用。

注册表查找与写入受锁保护，卸载移除注册后在锁外停止 Navigator、解除系统 availability 回调、清除前台身份。System deinit 同样停止和解除所有回调，外部保留共享 Navigator 也不能回调已销毁的 System。非前台 Navigator 不更新当前 Back UI。开始/停止/失败仍调用同一 Navigator；息屏不停止栈，PWR Home 使用既有 System 路径停止任务。

停止态声明更新与稳定身份的组件验证见 [夜间记录](../../013-firmware-structure-refactor/records/2026-10-02-overnight-frontier.md)。软件包更新、Runtime 绑定和 Card 配置清理分别由后续工作项持有，不新增 Native 在线软件包安装机制。

## 证据

- 真实 `native_page_installation.cpp` 与 `page_navigator.cpp` 主机行为测试通过：空 App、身份不匹配、缺 Root、Card 目标缺失均未调用 Core 安装；Core 失败透传；成功 ID/同一 Navigator；停止使旧页面与待决 token 失效。
- 统一 host 检查通过：16 项 unittest、M2 parser、Markdown。Navigator 包括停止态声明更新、未知/删除目标、Root、呈现失败、待决/重复/超时/迟到 Back、AppOwned 与标准控件去重；Settings Adapter 保留已锁定例外。
- Native Root/Detail、默认按钮、Edge Back、PWR Home、息屏恢复的既有用户观察见 [样机记录](2026-10-02-default-back-prototype.md)；Settings Edge Back 与 App 自主呈现观察见 [Settings 记录](2026-10-02-settings-adapter.md)。这些不是本轮新镜像的物理测试结果。
- 本轮固件构建结果追加到夜间记录；未刷写，设备保持 013 待验收镜像。

## 门槛归属

014/01–02 持有共同核心、Native 接入与组件分发条件。完整 Runtime/Native 待决确认 UI 样例归 014/04；Card 注册和配置归 014/03；物理触控/PWR/恢复/回收与全量 M7/M8 验收归各自硬件 tickets。013/04、06 的集中 smoke 继续等待用户，不由本记录替代。
