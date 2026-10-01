# App、构建与生成目录收敛

- 日期：2026-10-02
- 范围：013/05
- 基线：`28e13b3`

Hello Native 移入 native_apps/hello，Hello Runtime 移入 runtime_apps/hello。Native 的四个源码／资源／接口／测试文件及 Runtime 的十个受控文件与基线逐字节一致，仅 Native CMake 组件发现发生变化，manifest ID 和版本不变。System 继续显式安装 Native App。

LittleFS 输入移入当前 build tree 的 littlefs-root；通过 System 的 project_include.cmake 在组件 staging 前调用 Brookesia 公开路径配置接口，设备仍用 /littlefs 和 /littlefs/apps。原生成目录已保留到临时备份；当前构建图不再引用旧输入路径。新根包含 Settings、Store 和 Runtime Hello 三个包。

Kconfig.projbuild 改为 Kconfig，公开依赖与实现依赖分开；PROJECT_VER 为 0.3.0，SystemInfo 从 App descriptor 读取。Runtime 工具目录、managed components 和 Board Manager 输出仍遵循原工具位置。Host 目录规则拒绝旧目录和受控生成物。

## 构建中发现并处理的兼容问题

- 直接设置旧缓存的 staging root 被 Brookesia 配置来源标记覆盖，造成 LittleFS 输入缺失；改用其公开 setter 并在组件 staging 前执行，构建输入正确。
- 删除全局 attributes 豁免后，上游 HAL adaptor 的 display/device.cpp 因 IDF 6.0.1 hal/assert.h 的 __noreturn 宏泄漏到 Picolibc suffix 属性位置而失败。单个翻译单元使用 ESPocket compat 头将拼写改为同义 GNU 属性，保留 -Werror 与运行语义；上游源码未改。
- 实际 compile_commands 核对：-Wno-error=attributes 仅在 custom HAL，noreturn compat 仅在一个 display TU。每个 compat 文件都有版本、问题和删除条件。

## 验证

Host checks 通过；Native/Runtime 源码和 manifest 比对一致；完整重编译、链接与镜像大小门槛通过。构建目录为 /private/tmp/espocket-m78-build，普通镜像大小 0x5d1250，App 分区剩余 43%。

镜像 SHA-256：`a5ae9aa81a2a17199ce3c4f56047454e676b69992496fb79b13b434433a39c01`；ELF SHA-256：`e8bbe74ff0385c62f858a14a2158030caee730e67055f0eff854309eb7e3f0d2`。临时构建日志为 /private/tmp/espocket-refactor-05-build.log。

集中真机 smoke 仍由 04 持有；本记录不提前计入硬件通过。
