# 交互自动化测试协议（目标 v1）

本文定义主机 Test Driver 与 ESPocket Test Adapter 的开发协议语义。实施见[交互自动化工作项](../../.scratch/012-test-automation-contract/spec.md)，Owner 见[交互自动化架构](../design/architecture/08-interaction-test-seam.md)。当前源码实现 USB 准入、`hello`、只读 `snapshot`、`stimulus.powerShort` 与 `release`；触摸刺激与完整触摸清理仍是目标契约。

## 当前 USB 帧格式

USB Serial/JTAG 上的测试帧是以 `@ESPTEST ` 开头的一行 JSON，普通串口日志没有这个前缀。请求示例：

```text
@ESPTEST {"version":1,"request_id":42,"op":"hello"}
```

响应带相同前缀，包含 `version`、`request_id`、`ok`。成功的 `hello` 还返回 `image_identity`（当前为 ESP-IDF 保存的 ELF SHA 前 9 个字符）与 `capabilities`；错误响应带 `error_code`。当前版本号为 `1`，接入当前 System 后能力列表含 `hello`、`snapshot`、`stimulus.powerShort`、`release`；未绑定的能力不公布。未实现的操作返回 `unsupported`；开发者模式关闭时，版本正确的命令返回 `developer_mode_off`。重叠的协议调用或未完成 PWR 占用期间的新 PWR 返回 `busy`；触摸与 PWR 的共同序列占用仍待 ticket 02 完成。帧长上限为 1024 字节，超长帧被丢弃并返回 `bad_request`。开发者模式开关位于设备 Quick Settings，默认关闭并保存到 NVS。

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

## 当前 PWR 排队与释放

```text
@ESPTEST {"version":1,"request_id":44,"op":"stimulus.powerShort"}
@ESPTEST {"version":1,"request_id":45,"op":"release"}
```

PWR 成功响应仅表示已排队。USB worker 不直接执行导航；System 在既有 App 输入任务中调用与物理 PWR 相同的 `handle_power_short_press`。同一次 tick 同时收到物理和合成短按时合并成一次语义处理。合成输入不能证明 GPIO 链路。

PWR 槽位从排队到 Owner 调用结束保持占用。`release` 可重复取消尚未执行的输入，但不会撤销已经开始的 Owner 调用，也不会提前释放正在执行的槽位。System 消费时检查 1000 ms 排队期限，过期输入取消并记录警告，不补发迟到短按。Driver 应通过最终快照判断状态，不把 ACK 或 `inputBusy=false` 单独作为 PASS。

物理 USB 断开、响应写入失败、Adapter 停止和开发者模式关闭都会清理待执行 PWR。USB Serial/JTAG 的连接检测依据物理连接，不能检测线缆仍连接时主机关闭串口；Driver 应显式 `release`，未消费输入还受排队期限保护。关闭开发者模式后协议命令被拒绝，内部清理仍执行。触摸注入及其完整生命周期尚未接入，当前 `release` 不代表触摸清理已经实现。

## 快照契约

最小快照包含单调 `seq`、Home Space `surface`、`display` 开关状态、`foregroundAppId`，以及前台 App 的 `pageId`、`canBack`、`backPending`。无前台 App 时页面字段为空。Page ID 来自 App 安装声明和 ESPocket 唯一导航栈；测试协议不暴露页面参数、表单内容、私有控件树或整条栈。

当前请求为 `{"version":1,"request_id":43,"op":"snapshot"}`，仍使用 `@ESPTEST ` 行前缀。成功响应的 `snapshot` 对象包含上述七个字段及 `inputBusy`；后者表示 PWR 已排队或 System 正在消费，不表示页面转移已完成。布尔字段是 JSON boolean，身份是 string。`surface` 使用 `watch_face`、`launcher`、`quick_settings`、`shell.battery`、`shell.brightness`，表示 Shell 持有的 Home Space Surface；前台完整 App 存在时，它是保留的底层 Shell Surface，App 是否前台以 `foregroundAppId` 判断。无 App 时两个 ID 是空字符串，两个 Back 字段为 false。

`seq` 从 Adapter 本次启动后的 1 开始，仅成功采样递增；重启或 Adapter 重启后建立新的采样序列。Owner 读取失败、未绑定 Runtime Page 或读取期间前台/Surface/显示状态改变时返回 `invalid_state`，不伪造 Root、不带成功快照。Settings 实时通过官方 GUI 任务读取 Flow；USB worker 不从 raw GUI 回调访问它。当前源码尚未刷写，设备能力以它的 `hello` 为准。

Home Space 的 `surface` 至少能区分 Watch Face、Launcher、Quick Settings 和具体 Card 身份。需要验证 Launcher 顶部拉伸时，Shell 可提供只读滚动到顶和拉动阶段；这些是 Owner 的交互反馈事实，不由 Test Driver 复制。Launcher 滚动与拉动阶段的扩展字段仍待输入路径实现时定版。

## 错误与清理

协议至少区分：`developer_mode_off`、`bad_request`、`unsupported`、`busy`、`invalid_state`、`timeout` 和 `internal`。前五项不可被自动重试成成功。每次失败先 `release`，再采集最终 `snapshot` 和串口日志；再次运行作为新 attempt，保留原失败证据。设备重启、App 停止或导航任务替换后，旧刺激和旧 Back token 不得继续作用于新任务。

## 验收边界

| 证据类型 | 可证明 | 不能单独证明 |
|---|---|---|
| `synthetic-input` | LVGL、Shell、Navigator 和 System 共用的输入与导航路径 | 触摸芯片、坐标校准、PWR GPIO、实际画面 |
| `physical-input` | 真机触摸与 PWR 硬件链路 | 视觉提示是否足够清晰 |
| `visual` | 屏幕上的箭头、拉伸、Back 控件与状态信息 | 输入电气链路和内部状态转移 |

任务验收按 [.scratch](../../.scratch/README.md) 中对应 ticket 的证据条件判定；三类证据不能互相冒充。测试协议不注册为 Assistant 可调用能力，Assistant 的 Home、Back 和 App Action 仍使用正式语义接口。
