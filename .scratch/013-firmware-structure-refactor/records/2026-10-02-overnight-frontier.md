# 夜间执行与晨间介入

- 日期：2026-10-02
- 授权：用户要求完成 013 后检查剩余 issues，尽可能自动执行，醒来后统一介入。
- 结构重构提交基线：`e765c54`。013/01、02、03、05 已完成；04、06 的源码和构建完成，集中真机 smoke 尚未收到结果。

## 执行顺序

本记录只汇总执行选择；状态和 acceptance 仍以各 ticket 为准。不把未完成的硬件门槛用于阻塞本来独立的源码工作，也不把源码检查算成硬件通过。

1. [014/01 Navigator](../../014-app-navigation-card-contract/issues/01-page-declaration-navigator.md)：审计已实现的声明、生命周期和 Settings/Store 接入；剩余重点是 App 更新后的稳定 ID 处理与相应验证。
2. [014/02 Back](../../014-app-navigation-card-contract/issues/02-back-dispatch.md)：复核待决、失败、超时及旧 token；补具体缺口。待决样例的语言绑定归 014/04。
3. 01、02 条件满足后，可推进 [014/03 Card](../../014-app-navigation-card-contract/issues/03-card-registry-lifecycle.md)、[014/04 Native/Runtime](../../014-app-navigation-card-contract/issues/04-samples-api-finalization.md) 和 [012/02 输入/快照](../../012-test-automation-contract/issues/02-shared-input-and-snapshot.md)；优先形成可自动验证的完整 slice。
4. 012/02 后推进 [012/03 Driver](../../012-test-automation-contract/issues/03-host-driver-evidence.md)，让后续重复路径由 USB 执行；合成输入报告不得冒充 GPIO、触控硬件或视觉证据。
5. [007/02 源码门槛](../../007-m7-navigation/issues/02-close-navigation-source-gates.md) 依赖 014 的 Native 路径，可在上述证据充分后复核；008 的源代码工作遵守其 Spec 与 ticket 依赖。

009 的 Spec 等待 008/03 真机验收，不因个别 ticket 显示 ready-for-agent 就跳过。004/04、005 的信任/Store/键盘/发布事项缺少上游或发布条件，不能通过产品层复制 Owner 或修改 managed_components 绕过。

## 已执行

- 审计 014/02 发现：待决 Back 获得允许后，如果 Presenter 拒绝返回，pending 已清除但可见 Back 与 Edge Back 的发布状态仍保持关闭。
- 修复 `complete_back` 在失败路径重新发布同一 Navigator 的可用状态；当前 Page 不变，失败 token 不复用。新增真实 C++ 行为用例验证失败后两个入口恢复、重新请求能返回 Root。
- `python3 scripts/check.py` 通过：15 项 unittest、M2 parser、Markdown。
- ESP-IDF 6.0.1 构建/链接及分区大小检查通过；BIN SHA-256 `11855b9d3408fad94158e50ebfbc6bcdb5219fac27c3aa9cc1d7bd2cef080373`，ELF SHA-256 `218e8b9def9c58a80f1668e35fb2925bee6848ce608aa4240cf17edb7184dcae`。App 大小 `0x5d1250`，分区剩余 43%。日志 `/private/tmp/espocket-night-navigation-build.log`。
- 没有刷写此修复，设备保持 013 最终镜像，USB identity 仍应为 `e8bbe74ff`；构建目录中的新 ELF 已不同于设备镜像，不能直接以它判定当前设备身份。

## 第二轮自动执行

- 014/01 新增停止态 `update_declaration`：运行中拒绝；App/Root ID 不可变；新 Page/Card 声明完整校验后才替换旧声明。重排不改变身份，删除的 Card 打开时回 Root 并诊断，旧 Back token 不影响新任务。
- 实际 C++ 用例覆盖新增/删除、稳定 ID 与目标更新、无 Root、空 Page、重复 Card、失败原子性和迟到 token；统一 15 项 host tests、M2 parser、Markdown 通过。
- 这只是执行模型无关核心更新入口，没有新增软件包安装机制。014/01 仍开放：下一源码步骤是把通用 App 声明注册/更新与 Core 安装、卸载的生命周期连接起来；不得用这个组件测试宣称 Runtime 包更新通过。Runtime 语言绑定仍属于 014/04。
- 已逐项勾选 014/01 的既有可证明源码条件，未改变依赖或验收范围。
- 最终公开头文件与依赖组件重编译、完整链接、镜像生成及大小检查通过。BIN SHA-256 `8e2b455c1a994e7daaa701c7c3fb1e5958e55988b3226786aad39b8846ff226f`；ELF SHA-256 `a917f46fa2358dcb8fc763ae717661da339056df99f4889b182e433e62838db6`；日志 `/private/tmp/espocket-night-declaration-final-build.log`。未刷写，没有新增硬件通过项。

