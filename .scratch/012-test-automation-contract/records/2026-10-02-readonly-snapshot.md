# 只读 USB Snapshot 源码 slice

- 日期：2026-10-02
- 范围：012/02 的只读快照；刺激与释放仍未实现。

System 从真实 Owner 读取 Shell Surface、Display State、前台 token 和统一 PageSnapshot；Settings 继续实时读官方 Flow，不复制栈。采样期间前台/Surface/显示改变或页面适配失败时返回 `invalid_state`。无前台 App 时身份字段为空、Back 字段为 false，不把未知 Runtime 页面报告为 Root。

协议在开发者模式开启后允许 snapshot，只有成功采样递增 seq；hello 按已连接的 Owner reader 公布能力。USB JSON 使用嵌套 snapshot 与七个字段，编码见 [协议](../../../docs/development/interaction-test-protocol.md)。没有公开页面参数或私有控件数据，也未增加 Assistant 注册。

## 自动验证

- 16 项 host tests、M2 parser、Markdown 通过。真实 TestProtocol 用例覆盖模式关闭不读 Owner、能力公布、实时状态而非缓存、Owner 失败不伪造 Root、不分配成功序号、重叠 dispatch 返回 busy。
- ESP-IDF 6.0.1 构建/链接与镜像大小检查通过。App 大小 `0x5d2610`，分区剩余 43%。
- BIN SHA-256：`645d6e44012b70181e13fb3eedab9770bc0bd689f7158e46f9a09ebeb2c18545`。
- ELF SHA-256：`aac736640984a75441a966d6c10d0de880aea9201b329b60d5bb8a3cd0949dcf`。
- 原始构建日志：`/private/tmp/espocket-night-snapshot-build.log`。

## 未验证与后续

未刷写，设备仍为 013 identity `e8bbe74ff`、只公布 hello；没有本轮 USB snapshot 真机响应或刺激通过项。共享触摸、语义 PWR、序列 busy 和超时/断连 release 仍属 012/02，Driver 属 012/03；完整 Runtime Page 绑定属于 014/04。
