# Page Navigator 第一版源码验证

- 日期：2026-10-02
- 范围：`.scratch/014-app-navigation-card-contract/issues/01-page-declaration-navigator.md` 的执行模型无关核心与 Native 示例适配
- 设备状态：仍运行已验收的 M6 普通镜像；本记录没有真机刷写结果

## 实现

`espocket_navigation` 组件校验 App Root、Page 与 Card 声明，保存唯一 App Page 栈。`start`、`start_from_card`、`push`、`pop`、`replace`、`reset_to_root` 和 `stop` 使用同一栈生成 `app_id`、`page_id`、`can_back` 与 `back_pending` 快照。Root 不能 pop，未知 Page 和画面呈现失败不提交栈变化；Card ID 失效时停留在 Root 并返回错误。

Hello Native 自己提供声明和 Page 到 Brookesia Screen Flow 的映射。System 验证声明身份与 App Manifest 一致，管理 Navigator 生命周期，并从 Navigator 判断 Edge Back 是否可执行。Root Edge Back 不离开 App；PWR Home 结束 App，下一次启动从 Root 建栈。

## 验证

- 已确认的测试边界：公开 `PageNavigator` 接口，不读取 LVGL 内部对象。
- 主机 C++23 测试通过：声明校验、Root/Detail、Back、Card 直达和失效、停止后重启、呈现失败时保持栈。
- ESP-IDF `build/manual-clean-abs` 整机构建通过，镜像 SHA-256：`e5c2b2d51bce860df257f2920fb68ca7515f3bc9cac1cbe40c28613965f00fec`；镜像未刷写。

## 尚待验证

安装时 App 更新的稳定 ID 迁移、真机 Native Detail 的可见 Back 和触控、Card 动态配置、Runtime Adapter 不属于这次通过项。默认 Back 与待决请求属于 014/02；因此 M7 导航验收仍未通过。
