# 2026-10-03 — Runtime 异步栈配置补丁验证

## 授权与输入

用户在限定例外问题后回复「好，不要停，我去休息了，你把能做的都做了吧」。[ADR-0015](../../../docs/adr/0015-runtime-async-stack-patch-exception.md)只修订 ADR-0001 的 Runtime JS 0.8.3 栈配置限制，不授权任意组件补丁。

正式差异是 Kconfig、macro_configs.h 与 backend.cpp 三处：上游默认仍为 8192，产品先验证 16384 bytes；原有调度、优先级与分配策略不变。完整文件 hash、补丁 hash、commit 与删除条件见 firmware/patches/espressif__brookesia_runtime_js/0.8.3/manifest.json。上游问题尚未提交。

构建入口复制完整工程与缓存，在副本 manifest 使用 Component Manager override_path。将全部 Registry 版本固定为原始 lock 的精确值，配置后和构建后比较版本及 component hash；只有 Runtime JS 的来源变为本地副本。原始组件 31 个文件 hash 与正式 manifest 一致，原始 registry lock 保留。

## 已保留的准备失败

- 首次沙箱构建被 sysctl 权限阻止，未生成新的有效镜像；改用已授权的构建权限。
- 第一版副本忽略规则把嵌套 LittleFS 源码误当成生成目录，完整构建失败。规则修复为仅忽略工程根的 littlefs/build，新增嵌套源码保留回归；一次错误的恢复路径也失败，随后恢复正确 src/littlefs 并重新配置。
- 原始 override 解析使 libpng 从 1.6.58~1 变为 1.6.58~2；该产物不用于设备验收。新增精确传递约束和锁身份校验，最终副本的 Registry version/hash 与原始输入一致。

原始日志分别位于 `/private/tmp/espocket-runtime-patched-16k-build.log`、`build-escalated.log`、`build-repaired-copy.log`、`build-final.log` 与 `build-pinned.log`（后四者同 espocket-runtime-patched-16k 前缀）。这些失败没有改动原始 managed_components，也没有刷写设备。

## 主机检查

统一检查通过：62 项 unittest、M2 parser、188 份 Markdown。补丁准备包含 8 个失败关闭/副本测试；构建准备含 5 个隔离、嵌套源码、版本约束及 lock drift 测试。新增独立回收用例的两种模型语义与 busy 拒绝经主机测试；主机断言不代替设备。

新增 resources 用例仅执行三轮有限路径，串口 checkpoint 的 heap/最小剩余栈需独立判读。已有资源诊断开关下输出 RuntimeJsAsync 的真实 high-water mark；正式关闭诊断时无该输出。

## 当前验证状态

完整锁定构建与真实设备结果继续在本记录追加。尚未因为源码、host 或正在链接的产物宣称设备修复；008/03 的物理及资源条件继续保留。

## 普通锁定镜像与最小设备回归

完整构建通过，Registry version/hash 与原始 lock 一致，project_description 确认 Runtime 源码来自 patched_components。普通配置 Card/reclaim/resource trace 均关闭，异步栈为 16384。

- ELF SHA-256：`c8d56e5e23caa8bdccc1215860d083513745560aef6cb6d324f0cb1c15431f07`；hello identity `c8d56e5e2`。
- App BIN：`2781cba0c30c780645b59d78e8f5e52047a3d9fdbef8e2222f082640a40bed2f`。
- LittleFS：`a5a5f1cb08c7b02c82f60b996b5882147d494c33f61ec9b6bdbc7a3717096e32`，与已恢复普通资源一致，无资源刷写。
- 普通产物保存于 `/private/tmp/espocket-runtime-patched-normal-preserved`；仅刷应用分区 0x60000，写入 hash 校验通过。

真实设备 ESPocket-Waveshare-A0F262E30B68 的 runtime-confirm attempt `20261002T165829Z-54c3701c-fe9a-4c50-8a66-a98db61fd856` PASS，7 步。时间编号为 UTC，上海本地日期为 2026-10-03。Confirmation On 和待决 Back 保留完整资源；没有复现 RuntimeJsAsync 栈溢出。release=ok，最终 seq=37、Watch Face 亮屏、App/Page 空、canBack/backPending/inputBusy 均 false。

该证据为 synthetic-input；不证明文字视觉、物理触摸或 PWR GPIO，也不抹去原镜像的失败。原始 attempt 位于 `/private/tmp/espocket-runtime-patched-confirm/`。完整 apps 与资源/回收仍待独立结果。

## 完整 App 自动路径

普通 c8d56e5e2 的 apps attempt `20261002T165910Z-97893ee9-7013-4dbf-9be8-d989213cd12e` PASS，57 步。Native 与真实 Runtime 都通过 Root/Detail、普通横滑、未回收自动息屏/恢复、重复待决 Back、取消/允许/超时、过期确认拒绝和 PWR Home 后 Root 重启。release=ok，最终表盘亮屏且没有 App/Page、Back pending 或输入占用；无 panic/stack overflow。报告与串口位于 `/private/tmp/espocket-runtime-patched-apps/`。

