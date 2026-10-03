# 2026-10-04 — 真实 Runtime 键盘隔离回归

## 测试边界

用户要求验证其他 App 无法读取 Runtime 键盘结果及异常停止后清理。既有主机回归已覆盖真实 Core dispatch_event、stop_app 和 queued event token 的原版失败／补丁版通过；本轮补真实 JS backend 的设备门槛。

第一版尝试由 Runtime fixture 调用 SystemCore StartApp 启动观察者，被正常权限拒绝：Only native system apps can start other apps through SystemCore。该结果不属于隔离通过。重做为临时 Native 协调器，使用真实 Core start_app/stop_app，Runtime 权限规则保持原样。

两个隐藏 Runtime App 分别正常停止和在 on_stop 故意抛错；都订阅 KeyboardClosed/Display.BacklightBrightnessChanged 并启动 200 ms 定时器，退出时不自行清理。Hello Runtime 临时入口充当输入 Owner，真实 Shell 键盘以固定合成文字为初值，USB Ready 点击产生真实 KeyboardClosed。Owner 必须收到正确结果，观察者有公开事件与定时器正向证据，跨 Owner 收到任何键盘结果都失败。停止完成后，后续真实亮度事件与定时器回调不得到达旧实例。

测试材料在 firmware/test/device/fixtures/keyboard_isolation，prepare/run 入口在 scripts/firmware。它们仅显式装配到独立镜像及离线备份的 LittleFS；普通镜像不含 Native 协调器，测试结束后恢复普通 Runtime 入口与整个备份镜像。逐文件 hash 证明其他应用和用户文件未更改，不宣称签名安装或远程发布。日志不输出输入正文。

## 输入与门槛

初始临时镜像 ELF SHA-256 a5bde49ab1ada9d2f8e7dcc1139fdd41e68a9ba49f5e4e53c5dffb8a779334be；普通恢复镜像 53fb55e37。六个锁定组件补丁与普通配置相同。临时 Native 协调器仅在独立构建的 system_power.cpp serialized callback 中调用 poll，不改 managed_components 或产品配置。

文件系统 /private/tmp/espocket-keyboard-isolation-resume.bin，准备 ledger 同名 JSON，普通文件系统 /private/tmp/espocket-theme-updated-littlefs.bin。临时编译与原始 Native 协调输入记录保存在 /private/tmp/espocket-keyboard-coordinator-build.log、espocket-keyboard-coordinator-inputs.json。

## 设备结果

最终完整回放 PASS：`/private/tmp/espocket-keyboard-isolation-resumed-final/report.json`。真实 Owner 两次收到合成输入结果；正常及故意失败退出的观察者均未收到跨 Owner 键盘结果，停止后定时器与公开亮度事件不再到达旧实例。PWR Home、随后 Native 启动与 Home 收尾通过。日志未包含合成输入正文。原 failed-stop keyboard latch 保持。普通固件与文件系统恢复结果随后补录。

夹具校准：AppChanged 虽有 schema，锁定 Core 并不发布该事件；改用真实 Display.BacklightBrightnessChanged，并在临时包明确声明 Display 0.8.2。没有绕过 manifest 服务准入。亮度只偏移 1%，finally 恢复原值。首次完整回放已验证两个 Owner 结果与两个 observer 停止，但末尾点击被 3 秒自动关闭的预期失败告警拦截；此 attempt 判定 FAIL，等待告警关闭后重放。

完整重放已验证告警关闭后的真实公开事件不再到达观察者，但临时隐藏观察者会改变 Core active App 记录，PWR 未停止可见 Owner，报告仍判 FAIL。为避免把夹具调度误当普通产品 PWR 结论，Owner 现用受准入检查的 RequestCloseApp 只关闭自身；普通 PWR 另在恢复的普通配置验证。没有改 Core active 状态规则或产品 Home 实现。

Self-close 试验触发瞬态 snapshot invalid_state，因此不采用该绕行。最终 Native 协调器在管理隐藏观察者后通过 Core resume_app 恢复仍在运行的可见 Owner，再记录停止完成；这遵循 Core start_app 改变 active App 的实际语义，不建立另一份 Core active 状态。最终恢复常规 PWR/Native 收尾路径。

最终临时镜像 67b5de497，ELF SHA-256 67b5de4977dd67fde931f9c196d3be7a48c54b2fe7ace119ee3da5743b1e62bc，bin SHA-256 2a035df3615b90508fa4373691b1b94c043b7725c99a72a9269b1b1604ee0a06；Native 协调器 SHA-256 df739fad7b3fae8ccffb8e63f43b63b2bd868b77cf738dcd8b12c0f6da488f26。最终完整身份 ledger 位于 /private/tmp/espocket-keyboard-coordinator-final-identity.json。

## 普通状态恢复

已将普通主题资源 LittleFS /private/tmp/espocket-theme-updated-littlefs.bin 与不含协调器的普通镜像 fc107fb10 写回，app 与 LittleFS 均经 esptool hash 校验。/private/tmp/espocket-compact-flash.log 记录结果。普通 Native Root/Detail/Back/Home 已通过 Owner 回放；后续紧凑 Launcher 回归另发现排队点击问题，归 017/02 修复，不将该失败算作整体导航通过。输入 fixture 与两个隐藏观察者均随整份普通 LittleFS 恢复移除，未知文件保留。失败停止后的键盘 latch 仍保持，未据此自动解除。
