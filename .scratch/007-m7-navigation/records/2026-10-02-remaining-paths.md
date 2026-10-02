# 系统导航剩余路径对账与补测

Date: 2026-10-02
Scope: 007/03；不重复用户已接受的固定循环、亮度或 Wi-Fi 操作。

## 已有证据对账

- 两轮系统导航与亮度/Wi-Fi 实际效果继续引用本 Effort 的 two-navigation-loops 记录。
- 013 的 final-verification 记录保存用户“全部正常”：包括 Quick Settings 上滑、Launcher 顶部下拉返回、不误开 App、Native Back 和 PWR/显示路径，镜像 e8bbe74ff；不改写为当前镜像物理结果。
- 014 的 card-device-run 保存 Card fixture 37 步与用户接受；覆盖序列边界。此前 Runtime 空白、重启后恢复与未确定根因继续保留。
- 普通镜像 71567f599 的 34 步 navigation 与新 CLI 35 步结果分别见 014、015 记录；物理/GPIO 声明保持 false。

## 剩余路径自动套件

新增 device/e2e/surfaces.py，通过既有客户端和执行器访问同一 Owner 状态，不增加线缆命令或第二份页面栈。profile 增加 Quick Settings 的 Settings 按钮坐标和 Native 普通横滑；当前 Settings 0.8.3 稳定映射 pageId=settings.root、manifestId=brookesia.general.settings。

一次 surfaces attempt 20261002T145324Z-ad0d0a4e-ad62-462a-a75e-8e4b1432f557：PASS，22 步（含初始唤醒），真实普通镜像 71567f599，设备 ESPocket-Waveshare-A0F262E30B68。原始 report.json/serial.log 保留在 /private/tmp/espocket-m7-surface-attempts/<attempt>/。覆盖普通 Battery/Brightness outward 边界不循环、两个 Card/Quick Settings/Launcher/Settings/Native Detail 的 PWR Home、Quick Settings 打开 Settings Root、Native Detail 非边缘普通横滑及有限负向观察。

最终 release=ok，seq=826，Watch Face/display=true，foregroundAppId/pageId 为空、canBack/backPending/inputBusy=false。该报告为 synthetic-input，不代替手指/实体键或画面。

## 集中物理确认

实时日志 /private/tmp/espocket-m7-remaining-physical.log。仅发出一次四组路径：Quick Settings → Settings → PWR；Launcher → PWR；Battery/Brightness 各自 PWR；Native Detail 中部横滑保持 Detail → PWR。待用户答复，尚不关闭 007/03。

本次只增加测试工具与文档，没有固件/App 实现或资源改动，不重编译/刷写当前普通镜像。

## 主机门槛

`PATH=/Users/jiyu/.nvm/versions/node/v22.22.2/bin:$PATH python3 scripts/check.py` 通过：46 项 unittest、M2 parser 和 177 份 Markdown。实际 surfaces 设备 attempt 的 release 与最终快照检查通过，原始窗口未见 panic、watchdog、assert、App start/stop 或输入清理错误。该结论仅属于本窗口，既往失败仍保留在原记录。