## 第三轮自动执行

- 014/01 Native 安装收敛到 `System::install_navigated_app`，Hello/Store 复用同一声明校验与 Core 安装边界。加入真实生产源码的主机测试，验证无效声明不安装、上游失败透传、同一 Navigator 连接与停止后 token 失效。
- Core 卸载回调移除注册并停止旧 Navigator、解除系统回调；deinit 也逐个停止和解除。注册表读写加锁，非前台 App 不覆盖当前 Back UI，前台切换初始化该 App 的 Back 状态。
- 014/01–02 的共同核心/Native 与组件条件已完成；详见 [收尾记录](../../014-app-navigation-card-contract/records/2026-10-02-native-installation.md)。16 项主机测试、M2 parser、Markdown 通过。最终固件构建结果在提交前追加，未刷写。
- 下一 frontier 按 Sequence 先复核 007/02 源码门槛，再推进已解除 Navigator 依赖的 012/02 USB 输入/快照；014/03 Card 和 014/04 语言绑定也可独立实施。008 的 Spec-level blocker 与硬件依赖继续有效。
- 最终固件完整构建/链接与分区检查通过，App 大小 `0x5d17b0`、分区剩余 43%；BIN SHA-256 `9ba683489fa105d5087f37c86f8b9612063d1329e7cb18082fa259c4e2aeb19e`，ELF SHA-256 `6ac76887992e1cd5edbf0dfbc20cc9104ef7f271fdebf6ee23c5f3af0652e1da`，日志 `/private/tmp/espocket-night-installation-final-build.log`。设备仍是 013 `e8bbe74ff`，未刷写。
- 同时修正 007 Spec 残留的强制可见 Back 文案，与已接受 ADR-0013 对齐；没有重新开启产品决策或改变硬件验收范围。

## 第四轮自动执行

- 007/02 依据已完成的 Native 接入、真实 Helper 调用/错误反馈与构建证据关闭源码门槛；007/03 的物理路径保持开放，未宣称完整 M7 PASS。
- 012/02 先接入只读 snapshot：System 提供真实 Shell/显示/前台事实，Page 来自 Navigator 或 Settings 官方 Flow；状态变化或未知页面明确失败。USB JSON 编码七个最小字段，不暴露参数、控件树或栈；仅成功采样递增 seq。
- 16 项 host tests、M2 parser、Markdown 通过，新增快照行为用例覆盖模式关闭不读 Owner、能力公布、实际状态变化、不伪造 Root、失败不分配成功 seq、并发 dispatch busy。
- 012/02 仅快照组件/源码条件已勾选；触摸/PWR 刺激、占用与超时/断连 release 仍开放。下一步需要把 Shell 硬件手势 lambda 抽为同一处理入口，再接合成轨迹；合成 PWR 应排到现有 System tick 执行，不能让 USB worker 直接跑 App 停止或 NVS/GUI 业务。
- 固件构建/链接通过，镜像大小与 hash、未刷写边界见 [012 快照证据](../../012-test-automation-contract/records/2026-10-02-readonly-snapshot.md)。设备 hello 仍只公布原来的 hello，不能从新源码能力推断设备已支持 snapshot。

## 第五轮自动执行

- 012/02 抽出实际 Shell 手势仲裁，硬件与内部合成入口共用同一规则和 pending intent；未直接设置 Surface，也未新增 USB touch capability。
- 17 项 host tests、M2 parser、Markdown 与 ESP-IDF 完整构建通过。Xtensa 的 int32_t 模板推导失败已显式指定类型修复；规则、覆盖矩阵、镜像 identity 和未刷写边界见 [012 共享手势证据](../../012-test-automation-contract/records/2026-10-02-shared-shell-gesture.md)。
- 下一 slice 接输入占用、原始轨迹/LVGL 注入与 System PWR 排队。取消路径应清掉未消费 intent 和 Launcher pull 状态，再解除注入；正常 Release 与异常取消不能混用。设备仍保留 013 identity，不新增物理/视觉通过项。

