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

## 晨间最小介入

先回复已发出的单次 013 smoke 结果：Native Detail Edge Back；自动息屏唤醒保留 Detail；PWR Home/息屏/亮屏回表盘；Quick Settings 上滑、Launcher 顶部下拉返回。遇到异常停在该步即可。无需重做此前十轮资源验证。

后续新增硬件条件统一积累在此处，避免每完成一小段源码就要求用户重复操作。夜间只做必要构建、主机检查和本地提交，不 push；续跑安排在当前 chat，至工具本地时间 2026-10-02 09:00。
