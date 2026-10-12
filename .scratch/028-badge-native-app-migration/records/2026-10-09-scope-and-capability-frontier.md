# 2026-10-09 — 迁移范围与接口初查

## 用户已确认

第一轮“全部同意”：以 Native App 保留 C/LVGL 代码；泡泡纸、打砖块、弹球、水池、太阳系、重力迷宫分别独立，BLE 触控板和空中鼠标组合为蓝牙遥控；中文化用户可见文字、保留原作视觉与玩法、遵守现有系统交互。

## 已观察事实及限度

- 上轮从 [上游 README](https://github.com/curisama/The-Badge) 与 [依赖文件](https://github.com/curisama/The-Badge/blob/main/main/idf_component.yml) 读取：目标为 466px ESP32-S3 圆屏，LVGL 9.5.0、ESP-IDF >=5.5，QMI8658 依赖与 PC simulator 存在，README 声明 MIT 并引用 NOTICE。尚未获取、锁定或构建具体应用源码，资源授权逐项核查未完成。
- 当前 ESPocket 依赖锁定 LVGL 9.5.0。版本匹配只降低 API 适配成本，不能证明现有 GUI public seam 已能挂载原作自绘对象。
- 当前公开 HAL include 中未找到 IMU/accelerometer/gyroscope 接口，当前产品源码未找到 QMI8658 适配。此为接口初查结果，不证明硬件缺少 IMU，也不证明上游全部版本缺少该能力。
- 现有 [BLE PeripheralIface](../../../firmware/managed_components/espressif__brookesia_hal_interface/include/brookesia/hal_interface/interfaces/bluetooth/ble/peripheral.hpp) 为单连接动态 GATT。CharacteristicConfig 仅表达 write、write_without_response、notify；实际 backend 构建特征时也只设置这些 flags，没有可配置 read value 或 HID report reference descriptor。现有接口不足以直接表达完整 HID GATT，不能仅复用 notify 就认定鼠标可用。
- 没有访问物理设备、启动蓝牙、配对主机或发送 HID。现有主线程另在修改可靠性收尾；本线仅写新的迁移文档及 tracker 入口。

## 下一轮待决

缺失能力是否可在现有真实 Owner 内新增；游戏/玩具在 Quick Settings 和息屏的暂停/恢复；蓝牙遥控离开前台、Home 和息屏的输入与连接行为。之后确认目标主机和完整验收范围。所有选择在 [01](../issues/01-confirm-migration-contract.md) 跟踪，不把尚未选择的推荐写成既定行为。

## 第二轮答复与补充事实

- 用户 Q4 追问是否硬件不支持、有无官方实现；本线不能把平台未接入当成硬件不支持。
- 从 [上游 port_esp.c](https://github.com/curisama/The-Badge/blob/main/main/port_esp.c) 读取实际代码：使用 qmi8658.h，通过 qmi8658_init、qmi8658_read_accel、qmi8658_read_gyro 等厂商 API 实现加速度和陀螺仪。原作代码报告采样启动稳定窗口，并注明声明的 gyro_dps API 缺实现，需要调用实际存在的 read_gyro；这些具体驱动/稳定窗口需在锁定源码后独立验证，不复制未测门槛。
- 当前官方 HAL Boards 的 1.75C board_info 与目标型号一致，board_devices 注册电源、音频、显示和触摸，没有 IMU。存在厂商驱动与目标板型号支持证据，但没有本次实际设备连通证明。
- 用户 Q5 明确 App 内决定暂停且可以不暂停。现有 Shell 从 Display Service connect_touch_gesture 识别系统顶部边缘下拉，Shell Owner 消费手势并通过 lv_indev_wait_release 取消后续指针序列。与游戏是否持续模拟没有必然关系，但慢 GUI callback/长锁和绕过 GUI 的原始触摸路径会破坏响应或产生并行动作；七个迁移 App 的实际竞争路径尚未实现/验证。
- 用户 Q6 接受 Quick Settings 暂停输入保留连接、Home/息屏释放按键断开，要求平台暴露能力、App 内实现策略。set_quick_settings_display 当前只处理显示路由和恢复投影，不调用 Core pause；不能用已有 on_pause 回调假定 App 已收到覆盖事件，公共状态/输入资格接口仍需核查。
- 下一轮待决目标主机、配对和恢复行为，以及音效/息屏策略。没有为这些决定修改生产代码。

## 第三轮决定与生命周期核查

- 用户“其他同意”，接受 Q7 首批 macOS/Windows、首次手动配对、打开遥控 App 尝试重连；接受 Q8 真正息屏停止动画/采样、保留状态并唤醒恢复；接受 Q9 原作短音效使用现有 Audio、遵守音量/静音、其他业务占用时跳过。
- 用户继续询问 Q6 的 on_pause 是否存在及是否为行业默认。当前 [IApp](../../../firmware/managed_components/espressif__brookesia_system_core/include/brookesia/system_core/app/iapp.hpp) 定义 on_start/on_pause/on_resume/on_stop。Core manager 的 pause_app 分发 Native on_pause 或 Runtime 生命周期，成功后设置 Paused；resume_app 回调成功后设置 Running 并选择 active_app_id。默认 IApp on_pause/on_resume 为空，不自动停止 App 自有动画/采样或冻结独立任务。
- 当前 System set_quick_settings_display 只选择 source 并记录恢复投影；set_display_on 更新屏幕和 Card 状态，未调用 pause_app。不能假设底层 App 收到了暂停事件，也不能为了复用名称在关闭 Quick Settings 时无条件 resume_app 抢回前台。
- 行业常见生命周期通知、活动/焦点变化、后台执行限制是不同概念；各平台触发规则不同。本迁移采用 ESPocket/Brookesia 的明确契约，不把某个移动平台的命名当成跨平台默认规范。
- 本轮仅更新迁移文档；具体 GUI/输入资格/息屏通知接入和实际 App 实现尚未开始，完整共同理解尚待确认。

## Quick Settings 接入方案的补充核查

- 用户询问是否把 Quick Settings 接到 on_pause/on_resume。现有 [Core timer dispatch](../../../firmware/managed_components/espressif__brookesia_system_core/src/system/timer.cpp) 明确仅在 AppState::Running 时分发 App timer，其他状态直接返回。因此 pause_app 不是单纯告知遮挡；它会阻断平台管理的 App 定时回调。App 自建线程/外部 Service 等不等于被自动冻结，前述回调说明不能扩展为所有定时器仍继续分发。
- Core resume_app 回调成功后将 active_app_id_ 指向该 App。Quick Settings 关闭必须核验原 Running Instance 与前台资格，不能为了发送恢复通知无条件调用 resume_app。
- 当前 AppContext/SystemApi/AppGuiRuntime 初查未发现现成的系统覆盖/交互资格订阅接口；普通 GUI widget focus 事件不能代表完整 App 的系统交互资格。此前建议的公共通知属于待设计接入，不是已存在能力。
- 推荐保留既有 pause/resume 语义，Quick Settings 只更新真实 Owner 提供的 App 交互资格，App 执行自身暂停输入/是否继续模拟的政策；具体公共接入形态、失效/重复覆盖/停止竞态需后续方案证明。该推荐尚待用户确认，不新增第二套生命周期或让 App 依赖 CircularShell 内部字段。

## 后续生命周期选择与游戏源码初读

- 用户继续询问“真正暂停”、系统挂起场景、为何不直接用 pause/resume、当前息屏和生命周期接入是否完整。已说明当前没有自动产品挂起入口；Core API 存在而产品触发尚未接通。用户在统一 pause/resume 方向和其游戏更新暂停的代价说明后答复“好吧，继续 grill 吧”。不再坚持新增交互通知；该答复同意继续收敛该方案，不视为完整设计最终确认或开始固件实现。
- 初读 [app_games.c](https://github.com/curisama/The-Badge/blob/main/main/apps/app_games.c)，页面文本 1764 行，包含泡泡纸、打砖块、迷宫、弹球及太阳系入口；依赖 port_imu_accel、port_tone 系列和 Launcher 方法。游戏 timer 内自行检查 launcher_screen_is_off；有 LV_EVENT_PRESSED/PRESSING/RELEASED 交互及自建状态，必须适配共同系统手势、生命周期与音频 Owner。此轮尚未锁定 commit/hash，不计可复现构建或硬件验收。
- 暂停后恢复是否自动继续、缺失/失效 IMU 的产品反馈和 BLE/Wi-Fi 共存策略属于下一轮决策。碰撞/游戏数值沿原作，源码分拆不新增全局 GameManager；实际自绘 GUI seam、上游驱动和 HID 依赖仍由本线核查，不问用户代码事实。

## 第四轮用户决定

2026-10-09：用户对 Q11–Q13 答复“都同意”。恢复同次游戏自动继续、暂停时间不累计、旧触摸状态清除；返回同次遥控 App 时尝试重连已配对电脑，连接前不发送输入、不补发暂停期间移动，失败可重试；默认保留 Wi-Fi，不复制原作关闭系统网络的无线策略。该答复确认本轮三个选择，尚不等于完整设计确认或生产代码实施。

## 遥控源码补充核查

- 读取 [app_mouse.c](https://github.com/curisama/The-Badge/blob/main/main/apps/app_mouse.c)，页面文本 1218 行；包含触控板、外圈滚动、两指手势、空中鼠标、按 peer 地址保存的五档灵敏度、主机选择入口与长按模式按钮清空配对。现有首批目标 macOS/Windows 不因原作支持手机而扩大。
- 空中鼠标有陀螺仪校准及加速度倾斜回退；传感器未就绪和完全不可用须区分。原作数值及轴向来自其测量与注释，尚未在 ESPocket 上验证。
- 原作使用 lv_timer_create 管理发送、连接轮询和按键释放；Core Paused 只跳过平台 App timer，不会自动停这些 LVGL timer。迁移必须由 App 生命周期停止/恢复实际更新来源并清理持有输入，不能只添加空回调。
- 原作通过 Launcher keep_awake 表达遥控活动，闲置三分钟允许息屏；该策略不能直接跨层调用原 Launcher。是否将实际遥控移动视为 ESPocket 活动，以及配对清除和 AI Exposure Decision 仍待用户确认。

## 第五轮用户决定与公共接口限度

2026-10-09：用户对 Q14–Q17 答复“全部同意”。IMU 不可用时保留无传感器玩法并明确提示，空中鼠标可切回触控板；配对管理通过明确入口与确认，保留主机切换和按电脑灵敏度；有效遥控输入计为活动，主动息屏仍优先；首版不新增 AI 操作接口。完整共同理解未作最后确认，本轮尚未开始生产代码。

- 再读锁定组件的 AppGuiRuntime、gui::View、gui::lvgl::Backend：公开 View 不提供 LVGL 对象句柄，LVGL Backend 也未提供按 App/View 挂载自绘子树的公开方法。Canvas 已存在，但 CanvasCommand 字段仅含 type/x/y/width/height/color，且当前 Canvas 类没有额外动态绘制 API；不能据此断言原作绘制可原样挂载或必须改写全部玩法。完整 GUI 接入核查归 02，不能取后台私有句柄、挂全局 screen 或创建第二个 GUI Runtime。
- 当前 SystemApi 提供环境、存储、生命周期请求、键盘与对话框，但本次初查未发现 App 可公开查询覆盖/息屏原因或报告非触摸活动的接口。Quick Settings 保留 BLE、息屏断开及空中鼠标保持活动须沿真实 System/Shell Owner 补齐最小 seam，不能读取 CircularShell 私有字段。
- Runtime JS 对缺少 on_pause/on_resume 的 App 补 noop。接通 Core pause 仍会停止 App timer 分发，因此现有聊天、计算器、Settings、键盘和异步回调必须作为兼容回归，不能仅验证新游戏。实际后台 Service 工作与 UI timer 分别由真实 Owner 控制。
- 上述为公开头文件和源码初查结果；完整上游 commit、许可证、GUI/HID/IMU 接入形态和原作游戏依赖清单尚待 02–05 核实。当前状态是可审阅实施方案，而非已可构建或硬件可用。
