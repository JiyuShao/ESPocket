# 2026-10-05 Runtime 卡顿的硬件／软件诊断

用户要求判断 Flappy 低 FPS 主要来自硬件能力还是软件实现。保持 Store 安装的原 BPK，不修改游戏脚本；App-only 部署隔离诊断镜像，结束后恢复普通镜像。不刷 LittleFS，不读取 NVS 或全片 Flash。

## 已复现的症状

普通零缓存 `a2df08485/render-perf/e87f2d92-70a4-4e69-a843-cb2314205a5c/report.json` 的游玩输入阶段，完整刷新完成 FPS 样本中位数 4.5，game timer 实际周期 80.19 ms（请求 33 ms），不是可玩性能。诊断断言脚本 `/private/tmp/espocket-assert-playability.py` 对该报告输出 `FAIL completed FPS median=4.5, timer period=80.19ms`。脚本的 25 FPS／40 ms 是区分症状的诊断目标，不是新增产品验收契约。

既有同机缓存 A/B 表明：不换硬件，仅试 1 MiB 缓存，PNG 解码从 12.61 降到 3.70 次/秒，绘制平均从 53.53 降到 26.96 ms，game timer 周期只降到 74.05 ms。它证明软件重复工作确实存在，但不能独自证明硬件能稳定承载整个游戏；截图内存回归导致该预算没有作为默认交付。[完整原始结果与限制](2026-10-05-runtime-startup-performance.md)继续有效。

## 可验证的四个方向

1. 显示能力限制：简单原生全屏色块也慢，且刷屏提交／等待耗时占主要部分。
2. PNG 和软件重绘：原生色块快，原包场景慢；缓存对照降低解码／绘制。
3. GUI 调用与锁竞争：GUI 线程等 LVGL lock、控件更新与布局处理耗时大，App timer 被合并或等待。
4. timer 调度：不处理游戏逻辑的相同 33 ms Core timer 也明显迟到；若空回调准时，则重点在实际工作负载。

## 实验边界与源码核查

设备显示配置为 466 × 466 RGB565、CO5300、40 MHz quad_mode QSPI，CPU 240 MHz。单帧 434,312 bytes，理想四线有效载荷传输下限约 21.72 ms；这是忽略命令、调度与渲染的理论下限，不能当作实测 FPS。普通配置 LVGL task priority 6／core 0、Core worker priority 10、worker poll interval 2 ms，LVGL 最小休眠 5 ms；没有发现固定 200 ms 刷新周期或低频 CPU 配置。

锁定源码路径：Core GUI group pre-execute 取得 GUI thread guard；LVGL backend guard 等待 `esp_lv_adapter_lock(-1)`，与 LVGL timer handler／绘制共享锁。`BackendImpl::apply_props` 每次调用 `refresh_relative_placements`；有相对目标时扫描全部 records 并更新 known layer layouts。Flappy 原资源的 score 使用相对布局，tick 更新背景／草地 offset 与鸟／管道位置。源码关系仅作为待测方向，不以它替代运行证据。

诊断 overlay 只在 `/private/tmp/espocket-m5-direct-final` 的隔离工程和 `/private/tmp` 外部头文件中；记录七个显式输入摘要，普通 checkout 不插入临时原生动画。简单小色块与全屏色块均走同一 LVGL → Display Service → HAL → LCD 路径，交替各两次、每段约三秒，请求 LVGL timer 16 ms，绕过 JS／PNG／App GUI。同机还运行 33 ms Core Native 空回调，完成后取消。统计包含绘制、部分 flush 像素、提交耗时和等待传输的耗时；adapter FPS 仍是完整末次 flush 完成统计，不是面板光学测量。

Flappy 在同一诊断镜像上测量 GUI lock 等待、属性更新和相对布局时间、flush 提交与等待。wait 总时长可能来自多个调用线程，不能直接解释为单核占用率；绘制总时长包含部分 flush 提交／等待，不能把重叠项相加。完整且至少 1.5 秒的正常窗口才进入比较；开始／跳跃有实际 ExecuteBatch 证据，截图不进入性能窗口。

## 真机结果

