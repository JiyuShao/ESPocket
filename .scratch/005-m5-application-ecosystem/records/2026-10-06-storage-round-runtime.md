# 存储、圆屏与 Runtime 可用性验收

Recorded: 2026-10-06
Ticket: [005/12](../issues/12-storage-round-display-and-runtime-usability.md)

## 存储原因与迁移

设备 MAC `A0:F2:62:E3:0B:68`，Flash 芯片实测 GD 32 MB，PSRAM 8 MB。旧固件只声明 16 MB；LittleFS 分区总量 5,120,000 bytes、allocated 4,800,512、free 319,488。主要问题是系统少用了物理 Flash，以及 Store 成功安装后保留重复下载包；应用自己的用户文件不是这轮空间不足的主要原因。

迁移前读取完整旧 16 MiB Flash，另拆出系统区、App 和旧 LittleFS；离线扩容到 17.625 MiB，196 个非验证记录文件逐一校验摘要。只作废五个 Core 验证记录，由设备完整校验后重建；保留 NVS、原始安装包与用户文件。迁移镜像与所有写入区间经过 hash 校验。App 预算 14 MiB，位置 `0x60000`；LittleFS 起点 `0xe60000`，大小 `0x11a0000`。不能使用构建生成的空 LittleFS 覆盖设备。

Store Owner 将下载包缓存限制为 512 KiB，优先回收已安装重复版本，然后按时间回收；保护活动下载、等待开发者确认和排队操作，成功后仅删除 Store 自有下载副本。失败保留可重试包，不回收安装原包、手动导入或用户文件。Core 与 Store 使用实际文件系统容量检查下载、原包复制、解包和更新保留内容，并留 256 KiB 开销；容量未知或不足时拒绝，继续保留原版本。

安装后完整读回 LittleFS：total 18,481,152 bytes，allocated 6,336,512，free 12,144,640（11.58 MiB），315 个文件。对迁移前 201 个文件核对，193 个摘要完全相同，八个删除项全部是 Store 自有的已安装下载副本，没有修改任何原文件。Camera 缓存保留，Camera 安装目录不存在。Store 逻辑文件总量从 1,150,545 降到 154,977 bytes；剩余包含索引、图标和 Camera 下载缓存，不是重复安装原包。

当前最大的应用文件组为 Weather 1,177,357 bytes、Chronos 1,093,777、Music 730,764、2048 353,283、AI 318,279。它们包含安装原包、解压资源和用户初始文件；这些总量不能全部当作可删缓存。文件系统分配与逻辑字节不同，容量判定使用实际分配。921600 速率第一次读盘在约 81% 超时，没有产出完整文件；460800 重试 189.7 s 完整成功，失败不计为容量证明。

## 显示与性能对照

系统为未声明支持 ESPocket 的矩形 Runtime 提供圆内安全正方形 viewport：466px 屏幕使用 329px，中心偏移 68px，保持 480dp 逻辑画布。Native、Shell 与 Overlay 保留物理坐标。原包不重写，也不引入整帧离屏缓冲；底层背景为黑色。共享主题补齐官方 App 使用的六种按键／选中样式，启用小字号 Montserrat，避免 Calculator 运算符缺失或字体落到 8px。

全部对照使用同一设备与原包，CPU 均为 240 MHz；不把截图下载阶段计入活动测量。使用实际完成绘制窗口，排除启动和空闲的陈旧 FPS。

| 变更 | Launcher | Weather |
| --- | --- | --- |
| 原 Debug 编译 | 5–6 FPS，绘制约 122–150 ms | 约 1 FPS，绘制约 0.77–0.94 s |
| 性能优化编译 | 7–9 FPS，约 88–94 ms | 绘制约 0.45–0.54 s |
| 圆屏与 96/48/16 字形缓存 | 7–8 FPS，约 94–110 ms | 相同六次滚动 7–8 FPS，约 96–128 ms |
| 同样圆屏与字体，字形缓存降到 4 | 未作为 Launcher 对照 | 2–4 FPS，约 186–263 ms，单帧峰值 557 ms |

扩大字形缓存明显降低 Weather 重复字形渲染成本。96 字形试验镜像 `745dafaa0`，4 字形镜像 `5482364c6`，最终产品按字号使用 96/48/16。最终保留性能优化编译与小字体。Launcher 的软件绘制仍是主要限制，不能称已达到 30 FPS；其每帧 flush 约 16.6–17.2 ms、等待约 0.2–0.5 ms。Weather flush 约 10 ms、等待小于 0.2 ms，因此增大 SPI 传输上限不是主要收益。96 字形版 Weather root 初始化 8.222 s，总启动 9.803 s；启动延迟仍可感知。

新增真实 Service 后，第一轮 40 行双内部缓冲不能分配第二块 37,280 bytes，保留启动失败证据。中间 32 行配置能显示和安装，但普通镜像 `47ed7752b` 的 Wi-Fi 只能分配八个、而非预期十个静态 RX buffer，返回 `ESP_ERR_NO_MEM`。这属于系统内部 RAM 分配问题，不能解释成没有网络或外部凭据。