## 第六轮自动执行

- 012/02 完成 USB 合成 PWR 排队：System 原有输入任务消费，复用物理 PWR 语义；排队与执行期间 busy，重复 release 取消待执行输入，1000 ms 期限阻止迟到执行。快照增加 inputBusy。
- 17 项 host tests、M2 parser、Markdown 与完整固件构建通过；源码/镜像证据见 [012 PWR 记录](../../012-test-automation-contract/records/2026-10-02-power-input.md)。未刷写，不新增硬件通过项。
- 012/02 仍开放触摸轨迹/LVGL 注入、跨输入占用与触摸异常释放；后续应统一触摸与 PWR 槽位，不能让两个刺激交错。USB 物理连接 API 无法发现主机仅关闭串口，Driver 需显式 release。

## 第七轮自动执行

- 012/02 增加真实触摸序列组件，与 PWR 共用互斥输入槽位；调度时不挤压 press/release，异常取消与正常完成分开，清理失败保持 busy 并可重试。范围与组件证据见 [012 序列记录](../../012-test-automation-contract/records/2026-10-02-touch-sequence.md)。
- 17 项 host tests、M2 parser、Markdown 与 ESP-IDF 完整构建通过，未刷写。
- 该组件尚未接 USB/Display/Shell，不开放 touch capability，不提前关闭 012/02；下一步接 raw 轨迹与 Owner sink，并处理取消不提交 Launcher 返回。

## 第八轮自动执行

- 012/02 USB 轨迹接入实际 Display/LVGL 与正式 Shell 仲裁；硬件/合成输入互斥，PWR 与触摸共用槽位，异常取消不提交 Launcher 返回或按钮点击。旧前台任务 token 使触摸/PWR 失效。
- 主机组件用例与源码检查通过；最终固件构建和身份见 [012 Owner 记录](../../012-test-automation-contract/records/2026-10-02-touch-owner.md)。未刷写，不新增设备、物理或视觉 PASS。
- 012/02 源码/组件门槛完成，012/03 依赖解除；下一步用真实 USB Driver 等待快照和保存失败证据，不能以投递 ACK 代替输入效果。设备仍保留 013 smoke 镜像；Driver 的新能力设备验证应与早晨统一镜像安排协调。

## 第九轮自动执行

- 012/03 Driver 源码、466px 输入 profile 与错误/清理/快照主机用例完成；30 项 host unittest、M2 parser、Markdown 与固件增量构建通过。见 [Driver 证据](../../012-test-automation-contract/records/2026-10-02-host-driver.md)。
- 自动套件已编排 Launcher/Card、子页 Back、Root 无 Back、PWR Home/息屏/唤醒；坐标尚未设备验证，最后设备条件保持未勾选，012/03 ready-for-human。
- 没有刷写或执行新能力，设备仍为 013 identity；早晨收到单次 smoke 后，统一安排新镜像的一次 Driver 验证。每次失败保留原 attempt，合成路径不冒充物理或视觉证据。
- 012 的可自动源码 frontier 暂告一段落；继续评估 014/03 Card 注册/lifecycle 与 014/04 Runtime 绑定的独立源码条件，不跳过 008/009 的 Spec blocker。

## 第十轮自动执行

- 014/03 完成 CardRegistry 配置/迁移组件：稳定二元身份、左右排序/换侧、原子替换、更新删除/卸载清理与原因通知；复用 Navigator 声明校验，不复制页面栈。
- 31 项 host unittest、M2 parser、Markdown 通过；最终构建和范围见 [Card Registry 证据](../../014-app-navigation-card-contract/records/2026-10-02-card-registry.md)。尚未接 Core/GUI/lifecycle/NVS，整票保持开放，不宣称用户已能动态配置设备 Card。

## 第十一轮自动执行

- 014/03 增加真实 C++ CardSession 生命周期组件：创建、可见刷新、离屏暂停、切换/释放、更新/卸载通知回收，打开完整 App 前暂停，并覆盖失败与重入。范围和检查见 [CardSession 证据](../../014-app-navigation-card-contract/records/2026-10-02-card-session.md)。尚未接真实 GUI、Core 与 Card 提供者；整票保持开放。
- 014/04 审计到公开 RuntimeFunctionProvider 注册与 System Core 调用方身份接口，可作为后续语言绑定 seam；尚未实现绑定，不将私有 HostBridge 误报为必须改上游的 blocker。
- 32 项 host unittest、M2 parser、163 个 Markdown 与完整 ESP-IDF 构建通过；未接入的组件没有改变最终镜像 identity，没有刷写或新增硬件 PASS。