最终诊断镜像 `ad7a4a27e`，ELF SHA256 `ad7a4a27e6d01e503f20e4a9fd7b2f712356733a56db3b4bae2ee7598f32e91f`，BIN SHA256 `322077964ddd31476edb5edc34423f20f6bdee540d2c0c47c857dc5dcd8f8acf`。九个准确补丁 inventory、187 项产品源码检查点加七项显式 overlay、已部署 built-in 摘要、配置和内嵌 ELF 摘要核对通过；完整构建、仅写 `0x60000` App 分区的刷写摘要与启动 hello 通过。镜像只用于诊断，未改变 Store 原 BPK。

### 同一路径的原生绘制

连续受控重启采集 `native-benchmark/23454094-7de0-4b48-a8eb-41ae569d0028/report.json` 四段完整统计通过。每种场景交替测两段约三秒：

| 场景 | 完整刷新完成 FPS | 每次绘制平均 | flush 提交平均／帧 | 实际 timer 周期 | 提交像素／帧 |
|---|---|---|---|---|---|
| 30 × 30 小块移动，第一段 | 49 | 3.89 ms | 1.08 ms | 20.70 ms | 2,516 |
| 466 × 466 全屏变色，第一段 | 15 | 56.99 ms | 29.57 ms | 64.61 ms | 217,156 |
| 小块移动，第二段 | 48 | 3.99 ms | 1.16 ms | 20.70 ms | 2,560 |
| 全屏变色，第二段 | 15 | 56.20 ms | 29.64 ms | 63.49 ms | 217,156 |

全屏每帧分 12 次 flush。LVGL 独立的 flush wait 事件平均仅 0.15–0.17 ms／帧，但不能据此宣称传输几乎无成本：custom flush → Display Service → HAL → SPI 提交路径自身可能阻塞；其提交耗时已达约 29.6 ms，且包含在绘制总时间内。当前实验没有绕过渲染与 Service 单独测量裸 LCD DMA，所以 15 FPS 是当前显示实现的实测能力，不是芯片或面板的不可优化极限。

### 空 timer 与原包

早期镜像 `6b7eaa725` 未启动原生动画时的空 timer 统计保留为轻负载对照，报告 `native-benchmark/6f50d6e4-4055-4a7a-8b01-8384f11216e8/report.json` 的原生实验本身为 FAIL，不能整体写成通过。其 682 次空回调的实际周期 35.37 ms（请求 33 ms），平均 wake 2.27 ms、Owner queue 2.00 ms、callback 0.094 ms。最终镜像同时做原生刷新时，空 timer 部分窗口升到约 39 ms，说明 GUI 重负载会影响共用调度；不能把这一组当作纯空载。

原生四段完成、临时 widget／LVGL timer 删除、空 Core timer 取消后，在同一 `ad7a4a27e` 测两轮原 Flappy。证据 `render-perf/80f89047-fa82-4721-b662-363c343a5a34/report.json`：输入序列、日志采集和 Home 返回通过，两轮实际 jump ExecuteBatch 分别 7／6 次。整次统计 PNG open／success 为 398／398，无解码失败；89 次启动 snapshot `invalid_state` 重试全部保留，采集通过不代表没有启动阻塞。

游玩输入标记内，12 个完整窗口累计 24.92 秒、151 次绘制：

| 指标 | 实测 |
|---|---|
| 完整刷新完成 FPS 样本中位数 | 6（普通零缓存既有对照为 4.5） |
| 绘制平均／最大 | 52.30／226.84 ms |
| PNG 解码 | 12.16 次／秒；单次平均 18.14 ms；约 2 次／绘制 |
| PNG 累计／绘制累计 | 5.50／7.90 秒；两项有重叠，不相加 |
| flush 提交平均／帧 | 1.74 ms |
| flush 提交像素平均／帧 | 11,617，约全屏像素的 5.35% |
| GUI lock 等待 | 1,185 次取锁累计 6.24 秒；平均 5.26 ms，最大 227.21 ms |
| 属性更新 | 334 次累计 865 ms；平均 2.59 ms，最大 8.83 ms |
| 属性更新中的相对布局刷新 | 累计 452 ms；平均 1.35 ms／属性更新 |
| game timer 实际周期 | 83.02 ms（请求 33 ms），约 12.05 Hz |
| game timer 平均 wake／queue／callback | 24.75／31.55／6.69 ms；143 次 coalesced |

