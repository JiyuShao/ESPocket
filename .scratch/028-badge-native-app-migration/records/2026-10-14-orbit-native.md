# 2026-10-14 太阳系 Native App

## 范围与来源

继续执行 [028/06](../issues/06-native-games-and-toys.md)，交付 `firmware/native_apps/solar_system`、身份 `espocket.app.solar_system`。上游 The-Badge commit 为 `76172dfaf0fa0ffedee91a61da3261afdde56ce3`，`main/apps/orb.c` SHA-256 为 `3791ae9e8da2cfcf580f1659efdc5609e05c71836c530d6f7e72e9212f443c9f`。四份 `orb_tex_*.h` 材质、MIT LICENSE 与 NASA NOTICE 保持锁定原字节，在独立 App 目录发布，不编译参考输入目录。

源码核查澄清：原作叫 Orbit，是手指旋转月球、地球、太阳和木星的球体玩具，不含行星轨道或 IMU。此前计划文字里的“轨道”不作为新增功能依据。菜单保留原作圆形按钮颜色/尺寸，文字中文化；选择与球体页使用既有 PageNavigator，系统 Back 返回列表、Home 后从 Root 重开。

## 实现与边界

球体投影、光照、太阳自发光、地球亮度、UV 缓存、2×2 移动绘制和最终清晰帧保持原作数学。App Owner 执行轻量拖动/惯性，私有线程执行查表初始化和像素绘制；一个合并姿态、两个不可变图像槽限制积压。材质/查表与图像均在 PSRAM，只有球体页持有；工作线程为 core 1、priority 3、6 KiB PSRAM 栈。

受控触点取消、换指及越出球体后清空操作并等全松开。菜单只接受同一按钮的按下/释放，列表没有原始 LVGL 点击回调。暂停取消待处理渲染、确认当前工作收尾，恢复保留姿态并清除旧惯性/触摸，不补算暂停时间。停止确认退出后再卸载图像；超时失败保留真实 Owner。GUI 派发失败会重新提交同一姿态，避免丢失最终静止图像。动画不报告活动。

资源、计算、输入与生命周期都属于 App；System 仅新增依赖、注册与 PageNavigator 装配。没有修改 Core、HAL、managed_components、上游补丁或分区，没有新增音效、假传感器或第二个框架。具体入口见 [App README](../../../firmware/native_apps/solar_system/README.md)。

## 离线验证

专项 7 tests 已通过：直接执行锁定原作投影与输入/惯性代码；四材质的九组姿态逐像素一致（含移动状态打开后的首次清晰帧）；连续拖动及 600 次衰减更新与原作姿态一致。另验证四材质的多种极点/倾斜/侧倾、两图像槽并发持有、合并待处理姿态、真实 host 线程暂停/停止/重开、三处内存分配失败、每处 LVGL 部分创建失败、缓存/图像寿命、导航失败及旧实例回调。

生产 RGB565 渲染预览已检查（月球、地球、太阳、木星）。预览只用于离线像素检查，不代表真实 LVGL 页面、中文字体、圆屏触摸、持续帧率、功耗或可用 PSRAM 已验收。

最终统一检查、sanitizer 与完整隔离构建均已通过，具体证据见下文。本批不部署；[06](../issues/06-native-games-and-toys.md)、[08](../issues/08-offline-build-candidate.md) 保持未关闭，重力迷宫、IMU、BLE HID、蓝牙遥控及 [09 真机验收](../issues/09-device-acceptance.md) 仍待完成。

## 构建过程

首轮 v1 在依赖配置阶段主动中止，未生成成功 candidate。复核发现移植首次渲染会因移动姿态使用低精度，延后建立 UV 表；修正为遵循原作 orb_start 的首次清晰帧，并覆盖初始请求被合并的情况。原始日志与准备输入保留；后续使用新 workspace 冻结修正输入。

v2 在编译前头文件复核时主动中止：锁定 LVGL 的 lv_obj_flag_t 是枚举，C++ 中按位或的 int 不能直接传入；分开清除两个 flag 并将 host 替身改为真实枚举签名。v1/v2 均无成功 candidate，最终构建另用 v3。

v3 在最终逻辑复核时主动中止，尚未生成 candidate：持续被系统拒绝的指针帧会重复取消；移植每次取消都标记重绘，会让已静止球体继续刷新。改为只有实际拖动/惯性取消才标记变化，恢复单独请求一张清晰帧；加入连续 100 次取消不重绘及恢复单帧的生产回归。最终使用 v4 冻结全部修正。

为保留最终构建空间，已先记录中止事实，再清理本批 v1/v2/v3 非候选副本内可重建的 managed_components 和 firmware/build（约 2.8 GiB）。产品源码、patched_components、锁/配置、准备输入 inventory 与外部日志均保留；最终 v4 未清理，不修改 checkout 原始依赖。

## 最终结果

最后一次生产源码修改后，`python3 scripts/check.py` 全部通过：共 271 tests，跨模块 187 tests 中两项因当前 Python 缺 LittleFS 跳过，已在本批构建的 LittleFS Python 环境各独立补跑 1 test 并通过。太阳系专项 7 tests 与 ASan/UBSan 全部通过，包含连续取消不重复刷新及恢复清晰帧的最终回归。

完整构建使用 ESP-IDF 6.0.1、已验证的 Waveshare 1.75C 板级配置与 production 补丁。最终候选仅为 `/private/tmp/espocket-028-orbit-build-v4/candidate`，源码基于本批之前的 `7b929bf` 加本批冻结改动。所有 v1/v2/v3 中止输入均不代表最终候选；本批没有修改 checkout 的 managed_components 或补丁字节。

| 项目 | 结果 |
|---|---|
| Input fingerprint | `3c0440c40b171d98b3048112bef50a69f30b394ab6630f017e8a862974dc715c` |
| espocket.bin | 12,421,456 bytes，比水池 v4 增加 1,073,376 bytes |
| SHA-256 | `f9f844e933728f129e5e3d8bbc89c30887cc6e479d3158273e1cb396dc458e33` |
| App 分区余量 | 2,258,608 bytes（15%） |
| 归档校验 | 115 artifacts 的大小/hash 全部匹配；完整冻结输入复核通过；81 个相关太阳系/System 文件与 checkout 匹配 |
| 部署/物理验收 | `deployed=false`，`physical_validation=false` |

候选包含镜像、ELF、配置、精确 lock、补丁及完整输入证明。LittleFS 是 fresh filesystem，不能覆盖已有设备数据，本批不部署。最终日志为 `/private/tmp/espocket-028-orbit-build-v4.log`、`/private/tmp/espocket-028-orbit-checks-final-v4.log`、`/private/tmp/espocket-028-orbit-tests-final-v4.log`、`/private/tmp/espocket-028-orbit-sanitizers-final-v4.log`、`/private/tmp/espocket-028-orbit-builtin-update.log` 与 `/private/tmp/espocket-028-orbit-littlefs-migration.log`。Markdown 检查通过 364 文件。

仍未验证真实 LVGL 页面/字体、PSRAM 余量、持续帧率、功耗、触摸手感，以及 Quick Settings/息屏/PWR 的物理交互。统一设备步骤继续由 [09](../issues/09-device-acceptance.md) 持有。当前五个游戏/玩具已离线交付，重力迷宫另依赖 IMU；06、08 及整个 Effort 均保持未关闭。
