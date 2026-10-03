# 09 — 核对并统一产品主题消费

**What to build:** 核对官方 Settings/Store 的白色页面是否来自主题选择、持久偏好或解析/应用缺口；让遵循主题 token 的 App 使用真实系统主题，保留 App 自有界面的边界。

**Blocked by:** None

**Status:** resolved

- [x] 记录当前 theme ID、持久偏好与实际 Settings/Store 解析/应用结果，不凭资源存在宣称全局主题生效。
- [x] 在实际 Owner seam 修复确定的缺口并补充真实解析或渲染契约回归，避免另一套主题状态。
- [x] 完整构建、系统页面及官方 App 的有限视觉验收通过；硬编码颜色的 App 不冒充已自动跟随主题。

系统已注册 dark/light 资源，GUI Runtime/Core 持有主题；当前用户报告 Settings/Store Root 白色。实际原因仍待验证。见 [缺陷记录](../records/2026-10-03-display-glyph-theme-defects.md)。

## Comments

2026-10-03：已确定启动装配缺口：主题注册发生在 Core init 返回后，而官方 App 的 preload_dom 会在安装时加载文档；原装配也未调用主题恢复。主题注册与恢复改到 System on_init 的首步，在安装 App 前完成。使用 Core 的 stored preference、begin/mark restore 与 system_gui.set_theme；没有另一份偏好存储。实际方法的主机回归覆盖首次 dark、持久 light、未知偏好、解析失败和 backend 失败。Settings 继续采用上游“保存偏好 → 重启确认”的机制，现存页面不冒充支持实时重套主题。

2026-10-03 更新：旧保存的 Light 恢复与经 Settings 确认后的 Dark 恢复均有真实启动日志，确认后 Settings 仍可导航。还需一次 Settings/Store 背景视觉观察；不凭日志代替像素验收。

2026-10-03 用户确认：Settings → Display 背景深色，文字与控件显示正常。Store 背景仍待独立观察，整票暂不关闭。

## Resolution

2026-10-03：产品主题在 App DOM 预载前注册与恢复；真实启动日志验证 Light/Dark 保存与恢复，System 方法的主机行为回归覆盖选择、顺序与失败。完整构建和确认重启后导航通过；用户分别确认 Settings → Display 与 Store 均为深色、显示正常。共享 styleRefs 跟随产品主题，硬编码界面保持 App 自有边界。修正提交 `de10dde`，具体镜像身份及限制见[记录](../records/2026-10-03-display-glyph-theme-defects.md)。
