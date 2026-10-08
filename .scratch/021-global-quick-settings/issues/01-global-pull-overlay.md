# 01 — 全局顶部下拉与临时覆盖

**What to build:** 用户要求任何页面／场景下拉打开 Quick Settings。正常亮屏页面保留顶部边缘入口，普通内容滚动仍由原 Owner 处理；关闭临时覆盖恢复原页面。

**Blocked by:** 单个阻塞启动阶段的响应缺口；设备不在用户身边，真实触摸、原 App 状态及非 GUI 显示验收待设备返回。

**Status:** ready-for-agent

## Acceptance

- [x] App、Launcher、Card、键盘、Dialog 和 Loading 的顶部下拉共用 Release 提交，短滑／取消／息屏不补发。
- [x] Quick Settings 独立 SystemTop flow；关闭不导航 Home、不重启 App、不改 Page 栈。
- [x] Keyboard 草稿保持，隐藏确认不能提交；原请求失效不能恢复，超时不因面板延长。
- [x] 非 GUI 路由临时切到 GUI，Owner token 与 current／target source ID 原子检查；同名重注册、更新 Owner 与失败均有回归。
- [x] 主机统一检查、Markdown 与完整产品构建通过，保留输入与镜像证据。
- [ ] 启动 Loading 后单个阻塞阶段仍可及时处理顶部下拉；023 已释放 GUI 等待，阶段内阻塞尚不能满足。
- [ ] 真机从 Chat／Settings 子页／Launcher 第 2 页／Card／Keyboard／Dialog／Loading 各 3 次打开及收起，原页面／草稿／运行实例保持。
- [ ] 真机非 GUI source 打开收起、期间 source 注销／实例结束、PWR Home／熄屏唤醒均通过，无旧 source 复活或触摸穿透。

## Comments

控件内容改版另行决定；本轮没有麦克风开关，也没有部署。设备回来后先保存当前 App 与 LittleFS，从最新备份保留更新内置 Chat 0.1.2，核对完整 immutable allowlist 后刷候选 App 与匹配的 LittleFS；不覆盖私有数据或模型。截图放在连续音频／性能窗口之后，立即 release。任何 synthetic input tick timeout 都判失败，不以布局可见替代触摸验收。

离线诊断、回归与构建证据见[实现记录](../records/2026-10-08-global-quick-settings.md)。

022 审查复现了覆盖前已排队按钮导致 Dialog deadline 被跳过的问题；本轮已修复隐藏期间 Timeout 仲裁，并补充真实方法回归。
