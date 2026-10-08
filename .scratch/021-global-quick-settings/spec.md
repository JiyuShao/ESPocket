# 全局下拉 Quick Settings

Sequence: 021

Status: active
Blocked by: 单个阻塞启动阶段的 Loading 响应缺口；真机顶部手势、覆盖层恢复及非 GUI 显示需设备返回

## Problem Statement

Quick Settings 只能从 Watch Face 进入；App、Launcher、Card、键盘和确认弹窗内无法快速调整系统设置。直接切换 Shell 页面会丢失原页面的呈现关系。

## Solution

顶部边缘下拉打开独立 SystemTop Quick Settings，松手提交；上滑收起后保留原 App／Shell 页面和运行实例。覆盖期间键盘与确认弹窗保留原身份及草稿，真实请求期限继续生效。

## User Stories

1. 在任何亮屏的正常运行页面，包括键盘、确认与 Loading，顶部下拉即可打开 Quick Settings。
2. 收起面板返回原页面；聊天不中断，普通内容滚动继续归 App。
3. 非 GUI 显示源可临时切回 GUI；只有原运行实例与精确 source registration 仍有效时才恢复。

## Implementation Decisions

- 沿用真实 Display 手势与 Release 提交；466px 屏顶部入口为 37px、触发距离 93px。
- Quick Settings 使用独立 SystemTop screenFlow，关闭初态隐藏；不进入 App Page 栈，不暂停或重启 App。
- 临时覆盖优先于键盘／确认弹窗的呈现；Core 请求队列、授权与操作期限保持。
- Display Owner 在同一互斥区检查当前和目标 source ID；不按同名来源复活旧 registration。
- PWR 保持 Home／息屏／唤醒规则；Home 与新 App 启动丢弃原显示源恢复目标。

## Testing Decisions

- 真实手势 arbiter、Shell flow 方法、Keyboard／Dialog 方法和 Display source 切换方法的主机回归。
- 统一 checks、Markdown 与隔离完整构建；声学、触摸、非 GUI source 和 App 私有状态保持须真机验收。

## Out of Scope

- 本轮不改变 Quick Settings 控件内容；麦克风开关不加入。
- 故障启动页、已停止系统或息屏触摸不作为可操作 Quick Settings 的入口。
- 不部署，不访问串口，不以主机结果宣称真实手势已验收。

## Tickets

- [01 — 全局顶部下拉与临时覆盖](issues/01-global-pull-overlay.md)

## Further Notes

- [交互契约](../../docs/design/product/03-interaction-model.md)
- [Overlay 仲裁](../../docs/adr/0017-overlay-arbitration-preserves-request-ownership.md)
- [Release 提交](../../docs/adr/0020-shell-navigation-commits-on-release.md)

离线实现、统一检查与完整构建已通过，候选 `e178681cf` 未部署；真实触摸和场景恢复尚未验收。结果与镜像证明见[记录](records/2026-10-08-global-quick-settings.md)。

全仓审查确认：App 主动等待期间的顶部意图可以由 Shell tick 处理；023 已将启动改为 Core 持有的分阶段请求，GUI future 等待会释放 App Owner；但单阶段内的同步准入、Runtime/Native lifecycle 与持锁 GUI parse 仍可阻塞，不能保证启动期间及时打开 Quick Settings。该场景尚未完成，不能仅归为物理验收待办。见 [023 启动整改](../023-owner-seam-remediation/issues/04-phased-app-start.md)。
