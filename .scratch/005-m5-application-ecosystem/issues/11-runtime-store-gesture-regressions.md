# 11 — Runtime 图标、Weather、Store 安装与手势误点击

Sequence: 11

**Status:** resolved
**Blocked by:** 无。

## Problem

用户报告安装好的 Runtime App logo 显示不全、Weather 闪退、Store 其他 App 安装失败，以及滚动和 Edge Back 经常触发点击，要求在独立 worktree 修复。

用户补充下载期间进度一直为 0，以及 `unsafe_package_member` 拒绝 `data/*.pem.example` 和 mp3 成员。

## Implementation

- 使用 `fix-runtime-store-gestures` worktree，原修复基于 `1571929`；随后按用户要求整合最新 main `96ca9e2` 的 System/Shell 清理和性能改动，不复制其他 chat 的未提交修改。
- Launcher 图标使用 `contain` 完整呈现；Store Installed 复用 Core 已注册图标。
- 指针真实 LVGL read callback 按各 pointer 累计位移，离开 10px 点击容差后抑制控件点击；单点无 track_id 的快速大位移保持同一输入轨迹。系统手势先取消点击候选，抬手提交导航。取消、模态及息屏不补发导航。
- 使用原 Weather 包与真实 Store 安装路径定位故障，保持统一 Core gate；未得到复现证据前不扩大异步栈或放宽包准入。
- Weather root load 期间实际捕获 `std::bad_alloc`，随后 snapshot 连续失败。GUI Owner 现在把文件根文档的分配异常返回为错误，供 Core 执行已有启动失败清理。
- 原包真实 parser 的 child vector 预留容量，并在没有 interactionRefs 时直接读取原 JSON；主机测量减少 12.07% 峰值和 14.63% 保留分配，解析输出与验证错误保持一致。
- 解析优化候选已通过 Weather 的解析阶段，暴露缺少全局 `zh_CN` 字体。补充嵌入的 GB2312 中文字体资源与 16 个受控原生字号、每字号 4 glyph cache，覆盖原 Weather 的精确字号，保留原包。
- 字体原生资源由 System 持有，GUI Backend 只借用；Core 部分初始化与失败清理补丁确保 GUI 借用方先销毁，随后才能释放字体和 Display。真实 lifecycle host 回归覆盖失败返回、异常、拒绝清理投递、重复初始化与外部 Service 注册。
- 官方目录 9 个原包均已核对下载摘要，并用真实 Core 包准入代码检查；此前 4 个因 `data/files` 成员被拒绝，已按用户批准的兼容范围修复。NES、Camera 与 AI App 的安装仍要求设备具备各自声明的 Service。
- HTTP 从 1 worker 改为 2 workers，保留单请求限制；隔离构建入口同时纠正旧 sdkconfig 并验证进度调度容量。
- 用户已明确批准私有初始文件兼容方案，Core 019（整合前编号 012）已应用：原包与解包结果完整验证，私有目录禁止入口代码与 GUI root，更新保留已有 data/files 用户内容并补入新默认文件。真实安装、更新、写入与资源篡改拒绝回归通过。
- Weather 图片和 JS 模块读取改用 Storage RawBuffer，减少同一内容的字符串／RPC 副本；模块直接读入 QuickJS 所有的缓冲，失败时释放并返回空结果，不跨 C callback 传播异常。
- 禁止将约 5 MiB 指令与只读数据搬入 PSRAM，恢复 8 MiB heap 容量；独立构建入口纠正旧 sdkconfig 并核对，保留栈预算与 cache-safe Storage worker。最终干净镜像原 Weather 已真实显示上海天气，重复打开与 Home 通过；启动约 15 秒，未声称启动性能优化完成。
- Core 包解压检查分配失败返回短错误，避免 scheduler 吞掉异常后安装停留在进度弹窗；包快照和解包写入等待上限为 30 秒，超时不提交事务、保留此前版本。
- 最终干净镜像 `2a4049f5d` 已完成原 Music Player Store 安装及重启发现，全部 Owner suites、126 个跨模块 tests、完整构建与导航设备 suite 通过。

## Acceptance Criteria

- [x] 原 Launcher 图标在完整构建镜像中可完整显示。
- [x] 滚动与 Edge Back 不产生按钮点击，独立点按仍有效；完成主机及设备合成输入回归。
- [x] 原 Weather 包的闪退路径被复现并修复，启动、联网与 Home 回归通过。
- [x] 原 Music Player 的 mp3 成员拒绝与写入超时得到确认，真实 Store 安装与重启发现回归通过。
- [x] 受支持范围外的包有准确缺少 Service 说明；原 AI 包通过成员校验后准确列出缺少 AgentManager、XiaoZhi、Coze。
- [x] 实际下载过程中字节和百分比从 0 更新；原 Music Player 下载十秒画面为 `54.0 KiB / 324 KiB`、`16%`。
- [x] 失败、取消与完成的真实 HTTP host 回归通过；设备活动下载取消、重试及下载完成回归通过，安装和重启发现完成。网络故障的实际 UI 注入未执行，不能把 Service 不支持提示当作网络失败画面。
- [x] 精确补丁输入、完整 host checks、Markdown 与完整构建通过，设备结果与未验证项分别记录。

## Resolution

已在隔离 worktree 完成六项问题的修复，干净镜像 `2a4049f5d` 已 App-only 写入设备并核对 hash。原 Music Player 安装和重启发现、最终原 Weather 运行和联网、导航与 Native/Runtime 生命周期、无截图扰动的活动下载取消和重试均通过。代码与当前证据见[2026-10-06 排查记录](../records/2026-10-06-runtime-store-gestures.md)。实体手指与物理 panel 不在合成输入及渲染帧证据的证明范围内，后续人工体验验收独立记录。其它票的正式发行、Service 集成、1.5 秒退出与压力门槛保持独立。

## Comments

- 用户追加授权整合到 main 并删除其它分支。整合镜像 `55b5e929b` 已完成全部 Owner suites、138 个跨模块 tests、完整构建、App-only hash 校验、导航与 Native/Runtime 验收；原 Weather 预报、中文画面、重开与 Home 通过。Store 的实际远端刷新和 250 ms Refresh 合成点按完整场景通过；80 ms 点按两次未提交请求的失败证据保留，不声称该短点按门槛已通过。空气质量网络 fallback 和活动请求退出延迟也单独记录，见排查记录的整合小节。
- 用户授权创建 worktree 并继续排查。当前设备镜像在本次排查期间多次变化；设备测试必须核对实际 identity，避免覆盖其他 chat 的镜像。
- 合成触摸正常结束时保持本次点击判定，取消才重置；避免 LVGL 尚未消费 Release 时清理动作将普通点按改为抑制点击。
