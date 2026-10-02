# 2026-10-03 — Semantic contract 与 brightness 首个 slice

用户解除 008/03 对 009 的实施顺序约束，允许先实现语义接口与亮度能力。008 的未验收真机路径继续保留。

新增 Owner-local [semantic interfaces](../../../firmware/components/espocket_semantics/README.md)，统一 registration、caller、permission、risk、lifetime 与结果语义。公开接口主机测试覆盖声明与授权交集、复制 handle 失效及新实例不能复活旧 handle。

Brightness 使用真实 selected Display output 的公开 Helper；Shell 读写转入同一接口。设备当前仅准入内部 Shell caller，Assistant 用户目标授权尚未接通，保持拒绝。Changed Event 是本次 Action 的观察事实，无全局订阅。主机测试覆盖真实 caller、归一化值、取消/撤权、失败、提交后不确定及不重试。

当前两项独立 C++ host contract 测试通过。完整仓库检查与固件构建结果待本轮补录；没有刷机，也不宣称物理亮度验收通过。

完整固件构建通过：`/private/tmp/espocket-009-core-isolation-build/firmware/build`；逐项确认 Runtime/Core override 来源，registry 依赖无 drift。此构建包含最终 semantic header 与 Core 补丁，普通诊断配置关闭。ELF SHA-256：`5e79e3a82b1ed66069e9d741ace6a08cf4281e3428c7162aa4da90e0967a5020`。尚未刷机，物理显示/亮度不冒充验收。
