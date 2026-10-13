# App 短音效适配

泡泡纸与打砖块共用 `espocket::ShortEffect`，由调用方提供唯一音源名称。适配仅负责 1–130 ms 方波 PCM 经既有 Audio Service 播放，不提供 App 生命周期、玩法或音频仲裁状态机。

方波音色改编自锁定 [The-Badge 来源](../../native_apps/badge/README.md)，保留其 [MIT 授权](../../native_apps/badge/upstream/LICENSE)。

沿用 AudioDecoder Source/RequestOutput/OpenStream，只有真实 Audio Owner 原子确认空闲时才选择来源。静音、占用和服务错误均跳过；一次最多一段音效，16 kHz stereo、12 KiB 队列、零入队等待，不改变系统音量。`poll()` 异步检查借用缓冲释放及尾部时间，`close()` 在暂停/停止时释放 stream、output、source 和 binding。

PCM 与独立完成时间由 release callback 保留，回调不访问 App 或适配对象；旧完成回调不能关闭后续音效。调用方在自己的 App Owner 上串行调用，提供唯一名称，不建立额外线程。Host 测试执行生产适配方法，覆盖忙/静音、部分失败清理、缓冲寿命、尾部计时、迟到回调和不同调用方音源身份；实际声音仍需真机验证。
