# App 设备验收与 Runtime 异步栈溢出

Date: 2026-10-02
Scope: 008/03、008/04

## 前置与当前镜像

007/03 已得到用户“都正常”的剩余物理确认并关闭。当前普通 ELF identity 71567f599，设备 ESPocket-Waveshare-A0F262E30B68。两种 reclaim、Card fixture 与 resource trace 均关闭；开发者模式已开启。普通 BIN SHA-256 c43c7d0ea2414b92c3e5ff399c101ea34122b1eddda1682c82e46f50cb5ebf0c，ELF SHA-256 71567f599c68054a4a011a621f22c70bb1e8f85765342b8ff17c3466c4ab8a33，原始 LittleFS SHA-256 a5a5f1cb08c7b02c82f60b996b5882147d494c33f61ec9b6bdbc7a3717096e32。

## apps 集中自动路径

新增 firmware/test/device/e2e/apps.py，真实 Launcher 启动 Native/Runtime，真实页面按钮与共同 Edge Back 驱动，不新增 USB 命令，不复制页面栈。坐标按当前 466px 资源布局计算：Runtime Launcher (233,264)、Root Open Detail (233,263)，确认/允许/取消按钮覆盖原 profile 坐标。既有 navigation/cards 的初始输入占用分支残留 DriverError 未定义，改为共同 DeviceTestError；新增真实执行器测试断言初始占用时只读快照、不发送刺激，覆盖各套件。

Attempt 20261002T154159Z-17fff828-ba8c-400d-93d7-1ad1dc7d75f1：FAIL，41 步，其中 40 步 PASS。Native 的导航、普通横滑、Root 负向 Back、30 秒自动息屏唤醒保留 Detail、重复待决 Back、取消/允许、15 秒超时取消、迟到确认、待决 PWR Home 与重开 Root 均通过合成断言。Runtime 的 Root/Detail、普通横滑、Back、自动息屏/唤醒保留 Detail 通过；随后确认开关点击触发 RuntimeJsAsync 栈溢出、自动重启。release 与 final snapshot 因设备重启失败，不把 40 个通过步骤当整体 PASS。原始 report/serial.log 位于 /private/tmp/espocket-m8-app-attempts/<attempt>/。

## 最小复现与隔离

/private/tmp/espocket-runtime-confirm-repros/ 保存以下独立 report/serial.log；最初使用临时 Python 同一执行器，持久入口现为 CLI --suite runtime-confirm。

| Attempt | 资源/路径 | 结果 |
|---|---|---|
| f0abe46c-1006-471a-9825-edc811142a89 | 原始资源，不等息屏，Root → Detail → Confirm | 同一任务栈溢出 |
| e22c43b0-d248-4782-a1b4-ff8ccedcc802 | 仅省略确认标签更新，再 Edge Back | 开关 PASS，待决提示处栈溢出 |
| b8b0b580-f924-4252-b157-b9ea52b6fb8e | 再省略待决提示；启动中 | hello 超时，未发刺激 |
| 0c96f034-493a-44f9-8809-2f14d9ddfe3f | 同一诊断资源；启动中 | hello 超时，未发刺激；cleanup 最终 Watch Face/display=true |
| a396ac31-e22f-45f0-95bd-a1a8f106dfc4 | 同一诊断资源，已就绪 | 确认、待决 Back、PWR Home PASS；release=ok、seq=38、Watch Face/inputBusy=false |

第一诊断 LittleFS SHA-256 d22b66f012e7f50967b01e694f6929464989d95355878a9e5fafef125260566c；第二诊断 142c9a9fc56a061b54f9e83a5819c4ae45ffeefa5f8843f7dc5639ce99a238b7。期间 ELF 未改变。诊断修改只在临时 staging 副本，不修改正式 sample 或 managed_components。两次 hello 超时完整保留，无自动重试。

## 结论与未完成项

隔离支持异步完成微任务中的同步 GUI 服务调用触发 8 KiB RuntimeJsAsync 栈溢出。实际错误、锁定源码与需要的公开能力见[上游复现](2026-10-02-runtime-js-async-stack-overflow.md)。不删产品提示作为修复；未测调整栈大小、未确定完整溢出调用链或最小安全预算。

两个回收配置与 heap 门槛尚未执行。尝试准备回收 build 时，idf.py 扩展因未设置 ESP_IDF_VERSION 在配置前 TypeError，未产生回收镜像，也未刷入；实际设备故障与这个本机环境错误分开记录。当前只改测试工具及文档，既有生产源码/资源保持原样。

008/03 未取得完整 Runtime/回收/物理及资源证据，保持未完成；新增 04 承接上游能力依赖。原始资源已写回，esptool 校验通过；恢复日志为 /private/tmp/espocket-runtime-confirm-restore-flash.log。诊断 PASS 不算正式固件验收。后续先修复 04，再继续 03 与依赖它的 009。

## 持久最小回归复核

恢复原始资源后，正式 CLI runtime-confirm attempt 20261002T155311Z-230f3686-58b1-4ed0-995d-d4ccaeaceae6 再次 FAIL，实际 Confirm 点击处 RuntimeJsAsync 栈溢出；原始报告位于 /private/tmp/espocket-runtime-confirm-regression/<attempt>/。该独立失败证明保留的 CLI 能捕获原始错误，不把临时无 GUI 资源的成功迁移到普通固件。

## 最终状态与主机门槛

恢复原始资源后的第一次只读 hello 超时，原文保存在 /private/tmp/espocket-runtime-confirm-restored-state/serial.log；另一次独立读取 hello 明确返回 71567f599，release 成功，最终 seq=5、Watch Face/display=true、App/Page 为空、canBack/backPending/inputBusy=false，保存在同目录 state.json 与 ready-serial.log。该状态核对不重新运行 Runtime 故障路径。设备保留普通固件及完整提示。

统一主机检查通过：47 项 unittest、M2 parser、180 份 Markdown，日志 /private/tmp/espocket-app-regression-host.log。没有生产 firmware 或正式资源变更，不新增固件构建通过声明；设备普通镜像的既有完整 build 身份仍按前文记录。