## 第十二轮自动执行

- 014/04 Native Reference App 增加可控 Back 确认：默认关闭，开启后允许/取消，框架仍独占待决与 15 秒超时；生命周期停止清理回调、timer 和旧 token。真实 App 源码与 Navigator 的主机用例通过，范围见 [Native 确认证据](../../014-app-navigation-card-contract/records/2026-10-02-native-back-confirmation.md)。
- 完成信息型、控制型、列表型和工具型页面开发指导，勾选该独立文档条件。Runtime Adapter、schema、Native/Runtime 同等验证尚未完成，014/04 仍开放；008 Spec blocker 不变。
- 不刷写，不打断现有 013 smoke 镜像；新 Detail 布局的设备/视觉条件保留到统一硬件验收。
- 33 项 host unittest、M2 parser、164 个 Markdown 与最终固件构建通过。未刷写镜像的 hash/identity 在上述证据记录中，设备仍为 013 `e8bbe74ff`。

## 第十三轮自动执行

- 012/03 Driver 接入 Native Back 确认的完整编排，逐快照检查待决、取消、允许、自动解除、迟到确认及待决 PWR Home 后重开。新增等待不变量和失败步骤证据；仍未运行设备套件。见 [确认 Driver 记录](../../012-test-automation-contract/records/2026-10-02-back-confirmation-driver.md)。
- 修复 Native 超时反馈仅保持 100ms 的可读性问题，保留到操作或下一 Back 请求；真实 App + Navigator 测试验证提示保留与新请求更新。没有更改导航或超时契约。
- 最终 37 项 host unittest、M2 parser、165 个 Markdown 与 ESP-IDF 编译/链接通过。未刷写的新镜像 identity 为 `307f10707`，完整 hash 见上述 Driver 记录；设备仍是 013 `e8bbe74ff`。

## 晨间最小介入

先回复已发出的单次 013 smoke 结果：Native Detail Edge Back；自动息屏唤醒保留 Detail；PWR Home/息屏/亮屏回表盘；Quick Settings 上滑、Launcher 顶部下拉返回。遇到异常停在该步即可。无需重做此前十轮资源验证。

后续新增硬件条件统一积累在此处，避免每完成一小段源码就要求用户重复操作。夜间只做必要构建、主机检查和本地提交，不 push；续跑安排在当前 chat，至工具本地时间 2026-10-02 09:00。

## 晨间状态总览

以下是夜间结束前的 frontier，不把未实现事项冒充外部阻塞。014/03、04 仍有可自主源码工作，09:00 续跑期限结束后留给后续继续；它们不需要重新发起产品选择。

| 工作 | 当前结论 | 下一步 |
|---|---|---|
| 013 结构重构 | 01、02、03、05 已关闭；04、06 源码/主机/构建完成 | 收到既有单次 smoke 结果后关闭对应硬件条件。 |
| 014/01–02 Navigator 与 Back | 源码、Native 安装/卸载、稳定 ID 更新和待决规则已关闭 | 已有证据保持，不重复重做。 |
| 014/03 Card | Registry 配置/迁移和 Session 生命周期组件完成，整票未关闭 | 接 Core 安装/更新/卸载、真实 Shell 呈现、Card 提供者与 NVS；不能宣称设备已能动态配置。 |
| 014/04 导航语言绑定 | Native 确认样例、四类页面指导完成；公开 Runtime Provider seam 已确认 | 实现 Runtime Adapter、versioned Page schema、GUI Owner 调度和双方同等验证，再 clean build/staging。 |
| 014/05 Card 样例 | 前置 03、04 未完成 | 等待真实 Card 与语言绑定，不跳过依赖。 |
| 012 测试入口 | 01、02 源码关闭；03 Driver 源码与主机检查完成 | 013 smoke 后统一刷明确新镜像，只跑一次 USB suite；失败保留 attempt，坐标仍待校准。 |
| 007 导航 | 01、02 源码门槛关闭；03 物理条件仍开放 | 按 ticket 引用已有结果和剩余证据，不要求重做已接受的亮度/Wi-Fi 操作。 |
| 008 App 契约 | Spec 仍等待 014/04 | 后续再实施回收 seam、App 物理验收，不把单个 ready-for-agent 标签当成 Spec 已解除。 |
| 009 AI Native | Spec 等待 008/03 真机验收 | 不跳到 Semantic/Assistant 实现。 |
| 004 剩余项 | storage/developer 需人工证据；playback-only Audio 缺官方 capability 变更 | 保留人工与上游阻塞，不复制 HAL/Audio Owner。 |
| 005 生态剩余项 | package trust、Store 稳定性、Runtime keyboard 隔离和签名分发受上游/发布路径约束 | 不修改 managed_components、不绕过 Core trust；相关 Launcher/package lifecycle 按真实依赖保留。 |

