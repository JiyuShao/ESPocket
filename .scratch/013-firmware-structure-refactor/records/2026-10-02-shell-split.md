# Shell 拆分与 ShellHost

- 日期：2026-10-02
- 范围：013/03
- 基线：`b4a9249`

CircularShell 仍是唯一状态 Owner，生命周期与动作处理保留在 circular_shell.cpp，GUI descriptor、导航手势、键盘与状态刷新进入各自实现文件。ShellHost 是持有 std::function 的值对象，只表达产品查询与命令；原 PWR count/provider 保留在独立的过渡参数，未放入 ShellHost。

Host checks 通过；Shell 所有产品字符串与基线集合一致，GUI JSON 未变化；完整固件构建通过。构建目录为 `/private/tmp/espocket-m78-build`，临时日志为 `/private/tmp/espocket-refactor-03-build.log`。没有刷机或新增真机通过项，集中 smoke 留待 PWR Owner 切换之后。