仅降低内部显示缓冲进行对照：16 行镜像 `9416a8b2f` 和 24 行镜像 `e057a53be` 均成功初始化十个 RX buffer、恢复已有 Wi-Fi 连接并取得 IP。最终选择 24 行双缓冲，每块 22,368 bytes；比 32 行释放 14,912 bytes 内部 RAM。24 行预热 Launcher 完整活动窗口为 6–7 FPS，绘制约 105–125 ms；16 行约 7 FPS／123 ms 的预热窗口之前仍有 2–4 FPS 波动。32 行的离线性能不能作为最终联网性能声明。DisplaySource 实际初始化 host seam 收紧到每块不超过 24 KiB，原 32 行配置失败，最终 24 行通过；这个预算检查不替代真实 Wi-Fi 启动。

生成 SPI 配置从 9,320 提高为 29,824，作为传输上限，构建仅接受准确匹配的配置。不改原始组件或 HAL 所有权，不盲目压缩 GUI 栈。最终固件移除临时 flush 探针并关闭性能周期日志。Calculator 冻结渲染帧已确认 C、Del、四则运算符及底部 0／小数点／等号全部位于安全 viewport；最终普通镜像上的运算与 Home 单独验收。

## 应用安装

通过真实 Store 入口、开发者兼容确认和 Core 完整事务安装，并在重启重新发现：

| App | Version | 结果 |
| --- | --- | --- |
| 2048 | 0.3.0 | 已安装 |
| AI Chatbot | 0.2.1 | 已安装；在线对话仍需激活／凭据 |
| Calculator | 0.3.0 | 已安装 |
| Chronos | 0.2.0 | 已安装 |
| Flappy Bird | 0.3.0 | 已安装 |
| Music Player | 0.2.1 | 已安装，保留原音频文件 |
| NES Emulator | 0.2.1 | 已安装；实际游戏需要 ROM |
| Weather | 0.2.0 | 已安装，滚动对照使用此原包 |

Camera 未安装。Hello Runtime 与 Native Reference App 保留。新增 NES、AgentManager、XiaoZhi、Coze 的真实组件和依赖按版本及 hash 固定；不伪造可用服务。初期 Wi-Fi 因内存失败，降低显示缓冲后实际恢复；不声称 AI 云端对话或 NES 游戏 ROM 已验收。最终普通镜像上的 App 启动与 Home 由完成条目补充。

## 证据与验证

本地中间 artifact 保存在 `/private/tmp/`，不是发布物：`espocket-pre-migration-16m-20261006.bin`、各区间摘要、`espocket-migrated-littlefs-20261006.bin.json`、迁移与恢复启动日志、32 行候选、96/4 字形对照原始日志，以及最终构建／设备回归／文件系统审计。错误点按打开 NES 的记录与熄屏拒绝输入的记录保留，不计入 Weather 性能结果。

统一检查此前通过全部 Owner suites 与 146 个跨模块 host tests；默认 Python 缺少 LittleFS 的一个用例跳过，另使用实际 LittleFS 环境运行迁移测试通过。最终构建、镜像身份、设备操作与安装后容量由完成条目补充。USB 合成输入和冻结渲染帧不证明物理手指或 panel 手势体验。

中间普通镜像的 navigation 与 surfaces 套件通过；apps 套件在 Native Detail 步骤失败，串口同时明确记录实体 PWR 202 ms 操作，不能计为纯自动回归通过。16 行候选第一次 App 写入在约 20% 中断，保留退出码 120 的日志；恢复重刷后 hash 验证与启动通过。最终验收重新运行，不能复用这些失败为通过证据。

## 大型 GUI 初始化根因

普通镜像 `8a2a08dfb` 已恢复 Wi-Fi，2048、AI Chatbot、Calculator 启动与 Home 通过；Chronos 启动期间快照多次 `invalid_state`，稍后实际出现前台 Clock。第二轮重开在 uptime 412449 ms 触发 `IDLE0` Task Watchdog，CPU0 正在执行 `System2`。此后排队的其它 App 没有完成可靠验收，不能把这些脚本失败认定为各 App 分别闪退。

用该镜像匹配的 ELF 解码回溯，实际链路为 `create_subtree → apply_props → apply_common_transform → lv_obj_update_layout → layout_update_core`。GUI LVGL 0.8.5 每创建或更新一个普通节点都强制排版整棵增长中的对象树，构成大型界面的重复工作；并非 Clock 的包成员拒绝或服务缺失。

独立补丁 `005-defer-transform-pivot-layout.patch` 在真实 GUI Owner 中使用 LVGL 自带的百分比 pivot 编码，保留固定 pivot、缩放、旋转与恢复操作，尺寸变化时由 LVGL 当前对象尺寸解析，取消提前读取宽高与强制整树排版。回归调用真实 `apply_common_transform` 和锁定 LVGL 的百分比 helper：3000 个普通节点原版失败，修复后零次强制排版；同时覆盖百分比中心、固定中心、缩放下界、旋转和回到 identity。没有增大看门狗时限，也没有修改官方 App 原包。

