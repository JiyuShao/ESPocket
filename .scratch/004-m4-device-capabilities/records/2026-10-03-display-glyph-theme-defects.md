# 2026-10-03 — 返回字形、主题与亮度缺陷

## 用户观察与现场

当前普通 Audio 修正镜像 `b9b4a413f`。用户确认 Launcher 其他行为正常，但箭头显示空心方块；Settings/Store Root 白色；随后 Settings → Display 亮度滑块卡死。前期验收不能证明这些新路径正常。

只读 10 秒采集无新增日志；hello 正常且身份匹配，snapshot 返回 invalid_state，现场日志 `/private/tmp/espocket-brightness-freeze-usb.log` 与 state.log。不声称硬复位、panic 或具体 deadlock 根因。保存现场后以现有启动诊断重启，`/private/tmp/espocket-brightness-repro-reset.log` PASS。

## 亮度复现进度

独立重放脚本 `/private/tmp/espocket_settings_brightness_repro.py`：第一次 Display 行坐标误进 More，属于校准失败；修正 y=312 后进入 settings.display，但滚动后四条轨迹尚未命中实际 brightness Owner，判定 INCONCLUSIVE。不能将其当作卡死复现或修复通过；用户确认滑块在底部、需要滚动，但不希望截图；后续由 Agent 自动校准，不要求照片。追加无滚动和两次滚动后的扫描仍为 INCONCLUSIVE；一次初始脚本误计入唤醒时的亮度日志，已改为仅计入本次拖动之后的 Owner 写入，旧结果不作为 PASS。同步 service/回调循环等待、事件拥塞与 debug 绘制是待证伪假设。

自动校准后：两次从 (370,370) 到 (370,130) 的分段上滑，再在 y=380 从 x=140 拖至 x=320，实际 HAL 记录 51/59/68/76。同一实际轨迹往返 12 次，每次均检查本次日志包含亮度写入且 Settings Display 可读取；最终 PWR Home 回表盘。`/private/tmp/espocket-settings-brightness-repeat-result.log` 与 repeat-serial.log 保存结果。此项只证明这些合成轨迹通过，尚未重现用户的卡死，不关闭 004/08。

一次十点长请求超时后，只读 hello/snapshot 均成功，页面为 settings.display，inputBusy=false；它不具有原现场的 invalid_state 症状，不算 GUI 卡死复现。改用六点较短帧后成功；长帧丢失原因未定，不宣称 USB 根因已证实。


## 返回字形

15/16sp 小于当前启用的 Montserrat 18/20/32，锁定 GUI backend 会回退 LV_FONT_DEFAULT_UNSCII_8；该字体不包含 Unicode 方向箭头。新增 Shell glyph coverage 回归旧资源 RED（无配置文字字体可用），更换为 18sp 与真实字体 cmap 内的 LVGL 方向符号后 GREEN。四个 Home Space 返回提示统一处理；未新增字体依赖。主机 checks PASS，隔离构建完整 PASS（`/private/tmp/espocket-arrow-fix-build.log`，App 大小 0x735b10）；物理显示尚待验证，011/01 不关闭。构建 BIN SHA256 `b3fa26ae26b6f75209dbb8c2038459bafac992aee47bd7ba8a7950a6154dd40d`，ELF SHA256 `07038e5ec81db1c5ae485d2ddbb76189e84d9e77ee67420adeedc931fc7eae98`；尚未刷入，当前设备保持 b9。

## 主题边界

系统初始 environment.theme_id=dark，注册 dark/light 资源；Settings/Store 使用 App styleRefs，Settings 可读取保存主题并请求系统主题切换。实际白色页面的 active theme、持久偏好及样式应用仍待核对，不把它称为有意的白色产品设计。共享主题能够覆盖遵循主题 token 的页面；硬编码颜色需 App 适配，不强行改写任意 App 文档。

## 实际主题切换尝试

