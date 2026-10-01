# 默认 Back 真机样机记录

- 日期：2026-10-02
- 相关工作项：[014/02 默认 Back 与待决分发](../../../../.scratch/014-app-navigation-card-contract/issues/02-back-dispatch.md)
- 设备：ESP32-S3-Touch-AMOLED-1.75C，`/dev/cu.usbmodem101`
- App 镜像 SHA-256：`8c5a877bf65291c0c8b6f8a245a952fc769684fbfd194bb0a42c843500dd5bbb`

## 已完成检查

- `PageNavigator` 公开接口测试通过：Root、默认 Back、App 允许/取消/暂缓、重复请求、超时、过期 token、停止后新任务和 Back 呈现模式。
- Shell 文档 Action 唯一性测试通过。
- ESP-IDF 整机构建和分区大小检查通过；App 镜像约 `0x5d5ec0` 字节，最小 App 分区尚余约 43%。
- 仅刷入 App 分区 `0x60000`，esptool 报告 `Hash of data verified`；bootloader、NVS 与 LittleFS 未擦写。
- 串口记录启动完成、Native Root→Detail 转换，无 panic 或重启迹象。
- 用户真机确认：启动显示 Watch Face；Native Detail 有可见 `< Back`，点击返回 Native Root。
- 用户真机确认：Native Root 无可见 Back；Detail 从左边缘右滑回 Root；Root 同手势不导航；Root 短按 PWR 回 Watch Face。
- 用户真机确认：Native Detail 自动息屏后短按 PWR 仍显示 Detail 和 Back；再短按 PWR 回 Watch Face，重新打开 Native 从 Root 开始且无 Back。

## 待完成检查

- 暂缓 Back 的真机确认 UI 尚无样例；目前仅在 Navigator 公开接口测试中验证该语义。
- 本镜像是 M7 导航样机，未取得 M7 完整验收判定；M6 已验收镜像仍保留在 `firmware/build/m6-normal/espocket.bin`，SHA-256 为 `786f618a56015fb714474e1b6b3a062611ee1f29313875e4a33715ed219cb9ab`。
- 随后仅针对跨任务组访问为 Navigator 增加同步，更新镜像 SHA-256 为 `03edef4c8ae7af0cc35f68aa50906d3e8c6ca889b4d0213c527264df9eec0e15`，写入校验与自动启动日志通过；未要求用户重复本记录的触控步骤。
