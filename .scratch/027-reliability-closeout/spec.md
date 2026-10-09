# 旧票核对、离线可靠性与统一验收候选

Sequence: 027
Status: resolved
Blocked by: None. 原票中的设备／夹具条件不属于本轮离线关闭门槛。

## Problem Statement

017 与 019 的旧票仍混合未整合阶段描述、当前源码条件与真机条件；024–026 已覆盖其中一部分，继续按旧状态执行会重复修改。需要核实停止、重启、迟到回调、失败清理和 Card 更新迁移，形成一次设备验收的明确输入。

## Solution

对照实际源码、生产方法 host tests 和构建记录核对旧票，只修复可复现的离线可靠性缺口；以独立构建入口生成统一候选并汇总设备路径。历史记录不改写，旧票追加当前状态与权威验收归属。

## User Stories

1. 维护者能区分已实现、缺代码、离线证据有限和只差真机的条件。
2. 正常 stop 后不会保留上一轮系统弹窗请求，下一轮请求使用新身份。
3. 设备返回后可依据同一候选与一轮清单验收，不为每张旧票重复刷机。

## Implementation Decisions

- 核对 017、019/01–05、08；024 呈现和 025 恢复／构建是既有实现，不另建同义模块。
- Core stop 的请求失效留在原 App Owner 调度路径；不增加 rollback manager，不取消已经提交的业务副作用。
- Card replacement 的 commit、rollback 和持久化核对沿用真实 Core 事务和 System 方法。
- 独立副本完整构建，不改 managed_components，不访问设备、不刷机；本轮不自动提交或 push。
- 当前普通候选使用半双工防回音；实验 AEC 不混入本候选。AEC／唤醒词打断需要独立受控配置与数据迁移，不能冒称单一配置可覆盖互斥策略。

## Testing Decisions

- 真实 stop/enqueue/validity 方法建立失败回归，覆盖 handler 释放、队列和身份撤销、三轮独立请求以及下一次成功启动的请求身份；同步 scheduler fixture 不代替真实线程竞争。
- 现有失败清理、主题回退、Shell interface、Card replacement、Chat 归属与资源 staging 回归必须通过。
- 统一 host checks、Markdown、完整隔离构建与归档输入身份校验必须通过。
- 声学、打断、触摸、配色、关键失败显式重启与完整产品三轮重复生命周期须保留设备门槛。

## Out of Scope

Files、扩展模块、完整诊断浮层、正式签名发布、启动动画迁移与单阶段性能治理。本轮不通过编译关闭这些缺代码或物理验收条件。

## Tickets

1. [旧票核对与可靠性验证](issues/01-audit-and-offline-reliability.md)
2. [统一真机验收候选](issues/02-unified-device-candidate.md)

## Further Notes

[旧票核对与离线证据](records/2026-10-09-reliability-audit.md)。

真机验收继续由原票持有；本轮候选票只交付输入和执行顺序，不复制验收条件。


## Resolution

旧票核对、可复现的 stop／迟到输入／失败重启保护和统一普通候选准备完成；[候选 identity 与验证](records/2026-10-09-unified-candidate.md)。原票的物理与缺代码条件继续开放，未部署或提交。
