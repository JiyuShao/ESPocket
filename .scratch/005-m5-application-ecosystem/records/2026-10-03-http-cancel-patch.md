# 2026-10-03 — 协作式 HTTP cancellation candidate

在 [005/06](../issues/06-adopt-online-store-stability-fix.md)既有 TLS 崩溃证据上，新增 agent 可执行确定性回归：抽取锁定版 HAL 的完整真实 EspHttpTransaction 类与实现，使用 ESP client 替身在 open/read 内建立 barrier，另一线程 cancel。原版输出 `FAIL: cancel closed HTTP handle during active operation`。

三个假设为 concurrent close 破坏 active client、取消后 retry 仍继续访问、取消与 success 重复终结。此第一补丁只证明 HAL 边界修复，不冒充 HTTP Service 的 terminal-state 验收。

版本锁定 [HAL 0.8.4 patch](../../../firmware/patches/espressif__brookesia_hal_adaptor/0.8.4/001-cooperative-http-cancel.patch)让 cancel 仅设置原子 flag，不访问 client handle。worker 在 open/write/fetch/read 返回后观察取消；取消后的 complete 为 false。client 由操作完成后的生命周期清理释放。保留 TLS verification。

取消请求是即时的，阻塞操作的实际退出仍等待 request.timeout_ms 约束，不能称为即时中断 socket。锁定 ESP-IDF 6.0.1 的 esp_http_client_cancel_request 同样修改 transport，不作为可证明安全的 concurrent 替代。

回归现自动比较原版失败和准确应用补丁副本通过，包含 open/read 两种 barrier。尚未接入产品 baseline，完整构建、retry/timeout/stop/deinit 的单次 terminal 结果及真实 Store non-download Refresh 仍需验证，不重复刷入已知崩溃版刺激它。动态安装继续禁用。

HTTP-only HAL 候选完整构建通过：ELF `5428c2d7116fdfdf114be6a519c0f1c05a837627bd25c651a519ca552c50f1b9`，BIN `6c1d01fb9223c8fb40d13a7aaa36eb3e1e6638be1739519f77923421e52a046a`。确认 HAL override 来源与完整源码 inventory 对应 patch 001，除三项 local override 外原 registry lock 精确一致。输入 manifest 保存在 `/private/tmp/espocket-http-candidate-input-manifest.json`，其 hash 与 build patch-inputs 一致；该 build 不含后来增加的 Audio patch 002。未刷入，不算 online Store 通过。

Exposure Decision：原始 HTTP transaction/cancel 是内部 HAL seam，保持 unexposed；修复不自动授予 Assistant 任意 URL 或安装包访问能力。

候选可通过独立构建入口 `--patch-set hal-candidate` 准确重建；该集合现按顺序包含 HTTP 001 与 Audio 002，普通配置仍关闭 Processor。HTTP-only 已完成构建的历史输入 identity 单独保留，不与后来 Audio-enabled 镜像合并。
