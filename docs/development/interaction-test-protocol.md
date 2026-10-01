# 交互自动化测试协议（目标 v1）

本文定义主机 Test Driver 与 ESPocket Test Adapter 的开发协议语义。命令入口尚未实现；实施见[交互自动化工作项](../../.scratch/012-test-automation-contract/spec.md)，Owner 见[交互自动化架构](../design/architecture/08-interaction-test-seam.md)。C++ 接口、USB 帧格式和字段拼写将在实现时发布版本化 schema；本页不把示意名称当成已可调用命令。

## 准入与传输

- 正式固件可以包含 Test Adapter。设备上的开发者模式默认关闭并持久保存；关闭时测试命令不执行。
- 首版使用 USB。开启开发者模式后无需每次连接再确认。Wi-Fi 通道以后另行设计，不改变 Owner 语义。
- Test Driver 与设备协商协议版本和能力。未知版本或命令明确失败，不尝试猜测参数。
- 同一设备一次只接受一条刺激序列；快照读取不修改产品状态。
- 主机记录镜像 identity、设备 ID、协议版本、attempt、输入类型与完整日志。原始日志不进入源码树。

## 最小命令语义

| 操作 | 参数类别 | 成功含义 | Owner |
|---|---|---|---|
| `hello` | 协议版本 | 返回固件 identity 与支持的命令能力 | Test Adapter |
| `stimulus.touch` | tap / swipe 的坐标、轨迹与时长 | 输入已送入正式输入处理入口；不表示导航已经成功 | Display / Shell |
| `stimulus.powerShort` | 无 | PWR 短按语义已送入 System；不证明 GPIO 链路 | System |
| `snapshot` | 无 | 返回同一时点的只读 Owner 状态和单调序号 | Shell / Navigator / System |
| `release` | 无 | 清除注入触摸与待消费输入；重复调用安全 | Test Adapter |

触摸序列结束、超时、失败或 USB 连接断开时都必须释放注入状态。Test Driver 发送刺激后等待快照序号前进和目标状态出现，不凭一条“输入成功”响应、固定 sleep 或日志文案判定用例 PASS。

## 快照契约

最小快照包含单调 `seq`、Home Space `surface`、`display` 开关状态、`foregroundAppId`，以及前台 App 的 `pageId`、`canBack`、`backPending`。无前台 App 时页面字段为空。Page ID 来自 App 安装声明和 ESPocket 唯一导航栈；测试协议不暴露页面参数、表单内容、私有控件树或整条栈。

Home Space 的 `surface` 至少能区分 Watch Face、Launcher、Quick Settings 和具体 Card 身份。需要验证 Launcher 顶部拉伸时，Shell 可提供只读滚动到顶和拉动阶段；这些是 Owner 的交互反馈事实，不由 Test Driver 复制。精确字段、枚举值与序列化格式在首个协议实现中定版。

## 错误与清理

协议至少区分：`developer_mode_off`、`bad_request`、`unsupported`、`busy`、`invalid_state`、`timeout` 和 `internal`。前五项不可被自动重试成成功。每次失败先 `release`，再采集最终 `snapshot` 和串口日志；再次运行作为新 attempt，保留原失败证据。设备重启、App 停止或导航任务替换后，旧刺激和旧 Back token 不得继续作用于新任务。

## 验收边界

| 证据类型 | 可证明 | 不能单独证明 |
|---|---|---|
| `synthetic-input` | LVGL、Shell、Navigator 和 System 共用的输入与导航路径 | 触摸芯片、坐标校准、PWR GPIO、实际画面 |
| `physical-input` | 真机触摸与 PWR 硬件链路 | 视觉提示是否足够清晰 |
| `visual` | 屏幕上的箭头、拉伸、Back 控件与状态信息 | 输入电气链路和内部状态转移 |

阶段验收按相应 [Milestone](../milestones/README.md) 的证据门槛判定；三类证据不能互相冒充。测试协议不注册为 Assistant 可调用能力，Assistant 的 Home、Back 和 App Action 仍使用正式语义接口。
