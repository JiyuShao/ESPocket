# 08 — 修复 Settings 亮度滑块卡死

**What to build:** 在实际 Settings/Display/GUI Owner 边界修复拖动亮度后页面卡死，不以屏蔽亮度功能代替修复。

**Blocked by:** 原卡死的稳定复现；自动轨迹已命中真实滑块，往返 12 次通过，用户无需截图。

**Status:** ready-for-agent

- [ ] 建立能触发实际 SetBacklightBrightness 并检查 Display 页面响应的失败回归，区别坐标未命中与真实卡死。
- [ ] 定位同步服务、事件回调、GUI 调度或 debug 绘制的实际阻塞，必要补丁按 ADR-0016 维护。
- [ ] 必要 host checks、完整构建、实际滑块重放与 PWR Home 通过；只做一次必要物理复核。

用户于 2026-10-03 报告 Settings → Display 滑块卡死。只读 hello 仍响应 `b9b4a413f`，snapshot 返回 invalid_state；没有采集到 panic。现场保存后已重启恢复；不把 USB 可响应当作 GUI 正常。证据见 [缺陷记录](../records/2026-10-03-display-glyph-theme-defects.md)。

## Comments

2026-10-03 后续：用户补充触发顺序为主题选择 → 取消 → 拖动亮度。`c21fec136` 原现场仍有 hello 成功而 snapshot invalid_state，已保存后恢复。合成输入命中主题请求、Later 结果及真实亮度服务的一次路径正常；不能宣称已复现或修复卡死。同步 Display 调用与事件刷新 GUI 的竞争仍是待证假设，不据此直接添加补丁。
