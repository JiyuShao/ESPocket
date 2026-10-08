# Calculator 本地 Runtime App

应用身份为 `espocket.app.calculator`，版本 `0.1.0`，支持 `espocket`。圆屏界面、业务 JavaScript 和导航声明都位于本 App 的 `src/`，平台不替换界面文档。

## 构建

先在 `firmware/runtime_apps/hello` 执行 `npm ci`，物化锁定的官方 SDK；然后在本目录运行 `npm run build`。也可从仓库根目录运行：

```bash
python3 scripts/firmware/prepare_local_runtime_apps.py --app calculator
```

输出位于本目录 `dist/`，包含 BPK 和逐成员核对报告。独立 BPK 是本地未签名开发包，通过 Core 安装时需要开发者模式；固件使用 `builtin_apps.cmake` 明确列出的源码进行 staging，并按编译时不可变成员摘要验证内置 App。正式签名发行仍使用[发行入口](../../../docs/development/runtime-release.md)。

## 维护

- 修改 `src/res/root.json` 中的圆屏布局；不要在 System 中按 App ID 覆盖资源。
- 修改 `src/app/` 中的业务代码；导航状态由 ESPocket 的单一 App Page 栈管理。
- 用户配置放在 AppData，音频资源放在 AppFiles；更新时保留用户数据。
- 来源版本和原包摘要见 `upstream.json`。原包未附带许可证，本次为本地适配，尚未核实再发行条款，不上传 Catalog。

迁移状态、设备替换和证据由 [020](../../../.scratch/020-local-runtime-apps/spec.md) 持有。
