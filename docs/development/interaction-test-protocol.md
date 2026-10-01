# 交互自动化测试协议（目标 v1）

本文定义主机 Test Driver 与 ESPocket Test Adapter 的开发协议语义。实施见[交互自动化工作项](../../.scratch/012-test-automation-contract/spec.md)，Owner 见[交互自动化架构](../design/architecture/08-interaction-test-seam.md)。当前源码已接入 USB 准入、`hello`、只读 `snapshot`、`stimulus.powerShort`、`stimulus.touch` 与 `release`；设备支持能力仍以其 `hello` 为准，源码构建不等于已刷写或真机通过。

## 当前 USB 帧格式

USB Serial/JTAG 上的测试帧是以 `@ESPTEST ` 开头的一行 JSON，普通串口日志没有这个前缀。请求示例：

```text
@ESPTEST {"version":1,"request_id":42,"op":"hello"}
```

响应带相同前缀，包含 `version`、`request_id`、`ok`。成功的 `hello` 还返回 `image_identity`（当前为 ESP-IDF 保存的 ELF SHA 前 9 个字符）与 `capabilities`；错误响应带 `error_code`。当前版本号为 `1`，接入当前 System 后能力列表含 `hello`、`snapshot`、`stimulus.powerShort`、`stimulus.touch`、`release`；未绑定的能力不公布。未实现的操作返回 `unsupported`；开发者模式关闭时，版本正确的命令返回 `developer_mode_off`。重叠的协议调用或未完成触摸/PWR 占用期间的新刺激返回 `busy`；两类输入使用同一槽位。帧长上限为 1024 字节，超长帧被丢弃并返回 `bad_request`。开发者模式开关位于设备 Quick Settings，默认关闭并保存到 NVS。

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

物理 USB 断开、响应写入失败、Adapter 停止和开发者模式关闭都会清理待执行 PWR。USB Serial/JTAG 的连接检测依据物理连接，不能检测线缆仍连接时主机关闭串口；Driver 应显式 `release`，未消费输入还受排队期限保护。关闭开发者模式后协议命令被拒绝，内部清理仍执行。PWR 排队同时保存导航任务 token，消费时 token 已变化则丢弃，不对新的 App 任务执行旧输入。

## 当前触摸轨迹与清理

坐标是 Display 输出的整数像素。tap 与 swipe 都使用 `points` 数组，不发送 Surface 或 Page 目标。tap 示例：

```text
@ESPTEST {"version":1,"request_id":46,"op":"stimulus.touch","points":[{"x":233,"y":233,"elapsedMs":0,"pressed":true},{"x":233,"y":233,"elapsedMs":80,"pressed":false}]}
```

swipe 至少增加一个移动中的按下点：例如从 `(233,350)` 按下，在 160 ms 移至 `(233,150)` 并保持按下，在 240 ms 于同坐标松开。轨迹有 2–16 个点，首点时间为 0 且按下，仅末点松开；末点坐标必须与前一点相同。时间是相对首点的非负整数毫秒，相邻点间隔至少 40 ms，总时长最多 2000 ms。坐标必须位于实际输出范围内。超长 JSON 仍受 1024 字节帧上限约束；点数上限不保证任意序列能装入单帧。

ACK 只表示校验后预留了共同输入槽位；worker 按时逐点调用 Display 注入，并把同一轨迹转换为 Shell 正式仲裁事件。转换读取当前 Display 的方向与边缘配置，不复制导航规则。注入期间忽略硬件 Shell 手势事件，Display override 同时覆盖 LVGL 的触摸快照；不要混用人工触摸与合成序列。物理 PWR 仍有优先权，会取消未完成触摸。

末点 release 后保留至少 40 ms，再清除 override。调度延迟不把多个点挤在一次 tick；超过声明总时长加 500 ms 则取消，不补发迟到点。App 任务 token 变化、息屏、关闭开发者模式、物理 USB 断连或响应写失败同样取消。`release` 在输入 worker 上重复安全；取消先清除 Shell 未消费 intent 和 pull 状态，并重置 LVGL 按压，再清除 Display override，避免用正常 release 提交 Launcher 返回或按钮点击。已经执行的导航和业务动作不能撤销。

清理失败返回错误并保留 inputBusy，后续 tick 或内部清理重试；Adapter 停止时最多重试五次并记录失败。Driver 不能把清理错误当成空闲，也不能忽略日志中的 tick/停止清理失败。USB API 无法检测仅关闭主机串口，仍应显式 release；轨迹绝对期限限制遗留注入。重启后旧内存序列及 override 不恢复。上述处理已接入源码，LVGL 实际点击、屏幕反馈与设备上的断连行为还需 Driver/真机证据。

## 快照契约

最小快照包含单调 `seq`、Home Space `surface`、`display` 开关状态、`foregroundAppId`，以及前台 App 的 `pageId`、`canBack`、`backPending`。无前台 App 时页面字段为空。Page ID 来自 App 安装声明和 ESPocket 唯一导航栈；测试协议不暴露页面参数、表单内容、私有控件树或整条栈。

当前请求为 `{"version":1,"request_id":43,"op":"snapshot"}`，仍使用 `@ESPTEST ` 行前缀。成功响应的 `snapshot` 对象包含上述七个字段及 `inputBusy`；后者表示 触摸序列占用、PWR 已排队或 System 正在消费，不表示页面转移已完成。布尔字段是 JSON boolean，身份是 string。`surface` 使用 `watch_face`、`launcher`、`quick_settings`、`shell.battery`、`shell.brightness`，表示 Shell 持有的 Home Space Surface；前台完整 App 存在时，它是保留的底层 Shell Surface，App 是否前台以 `foregroundAppId` 判断。无 App 时两个 ID 是空字符串，两个 Back 字段为 false。

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