这是 synthetic-input；008/03 的 Runtime 物理和回收/资源条件仍独立保留。原镜像失败与本次修复后的 attempt 不合并计数。

## Native 独立回收与有限资源结果

Native-only / resource trace 镜像完整构建通过，hello `01a86838e`。ELF `01a86838eca13871595c239e3433cc2e36760387ab06907e9a6e48151cf639f4`；BIN `76d592cf43cb98859960ab0eb2b01b3f351c80e4c8d5e39803023d81d4d30d6b`。仅 Native reclaim 和 resource trace 开启，Runtime reclaim/Card fixture 关闭，预算 16384。

reclaim-native attempt `20261002T170549Z-8d3b4f21-050a-43b0-a111-6370a099c041` PASS：自动息屏后日志确认 native stop，wake 回表盘；重开从 Root，旧 confirmation 状态清除；同镜像的 Runtime 自动息屏后恢复 Detail。最终 release=ok。路径是 synthetic-input，物理/视觉未验收。

resources attempt `20261002T170529Z-3b604f88-8582-4bc2-b601-49bf0aaa629c` 的 45 步语义路径 PASS，但仅收齐一条 heap 日志，资源证据不完整。为具体采样缺口增加 0.4 秒无请求读取窗口；quiet attempt `20261002T170902Z-91ea6724-ed05-4c26-be79-e7cf17a761a5` 同样 45 步 PASS、release=ok，收到两条完整 heap 日志，仍没有收齐每个 checkpoint。保留缺项，不将 quiet window 声称为日志丢失根因修复。

| 同一诊断镜像有效 checkpoint | internal free | PSRAM free | internal largest | PSRAM largest |
|---|---:|---:|---:|---:|
| sample 4 | 51531 | 2190152 | 40960 | 2097152 |
| sample 7 | 51567 | 2190496 | 40960 | 2097152 |
| sample 12 | 51655 | 2190500 | 40960 | 2097152 |

有限工作负载的有效数据未出现持续下降，最大空闲块相同。不是长时稳定性证明，也不为缺失 checkpoint 补造数据。RuntimeJsAsync 高水位记录的最小剩余栈先为 7416，随后稳定为 7400 bytes；IDF Xtensa StackType_t 为 uint8_t，数据单位是 bytes。所观测最大栈消耗为 8984，解释原 8192 预算不足；不保证任意未来 App 的栈上界。

报告/日志位于 `/private/tmp/espocket-runtime-patched-resources/`、`resources-quiet/` 与 `reclaim-native/`（后二者同 espocket-runtime-patched 前缀）。生产 GUI 反馈与资源没有删改。新增 quiet 读取测试验证日志保存、无额外请求及 panic 检测；最终统一检查 63 项 unittest 通过。

## Runtime 独立回收与普通镜像恢复

Runtime-only / resource trace 镜像完整构建通过，hello `439f6431a`。ELF `439f6431aa86b1dffa975fb8cb529668a10cd9b09f6361f0015d678db3906c8f`；BIN `504b7562e66fc652b26f24adb08616ea730be690858a6f6108bbe84aaf4db854`。仅 Runtime reclaim/resource trace 开启，Native reclaim/Card fixture 关闭，预算 16384，Registry lock 身份核对通过。

reclaim-runtime attempt `20261002T171315Z-faaa66a6-9cfd-4f84-b5b6-faa077021fec` PASS，17 步。Native 未回收时保留 Detail；Runtime 自动息屏后日志确认 runtime stop，wake 回表盘；重开 Root，旧 confirmation 状态清除，新 Detail 的 Edge Back 即时回 Root。release=ok，最终 seq=657、表盘亮屏、App/Page 空、Back/inputBusy false。没有 panic/stack overflow；原始报告位于 `/private/tmp/espocket-runtime-patched-reclaim-runtime/`。

已重新刷回普通 c8d56e5e2，只写应用分区并校验成功；LittleFS/NVS 未写。独立只读 hello 匹配，release=ok，最终 seq=1、Watch Face/display=true、App/Page 空、canBack/backPending/inputBusy false。身份和快照保存 `/private/tmp/espocket-runtime-final-normal-state.json`，写入和启动日志同 final-normal 前缀。普通保存配置的 Card、两种 reclaim、旧 M6 reclaim 和 resource trace 均关闭。

两种回收的设备语义已验证；所有 synthetic-input 证据仍不能代替物理/视觉条件，008/03 不关闭。剩余依赖与晨间最小操作见[续跑 frontier](2026-10-03-overnight-frontier.md)。
