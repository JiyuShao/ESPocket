# CardSession 生命周期组件

- 日期：2026-10-02
- 任务：[014/03](../issues/03-card-registry-lifecycle.md)
- 起点：`56e9067`，CardRegistry 配置与迁移组件。

## 完成范围

真实 C++ CardSession 管理单个 Home Space 呈现槽位的 Empty/Paused/Visible 生命周期。App 绑定实现 CardContent 的显示、同步刷新、暂停与析构；Core App 实例、Page 栈和长期业务数据保持独立。

首次显示创建内容，再次可见请求新数据，重复可见 show 不重复刷新；离屏暂停可保留 UI，切换和 release/析构先暂停再销毁。打开完整 App 重新解析声明目标，暂停后调用 Launcher；失败保持暂停，由 Shell 决定重显。声明或配置失效拒绝启动并回收旧 UI。移除通知由装配 Owner 转发 invalidate，不隐式接管 Registry 的其他通知订阅。

创建、显示、刷新、启动失败均有明确返回；回调重入返回 Busy。GUI Owner 串行调用，回调不抛异常、不修改 Registry。本版不提供异步结果提交或后台驻留保证。

## 检查边界

真实 C++ 用例覆盖未配置/未知 Card、工厂失败、可见幂等、暂停恢复刷新、切换释放顺序、目标更新、先暂停再启动、失败重试、移除/更新/卸载回收、缺少通知时的启动防护、重入和析构。

尚未接 Shell GUI 容器、Core 安装/卸载、Native/Runtime Card 提供者或 NVS 配置。未刷写，不新增设备、物理或视觉 PASS；014/03 acceptance 保持开放。

`python3 scripts/check.py` 通过：32 项 unittest、M2 parser、163 个 Markdown；文档追加后再运行 `python3 scripts/docs/check.py --markdown` 通过。日志 `/private/tmp/espocket-night-card-session-check.log`。

ESP-IDF 6.0.1 编译新组件、完整链接、镜像生成和分区检查通过，日志 `/private/tmp/espocket-night-card-session-build.log`。App 大小 `0x5d6370`，分区剩余 43%。BIN SHA-256 `f63e521e096568e1656858e67248e162c615e6f36a24527e04319c11cc1099ee`；ELF SHA-256 `8abd8a41ac38874c922677c9b56992304f8bd775af2a7c5b91091a44311e498b`。组件尚未被产品装配引用，最终镜像 identity 与前一构建相同；编译通过不代表设备开始使用 CardSession。设备仍保留 013 `e8bbe74ff`，未刷写。
