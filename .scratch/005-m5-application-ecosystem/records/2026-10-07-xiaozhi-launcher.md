# 小智激活与 Launcher 分页验收

工作从 2026-10-06 延续至 2026-10-07，由 [13](../issues/13-xiaozhi-and-launcher-performance.md) 持有验收。复用保留用户数据、app-only 写入、完成后合并本地 main 的授权，不 push。

## 真实复现与修复

普通基线 `69edbcc15` 打开官方 AI Chatbot 0.2.1 后显示 Coze／coze.json 配置错误；缺少凭据不是崩溃。该 App 固定 800×480dp 布局，原 480dp 方形兼容画布把 Settings 入口裁掉。产品仅对该 identity／版本使用 329×197px、偏移 (68,134)、800dp 宽的居中画布，原 BPK／安装代码不改。原 presentation header 的真实挂载回归 RED，修改后通过；其它 Runtime、新版本和声明支持 ESPocket 的 App 保持各自规则。

修正画布后通过实际 UI 的 Settings → Agent 选择 XiaoZhi，AgentManager 的 SetTargetAgent 保存到 Storage。随后 Chat 页准确复现 `AudioEncoder0` 缺少 HAL encoder、Agent 服务启动失败；没有将缺失录音能力当作云端故障。Agent Manager 0.8.2 的精确补丁把 capture DataFlow 获取从服务启动移到会话启动，保留真正的 microphone 检查。真实 on_start／do_activate／do_start 主机回归比较原始／精确补丁源码：原始初始化被缺失 capture 拒绝；修正后可激活，实际会话缺少 capture 仍拒绝；具备 capture 时可启动和复用。

Profile 候选 `f4ac10281` 重启后从 Storage 加载 XiaoZhi，实际服务启动、OTA 请求、等待账号激活通过。取得六位激活码，原 App 界面显示 Activation code，实际 Playback 播放 activation.mp3 和六个数字 MP3；观察窗口无 Coze 配置弹窗、Start failed 或服务错误日志。未在记录保存短期激活码／云端 challenge。尚未绑定用户账号，未验证云端对话或录音；产品 Recorder／AFE 仍关闭，本票不伪造语音能力或替代系统 Assistant 的外部授权。

## Launcher 对照

原列表 warm 渲染期间 PNG open 为零，瓶颈仍在软件绘制。源码已将 shadow_width 默认为零，因此关闭默认阴影没有可试的新变量。改为第一页四个固定入口、后续每页最多四个 Core 已提交动态入口：上滑下一页、下滑上一页；第一页继续下拉返回 Watch Face，Release 才提交；无连续拖动或翻页动画。页码、末页边界、重进第一页和安装集合收敛由 Shell Owner 持有；不扫描目录或保存第二份安装数据库。

同设备、同 16 条轨迹：四轮 Up/Up/Down/Down；每条移动 180px、40ms 采样、移动阶段 160ms、hold 400ms、quiet 1.2s。基线 `ed20f6076` 仅有 AI 画布与 profile 开关，Launcher 保持原实现。两版本最终均断言仍在 Launcher、前台 App 为空。RenderProbe 是含按压、Home 切换和绘制的累计窗口，不把这些数据当作持续滚动 FPS 或纯 release 延迟。

| 方案 | Draw frames | 累计 draw | 平均 draw | 最大 draw | PNG open |
|---|---:|---:|---:|---:|---:|
| 原列表 warm | 49 | 4.719140 s | 96.309 ms | 150.342 ms | 0 |
| 分页首次 | 47 | 2.838063 s | 60.384 ms | 252.208 ms | 8 |
| 分页 warm | 47 | 2.111939 s | 44.935 ms | 116.508 ms | 0 |

分页 warm 累计绘制减少 55.25%，平均 draw 减少 53.34%；首次仍有图标解码尖峰，不宣称所有页面 30 FPS。性能测量使用 18sp 提示；最终普通镜像仅将提示改为 14sp／顶部 10dp 内边距，避免圆边裁切，未单独量化该小样式变化。

Core 投影替换失败、页切换失败、旧 view／已卸载／不可见行意图拒绝、9 个动态 App 的分页和移除后收敛、图标 lease 与重启清理回归通过。GUI public batch 统一改变行可见性；旧 raw LVGL 列表定位／scroll-top 探测已移除。真机 Apps 2/3 的 2048／AI／Calculator／Chronos 和 Apps 3/3 的 Flappy／Music／NES／Weather 截图可辨识；末页额外上滑没有启动 App。

## 验证与边界

