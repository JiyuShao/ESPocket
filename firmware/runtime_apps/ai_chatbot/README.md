# AI Chatbot 本地 Runtime App

应用身份为 `espocket.app.ai_chatbot`，版本 `0.1.6`，支持 `espocket`。圆屏界面、业务 JavaScript 和导航声明都位于本 App 的 `src/`，平台不替换界面文档。

## 构建

先在 `firmware/runtime_apps/hello` 执行 `npm ci`，物化锁定的官方 SDK；然后在本目录运行 `npm run build`。也可从仓库根目录运行：

```bash
python3 scripts/firmware/prepare_local_runtime_apps.py --app ai_chatbot
```

输出位于本目录 `dist/`，包含 BPK 和逐成员核对报告。独立 BPK 是本地未签名开发包，通过 Core 安装时需要开发者模式；固件使用 `builtin_apps.cmake` 明确列出的源码进行 staging，并按编译时不可变成员摘要验证内置 App。正式签名发行仍使用[发行入口](../../../docs/development/runtime-release.md)。

## 维护

- 修改 `src/res/root.json` 中的圆屏布局；不要在 System 中按 App ID 覆盖资源。
- 修改 `src/app/` 中的业务代码；导航状态由 ESPocket 的单一 App Page 栈管理。
- 配置格式见[上游配置说明](src/data/README.md)。
- 用户配置放在 AppData，音频资源放在 AppFiles；更新时保留用户数据。
- 来源版本和原包摘要见 `upstream.json`。原包未附带许可证，本次为本地适配，尚未核实再发行条款，不上传 Catalog。

迁移状态、设备替换和证据由 [020](../../../.scratch/020-local-runtime-apps/spec.md) 持有。

## 主题与电源声明

普通界面和动态导航绑定引用产品语义颜色，由真实 GUI Runtime 按当前文档主题解析；App 不另存主题偏好。`package.keep_screen_on: true` 请求前台 Running 时免自动息屏；System 仍执行显式 PWR／Home，实例停止后不保留豁免。声明由 Core 严格解析并经原有包信任路径校验。

启动后 Agent 列表、目标与网络状态通过原 Runtime 异步桥读取，Agent 配置和 AppData 配置／Coze 私钥读取也通过该桥提交；业务初始化期间显示加载状态，停止／重启会撤销旧结果。Core 完成 App 启动不代表远端 Agent 已准备完毕。服务绑定与 GUI 操作仍有同步调用，JSON 解析也仍在 App 执行链上，本包不宣称所有 Owner callback 已满足 250ms。

## 异步操作归属

App 内部的 operations module 集中维护 discovery、network、configure、start 与 wake 的 pending 归属。每次恢复结果都核对本次 App 运行、实际依赖 handle、Agent 选择代次和同类操作身份；切换 A→B→A 不会复活旧结果。旧结果的 finally 也不能清掉新请求的 pending。停止或重新开始使所有旧结果失效，真实 Agent 运行状态仍由原事件提供。

失效仅撤销 App 对结果的提交权，不声称取消已提交的 Brookesia 操作；原停止、暂停和重试策略保留。Started/Awake 等实际事件使已完成的操作归属结束。没有请求身份的服务事件仍按原路径消费，本实现不声称可以识别其跨目标迟到归属。
