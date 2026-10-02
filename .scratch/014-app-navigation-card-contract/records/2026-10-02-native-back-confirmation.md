# Native Back 确认样例

- 日期：2026-10-02
- 任务：[014/04](../issues/04-samples-api-finalization.md)
- 起点：`bf2f7dc`

## 实施

Hello Native Detail 提供确认开关、Allow Back、Cancel Back，默认 Off 维持已有 Back 路径。开启后 Back handler 只登记 Navigator 提供的 token 并返回 Defer；不持有 App 指针或页面栈，也不从 System 的 Back 回调直接更新 GUI。App 自身 action/timer 更新控件和提示。

允许/取消通过共同 complete_back，重复请求由 Navigator 拒绝。超时仍由既有 System poll 调用 expire_back，App 100ms timer 读取当前 Page/backPending，仅清理已失效的本地 token 和反馈。停止释放 timer、解绑回调、清理 flags；每次 start 使用独立确认状态，迟到旧回调不写入新运行。PWR 不经过这个确认入口。

Root 布局和 Open Detail 按钮位置不变；Detail 增加三项单列控件。控件位置源于资源，未完成视觉或触控验收。未刷写，设备仍是 013 `e8bbe74ff`。

## 验证

主机编译并执行生产 HelloApp 与实际 PageNavigator，仅替换外部 GUI/Timer 端口。覆盖默认立即返回、待决时重复 Back/切换开关拒绝、取消保留 Detail、允许回 Root、无待决拒绝、15 秒超时后迟到允许拒绝、Presenter 失败恢复 Back、stop/PWR 生命周期清理、旧 token 失效和新运行默认 Off。

Action checker 的负例从旧单独订阅写法改为当前批量订阅；新增断言确保每个负例实际修改源码，防止 fixture 静默失效。资源、订阅和 handler 仍由统一 checker 对比。

开发 API 补全四类页面的呈现、导航、Owner 和生命周期指导，并链接产品与架构权威文档。014/04 的独立指导条件完成，其他条件不随之勾选。

`python3 scripts/check.py` 通过：33 项 unittest、M2 parser、164 个 Markdown。追加记录后 `python3 scripts/docs/check.py --markdown` 再次通过。主机检查日志 `/private/tmp/espocket-night-native-confirm-complete-check.log`。

最终 ESP-IDF 6.0.1 编译、链接、镜像生成与分区检查通过，日志 `/private/tmp/espocket-night-native-confirm-final-build.log`；App 大小 `0x5d7c40`，分区剩余 43%。BIN SHA-256 `91551c8fe80ada2045e51ade4693c69b415917a59c961370ea2306bc1acc8ae7`，ELF SHA-256 `8e04cf3f7457da05e79fb4b6fcb6c91cdf66f269c7464eb37a11c773e48ca3f9`。这是未刷写镜像；若后续刷写，其 hello identity 应为 `8e04cf3f7`，不能用于判断目前设备的旧镜像身份。

Runtime 同等绑定/样例与 versioned schema 未完成，014/04 acceptance 保持开放；物理与视觉条件归 008/03。未新增设备 PASS。