联网 Weather 的 24 行对照中，六次滚动全部收到 ACK，预报通过证书校验并打印 `forecast updated`，活动窗口 4–6 FPS，约 138–187 ms；最终 snapshot 的 USB response write failed，release 成功，整次脚本仍记录 FAIL。后续尝试开始时 Weather 已不在前台，不计为其预热性能。大型 GUI 修复后的最终普通镜像另做启动、运行和 Home 验收。

仅修复 transform 的普通镜像 `a9fe650f9` 仍在 Chronos 初始化期间触发 Watchdog。匹配 ELF 回溯显示 `create_subtree → apply_layout → refresh_relative_placements → get_record_placement`：Shell 已有相对锚点，使每个新节点都扫描所有 records 并两次排版所有已知层。第二个独立补丁 `006-batch-relative-layout-at-gui-owner.patch` 复用 Core 已有 GUI ThreadGuard，在最外层 GUI 操作结束、仍持有 LVGL 锁时统一刷新；嵌套操作不提前刷新，同步坐标读取及滚动操作先刷新待处理锚点。直接调用没有批次 guard 时保持立即更新。

新增回归调用实际 ThreadGuard、apply_layout、get_node_frame 和 relative refresh 编排：3000 次更新原版失败，修复后仅一次刷新／两次已知层排版；覆盖嵌套 guard、相对目标新坐标、操作中同步读取、无效节点、目标删除及异常退出释放锁。既有图像偏移回归仍确认纯像素滚动不申请锚点重排。真机启动验收待补充。

## 最终普通镜像验收

最终普通镜像 `69edbcc15`，ELF SHA256 `69edbcc1510620253aeb278ff914a0082d39a6cc90b76ee69834b1a411884155`，BIN SHA256 `2d8c4d0d905eb50be65d31b27021badac656c674e1c0caf38de61743753775d8`。App-only 写入 `0x60000`，写入后 hash 验证通过；没有写入空文件系统。Wi-Fi 成功分配十个 RX buffer 并连接已有网络。性能周期日志及临时探针关闭。

`espocket-round-batch-apps` 逐一通过全部八个非 Camera App 的启动、前台身份、唤醒、Home 和 Watch Face 恢复；日志无 Task Watchdog、panic 或栈溢出。最终普通镜像打印的实际启动时间如下，包含资源加载与 Runtime 启动，不是绘制 FPS：

| App | 启动时间 |
| --- | --- |
| 2048 | 2.512 s |
| AI Chatbot | 3.379 s |
| Calculator | 1.590 s |
| Chronos | 12.289 s |
| Flappy Bird | 2.754 s |
| Music Player | 2.086 s |
| NES Emulator | 2.552 s |
| Weather | 6.554 s |

Chronos 已不再触发先前的 GUI 初始化 Watchdog，但首次启动仍明显慢，不能宣称瞬时打开。Weather 首次启动由原 Debug 基线 12.722 s 降到 6.554 s；最终镜像实际打印 `forecast updated`。退出时取消尚在进行的空气质量请求，HTTP 关闭阶段的连接取消日志不计作 Weather 崩溃。AI 云端激活与 NES ROM 的外部条件保持原说明。

Calculator 最终真机输入 C、0、7、9、Del、+、8、=，截图显示 `7+8=` 与 `15`，四角 C／Del／0／= 均可见、可点；返回 Home 通过。截图 `espocket-round-batch-calculator-15.png`。同一镜像的 `espocket-round-batch-final-device-suites` 中 apps、navigation、surfaces 全部 PASS，覆盖 Native/Runtime 的立即 Back、等待确认、重复 Back、取消、允许、超时、熄屏唤醒、Home、重开，以及 Shell/系统表面坐标。没有复用此前受物理 PWR 干扰的失败结果。

最终统一检查全部 Owner suites 与 148 个跨模块 host tests 通过；默认 Python 缺少 LittleFS 的一个测试跳过，实际 LittleFS 环境的迁移回归另已通过。Markdown 检查 276 文件通过。完整构建 App 二进制 `0xa2b450` bytes，14 MiB App 分区剩余 27%。精确输入证明重新从原始组件与版本化补丁生成 14 个组件，选中构建目录的全文件 inventory 完全一致；106 个产品文件摘要一致。`patch-inputs.json` SHA256 `18902e5747b5b5d919614bd3417eecd45ec83ce3f0e3175192a6b8974b0f9d10`，registry、32 MiB 分区、性能编译、字体、音频和关闭探针设置通过验证。最终 GUI 初始化优化后的 FPS 未重新采样，不把中间候选 FPS 当作最终镜像新测量。

最终 `espocket-round-batch-weather-scroll` 使用原 Weather，六次纵向滚动全部 ACK，滚动后前台与亮屏断言、截图、Home 通过。截图从当前温度／逐小时预报移动到紫外线、风、湿度、能见度、气压和日出日落卡片，证实内容实际发生滚动，不只检查输入响应；安全区域内可见。上游页脚仍带演示数据标记，这轮没有声称全部气象字段的实时准确性。截图下载与操作验收不作为 FPS 样本。
