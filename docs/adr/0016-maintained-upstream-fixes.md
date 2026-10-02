# ADR-0016: 允许维护真实 Owner 内的上游修复补丁

- Status: `accepted`
- Recorded: 2026-10-03
- Origin: 用户授权启动键盘隔离与退出清理、Store 请求取消、Audio，并明确允许 patch 修复 bug

## Decision

允许对锁定版本的 Brookesia 组件维护必要修复补丁。此决定取代 [ADR-0001](0001-espocket-is-a-product-layer-over-brookesia.md) 的普遍补丁限制及 [ADR-0015](0015-runtime-async-stack-patch-exception.md) 的授权范围限制；产品层与真实 Owner 的职责约束继续有效。[Settings 的适配决定](0012-official-settings-keeps-its-navigation-owner.md)继续有效，不能仅因为允许补丁就改写其导航事实源。

补丁按组件/版本保存在 firmware/patches，记录完整源码与补丁 hash、故障回归、工作票、上游身份及移除条件。在独立构建副本中准确应用；原始 managed_components 不手工修改。升级不匹配时停止，修复在实际 Owner 内完成，不创建第二套 Installer、权限、状态或生命周期管理器。

每个修复独立完成可复现失败、回归测试、必要完整构建及 ticket 的设备门槛，再本地提交。未验证的物理路径、正式签名与发布条件不能因 patch 可用而关闭。上游等价修复验证通过后同次审查移除补丁。
