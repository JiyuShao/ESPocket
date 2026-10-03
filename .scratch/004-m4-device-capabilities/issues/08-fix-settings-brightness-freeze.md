# 08 — 修复 Settings 亮度滑块卡死

**What to build:** 在实际 Settings/Display/GUI Owner 边界修复拖动亮度后页面卡死，不以屏蔽亮度功能代替修复。

**Blocked by:** 一次有限实体触摸观察；候选修复、构建与设备自动回归全部通过。

**Status:** ready-for-agent

- [x] 建立能触发实际 SetBacklightBrightness 并检查 Display 页面响应的失败回归，区别坐标未命中与真实卡死。
- [x] 定位同一 LCD SPI 设备的背光/刷屏并发与输出锁缺口；真实 Owner Display 0.8.2 修复按 ADR-0016 维护。
- [x] 必要 host checks、完整构建、真实设备自动滑块重放 100 次与 Back/PWR Home 通过。
- [ ] 只做一次必要实体触摸复核；当前自动输入不冒充物理验收。

用户于 2026-10-03 报告 Settings → Display 滑块卡死。只读 hello 仍响应 `b9b4a413f`，snapshot 返回 invalid_state；没有采集到 panic。现场保存后已重启恢复；不把 USB 可响应当作 GUI 正常。证据见 [缺陷记录](../records/2026-10-03-display-glyph-theme-defects.md)。

## Comments

2026-10-03 后续：用户补充触发顺序为主题选择 → 取消 → 拖动亮度。`c21fec136` 原现场仍有 hello 成功而 snapshot invalid_state，已保存后恢复。合成输入命中主题请求、Later 结果及真实亮度服务的一次路径正常；不能宣称已复现或修复卡死。同步 Display 调用与事件刷新 GUI 的竞争仍是待证假设，不据此直接添加补丁。

2026-10-03 修正版 `ac2485543`：用户再次强调“点击主题 → 弹窗 → Later → 调亮度”的卡死顺序。只读采集时设备已息屏，hello 与 settings.display 快照均成功，没有证明此前物理触摸正常。加强自动路径为取消后调亮度、观察 12 秒、实际边缘触摸返回 settings.root；本次全部通过，故卡死仍未复现、未修复，不能关闭本票。当前需确认该报告是否来自本修正版及唤醒后的物理触摸响应；不要求重启或截图。

2026-10-03 更正与最小化：主题/Later 不必要；旧 ac2485543 仅左右拖动滑块在第 60 次实际服务 timeout、快照随后 timeout。Display frame/backlight 方法的同一 LCD IO 重叠有稳定主机失败，候选在输出 draw_mutex 下串行化并检查锁顺序。完整证据、JTAG 自动复位限制和未完成设备门槛见[IO 串行化记录](../records/2026-10-03-display-io-serialization.md)。

候选 e15f52712 已刷入：旧 ac2485543 第 60 次失败，修正版同一最小路径 100 次通过，每次命中 Owner，Back/Home 与清理通过。保留上述唯一物理观察，未虚报为已验收；原始源码保持未修改。
