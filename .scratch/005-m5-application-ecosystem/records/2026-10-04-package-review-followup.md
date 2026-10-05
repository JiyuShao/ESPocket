# 2026-10-04 Package review follow-up

Origin: Codex 对 f84e085 的定向评审；以下均为 03/09 既有契约内修复，不扩大任务范围。

## R1 — 关闭模式停止失败后的重试

system_power.cpp 的 poll_system_input 在 enforce_runtime_package_policy 失败时仍将 package_developer_was_enabled_ 清为 false。Core 保留 stop 失败的 running App，因此模式保持 Off 时无法再次触发停止。需由真实 Owner 持有待重试状态／有界退避，避免每帧重新哈希整个 App。测试 stop 失败后后续停止成功、仍禁止启动、不进入无限高频重试。

## R2 — 更新失败后 Card 配置丢失

新版本 on_app_installed 在事务提交前调用 CardRegistry::update_app；后者 prune_locked 删除新声明中缺失的旧 Card，RemovalHandler 可能立即持久化配置。若随后 on_app_replaced 或 receipt commit 失败，重新注册旧声明不会补回已删除的 CardKey 和顺序。当前 package host harness 的 on_app_replaced 为无操作 stub，不能证明产品 Card rollback 完整。

需在正确事务 Owner 与 Card 配置 Owner 间保持可恢复的旧声明／配置或推迟提交副作用；测试旧版本 Card 被配置后，新版本去掉该 Card，随后注入 commit/migration 失败，旧版本恢复且 CardKey、顺序、持久配置均保持。证据中“失败回滚恢复 Card 配置”目前尚未被这个路径证明。

## R3 — 清理失败的 rollback 证据

Core rollback 忽略 failed final 删除结果。核对 fs_rename 在目标仍存在时的实际行为；清理失败必须保留 backup、明确报错，不覆盖或丢失旧版本。已有 restore-failure matrix 不自动替代 remove-failure matrix。

### R2 补充边界

没有导航／Card 声明的开发者旧包也允许更新。其 prepared 阶段没有 Card 快照，rollback 不应以 card_replacement_state_unavailable 失败；需区分“原本无 Card 状态”与“应有快照但丢失”。恢复声明之前的 migration/persistence 错误也不应阻止尽最大可能恢复旧 Card 配置。测试无 Card 旧包更新失败仍恢复正常。

### R2 原本无 Card → 新版本有 Card

`replacement_without_cards_` 的 restore 分支不能只清标记并成功返回：旧包原本无声明，新版本在 on_app_installed 注册了声明/卡片后 commit 失败，旧包重装不执行 Card 注册，CardRegistry 仍可能保留失败新版本声明。需移除该 App 的 speculative 声明与 CardKey，再恢复旧配置；测试无 Card 旧包 → 带 Card 新包 → commit 失败，不残留可用 Card 或配置污染。

### R2 掉电与持久化次序

当前 on_app_replaced 在 receipt commit 前调用 card_store_->save_current，RAM snapshot 无法覆盖保存成功到 receipt 提交之间的掉电窗口。旧 App 从 backup 恢复后，全局配置已被新版本 prune 并持久化。实现需让旧持久配置在 committed receipt 之前保持可恢复：例如先只更新内存，在 committed 回调中持久化新配置，并为该步骤失败定义可审计恢复路径；或由真实配置 Owner 持有持久 checkpoint。测试顺序应证明未提交更新不会把旧配置写丢；不得用 RAM-only rollback 声称掉电安全。既有 handler 只做 CardSession invalidate/log，持久写主要发生在 on_app_replaced，可定向处理。

## 检查点进展（2026-10-04）

- R1：CC 报告实际 `tick_runtime_package_policy` 编译回归通过（1 test，1.204s），覆盖停止失败退避、成功清理与重新开启后再次关闭。Codex 已定向阅读方法与测试。
- R2：CC 报告真实 CardRegistry／CardConfigurationStore 编译回归通过（1 test，4.814s），覆盖裁剪后的声明、CardKey 顺序与持久配置恢复，以及旧包无 Card 的失败更新清理。Codex 已定向阅读方法与测试；提交后持久写失败用例、Core 回调签名／错误语义与完整门槛仍待完成。
- R3、最终完整构建、真实 Store 安装／运行／模式切换均未在此检查点确认通过。

### Core 同步后的定向门槛

CC 于 2026-10-04 14:13（Asia/Shanghai）报告 `test_runtime_package_admission.py` PASS 与 Card rollback 编译回归通过（1 test，5.743s）。Core 声明、默认实现、产品 override 与 host stub 均采用 expected 返回；receipt 已提交后的配置写失败明确返回 `committed_package_card_persistence_failed`，保留 backup，不执行提交前 rollback。Codex 已核对对应 Core 调用顺序及注入失败用例。补丁报告 SHA-256：`aed488c83669985b3395d515bc9eaba0575fbc638aadd62c5e0c0c01a3b22b0d`。完整主机检查、最终固件构建与设备验收仍待执行。

### 完整主机门槛尚未通过

2026-10-04 14:19（Asia/Shanghai）完整 host suite 为 80 tests、3 failures：撤销订阅后 queued event 仍投递、失败 on_stop 跳过 Runtime 清理、键盘 Text 被送到其他 App。定向安装／Card 测试的 PASS 不替代这些既有门槛；Codex 已通过原 CC CLI 会话回流，要求核对 005 补丁生成基点／前序补丁顺序并修复，禁止弱化断言。完整构建与刷机保持未验收。

### 后续完整门槛通过

当前补丁组合重新执行完整 `scripts/check.py` 通过，各组件测试和 80 项跨模块主机测试均通过；上述三项真实控制流测试保留未修复上游失败的对照和原有断言。R1/R2/R3 的停止重试、Card 配置恢复、提交后持久写失败和 failed final 删除失败亦通过现有回归。候选 `f6cb09bbd` 的完整构建与精确输入核对通过，未刷机；结果、产物身份与剩余设备门槛见 [最终构建记录](2026-10-04-package-final-build.md)。
