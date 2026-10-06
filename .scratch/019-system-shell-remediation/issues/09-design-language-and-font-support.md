# 09 — 设计中文与多语言支持

**What to build:** 以 Super 已实现的语言切换、字体预载与回退链路为默认对齐目标，定义 ESPocket Shell/App 的覆盖、资源预算与兼容实施路径。

**Blocked by:** 字体 backend、实际 cmap/翻译覆盖和 LittleFS/heap 预算需独立兼容验证；语言切换部分失败规则与 10 共同确认。

**Status:** needs-info

- [ ] 核对固定上游字体/语言 API 与锁定产品版本，区分 manifest localized name、产品文本、输入显示及输入法能力。
- [ ] 确认 Shell、Overlay、Settings/Store 与 App 作者职责；字体覆盖和资源预算有明确边界。
- [ ] 定义不支持语言/缺字/字体加载失败的行为，及重启或运行中切换选择。
- [ ] 更新产品/开发契约并拆出资源、构建、中文文本/键盘显示与真机验收条件；引用 08 staging 核查。
- [ ] 用户确认完整设计，Markdown 检查通过；不以中文 manifest 名称证明中文产品支持。

## 兼容设计与执行单元

[源码核查](../records/2026-10-04-compatibility-design.md#09-语言与字体)确认 fontSet/list_supported_fonts/set_default_font_for_language 与 language hook 已在锁定接口中；尚缺的是 backend、资源和原生控件接通，不能由 manifest 中文名称替代。

1. 默认沿 Super 的 `en`/`zh_CN` 资源与支持字体，preload 在所有 App 文档前执行。固定索引、字体文件及许可，注册 default/zh_CN；请求语言无字体时回可用语言/字体，记录有效值和保存偏好分别为何物。默认字体/语言也不可用时走关键失败；临时 fallback 不覆盖用户保存值。
2. 底层文件字体依赖单独准备、精确锁定并核对当前 FreeType 禁用事实。优先验证 GUI LVGL 文件字体 backend，不自动把整个 Super System 引入；若需要新增依赖，检查传递 lock/hash 无漂移。字体与索引通过 build tree staging 的显式依赖进入 LittleFS。
3. 翻译 Shell Surface、状态文案、默认 Back、原生 Keyboard/Dialog/Loading 与 Expansion；官方 Settings/Store/Files 使用其 i18n，但必须验证其当前版本。Launcher 从 Core 已提交 registry 解析 localized name，与 005 的动态投影 seam 协作，不修改其实现。
4. 所有原生 LVGL label/textarea 选真实 font，保留 icon fallback 和字号。中文文件名/键盘草稿/网络名称是动态显示覆盖；系统中文 IME 不属于 Super 已接通功能，不宣称中文显示可输入拼音。外部 App literal 文案归作者；语言切换不强行翻译表单或用户文本。
5. 同步语言/字体刷新与 10 的失败规则；App 实例/Page/request 不变。Exposure deferred，未来 language Context/显式设置 Action 归 Core/System，当前不授权 Assistant。

### 实施前置与验收

- [ ] [08](08-audit-resource-staging-integrity.md) 持有 staging 依赖门槛；本票持有字体输入清单、授权、SHA256、实际文件字节、分区余量和 heap/cache 开销。
- [ ] 在 host 解析实际字体 cmap，比对维护 i18n 全集合及动态代表集（中文人名/文件名、长 SSID、符号/图标、混合中英文）；未知 glyph 不静默通过。subset 字体不保证全部汉字。
- [ ] 回归无字体/索引、缺 glyph、未知语言、fallback、切换时键盘草稿与 Dialog、保存失败、冷启动偏好恢复。字体失败不得成功宣布 supported。
- [ ] 执行统一检查、两种语言与有效配置完整构建；记录 clean/incremental staging 变化、LittleFS 占用、加载峰值和多次切换 heap。验收预算由实测确定，资源不足仍阻塞，不默认删中文或动态内容。
- [ ] 466px 设备逐 Surface/Overlay、Settings/Store/Files 与 Native/Runtime 代表页中英文像素及输入显示验证；字体不裁切、触摸区域不被长文案挤出，息屏/wake 保持有效语言。尚未验收。

## Comments

2026-10-04 隔离兼容设计：补充锁定 API、真实 Owner、圆屏/资源、停止安全、Exposure Decision 与执行单元；仅文档核查，不计实施/构建/设备完成。详见[核查记录](../records/2026-10-04-compatibility-design.md)。