窗口是按主机输入阶段标记归属的聚合采样，可能跨阶段边界，也包括游戏开始／死亡后的页面状态；没有单独断言每个窗口都持续存活。因此不把 6 FPS 与旧 4.5 FPS 的差别宣称为优化收益。此次目标是成本分解，原包和默认缓存预算均未改变。GUI lock 统计是全局调用者累计；不能把 6.24 秒直接算成某一个线程的 CPU 占用，或仅凭相关性把全部 timer 排队时间归给该锁。

## 诊断结论与后续顺序

原包 4–6 FPS 的主要可见成本在软件解码／绘制以及由重负载引起的锁等待和调度延迟；未发现要求换设备的硬件故障证据。依据是同机小范围原生刷新达到 48–49 FPS，而 Flappy 平均绘制 52 ms、flush 提交仅约 1.7 ms，重复 PNG 解码累计成本很高，轻负载 33 ms timer 也能接近目标。属性／相对布局刷新有额外成本，但此次量级不足以单独解释整个掉帧，不能将它认定为唯一根因。

硬件带宽和当前显示软件路径仍是约束：全屏原生刷新实测只有 15 FPS。保持频繁全屏复杂重绘时，不能承诺仅开启 PNG 缓存便稳定 30 FPS；也不能把这一结果说成硬件只能跑 15 FPS。未做裸 DMA／光学面板测试，不能彻底排除全部硬件异常。此次完成的是诊断，不是可玩性修复，原症状仍存在。

10 持有后续性能工作，建议按以下顺序继续，每一步都用同一原包、无截图窗口与输入证据做 A/B：

1. 优先减少 PNG 重复解码；采用有界缓存前必须解决并复测既有截图连续内存回归，不能直接交付已失败的 1 MiB 默认预算。
2. 减少无效 GUI 属性更新、背景变化引起的大面积重绘与冗余布局；分别测 dirty area、渲染和 queue，保留 App 生命周期与输入期限。
3. 单独分解全屏纯色的绘制／字节交换／Service／SPI 提交成本，再对显示缓冲和并行传输做单变量实验。稳定完成这些之后才评估是否需要更高硬件配置。

## 失败保留与恢复

- 第一版 `6b7eaa725` 没有原生样本；当时未记录队列／timer 创建状态，内存分配失败只是推测，不作确定归因。第二版缩小队列并加创建日志，最终日志确认 queue／timer 都成功。
- 第二版首次切换串口的采集 `d18b6b44-71ca-4caa-91a0-c55421a0f534` 只取得两段，判定 FAIL；连续重启采集避免漏收日志，取得四段 PASS。中间一次采集器把预期 ROM 重启标记作为异常，留下 `6fa03f50-61bb-4c4a-86fe-9fb8fd12c9aa/serial.log`；修正采集器的预期启动阶段后重测，不把工具错误当成设备故障。
- 完成后 App-only 恢复普通零缓存 `a2df08485`，hello、Watch Face 点亮、无活动 App、inputBusy=false 通过。证据 `a2df08485/reflash/33eb9415-04d0-4362-a60c-3c22b8dbe669/first-boot.json`；未刷 LittleFS、未读取 NVS／全片 Flash。
- 临时 GUI／System／RenderProbe／Core timer overlay 已从隔离工程移除；187 项源码摘要、九个准确补丁 inventory 与两个 managed GUI 原文件核对通过。临时外部头已归档到明确的诊断目录并移除，证据 `ad7a4a27e/overlay-cleanup.json`。隔离 build 输出仍是诊断镜像，未来部署前必须重新普通构建和核对，不能复用这一 ELF。
- 原始报告、失败日志与诊断镜像保存于 `/private/tmp/espocket-m5-diagnostic-ad7a4a27e`；恢复汇总 `restoration.json`。本轮未把实验 overlay 写入普通 checkout 的 firmware 源码。
