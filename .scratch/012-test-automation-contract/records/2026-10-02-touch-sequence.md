# 触摸序列与共同输入占用组件

- 日期：2026-10-02
- Ticket：[012/02](../issues/02-shared-input-and-snapshot.md)
- 范围：真实生产 C++ 序列组件与主机行为测试；未接 USB schema、Display 或 Shell。

## 实现

PWR 队列扩展为 `TestInputQueue`，由同一互斥状态仲裁 PWR 排队/执行与触摸序列。触摸占用期间不能排队 PWR；PWR 排队或执行期间不能预留触摸。System 的已有消费行为保持原语义。

`TouchInputSequence` 由单一输入 worker 驱动。轨迹在预留槽位前验证：2–16 个点、首点为零时刻按下、仅末点松开、坐标在实际输出宽高内、相邻点间隔至少 40 ms、总时长不超过 2000 ms。接通协议时应复用这个校验，不复制到另一套输入状态机。

worker 一次 tick 最多送一个点，延迟后不把按下与松开挤在同一 tick。末点松开后再保留 40 ms，给实际输入管线观察 release 的机会。绝对期限为声明总时长加 500 ms；过期不补发轨迹。上述时长是序列调度下限，不证明实际 LVGL 或屏幕已消费，Driver 仍需等待 Owner 状态。

正常完成与异常取消传给 cleanup 的语义不同：取消不能调用正常 Shell Release 提交导航。cleanup 成功后才释放共同槽位；cleanup 失败保持 busy 并允许下一 tick 重试。重复取消空闲序列安全。

## 主机覆盖

实际 C++ 用例覆盖坐标越界、途中 release、过密时间点、不合法轨迹不注入；PWR 与触摸双向 busy（包含 PWR 执行中）；PWR 取消/消费不解除触摸；逐点调度与延迟保持；正常 release 后等待；重复清理；清理失败保持占用、重试不发送正常 release；过期不送迟到点；sink 失败取消。

没有开放 `stimulus.touch` capability，不勾选完整触摸、共同协议占用或触摸释放验收条件。触摸 sink、取消时清除 Shell pending intent/pull、实际 LVGL override、硬件手势抑制和 USB 轨迹解析仍待下一 slice 接入。源码未刷写，设备仍为 013 identity `e8bbe74ff`，没有新增真机或视觉证据。

## 构建证据

- `python3 scripts/check.py`：17 项 unittest、M2 parser、159 个 Markdown 文件通过。
- ESP-IDF 6.0.1 完整构建、链接与分区检查通过；新增序列源码已编译，但尚未绑定 Owner，不能据此宣称设备触摸执行成功。
- App 大小 `0x5d3310`，分区剩余 43%。日志 `/private/tmp/espocket-night-touch-sequence-build.log`。
- BIN SHA-256：`e1cd8c1a11d0f71067ce6009a456baedd6ca9435d3da1f11325f8e87392ff209`。
- ELF SHA-256：`b429457f822125572d13f3ca0b59fe006f621eb573699e942d6d8d28b3be5e1f`。