首个普通镜像 `5ed31b9af` 的三组系统 suite 通过，但八 App 联合回归在 AI 激活码播报中 Home 失败：Core stop 等待 AudioPlayback close，GMF 已发 STOPPED 却不能退出；120s 内快照持续 invalid_state。其后六个 App 无法从这一已阻塞状态启动，不是六个独立 App 崩溃，全部失败记录保留，不能当作验收通过。真实 release／close_common／on_playback_event 主机回归以后台线程递送最终 STOPPED：旧 HAL 持生命周期 mutex 等 worker，worker 取同一 mutex，3s 超时 RED。精确 HAL 003 把 callback 存储锁独立后 GREEN，仍等待实际 worker 完成和回收，不超时强杀线程、不绕过 stop 或复用无效句柄。后续最终镜像重新验收。

首个普通镜像 `5ed31b9af` 完整构建和 app-only 写入／启动通过；两类诊断 profile 关闭，Recorder／AFE 继续关闭。BIN SHA-256 `dab4b1e9c56b5147b42892e7eae915d8ec7181048b24e422da57edc417b6d734`，ELF SHA-256 `5ed31b9afb8e034db1251f5014f0f048a4553161b14bbf074e0f19348023b8c6`。当时精确 proof：15 个组件、107 个产品文件，patch-inputs SHA-256 `16105415aa92338227f0265e3600b608b96a3a8f6985df660741929334d98dc5`。未写入 LittleFS、NVS、partition table 或 bootloader；该镜像的 apps／navigation／surfaces 三个 suite 全部 PASS，共 113 步，覆盖 Native／Runtime、Root／Detail、息屏唤醒、延迟 Back、取消／超时、PWR、Card 边界和 Launcher 下拉误点击隔离；其后发现的活跃播放关闭失败已另行修复。

HAL 003 修正后的最终普通镜像为 `0203fb1fc`，BIN SHA-256 `f216d397758a92193e9429ecda53eb95ba69c1efa3deb26bcc90d6a81afe6385`，ELF SHA-256 `0203fb1fc0950018b977e08c4254e7e6ae18a665545d9bc2896dc2fa5bbc8b0f`；精确 proof 仍为 15 个组件／107 个产品文件，patch-inputs SHA-256 `ba08b5bd8bd759ea198f5ff1f078b37639c4431d2f859654a7c047c31daec801`。完整构建、app-only 写入和启动通过。激活播报中分别等待 8／10／12s 再 Home 的三轮全部 PASS，每轮证据都包含实际 Starting playback，退出后回 Watch Face 且无占用 input，也没有 GMF Stop timeout 或缺少 encoder 的启动错误。全 App 联合中的 AI 重开／播报／Home 也已通过。

最终镜像八个官方已安装 App 的分页打开／保持前台／Home 全部 PASS：2048、AI Chatbot、Calculator、Chronos、Flappy Bird、Music Player、NES Emulator、Weather；Camera 未安装。该镜像重跑 navigation 34 步和 surfaces 22 步全部 PASS。完整非音频 apps 57 步沿用上一普通镜像的结果，未把它改写为新镜像证据。此次仅改变 HAL playback callback 锁；Runtime／Core／GUI 与产品 Source 已逐文件核对，必要的音频退出和全部 Runtime 启停已在最终镜像重测。

最终普通镜像的 Launcher 截图确认 14sp 提示在圆内安全位置，页码和四个入口清晰；AI 截图确认真实激活码可读且没有错误弹窗，随后 Home 再次成功，最终设备在 Watch Face，无前台 App 和占用 input。最终视觉证据为 `/private/tmp/espocket-xiaozhi-launcher-final-visual-{launcher,ai}.png`，对应同名前缀的 log／json。

Host 检查通过：最终 150 项跨模块 host tests（1 项已有 skip），Shell 13 项及其它组件／样例检查全部通过；HAL 003 后完整运行 `scripts/check.py` 返回成功。第一次全量检查的补丁列表断言未包含新增 Agent Manager，以及测试运行时 mock／版本条件修改造成的编译失败已修正并完整重跑通过。新增本记录时 Markdown 检查发现缺少入站链接，补齐工作票引用后独立检查 278 个文档通过。

串口重启脚本第一次使用默认 DTR 设置，未得到重启日志并超时；改为与已验证 flash helper 相同的 DTR／RTS 初始化后重启成功。临时多点轨迹第一次使用 20ms 间隔，低于真实适配器的 40ms 最小间隔，被准确拒绝为 bad_request；按 40ms 重跑通过。这两次不作为设备性能或固件崩溃证据。

原始证据保留在 `/private/tmp/espocket-ai-*.log`、`espocket-launcher-continuous-*.log`、`espocket-launcher-pages-comparison.json`、`espocket-xiaozhi-launcher-*.log` 与设备 suite JSON。原有备份、用户文件和其它工作的未完成门槛保留。
