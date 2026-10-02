# Runtime 异步任务栈配置补丁提案

Date: 2026-10-03
Scope: 008/04；待决提案，不是正式固件修复

## 核查

main/idf_component.yml、dependencies.lock 与实际编译 flags 一致：Runtime JS 0.8.3，Runtime Manager 0.8.2。组件 hash be4ae9c11b34b259ea9148fb3b4f475125587849d2b635bc2c8c5026883359cb，发布源码 commit 01939b5e58fd50d18339b1c35fb74c4e808962c7。此前 008/04 与上游草稿误记 JS 0.8.2，已勘误，原始失败身份未变。

[官方 Registry](https://components.espressif.com/components/espressif/brookesia_runtime_js/versions/0.8.3/readme?language=en) 当前 latest 为 0.8.3。未取得 master 源码成功响应，不能据此断言 master 是否已修复。现有 Backend::init 的 8 KiB 写死值覆盖 ThreadConfig 默认；Backend 的 scheduler 为私有对象，调整产品侧线程默认不构成该 worker 的公开配置路径。

## 提案

保留上游默认 8192 字节，只增加一个公开预算配置。ESP-IDF 通过 Kconfig，其他构建可使用同名宏。现有 ThreadConfig 的栈分配位置/优先级/串行调度保持其规则；当前提案不改变 JS 微任务执行语义。

```diff
--- a/Kconfig
+++ b/Kconfig
@@ -4,0 +5,9 @@
+
+    config BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE
+        int "JavaScript async completion worker stack size (bytes)"
+        range 8192 65536
+        default 8192
+        help
+            Stack budget for Promise resolution and JavaScript microtasks.
+            Continuations may call synchronous native service functions.
+            Tune this budget for the application's deepest supported call path.
--- a/include/brookesia/runtime_js/macro_configs.h
+++ b/include/brookesia/runtime_js/macro_configs.h
@@ -45,0 +46,8 @@
+
+#if !defined(BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE)
+#   if defined(CONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE)
+#       define BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE CONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE
+#   else
+#       define BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE (8 * 1024)
+#   endif
+#endif
--- a/src/backend.cpp
+++ b/src/backend.cpp
@@ -607 +607 @@
-            .stack_size = 8 * 1024,
+            .stack_size = BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE,
```

## 正式接入边界

当前补丁只在 /private/tmp/espocket-runtime-stack-proposal-20261003 的副本中，没有修改 managed_components、依赖锁、正式 App 或设备资源。不能将编译通过当作栈溢出已修复。

建议正式接入时以发布源码 commit/hash 为基点，保留小补丁及自动应用校验，通过 Component Manager 的受支持组件 override 指向构建产物副本；不手工改受管理缓存。升级时，同次审查依赖锁、补丁是否仍适用、最小 Runtime 回归和完整 apps 套件；若上游接受该配置则删除本地补丁。维护这个源码差异需要用户明确授权，当前 ticket 保持 needs-info。

获授权后先试 16 KiB 并测真实可用余量；不足再试 24 KiB。预算选择需覆盖原确认文字、待决提示、完整 apps 路径以及 heap 门槛；不能仅凭调大数值或单次不崩溃关闭 04。正式固件保留确认 UI，不采用此前无 GUI 的诊断资源。

## 临时副本编译结果

原实际 compile_commands 交叉编译参数用于修改后的 backend.cpp，default/16k/24k 三种宏配置全部通过。开始时旧 build/toolchain/cxxflags 引用的 specs/picolibc.specs 缺失，编译尚未进入源码；按照 IDF esp_libc/project_include.cmake 生成规则在提案临时目录重建去除 --gc-sections 的 specs，展开 response flags 后完成上述检查，没有改正式 build 文件。原失败和成功日志均为本地临时诊断；不是完整链接、不是设备或栈余量验证。

`python3 scripts/docs/check.py --markdown` 通过 181 份 Markdown。当前仓库只提交版本勘误、补丁内容和编译证据；正式 firmware、managed_components 和设备内容没有改变。
