# M1 — ESPocket System acceptance

> 文档类型：阶段判定与证据索引。详细历史叙述见 [`records/`](records/2026-09-25-acceptance-report.md)。

## 判定

- Status: `PASS`
- Date: 2026-09-25
- M0: `WAIVED`, not `PASS`
- Release marker: `v0.1-system`

## 固定门槛

| Gate | Accepted result |
|---|---|
| Platform Baseline | ESP-IDF 6.0.1、ESP32-S3、Waveshare 1.75C selector 与解析后的 Brookesia v0.8 组件完成构建 |
| Clean reproduction | 删除生成目录后重新解析 37 项依赖、生成板配置并完整构建通过 |
| Hardware smoke | Launcher、最终圆屏 UI、触控、Home gesture 和降级状态均由项目所有者确认 |
| Cold boot | 5/5 到达 `ESPocket started` |
| EN/software reset | 10/10 到达 `ESPocket started`，无 panic、watchdog、assert 或 heap corruption |
| Fatal diagnostics | Storage/Display 启动失败保留串口诊断并停止启动，没有自动重启 |

## 证据索引

- [2026-09-25 acceptance report](records/2026-09-25-acceptance-report.md) 保存环境、镜像尺寸、内存、复现命令、真机观察和已知问题。
- 本阶段没有保留独立原始成功串口文件；报告明确记录这一证据边界。

## 历史边界

M0 官方基线风险由项目所有者明确豁免。该事实保持 `WAIVED`，不能被后续成功构建改写成 `PASS`。
