# 02 — 部署主题迁移并修复控件普通态

**What to build:** 同时部署主题固件与 Runtime 页面资源，修复按钮普通态，统一 Home Space 的系统配色。

**Blocked by:** 最终配色与按钮像素确认。

**Status:** ready-for-agent

- [x] 核对旧设备固件与 017 源码迁移未部署的差异，备份 LittleFS，仅更新 Runtime 的完整页面资源。
- [x] 复现 Theme 普通态嵌套 style 被 GUI parser 忽略；移除错误包装，保留正确 stateStyles/partStyles。
- [x] Watch Face、Launcher、Quick Settings 使用集中定义的系统配色，Battery/Brightness 保留绿色/黄色语义。
- [x] 主机检查与完整生产补丁构建通过，普通产物独立保存。
- [ ] 刷写校验、最终 light/dark 像素结果与普通状态回归记入记录。

## Comments

2026-10-04：用户确认迁移后 Native/Runtime 页面背景已正常，但按钮只有按下时正常。补充主题 schema 约束，主机检查复现同类错误并通过修复；不修改上游源码。键盘隔离测试使用独立临时镜像，结束后恢复此普通产物。

2026-10-04 深色反馈：亮度卡按钮改为黄色语义，Quick Settings 改双列，Launcher 改紧凑行。自动回归定位并修复下拉松手后排队点击误开 Settings；普通 24acc698e 完整构建、host checks、刷写校验及对应设备回放通过。新版布局最终视觉确认待用户一次反馈。

2026-10-04 隔离核查：已有构建/刷写和软件截图证据与剩余条件见[剩余证据核查](../records/2026-10-04-remaining-evidence-audit.md)。最终像素门槛保持未完成，本线未访问设备。
