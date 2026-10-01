# System 拆分与 PWR Owner

- 日期：2026-10-02
- 范围：013/04
- 基线：`39560d0`

System 的启动装配、App lifecycle、导航、显示和 PWR 分别进入职责文件，公开类和状态 Owner 不变，内置 App 仍显式安装。

PowerKeyMonitor 输出待决短按事件，System 用 take_short_press 消费并执行原有 Home/息屏/唤醒规则。ShellHost 的通用 tick 在原有 50ms App callback task 中调用 System，位于原先 PWR 消费位置；Shell 不再接触按键计数或转发 PWR Home。原有同一 tick 多个短按合并语义保留，不新增执行线程。监控启动清空旧待决事件，System 停止 guard 保留。

Host checks、Owner 结构断言、System 产品字符串比对与完整固件构建通过。构建目录 `/private/tmp/espocket-m78-build`，临时日志 `/private/tmp/espocket-refactor-04-build.log`。尚未刷机或执行集中 smoke；04 仍等待最终镜像上的人工结果，05/06 的独立源码整理可先进行。
