# 2026-10-08 — 全局 Quick Settings 离线实现

用户要求任何页面／场景下拉打开 Quick Settings。本轮使用顶部边缘入口保护 App 中部滚动；466px 板的顶部区域 37px、触发距离 93px。Watch Face 原有整页下拉仍可使用。设备不在用户身边；没有访问串口、播放声学测试或部署。控件内容未改版，未添加麦克风开关。

## 呈现与所有权

Quick Settings 从 shell_pages 移至独立 SystemTop quick_settings_flow，初态为隐藏屏。打开时不停止、暂停或重启 App，也不改 App Page 栈或导航来源；上滑收起恢复之前的 Shell Surface。Launcher 分页与 Card 原位置保留；内容区域的 Launcher 下拉仍按原分页／Home 规则运行。PWR Home 关闭临时覆盖，新 App 启动不恢复旧显示源。

Keyboard／Dialog 保持真实 Core 请求身份；面板期间隐藏并阻止提交，键盘 textarea 草稿保持。收起后重新核对原请求；Dialog 自动关闭期限继续运行，没有暂停原 Owner timeout。Quick Settings flow 打开／关闭失败不报告转移成功；Shell stop 的 Quick Settings 关闭失败保留 cleanup pending，但继续撤销其他资源，拒绝启动新实例直到清理重试完成。

非 GUI 显示通过真实 Display Owner 暂选 LVGL，记录原注册 ID、GUI 注册 ID 与 foreground token。恢复仅允许同一个运行实例与原 source registration，不能覆盖更晚的来源选择。Display 002 补丁把当前／目标 ID 校验与切换放在同一个 Owner mutex 内，避免读取 source inventory 后同名来源重注册的竞态；原始 managed source 未修改。

## 主机验证

新增手势测试先在旧 arbiter 上失败：modal 的顶部下拉不能取消 pointer，也不能打开 Quick Settings；修复后覆盖 App／Launcher／Card／Keyboard／Dialog、短距离前导样本、松手提交与取消。普通 App 中部下拉不产生系统意图。真实 Shell show_surface／dismiss 方法验证独立 flow、原 Surface 与 Launcher 分页保留、GUI／路由失败及 Home 关闭路径。

真实 Dialog／Keyboard 方法覆盖隐藏点击拒绝、草稿恢复、原请求失效及原始超时仍执行；已有 Overlay idle 回归曾发现新增的无用 LVGL lock，改为仅在显示状态变化时获取锁后通过。真实 on_action 验证面板关闭后的排队旧动作不能更改 Owner 状态。真实 Display set_active_source 与 System 临时路由方法覆盖 source 替换、active Owner 变化、foreground token 变化、显式放弃恢复、同名重注册竞态和失败前不改变输出／lease。

## 构建过程

使用 `/private/tmp/espocket-local-runtime-20261007-v4` 的精确缓存依赖与已批准补丁。全局 Quick Settings 候选关闭软件 AEC，保留产品当前 250ms 半双工 capture suppression。首次完整构建发现 System 未包含真实 Display Owner 头文件，编译失败；增加明确 include 后以最终源码重新构建。初次日志 `/private/tmp/global-quick-build.log`，最终输入 `/private/tmp/global-quick-final-build-inputs.json`，最终构建日志 `/private/tmp/global-quick-final-build.log`。

## 未验证

真机顶部手势、触摸穿透、Chat／Settings 子页／Launcher 第 2 页／Card／Keyboard／Dialog／Loading 的保持与返回，以及游戏等非 GUI source 的真实暂停／恢复均待设备返回。既有 Chat 滚动 timeout 仍由 [020/03](../../020-local-runtime-apps/issues/03-conversation-stutter-echo.md) 持有，不能用此次手势主机通过将其关闭。真机次数与回退规则由 [01](../issues/01-global-pull-overlay.md) 持有。


## 最终离线结果

最终 `python3 scripts/check.py` exit 0，Shell 的 14 项回归与 host 的 165 项回归通过（host 2 项因 LittleFS 环境跳过），统一检查通过。完整构建通过，App 11,202,368 bytes／14 MiB，分区余量 24%，镜像身份 `e178681cf`。App SHA-256 `2c8853c7b56d5c1d48736532cfc822632fe9bfff0e4f2166d6c3cf6aeb87de66`；ELF SHA-256 `e178681cfc271a5ca81d77fd688ce93e56c9c3e9c23afcfd7545ae92cbcd57ab`。

镜像、ELF、有效 sdkconfig／lock／主组件 YAML、精确 Display 补丁 manifest、源码输入证明及 release.json 保存在 `/private/tmp/espocket-global-quick-settings-release/`。最终复制的源码与配置 hash 逐项核对通过；构建没有打开软件 AEC。原始统一日志 `/private/tmp/global-quick-final-check.log`。收尾记录更新后另跑 Markdown，`git diff --check` 通过。

此固件内置 Chat 为 0.1.2，与当前设备 0.1.1 不同；未来部署必须从最新设备 LittleFS 备份用 `stage_local_runtime_apps.py --update-builtins` 保留更新，逐成员核对候选 immutable allowlist 后再写 App 和匹配的保留镜像，不能只刷 App 假定旧内置包已匹配，更不能直接执行整体 `idf.py flash`。回退使用已核对的 `c60a29d3b` 和部署前匹配备份，先保留候选期间新增的用户内容。当前设备未改动。
