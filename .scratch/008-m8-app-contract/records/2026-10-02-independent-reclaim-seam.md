# 独立 Native / Runtime 回收测试入口

Date: 2026-10-02
Ticket: 008/02

## 源码与边界

新增默认关闭的 ESPOCKET_M8_RECLAIM_NATIVE_TEST / ESPOCKET_M8_RECLAIM_RUNTIME_TEST。原有自动息屏 Owner 路径在背光成功关闭后重新读取真实 Core resume target，只对选中的可见 App model 调用 stop_app。旧 M6 开关仍覆盖两类并保留旧日志；新增事件携带 model、manifest 与 App ID。缺目标、隐藏 App、未选中模型、息屏失败或停止状态不回收。

没有通用低内存调度器，没有新的 USB 语义命令。测试入口在真实 App callback task 上执行。Core 0.8.4 stop_app 的 cleanup_app_transient_resources 关闭加载、键盘和对话框并取消 timer；cleanup_stopped_app_gui 清除 pending binding 并释放 presentation/unload。System 的真实 stopped/failed hook 停止共享 Native Navigator 或 RuntimePageAdapter，使旧 Page、Back token 与前台代际失效；下次 start 从声明 Root 开始。未回收的模型保持原任务，wake 按 Running 状态恢复，已停止目标降级 Watch Face。

## 检查

- 生产 system_timeout.cpp 在 host 使用外部 Core/Display 端口测试正常、Native-only、Runtime-only、both 与 legacy 五种配置；覆盖选择、缺目标、隐藏目标、无 resume、屏幕失败、停止状态和 stop 失败。
- 复用真实 Navigator / RuntimeAdapter 组件已有 stop、旧 token 拒绝、relaunch Root 断言，未复制导航栈。
- 按固件真实 compile_commands 对 Native-only、Runtime-only 两条启用分支完成 ESP32-S3 交叉编译，均通过。
- 全仓 42 项 unittest、M2 parser、Markdown 通过；ESP-IDF 6.0.1 普通完整 build 通过。镜像 hash 与大小见 [共同 Card/回收镜像证据](../../014-app-navigation-card-contract/records/2026-10-02-card-owner-presentation.md)。

这是源码入口和构建证据，未构建并刷写两种回收测试镜像，未取得物理显示、触摸或 PWR 证据。008/03 保持开放，用户要求减少重复操作已落实为每条集中一次。