设备没有收到任何夜间刷写，仍为 013 identity `e8bbe74ff`。当前 build tree 的镜像不同；刷写前使用最新记录的 BIN/ELF hash 与 hello identity，不拿构建目录 ELF 误判旧设备。临时构建/Driver 日志与本地 commits 只记录源码或合成证据，不能自动关闭物理/视觉条件。

## 用户恢复后的推进（2026-10-02）

用户明确要求继续直到完成，覆盖此前 09:00 夜间截止。014/04 的 Runtime 绑定、schema、Owner 队列、确认样例、对等组件与 clean build/staging 已完成并 resolved；详见 [绑定证据](../../014-app-navigation-card-contract/records/2026-10-02-runtime-navigation-binding.md)。008 的这项源码前置已满足，008/03 真机门槛保留。下一步继续 014/03 实际 Card 呈现与持久配置，再按依赖推进 014/05、008；本记录之前的夜间状态保留为历史。


## 用户恢复后的第二个 slice

- 014/03 的 Core/NVS/Shell/Native Card/GUI Owner 队列接入完成，前三项源码条件勾选；Runtime replacement 的配置保留与更新原因仍缺真实事务 seam，不关闭整票。014/05 仍缺 Runtime Card 提供者及设备证据。详见 [Card 接入记录](../../014-app-navigation-card-contract/records/2026-10-02-card-owner-presentation.md)。
- 008/02 独立回收测试入口 resolved；五种配置生产边界主机测试、Native/Runtime 启用分支 ESP32-S3 交叉编译和普通完整 build 通过。008/03 每条路径按用户减量要求集中一次，硬件条件保留。
- 新镜像未刷写，设备仍为旧 013 identity。013 smoke 仍等待既有问题的结果，不重复请求；012/03 的设备 Driver attempt 排在该 smoke 后。
- Runtime Card 的独立可执行实例不能通过另建 Runtime 安全提供：当前注册表返回共享 JS backend，且其构造私有。另一个 Runtime deinit 可能清理 Core 的 backend。需明确声明式 Card 边界或获得上游专用实例 seam，不伪造 App 运行身份、不自行分配共享 backend 私有 ID、不复制 Runtime。
- 009 继续等待 008/03；004 Audio、005 trust/keyboard/Store/publication 的外部条件未改变。所有前置均按真实 ticket 保留。


## 当前可执行 frontier 核对

截至本轮本地提交 cd4e72d，008/02 源码已关闭；014/03 余下真实 package update 事务条件转为 needs-info，014/05 等待该条件、Runtime Card 范围答复和设备结果。其余未完成 tickets 都有未满足的具体人工、上游或 ticket 依赖；没有把 009 的 ready-for-agent 标签当成越过 008/03 的授权。

[本轮上游核对](../../../docs/upstream/status-2026-10-02.md)取得 Core 0.8.4、JS 0.8.3 与 Audio 0.8.2 官方发行页面，与现有锁一致；HTTP/HAL 和部分源码请求未取得内容，不能据此作出已修复/绝无修复结论。没有采用未经核实的新依赖。

人工最小介入仍为：回应既有 013 单次 smoke；Runtime Card 首版接口范围选择。之后才能按原依赖推进一次明确镜像的 USB Driver 与 Native/Runtime 单次物理路径。已有已接受结果不重做，旧镜像/新构建身份不混用。

## 用户恢复后的声明式 Runtime Card slice

用户已接受声明式 Runtime Card 首版并要求继续，范围选择不再待答复。已实现真实安装声明校验、Core 元数据刷新、独立 GUI 文档、summary/目标 Detail 样例、版本化 schema 和开发 API；没有创建独立 JS Runtime。见 [首版实施证据](../../014-app-navigation-card-contract/records/2026-10-02-declarative-runtime-card.md)。

