# Runtime Page 绑定与版本化声明（2026-10-02）

## 已完成范围

- ESPocket RuntimeFunctionProvider 使用上游公开 NativeModule 注册入口，不修改 managed_components。JS 调用只入队，由现有 App callback Owner 消费，共同 PageNavigator 持有唯一栈。
- 可见 Runtime package 安装从 resource_dir/navigation.json 读取 version 1 声明，核对 manifest 身份；解析/语义错误使真实 Core 安装失败。没有为缺声明 App 伪造 Root。
- 启动核对实际 Screen Flow 与 Root；转移前后核对 GUI 状态。不匹配时返回错误、停用默认 Back，不另维护 Flow 栈。停止、失败、卸载清理导航任务与 token。
- 队列最多 16 项、执行期限 2 秒；捕获真实 Runtime Owner 与前台代次。PWR 优先，旧代次请求报 stale_request。System 关闭取消队列和 Provider binding。
- 框架提供 50ms Core timer 刷新锁定 JS backend 的 Promise completion，App 不自行实现该基础设施。App 的 100ms 样例 timer 仅呈现确认 UI；Core 停止回收全部 App timer。
- Hello Runtime 真实 JS/GUI 具备 Root/Detail、默认 Back、确认开关、允许/取消路径。Root 无 Back，PWR 与息屏规则复用 System；JS 不维护页面栈，旧运行异步结果不会修改新运行 UI。
- [开发 API](../../../docs/development/app-navigation-card-api.md) 固定 JSON 请求/响应、十进制 token、线程、参数边界、13 个 Navigator 错误与绑定错误；[schema](../../../docs/development/schemas/runtime-pages-v1.schema.json) 发布 version 1。当前两种语言均以 Page ID 导航，业务参数保留 App 数据；Runtime 额外 parameters 显式拒绝，参数交付仍为未来扩展。

## 自动验证

- scripts/check.py：39 个 unittest、M2 lifecycle parser 与 165 Markdown 通过。真实 C++ codec/Runtime Adapter 与 Native Navigator 对比声明、push/pop/replace/reset、重复/超时 Back、停止 token 失效和呈现失败；确认失败/取消/允许测试共用生产 Navigator。
- 真实 NavigationRequestQueue 验证执行期限边界、满队列、旧前台代次与关闭取消，证明 producer 无副作用。
- Node 执行真实 JS 样例，验证动作参数、uint64 字符串 token、确认策略失败不提交、单一在途快照、stop/start 后迟到结果隔离；这不是 QuickJS 真机证据。
- 锁定 Toolkit 1.0.1 npm run build：真实 debug BPK 打包通过。
- ESP-IDF 6.0.1 clean build/link 通过，再构建最后的不一致保护。LittleFS staged app/main.js、navigation.json、Detail 与 Flow 资源逐字节等于当前源码。
- 固件大小 0x5e0fb0，App partition 43% 空闲。BIN SHA256：0aff9b02bd130643c3f4defe833122509d0b312df2d6d683c4e37d4085cfa285。
- ELF SHA256：ccc8ae941792d298aeb41f66117f51eb4a58f4c4ef80eafd50b1461815a4f234。
- debug BPK SHA256：be2d021665e3dd7e29e8934cdef5150dc70b45f467717f5304a3b96876547e68。debug unsigned 定位保持既有 M3 规则，不作为正式分发信任证据。

原始日志位于本地主机 /private/tmp/espocket-runtime-clean-build.log、espocket-runtime-final-build.log 与 espocket-runtime-host-check-release.log。临时产物未提交。

## 未验证项

未刷写设备，未执行实际 QuickJS/USB/触控/PWR 路径；Root/Detail、Promise pump、待决、恢复与回收的硬件证据归 008/03。013/04、06 的既有单次 smoke 继续等待人工，不被本次源码或构建代替。动态 Card 和 Card 目标 Page 打开属于 014/03、05，不包含在本记录中。
