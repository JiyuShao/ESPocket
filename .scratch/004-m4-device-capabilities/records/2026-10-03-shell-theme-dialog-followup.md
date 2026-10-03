# 2026-10-03 — Home Space 主题与弹窗后续反馈

用户在 `c21fec136` 上补充：系统确认弹窗占比过大，浅色时弹窗按钮不可见；Store 启动提示同样显得过大。Shell Home Space 应随主题变化，App Card 由其 App 适配。另有“主题选择 → 取消 → 拖亮度”卡死，单独由 08 持有。

## 实施与主机证据

- 系统弹窗原固定 326×326，改为 316 宽、内容高度；正文最大 112，过长滚动，动作保持 46 高和稳定按钮索引。按钮显式不透明蓝/红背景与白字，避免依赖 LVGL 默认按钮背景透明度；尚不据此宣称像素根因已被证明。
- 旧实际呈现源码在新回归中因固定尺寸失败；新实际源码通过包含请求 owner、更新、超时、清理和按钮不透明的回归。主机 sink 不代替像素验收。
- Shell GUI 的颜色改为产品主题引用，保留原 Dark 色彩，Light 使用浅背景和深文字；没有独立主题状态。
- Native/Runtime Reference App Card 自行声明 app.page/caption/cardTitle/action/actionText；Runtime toolkit 构建成功。Runtime 包尚未装入设备，App-only 刷写不会替换旧包。
- Store 官方 remote_index 的启动 checking_network、refreshing_app_list 使用 ensure_message_dialog，复用 Shell 呈现，无需修改 Store 源码。
- 主机检查（含 61 个 firmware/test/host 测试及各组件测试）通过；Markdown 检查通过。完整构建通过，依赖锁与 playback-only 配置检查通过。

## 卡死诊断边界

原现场 hello 成功、snapshot invalid_state 已保存；恢复后 1 次新序列、4 次自动重复均命中真实亮度 Owner 并响应，未复现卡死。更快 25ms 点间隔被测试协议拒绝为 bad_request，不作为 GUI 卡死证据；改为允许的 40ms 点间隔、200ms 大幅拖动后同样命中 Owner 且页面响应。没有为未证实的同步等待或事件竞争添加推测性补丁；08 仍开放。

原始日志位于本地 `/private/tmp/espocket-theme-cancel-*`；不保存密码/表单内容到快照。

## 修正版设备证据

候选 `ac2485543`：ELF SHA256 `ac248554361c987fdf5cf1abdf84b6a0731a4fcc6fc0ddd5ae376c9d49ce5bf0`，App BIN SHA256 `0d3ca09cb19a4a696d07fd40d719e21694c2ed21902c6fa6b16144adb55bcb1d`。仅刷写 App offset 0x60000 并校验；未覆盖 NVS 或文件系统。启动恢复 Light，主题在零文档时应用，ESPocket started 正常。

自动进入 Settings/Display，选择 Dark，取消紧凑确认弹窗；继续滚动并拖动实际亮度 Owner，通过日志确认亮度调用和 Display 快照响应。未发现 panic；原卡死没有获得失败回归，仍未关闭 08。布局/按钮真实像素与 Home Space Light 可读性尚待有限观察。Runtime 新主题包仅构建，未安装；不能将源资源适配算作旧设备包已更新。
