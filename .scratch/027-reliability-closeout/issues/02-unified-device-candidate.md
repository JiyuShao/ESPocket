# 02 — 统一真机验收候选

**What to build:** 基于当前普通配置，在新隔离目录构建、归档输入与镜像，给出一次验收的执行顺序。

**Blocked by:** [01 离线可靠性](01-audit-and-offline-reliability.md)。

**Status:** resolved

## Acceptance

- [x] 全新完整固件构建及精确输入／产物归档校验通过。
- [x] 记录源码基线、工作树差异、补丁、资源、App 版本和有效配置。
- [x] 一轮设备清单引用原票的次数／验收条件，明确备份、保留数据更新和回退。
- [x] 半双工与 AEC 互斥配置、缺代码项、物理未验证项明确，不将 fresh LittleFS 当迁移镜像。

## Comments

本票完成表示候选与清单已准备，不表示设备通过或源码已提交。

## Resolution

候选与验收顺序已准备；没有设备验收。见[最终候选记录](../records/2026-10-09-unified-candidate.md)。


## 设备返回后的单轮执行顺序

1. **锁定输入与备份**：确认实际设备 identity、串口与当前 image；确保只有一个 USB 客户端。读取最新 App / LittleFS 备份及 hash，保留 NVS、私有数据和 Card 配置；候选期间新增数据另保存。只凭旧备份不能开始迁移。
2. **准备保留数据的资源镜像**：本轮候选 LittleFS 是 fresh FS，禁止直接用它覆盖用户设备。当前内置 Chat／Calculator 更新使用现有 `stage_local_runtime_apps.py --backup <new-backup> --output <new-image> --update-builtins`，核对全部私有文件和无关文件 inventory。迁移工具必须使用与候选内置 allowlist 完全相同的 frozen App 源码；可将工具副本的 ROOT 指向隔离工程，并逐文件核对原工具 hash。动态安装包触发工具拒绝时改走 Core installer，不能删除 receipt 绕过。另核对 Settings／Store／Hello 与候选期望资源，任何不一致都先明确各自更新 Owner。
3. **一次部署普通候选**：复核 partition / board / flash 配置与旧设备相容后，按原迁移票只更新必要 App 和保留数据资源，不写 NVS、bootloader、分区表或模型。固件 allowlist 与资源必须成套。部署后核对实际 image identity、hello、Watch Face、Native/Runtime Root 和私有配置，失败先回退。
4. **自动软件回归**：同一普通候选串行运行现有 navigation、surfaces、apps、runtime-confirm、resources、settings-brightness；每次使用新 output 目录和准确 expected-image。通过的合成输入不作为实体触摸／实体 PWR 证据。`cards` suite 依赖 M8 sample configuration，本候选该开关关闭，不能直接当作现成测试或为通过自动覆盖用户 Card 配置；使用已确认的实际配置做原 Card 路径，样例夹具另明确准备。
5. **一次收集两主题画面**：017/02–03 的维护页面、按钮普通/按下态、箭头与 Loading；切换由 Settings 实际 Owner 执行，重启恢复与即时刷新区分。截图全部实际查看并立即 release，同时一次人工确认实体面板；019/05 的 unknown/apply-failure 注入不通过随意改 NVS 制造，仍需测试夹具。
6. **全局下拉与恢复**：按 021/01、024/01 覆盖 Watch Face、Launcher、Card、Chat、其他 App、Keyboard 草稿、Dialog、Loading；请求过期／更新、Home、息屏／唤醒分别记录原实例、page、草稿和返回来源。非 GUI source 必须实际存在才验，不按依赖存在推断支持。
7. **语音集中验收**：原 020/03–04 路径集中一次执行，安静时误 STT、连续对话／滚动的声音缺口与绘制延迟、告别后当前页继续、实体 Reset 和 Home 后 Reset 均留真实证据。普通候选保留半双工，播音期间普通说话不能用来宣称打断支持；“啊灰啊灰”目标模型未准备时该目标继续开放。声学／性能窗口内不截图。
8. **带条件的生命周期／事务验收**：019/01–02 的逐失败点、外部 System 三轮协调、019/05 的主题故障注入需要独立测试夹具，当前普通候选不提供这些操作；019/04 动画与单阶段治理缺代码，不能安排为必过。Card 更新／卸载／rollback／掉电使用 005/03 的真实 package 事务和已确认测试包；未准备正式发行输入时不宣称正式信任成功。
9. **AEC 独立实验最后执行**：仅普通候选稳定且 020/05 的参考／MR／内存／延迟条件满足后，用由最新同一源码冻结生成的实验候选；关闭半双工抑制再启 AEC，记录新的 image/config identity。AEC 开关与普通配置互斥，这一配置切换不能消除为“只刷一次”；本票先准备普通候选，不使用旧 AEC 镜像覆盖新功能。按 020/05 原次数验唤醒词打断，普通说话全双工仍未承诺。
10. **结束与回退**：验收结束回到点亮 Watch Face，保存全部有日期报告、失败与未执行项。任何关键失败、误识别、资源不匹配或回退需求都先保存新增数据，再恢复匹配的 App/文件系统备份并复核 hello/Chat/Home/实体 Reset；不删除未知文件，不用旧 LittleFS 覆盖新增用户数据。

上述顺序复用原票的验收次数与条件；本票不另规定物理通过门槛。普通候选可以减少重复部署，不能在缺夹具或互斥声学配置时保证所有旧票一次关闭。

## 现有自动套件调用模板

以下仅是设备返回后的模板，本轮未执行；端口、设备 identity 和实际镜像摘要须现场核对，输出目录须新建。依次替换 suite 为已符合前提的套件，不并发占用串口。

```sh
python3 scripts/firmware/run_device_tests.py \
  --suite navigation --port <actual-port> --device-id <actual-device-id> \
  --expected-image <verified-image-identity> --output <new-output-directory>
```
