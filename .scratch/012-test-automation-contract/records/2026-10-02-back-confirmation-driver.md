# Back 确认 Driver 路径

- 日期：2026-10-02
- 任务：[012/03](../issues/03-host-driver-evidence.md)
- Native 控件源码基线：`18a6ec0`，同一 App 与同一 Navigator。

## 实施

USB Driver 通过真实轨迹进入 Native Detail，启用确认，检查待决重复 Back 不导航、取消保持 Detail、允许回 Root、自动解除待决后恢复 Back、迟到确认不 pop。另在待决时 PWR Home，重开验证 Root 和新运行默认关闭确认。未开放任意 App Action，没有协议版本或 capability 变更。

18 秒上限的状态等待保存独立步骤，并对每次快照检查前台 App ID、Detail 与亮屏；错误中途跳 Root 立即失败，不能以最终又回到 Detail 掩盖。pending 与 canBack 同时为 true 拒绝。结束仍等待两个新快照，不以 ACK 或 sleep 判 PASS。这里不精确测量 15 秒超时边界；Navigator 的真实 C++ 用例负责边界。

Root/待决的有限观察窗口在开始采样前保存 RUNNING 步骤；失败记录具体期望、最后 seq、样本数和错误，避免 invariant 失败只有 attempt 总错误而没有对应 FAIL 步骤。

466px profile 的确认/允许/取消坐标分别为 `(233,224)`、`(233,282)`、`(233,340)`，来自当前 Detail 资源布局，尚未设备校准。测试 capability 不证明旧固件有这些控件，须配合明确镜像 identity。

同时修正 Native 超时/失效提示只停留一个 100ms tick 的问题：现在保留到下一次操作或新 Back 待决提示。实际 App + Navigator 用例验证重复 timer 不清掉错误、新请求仍能更新提示。不改变 Navigator 超时或页面规则。

## 检查与限制

Driver 主机用例增加到 17 项，覆盖不合法 Back 状态、待决到完成的新快照、等待期间页面不变量、期限未完成保存失败证据，并检查套件编排。假 transport 不保存为设备 PASS。最终 `python3 scripts/check.py` 通过：37 项 unittest、M2 parser、165 个 Markdown，日志 `/private/tmp/espocket-night-confirm-driver-complete-check.log`。追加记录后 Markdown 检查再通过。

ESP-IDF 6.0.1 最终编译、链接、镜像生成和分区检查通过；App 大小 `0x5d7c60`，分区剩余 43%，日志 `/private/tmp/espocket-night-confirm-driver-final-build.log`。BIN SHA-256 `3573ac66bc85c49194a28f16dbd2fa9947e3cc4e05ac51bb2bfd944727c94a46`，ELF SHA-256 `307f10707f75499e1e101441cc5fd79f3576a112fc882a1a49a43ec99037ca50`。若后续刷入此准确镜像，hello identity 应为 `307f10707`；目前未刷写，不能拿它判断旧设备。

未刷写、未执行设备套件。设备仍保持 013 identity `e8bbe74ff`，012/03 的真实运行条件保持开放；新增输入路径不替代 GPIO、触控芯片、视觉或 App 完整生命周期验收。
