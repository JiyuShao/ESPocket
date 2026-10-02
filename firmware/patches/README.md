# 上游源码补丁

本目录保存已经接受的上游源码修改。自有兼容头文件与编译适配放在[compat](../compat/README.md)；managed_components 是依赖解析产物，不手工修改。

## 当前清单

当前没有正式接入的补丁。[Runtime 异步栈配置提案](../../.scratch/008-m8-app-contract/records/2026-10-03-runtime-stack-proposal.md)仍待维护策略决定，未放入本目录，也未接入正式构建。

## 接入后的组织约定

```text
patches/
└── <registry-component>/
    └── <upstream-version>/
        ├── manifest.json
        ├── 001-<change>.patch
        └── 002-<change>.patch
```

例如 registry component 可使用 `espressif__brookesia_runtime_js`。该布局是后续接入约定，当前尚未实现补丁应用工具。

manifest 记录原始组件版本、源码 commit/hash、按顺序排列的补丁文件及其 hash、上游问题/修复链接、负责验证的工作票和删除条件。未提交的问题应链接本地草稿并明确该状态。

正式应用工具应先验证上游身份，再复制到构建目录、准确应用补丁，并让构建使用该副本。版本/hash 不匹配或补丁不能准确应用时停止，不做模糊匹配；副本和中间产物不提交 Git。工具实现与 Component Manager override 的验证由实际接入工作票负责，不把这里的目标流程写成已实现。

依赖升级时一起审查版本锁、补丁适用性及对应测试/构建/真机证据；上游提供等价修复后移除本地补丁。源码差异持续扩大时，单独决定是否维护 fork，不在补丁目录内复制整套组件源码。
