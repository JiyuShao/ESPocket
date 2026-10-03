# 2026-10-04 — Store 当前可用性诊断

## 用户结果与范围

用户指出 Store 当前无法稳定请求或安装。打开 Root、显示缓存列表或退出不等于 Store 可用。本轮优先核对实际失败；尚未修复，不关闭在线与安装票。

## 当前设备反馈

普通镜像 24acc698e，以 `/private/tmp/espocket_store_probe.py` 自动 Home → Launcher → Store，采集 20 秒并 PWR Home，未点击下载、安装或手动 Refresh。原始串口与报告位于 `/private/tmp/espocket-store-current-probe/`。首次探针未包含并发拒绝和包不兼容的判定，误记 INCONCLUSIVE；补充同一已捕获日志的症状分类后报告 FAIL，不宣称 catalog 成功。

- 实际从缓存加载 index 与已有 metadata；ai_chatbot、camera 的远程 metadata 写入 cache，说明本次存在成功的 HTTP 传输，不表示完整在线刷新成功。
- 4 个图标提交失败均报 `Too many concurrent HTTP requests`。
- 当前普通配置 `HTTP_WORKER_NUM=1`，`HTTP_MAX_CONCURRENT_REQUESTS=1`；HAL cooperative cancel 已在生产补丁组合中，历史候选未接入的记录不能作为当前配置事实。
- 缓存 Flappy Bird 0.3.0 包扫描报 `Package does not support system type: espocket`。它证明这个实际包不兼容，不证明所有最新官方包都不兼容，也不是新安装尝试。
- SNTP 已同步；Device 报 LocalNetworkReady / internet_ready(false)，同时实际 metadata 传输成功。不能只凭 connectivity 标志将失败归为断网。
- 普通 Home 收尾通过，设备留在 Watch Face。本轮没有证实手动 Refresh、TLS retry/timeout、活动请求取消或安装可用。

## 下一步诊断边界

优先测试 Store 的 index、metadata、icon 对 HTTP 容量的协调；源码显示图标提交失败直接 advance_refresh_icon_step，而 size metadata 对容量拒绝已有延后重试。需在真实调用控制流构造回归，验证瞬时容量满不会永久丢弃图标，且停止／代际变化撤销延后工作。另检查 HTTP terminal 后释放容量，不能只扩大并发掩盖调度问题。

在线路径由 005/06 持有，兼容签名包由 005/08 持有，统一包验证与安装事务由 005/03 持有。修复 HTTP 不等于安装可用。真实可用的最终路径需稳定刷新、取得兼容可信包、安装、启动；之后才能验证更新、回滚、卸载及 Launcher。