用户要求切换主题。普通 b9 镜像自动进入 Settings → Display，依次点 Light (233,160) 与 Dark (233,290)。Light 确实命中 action，但日志报告 `Message dialog is not supported by this system` 与 `Failed to show restart confirmation dialog`；页面仍可读取。官方实现先保存主题偏好、再显示重启确认，因此不把这个失败误报成偏好完全未写入或主题已经生效。随后 Dark 点击无同类错误，按当前主题路径恢复 Dark 偏好；未执行重启，也未验证像素/active theme。日志保存在 `/private/tmp/espocket-theme-switch-serial.log`、theme-switch-result.log。004/09 继续待定位，并包含重启确认 UI 缺口。

最终 `python3 scripts/check.py` PASS；锁定 Settings 0.8.3、Boost 0.6.0、LVGL 9.5.0 的 host 依赖校验 PASS。

## 主题与系统确认弹窗修正版

System 实现锁定 Core 的公开 show/update/hide hooks，Shell 在圆屏安全区域呈现最多三个按钮和可滚动说明。LVGL 回调只记录选择，Shell App 任务在 UI 清理后调用 Core complete_app_message_dialog；Core 继续管理请求归属、队列和 App 停止清理。modal 期间禁止底层 Home Space/Edge Back 手势，PWR Home 仍由 System 处理。呈现自动超时按 options 回交 Core。没有修改 managed_components，也没有另建 App 页面栈。

启动装配将 theme 注册提前到 System on_init 的首步，先于会 preload_dom 的官方 App 安装；使用 Core 已保存偏好选择 dark/light，调用 set_theme，未知偏好和后端失败显式报错。旧装配在 Core init 返回之后才注册 theme，且没有恢复保存的主题。Theme 恢复真实方法与 dialog 呈现真实方法均有主机行为回归；modal 手势共享仲裁也有回归。

最终 checks PASS（`/private/tmp/espocket-theme-dialog-final-host.log`），完整构建 PASS（theme-dialog-final-build.log）。依赖锁与 playback-only 配置验证 PASS，沿用已接受 Audio 候选，不扩展 Recorder/AFE。最终镜像 `c21fec136`，BIN SHA256 `9d1f69b9898e51fd57ff40fc82fe10f0c4fc16b5aab186d58a43319aab38ca7f`，ELF SHA256 `c21fec136acefc27b46350a0cd34ff7d66bfaa9701f1e8481c872893dac9e49a`；配置、patch inputs、产品输入 hash 与产物保存在 `/private/tmp/espocket-theme-dialog-preserved/`。仅 App 0x60000 刷写及校验通过，启动恢复此前保存的 light 并完成 ESPocket started。启动有一次原 HAL touch read 警告，后续输入成功；未把它冒充 panic。

自动真实设备重放：Later 关闭确认并保留 settings.display；再次选择主题后 PWR Home 关闭 dialog 并回 Watch Face。之后正常点击 Dark 的立即重启按钮，HAL restart 执行，启动读取 Dark 并记录 Product GUI theme active: dark；Watch Face 和重新进入 Settings → Display 通过。原始结果在 `/private/tmp/espocket-theme-later-home-result.log`、theme-dark-result.log 及相应 serial.log；诊断脚本 theme_dialog_e2e.py 为临时校准重放。保留上游“选择时保存偏好”的行为，Later/Home 只关闭当前确认，不声称撤销已保存的主题。当前设备停在 Dark 的 Display 页，颜色/字形视觉门槛待一次用户反馈；合成输入不验证真实触摸硬件。004/08 的原始卡死尚未复现，不能借主题修正关闭。

用户已确认修正版 Settings → Display 为深色、显示正常。Store 自动点击先落在列表间隙，追加滚动后的点击也未命中 App（快照仍为 launcher）；这是坐标校准失败，不是 Store 崩溃或通过。设备留在 Launcher，待用户一次观察 Store 背景与返回字形。日志 theme-store-result.log/serial.log 仅代表最后一次未命中尝试。

## 最终显示验收

用户确认修正版“箭头正常，Store 也是深色”，并已确认 Settings → Display 深色、显示正常。字形条件与两个官方 App 的 Dark 呈现通过；源码与 host/build/设备业务证据对应本地提交 `de10dde`。004/09 与 011/01 关闭，011 Effort 关闭；不扩张为所有硬编码 App/Shell 界面都实时跟随主题。原 Settings 亮度卡死保持 004/08 开放。
