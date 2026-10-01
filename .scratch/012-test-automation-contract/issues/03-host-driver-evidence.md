# 03 — 主机 Driver 与证据分类

**What to build:** 可重复运行的 USB 主机 Driver，按协议发刺激、等待快照、保存镜像和设备 identity，并区分合成、物理与视觉证据。

**Blocked by:** 02。

**Status:** ready-for-agent

- [ ] 失败和超时先执行 `release`，再采集最终快照及日志；重试作为新 attempt 保留原失败。
- [ ] 用例断言等待快照序号和目标状态，不以固定 sleep 或成功投递响应判 PASS。
- [ ] 报告明确 `synthetic-input` 不满足触摸硬件、PWR GPIO 或画面门槛。
- [ ] 至少覆盖表盘到 Launcher/Card、子页面 Back、Root 无 Back、PWR Home 与息屏唤醒的自动化路径。