新增默认关闭的 Card 样例入口，仅在 Developer Mode On、空持久配置时使用 RAM 序列，保留既有 NVS。未刷写或新增硬件 PASS。014/03 package replacement 事务条件、014/05 硬件/迁移条件、013/04 与 013/06 既有单次 smoke、012/03 一次设备 Driver、008/03 各路径一次仍保留。早前已接受的亮度/Wi-Fi 与十轮资源结果不重复。

## 013 人工验收解除

2026-10-02 用户确认旧镜像 e8bbe74ff 的集中 smoke 全部正常。013/04、013/06 与 Spec 全部 resolved；不再请求该 smoke。012/03 的设备 Driver 验证可以按明确新镜像推进，014/05 Card 与 008/03 剩余物理条件仍分别保留。

## USB 合成设备门槛解除

013 smoke 之后已刷入新镜像并完成 012/03，最终 09e8eb00d 的独立 35 步 attempt PASS，012 Spec resolved。过程中实际捕获并修复测试 worker 栈容量/分配与导航滑动尾部误触，所有失败保留；见 [设备 Driver 记录](../../012-test-automation-contract/records/2026-10-02-device-driver-run.md)。007/008/014 的物理/视觉条件仍按各自证据区分，不重新要求十轮人工。


## Card 合成设备门槛与当前人工 frontier

37 步 Native/真实 Runtime Card attempt PASS，详细镜像、资源 hash、前八次失败及修复见 [Card 设备记录](../../014-app-navigation-card-contract/records/2026-10-02-card-device-run.md)。新增真实重复加载回归，修复 Runtime 样例顶层绑定无法二次启动；Driver 不自动重试，不通过放宽 JSON/Owner 错误取得 PASS。

设备当前 c4dfa5af8，RAM Card 样例开、reclaim 关，持久 Card 配置保持原样。两侧目标打开、普通横滑、Root 手势与 Card 息屏画面已合成验证，物理/视觉各侧一次的集中问题已发出；待回答期间不切换设备固件或注入手势。普通配置完整构建可继续准备，验收之后恢复。013 全部 resolved、012 既有 35 步普通配置 PASS 继续有效；新增 Owner 采样实现之后应在普通配置补一次 Driver 检查。

014/03 package replacement 事务仍依赖 005/03；014/05 不能因合成 PASS 提前关闭物理与迁移条件。007/03 剩余路径与 008/03 两种模型恢复/回收仍是后续集中真机工作，009 按其依赖等待。未绕过上游阻塞，未 push。


普通配置 71567f599 全量构建与最终 host checks 已通过，资源 hash 与 Card 测试资源一致；尚未刷入。用户回复当前 Card 集中问题后再恢复普通镜像、补一次新 Owner 采样的 navigation Driver，并汇总剩余 007/008 单次物理门槛，不再重复已接受的 013/亮度/Wi-Fi。

## 用户接受 Card 后的当前状态

用户明确“没问题就过吧”，接受当前 Card 样例交互。右侧曾实际空白的失败与重启对比完整保留，重启后视觉和一次物理 Open 正常；未确定根因，不声称实现修复。014/05 样例交互/呈现/记录条件勾选，剩余实际 package replacement/迁移依赖 014/03 → 005/03，状态 needs-info。

设备已恢复普通 71567f599，App 写入校验通过。新 Owner 采样实现的一次 34 步 navigation attempt PASS、release=ok、最终表盘亮屏，见更新后的 [Card 设备记录](../../014-app-navigation-card-contract/records/2026-10-02-card-device-run.md)。Card/reclaim/trace 配置关闭，LittleFS 与 NVS 保留。剩余真实 frontier 为 007/03 尚缺的物理路径、008/03 两种 App 恢复与回收、以及已记录的上游更新事务阻塞。不会重做已经接受的 013 或亮度/Wi-Fi 多轮。

## 导航验收完成与新的 Runtime frontier

015 测试职责目录重构已提交，007/03 剩余集中物理路径由用户回复“都正常”，007 全部 resolved。008 apps 自动验收在普通 71567f599 上发现 RuntimeJsAsync 栈溢出；最小复现与隔离记录见[008 设备记录](../../008-m8-app-contract/records/2026-10-02-app-device-frontier.md)，新增 008/04 needs-info 等待上游公开执行/栈配置能力。008 保持 blocked，009 按依赖等待。诊断资源已撤销，普通资源写回校验通过，最终真实快照为表盘亮屏且无输入占用。未改 managed_components，未 push。
