# Card Registry 配置与迁移组件

- 日期：2026-10-02
- Ticket：[014/03](../issues/03-card-registry-lifecycle.md)
- 范围：无 GUI 的真实生产 C++ 核心；不宣称动态 App Card 已在设备出现。

## 实现

`CardKey` 使用 appId+cardId 二元身份；CardRegistry 提供可添加声明、左右增删/跨侧移动、按最终索引排序和原子替换配置。CardSide 只允许 Left/Right，不涉及 Quick Settings 和 Launcher。目标 Page 空值解析到声明 Root，Registry 不执行导航。

PageNavigator 与 CardRegistry 共享 `validate_page_declaration`；缺 Root、重复 ID、未知 Card 目标统一拒绝。更新 Root 身份变化失败，合法声明重排/目标变化不改变用户配置的稳定 ID 与顺序。删除 Card ID 或卸载 App 会移除对应配置并通知明确原因。用户 remove 或批量替换删除配置也通知 UserRemoved。回调在提交后、锁外执行；测试从回调查询配置，验证不死锁且已删除。

## 真实组件验证

主机编译执行实际 card_registry.cpp 与 page_navigator.cpp，覆盖：同名 Card 跨 App 并存；同一身份跨侧重复拒绝；已配置的不同 Card 并存；排序/换侧；未知 App/Card、非法索引/方向；重复或未知身份批量替换的失败原子性；稳定 ID 更新/声明重排；空目标 Root；无效更新/Root 改变不影响旧配置；删除 Card 配置、卸载保留其他 App、删除原因/回调时机、用户移除不卸载声明及重复删除不通知。

- `python3 scripts/check.py`：31 项 unittest、M2 parser、Markdown 通过。
- ESP-IDF 6.0.1 最终构建、链接及分区检查通过。新增 Registry 源码已编译，但尚未从 Shell 调用，不能据此宣称界面路径已通过。

## 尚未完成

Core 安装/卸载/更新与 Registry 的连接、Shell 动态横向 Card 序列、Card 内容提供者、可见/暂停/重新请求数据、打开完整 App 时暂停及 NVS 配置持久化仍待接入。014/03 保持 ready-for-agent，不提前勾选整项 acceptance；014/04 Runtime 导航绑定仍可独立实施，014/05 Card 样例继续等待。

未刷写；设备保持 013 identity `e8bbe74ff`。没有新的设备、物理或视觉 PASS，不改变 013 smoke、007/03 或 008/03 状态。

## 最终镜像

- 日志 `/private/tmp/espocket-night-card-registry-final-build.log`；包含最终批量替换移除通知。
- App 大小 `0x5d6370`，分区剩余 43%。
- BIN SHA-256：`f63e521e096568e1656858e67248e162c615e6f36a24527e04319c11cc1099ee`。
- ELF SHA-256：`8abd8a41ac38874c922677c9b56992304f8bd775af2a7c5b91091a44311e498b`。
- 未刷写，设备 capability 和镜像不随构建目录改变。
