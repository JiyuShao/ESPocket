import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const OUT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "assets");
mkdirSync(OUT, { recursive: true });

const esc = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");

function label(x, y, value, css = "label", anchor = "start") {
  return `<text class="${css}" x="${x}" y="${y}" text-anchor="${anchor}">${esc(value)}</text>`;
}

function multi(x, y, values, css = "detail", step = 18, anchor = "start") {
  return `<text class="${css}" x="${x}" y="${y}" text-anchor="${anchor}">${values.map((value, index) =>
    `<tspan x="${x}" dy="${index === 0 ? 0 : step}">${esc(value)}</tspan>`).join("")}</text>`;
}

function band(x, y, w, h, title, meta, tone = "neutral") {
  return [
    `<g class="band ${tone}"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="6"/>`,
    label(x + 18, y + 26, title, "band-title"),
    meta ? label(x + 18, y + 44, meta, "band-meta") : "",
    "</g>",
  ].join("");
}

function node(x, y, w, h, title, details = [], tone = "neutral", eyebrow = "") {
  const titleY = y + (eyebrow ? 42 : 29);
  return [
    `<g class="node ${tone}"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="4"/>`,
    eyebrow ? label(x + 14, y + 19, eyebrow, "eyebrow") : "",
    label(x + 14, titleY, title, "node-title"),
    details.length ? multi(x + 14, titleY + 19, details, "detail", 16) : "",
    "</g>",
  ].join("");
}

function chip(x, y, w, title, meta = "", tone = "neutral") {
  return [
    `<g class="chip ${tone}"><rect x="${x}" y="${y}" width="${w}" height="36" rx="3"/>`,
    label(x + 11, y + 16, title, "chip-title"),
    meta ? label(x + 11, y + 29, meta, "chip-meta") : "",
    "</g>",
  ].join("");
}

function edge(d, text = "", tx = 0, ty = 0, type = "direct") {
  return [
    `<path class="edge ${type}" d="${d}" marker-end="url(#arrow-${type})"/>`,
    text ? label(tx, ty, text, `edge-text ${type}`) : "",
  ].join("");
}

function plainLine(d, type = "direct") {
  return `<path class="edge ${type}" d="${d}"/>`;
}

function lane(x, title, tone = "neutral", top = 148, bottom = 690) {
  return [
    `<line class="lane" x1="${x}" y1="${top}" x2="${x}" y2="${bottom}"/>`,
    `<g class="lane-head ${tone}"><rect x="${x - 78}" y="108" width="156" height="34" rx="3"/>`,
    label(x, 130, title, "lane-title", "middle"),
    "</g>",
  ].join("");
}

function step(x, y, w, number, title, detail, tone = "neutral") {
  return [
    `<g class="step ${tone}"><rect x="${x}" y="${y}" width="${w}" height="68" rx="4"/>`,
    label(x + 13, y + 19, String(number).padStart(2, "0"), "step-num"),
    label(x + 13, y + 40, title, "step-title"),
    detail ? label(x + 13, y + 57, detail, "step-detail") : "",
    "</g>",
  ].join("");
}

const STYLE = `
  svg{--paper:#f3f6f9;--surface:#fff;--surface-soft:#f8fafc;--ink:#182b3d;--muted:#667b8e;--rule:#c7d2dc;--grid:rgba(48,78,103,.045);--blue:#1974c8;--blue-soft:#edf6ff;--teal:#178873;--teal-soft:#eef9f6;--amber:#a56d1d;--amber-soft:#fbf7ef;--danger:#b04f45;--danger-soft:#fdf1ef;--edge:#71879a;background:var(--paper);color-scheme:light}
  text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;fill:var(--ink)}
  .sheet{fill:var(--paper)}.grid{fill:url(#grid)}
  .doc-kicker{font:500 11px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:1.7px;fill:var(--blue)}
  .doc-title{font-size:28px;font-weight:600;letter-spacing:-.7px}.doc-subtitle{font-size:13px;fill:var(--muted)}
  .legend-text{font-size:11px;fill:var(--muted)}.legend-line{stroke:var(--edge);stroke-width:1.4}.legend-line.event{stroke-dasharray:5 5}.legend-line.package{stroke:var(--amber);stroke-dasharray:2 5}
  .band rect{fill:rgba(255,255,255,.86);stroke:var(--rule);stroke-width:1}.band.product rect{fill:rgba(237,246,255,.7);stroke:#a8c5de}.band.framework rect{fill:rgba(238,249,246,.78);stroke:#acd1c9}.band.platform rect{fill:rgba(251,247,239,.82);stroke:#d8c5a6}.band.danger rect{fill:var(--danger-soft);stroke:#dfb5b0}
  .band-title{font-size:15px;font-weight:600}.band-meta{font:500 10px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:1px;fill:var(--muted)}
  .node rect{fill:var(--surface);stroke:#aebdca;stroke-width:1}.node.product rect{fill:var(--blue-soft);stroke:#79a8d1}.node.focus-product rect{fill:#e7f3ff;stroke:var(--blue);stroke-width:1.6}.node.framework rect{fill:var(--teal-soft);stroke:#7eb9ad}.node.focus-framework rect{fill:#e7f7f3;stroke:var(--teal);stroke-width:1.6}.node.platform rect{fill:var(--amber-soft);stroke:#c5a77a}.node.danger rect{fill:var(--danger-soft);stroke:#d79a94}
  .eyebrow{font:500 10px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:1.2px;fill:var(--muted)}.node-title{font-size:14px;font-weight:600}.detail{font:400 11px ui-monospace,SFMono-Regular,Menlo,monospace;fill:var(--muted)}
  .chip rect{fill:var(--surface);stroke:#b6c4cf;stroke-width:1}.chip.product rect{fill:var(--blue-soft);stroke:#91b5d5}.chip.framework rect{fill:var(--teal-soft);stroke:#8ebeb5}.chip.platform rect{fill:var(--amber-soft);stroke:#c8ae85}.chip.danger rect{fill:var(--danger-soft);stroke:#d5a39e}.chip-title{font-size:11px;font-weight:600}.chip-meta{font:400 9px ui-monospace,SFMono-Regular,Menlo,monospace;fill:var(--muted)}
  .edge{fill:none;stroke:var(--edge);stroke-width:1.35}.edge.direct{marker-end:url(#arrow-direct)}.edge.event{stroke-dasharray:5 5;marker-end:url(#arrow-event)}.edge.package{stroke:var(--amber);stroke-dasharray:2 5;marker-end:url(#arrow-package)}.edge.strong{stroke:var(--blue);stroke-width:1.65;marker-end:url(#arrow-strong)}.edge.safe{stroke:var(--teal);marker-end:url(#arrow-safe)}.edge.fail{stroke:var(--danger);stroke-dasharray:5 5;marker-end:url(#arrow-fail)}
  .edge-text{font:500 10px ui-monospace,SFMono-Regular,Menlo,monospace;fill:var(--muted)}.edge-text.package{fill:var(--amber)}.edge-text.strong{fill:var(--blue)}.edge-text.safe{fill:var(--teal)}.edge-text.fail{fill:var(--danger)}
  .lane{stroke:#b9c6d0;stroke-width:1;stroke-dasharray:3 5}.lane-head rect{fill:var(--surface);stroke:var(--rule)}.lane-head.product rect{fill:var(--blue-soft);stroke:#91b5d5}.lane-head.framework rect{fill:var(--teal-soft);stroke:#8ebeb5}.lane-title{font-size:12px;font-weight:600}
  .step rect{fill:var(--surface);stroke:#aebdca}.step.product rect{fill:var(--blue-soft);stroke:#79a8d1}.step.framework rect{fill:var(--teal-soft);stroke:#7eb9ad}.step.platform rect{fill:var(--amber-soft);stroke:#c5a77a}.step-num{font:500 9px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:1px;fill:var(--muted)}.step-title{font-size:12px;font-weight:600}.step-detail{font:400 9px ui-monospace,SFMono-Regular,Menlo,monospace;fill:var(--muted)}
  .section{font:500 11px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:1.4px;fill:var(--muted)}.caption{font-size:11px;fill:var(--muted)}.caption-strong{font-size:11px;font-weight:600;fill:var(--ink)}
  .state{fill:var(--surface);stroke:#aebdca;stroke-width:1.2}.state.product{fill:var(--blue-soft);stroke:var(--blue)}.state.framework{fill:var(--teal-soft);stroke:var(--teal)}.state.platform{fill:var(--amber-soft);stroke:var(--amber)}.state-title{font-size:14px;font-weight:600}.state-detail{font-size:10px;fill:var(--muted)}
`;

function documentSvg(width, height, title, subtitle, body, desc = title) {
  const legendX = width - 330;
  return [
    `<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 ${width} ${height}">`,
    `<title id="title">${esc(title)}</title><desc id="desc">${esc(desc)}</desc>`,
    `<defs>`,
    `<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="var(--grid)"/></pattern>`,
    ...["direct", "event", "package", "strong", "safe", "fail"].map((name) =>
      `<marker id="arrow-${name}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="context-stroke"/></marker>`),
    `</defs><style>${STYLE}</style>`,
    `<rect class="sheet" width="${width}" height="${height}"/><rect class="grid" width="${width}" height="${height}"/>`,
    label(40, 34, "ESPOCKET · ARCHITECTURE", "doc-kicker"),
    label(40, 67, title, "doc-title"),
    label(40, 91, subtitle, "doc-subtitle"),
    `<g aria-label="连线图例"><line class="legend-line" x1="${legendX}" y1="62" x2="${legendX + 24}" y2="62"/>${label(legendX + 32, 66, "调用 / 依赖", "legend-text")}<line class="legend-line event" x1="${legendX + 116}" y1="62" x2="${legendX + 140}" y2="62"/>${label(legendX + 148, 66, "事件", "legend-text")}<line class="legend-line package" x1="${legendX + 202}" y1="62" x2="${legendX + 226}" y2="62"/>${label(legendX + 234, 66, "包加载", "legend-text")}</g>`,
    body,
    `</svg>`,
  ].join("");
}

function write(name, width, height, title, subtitle, body, desc) {
  writeFileSync(join(OUT, `${name}.svg`), `${documentSvg(width, height, title, subtitle, body, desc)}\n`);
}

// 01 · 系统上下文：只画设备内外关系，不展开内部调用细节。
write("system-context", 1200, 720, "ESPocket 系统上下文", "设备内运行面、构建输入与外部依赖", [
  band(300, 125, 600, 520, "ESPocket Device", "WAVESHARE ESP32-S3 1.75C", "product"),
  node(345, 175, 510, 72, "ESPocket 产品宿主", ["espocket::System · CircularShell · PowerKeyMonitor"], "focus-product", "PRODUCT"),
  node(345, 270, 510, 90, "统一应用运行面", ["Shell IApp · Native Apps · Official Apps", "Runtime JS Packages"], "framework", "SYSTEM CORE"),
  node(345, 383, 245, 96, "设备服务面", ["Display · Device", "Wi-Fi · SNTP · HTTP"], "framework", "SERVICE MANAGER"),
  node(610, 383, 245, 96, "执行与图形", ["GUI LVGL", "Runtime JS · QuickJS"], "framework", "BACKENDS"),
  node(345, 502, 510, 94, "平台与硬件", ["ESP-IDF · FreeRTOS · LittleFS · Board Manager", "AMOLED · Touch · Battery · Wi-Fi · PWR"], "platform", "PLATFORM"),
  node(35, 178, 210, 82, "用户", ["触控 · PWR · 屏幕输出"], "neutral", "ACTOR"),
  node(35, 470, 210, 100, "开发与诊断", ["CMake / ESP-IDF 构建", "烧录 · 串口日志 · 验收"], "neutral", "TOOLING"),
  node(955, 178, 210, 82, "构建输入", ["源码 · Runtime App 包"], "neutral", "BUILD"),
  node(955, 470, 210, 100, "网络服务", ["SNTP · HTTP Catalog", "Runtime Package Source"], "neutral", "EXTERNAL"),
  edge("M245 219H300", "交互", 258, 210, "strong"),
  edge("M955 219H900", "固件 + LittleFS", 844, 210, "package"),
  edge("M245 520H300", "日志 / 验收", 252, 511, "event"),
  edge("M955 520H900", "网络请求", 906, 511, "event"),
  edge("M600 247V270", "", 0, 0, "strong"),
  edge("M470 360V383", "", 0, 0, "safe"),
  edge("M730 360V383", "", 0, 0, "safe"),
  edge("M470 479V502", "", 0, 0, "direct"),
  edge("M730 479V502", "", 0, 0, "direct"),
  label(345, 625, "设备内：产品策略与框架实现同机运行", "caption-strong"),
  label(855, 625, "设备外：输入与依赖", "caption", "end"),
].join(""), "用户、构建系统、网络服务与 ESPocket 设备内模块的关系。"),

// 02 · 总体分层：纵向所有权，横向运行面。
write("layered-architecture", 1200, 860, "ESPocket 总体分层架构", "纵向所有权分层 × 横向应用运行面与设备服务面", [
  label(350, 126, "应用运行面", "section", "middle"),
  label(790, 126, "设备服务面", "section", "middle"),
  band(95, 145, 1010, 120, "01 · ESPocket 产品体验", "PRODUCT-OWNED", "product"),
  node(125, 190, 240, 55, "CircularShell", ["表盘 · 卡片 · 启动器 · 键盘"], "product"),
  node(385, 190, 310, 55, "Installed Apps", ["Native · Official · Runtime"], "product"),
  node(715, 190, 360, 55, "Power / Display Policy", ["PWR · Home · timeout · wake"], "product"),
  band(95, 280, 1010, 115, "02 · ESPocket 产品宿主", "COMPOSITION ROOT", "product"),
  node(280, 322, 640, 54, "espocket::System", ["继承 System Core · 装配 App · 集中产品策略"], "focus-product"),
  band(95, 410, 1010, 170, "03 · ESP-Brookesia 框架", "TWO COLLABORATING PLANES", "framework"),
  node(125, 462, 470, 90, "System Core", ["App Manager · GUI / Timer Runtime", "Package Manager · Runtime Host Bridge"], "focus-framework"),
  node(615, 462, 460, 90, "ServiceManager", ["Display · Device · Wi-Fi · SNTP · HTTP", "Binding · Helper · Event Registry"], "framework"),
  band(95, 595, 1010, 104, "04 · 平台 Adapter", "FRAMEWORK SEAMS", "platform"),
  chip(125, 640, 210, "GUI LVGL", "Backend · DisplaySource", "platform"),
  chip(355, 640, 210, "Runtime JS", "Backend · QuickJS", "platform"),
  chip(585, 640, 220, "Service Adapters", "HAL · Board Manager", "platform"),
  chip(825, 640, 250, "ESP-IDF", "FreeRTOS · LittleFS", "platform"),
  band(95, 714, 1010, 102, "05 · 硬件", "DEVICE", "neutral"),
  chip(125, 759, 210, "AMOLED + Touch"),
  chip(355, 759, 210, "ESP32-S3 + Flash"),
  chip(585, 759, 220, "Wi-Fi Radio"),
  chip(825, 759, 250, "PMIC · Battery · TCA9554"),
  edge("M600 265V280", "", 0, 0, "strong"),
  edge("M450 395V410", "", 0, 0, "strong"),
  edge("M595 507H615", "service calls", 520, 498, "safe"),
  edge("M360 552V595", "GUI / Runtime", 372, 586, "safe"),
  edge("M845 552V595", "device services", 856, 586, "safe"),
  edge("M600 699V714", "", 0, 0, "direct"),
].join(""), "ESPocket 从产品体验和产品宿主，经 System Core 与 ServiceManager 两个框架运行面，到 Adapter 和硬件的分层。"),

// 03 · 核心模块：源码级关系图。
write("core-modules", 1200, 780, "ESPocket 核心模块协作", "产品宿主、统一 App 平台与设备服务面的真实关系", [
  band(40, 125, 1120, 590, "Runtime module map", "SOURCE-MAPPED DEPENDENCIES", "neutral"),
  node(80, 175, 150, 64, "app_main", ["static System"], "neutral", "ENTRY"),
  node(285, 160, 300, 88, "espocket::System", ["System Core subclass", "policy · restore · display"], "focus-product", "PRODUCT HOST"),
  node(720, 160, 360, 88, "CircularShell", ["IApp · Surface interface", "gesture · keyboard · status"], "product", "SYSTEM APP"),
  node(80, 300, 150, 72, "PowerKeyMonitor", ["BoardManager", "TCA9554 EXIO4"], "product", "INPUT"),
  node(285, 305, 470, 220, "System Core", ["single lifecycle + foreground model"], "focus-framework", "DEEP MODULE"),
  chip(310, 375, 200, "App Manager", "install · start · stop", "framework"),
  chip(530, 375, 200, "GUI + Timer", "AppContext · flows", "framework"),
  chip(310, 430, 200, "Package Manager", "scan · validate", "framework"),
  chip(530, 430, 200, "Runtime Host Bridge", "JS host calls", "framework"),
  node(790, 305, 290, 220, "ServiceManager", ["binding · helper · events"], "framework", "DEVICE SERVICE PLANE"),
  chip(815, 375, 110, "Display", "", "framework"),
  chip(945, 375, 110, "Device", "", "framework"),
  chip(815, 430, 110, "Wi-Fi", "", "framework"),
  chip(945, 430, 110, "SNTP", "", "framework"),
  chip(815, 475, 240, "HTTP · App Store", "", "framework"),
  node(285, 585, 220, 70, "GUI LVGL", ["Backend · DisplaySource"], "platform"),
  node(525, 585, 220, 70, "Runtime JS", ["Backend · QuickJS"], "platform"),
  node(790, 585, 290, 70, "HAL · Board Manager", ["service implementations"], "platform"),
  edge("M230 207H285", "", 0, 0, "strong"),
  edge("M285 204H255V336H230", "", 0, 0, "event"),
  edge("M585 204H720", "construct / install", 607, 194, "strong"),
  edge("M720 230H680V275H565", "callbacks", 603, 257, "event"),
  edge("M435 248V305", "extends / orchestrates", 447, 285, "strong"),
  edge("M900 248V305", "Service Helper", 912, 284, "direct"),
  edge("M755 410H790", "", 0, 0, "safe"),
  edge("M395 525V585", "GUI backend", 407, 574, "safe"),
  edge("M635 525V585", "runtime backend", 647, 574, "safe"),
  edge("M935 525V585", "adapters", 947, 574, "safe"),
  label(80, 684, "产品代码", "caption-strong"), label(150, 684, "蓝色", "caption"),
  label(285, 684, "框架深模块", "caption-strong"), label(377, 684, "青色", "caption"),
  label(525, 684, "平台 Adapter", "caption-strong"), label(616, 684, "琥珀色", "caption"),
].join(""), "espocket::System 继承 System Core；CircularShell 是 IApp；设备能力通过 ServiceManager；平台差异位于 Adapter。"),

// 04a · 启动时序：按 system.cpp 的真实顺序。
write("boot-lifecycle", 1200, 770, "ESPocket 启动生命周期", "从 app_main 到 Watch Face 的确定性启动顺序", [
  lane(120, "app_main"), lane(335, "espocket::System", "product"), lane(565, "Service / Display", "framework"), lane(805, "System Core", "framework"), lane(1060, "Apps / Shell", "product"),
  step(48, 132, 144, 1, "构造 System", "static lifetime"),
  step(263, 210, 144, 2, "System::init", "product preflight", "product"),
  step(493, 288, 144, 3, "ServiceManager", "init + start", "framework"),
  step(493, 375, 144, 4, "Display ready", "bind · backlight · source", "framework"),
  step(733, 462, 144, 5, "Core init(config)", "backend + environment", "framework"),
  step(988, 540, 144, 6, "Install Apps", "native · official · package", "product"),
  step(263, 618, 144, 7, "System::start", "Shell + PWR monitor", "product"),
  edge("M192 166H228V244H263", "", 0, 0, "strong"),
  edge("M407 244H450V322H493", "", 0, 0, "strong"),
  edge("M565 356V375", "", 0, 0, "safe"),
  edge("M637 409H684V496H733", "", 0, 0, "safe"),
  edge("M877 496H930V574H988", "", 0, 0, "safe"),
  edge("M988 574H950V652H407", "core ready", 668, 643, "event"),
  label(48, 730, "Fatal：Service / Display / Touch / System Core / Shell", "caption-strong"),
  label(1150, 730, "Recoverable：Time / Wi-Fi / Battery status", "caption", "end"),
].join(""), "ServiceManager 和 DisplaySource 先于 System Core 初始化；应用安装完成后，System::start 启动 CircularShell 与 PowerKeyMonitor。"),

// 04b · App 生命周期：Native 与 Runtime 共用同一状态机。
write("app-lifecycle", 1200, 690, "ESPocket App 生命周期", "Shell 发起、System Core 执行、产品宿主恢复来源", [
  lane(120, "CircularShell", "product", 118, 620), lane(360, "espocket::System", "product", 118, 620), lane(620, "System Core", "framework", 118, 620), lane(870, "App instance", "neutral", 118, 620), lane(1080, "CircularShell", "product", 118, 620),
  step(48, 140, 144, 1, "选择 App", "capture source", "product"),
  step(288, 220, 144, 2, "launch_app", "manifest → app_id", "product"),
  step(548, 300, 144, 3, "start_app", "state + GUI / runtime", "framework"),
  step(798, 380, 144, 4, "on_start", "Native or Runtime"),
  step(548, 460, 144, 5, "stop_app", "Back / Home", "framework"),
  step(288, 540, 144, 6, "lifecycle hook", "clear foreground", "product"),
  step(1008, 540, 144, 7, "restore_surface", "source or Watch Face", "product"),
  edge("M192 174H240V254H288", "", 0, 0, "strong"),
  edge("M432 254H488V334H548", "", 0, 0, "strong"),
  edge("M692 334H742V414H798", "", 0, 0, "safe"),
  edge("M798 414H742V494H692", "", 0, 0, "event"),
  edge("M548 494H490V574H432", "", 0, 0, "event"),
  edge("M432 574H1008", "restore launch source", 660, 565, "strong"),
  label(48, 655, "Native 与 Runtime 的加载实现不同，但状态机、前台跟踪与恢复 hook 相同。", "caption-strong"),
].join(""), "App 从 Shell 回调进入 espocket::System，再由 System Core 统一启动或停止，最终恢复原 Shell Surface。"),

// 05a · Shell Surface：只画 Shell 内 Surface 与 App 边界。
write("navigation-surfaces", 1200, 720, "ESPocket 顶层导航 Surface", "Watch Face 是 Home 锚点；前台 App 不属于 ShellSurface", [
  label(600, 128, "SHELL SURFACES", "section", "middle"),
  `<circle class="state product" cx="600" cy="342" r="92"/>`,
  label(600, 334, "Watch Face", "state-title", "middle"),
  label(600, 354, "HOME ANCHOR", "state-detail", "middle"),
  `<rect class="state product" x="475" y="145" width="250" height="72" rx="4"/>`,
  label(600, 176, "Quick Settings", "state-title", "middle"), label(600, 196, "下滑进入 · Back 返回", "state-detail", "middle"),
  `<rect class="state product" x="475" y="493" width="250" height="72" rx="4"/>`,
  label(600, 524, "Launcher", "state-title", "middle"), label(600, 544, "上滑进入 · 选择 App", "state-detail", "middle"),
  `<rect class="state product" x="120" y="306" width="235" height="72" rx="4"/>`,
  label(237, 337, "Battery Card", "state-title", "middle"), label(237, 357, "水平滑动", "state-detail", "middle"),
  `<rect class="state product" x="845" y="306" width="235" height="72" rx="4"/>`,
  label(962, 337, "Brightness Card", "state-title", "middle"), label(962, 357, "水平滑动", "state-detail", "middle"),
  band(780, 480, 350, 145, "Foreground App", "NOT A SHELL SURFACE", "neutral"),
  chip(805, 528, 140, "App Root", "Root Back → stop", "neutral"),
  chip(965, 528, 140, "App Detail", "Edge Back → Root", "neutral"),
  edge("M600 250V217", "swipe down", 612, 240, "direct"),
  edge("M600 434V493", "swipe up", 612, 470, "direct"),
  edge("M508 342H355", "horizontal", 397, 332, "direct"),
  edge("M692 342H845", "horizontal", 721, 332, "direct"),
  edge("M725 529H780", "launch", 733, 519, "strong"),
  edge("M955 480V430H692", "Root Back → source", 802, 421, "event"),
  label(120, 636, "PWR Home", "caption-strong"), label(190, 636, "任何非 Home 状态最终回到 Watch Face", "caption"),
  label(120, 660, "Screen Off", "caption-strong"), label(190, 660, "与导航状态正交，不执行 Back", "caption"),
].join(""), "CircularShell 的五个 Surface 围绕 Watch Face；App Root 和 Detail 由 System Core 管理，不属于 ShellSurface。"),

// 05b · 显示状态：准确反映 handle_power_short_press 与 timeout。
write("display-state", 1200, 520, "ESPocket 显示状态", "PWR 是 Home 与显示电源的组合键；timeout 只改变显示状态", [
  `<rect class="state" x="70" y="180" width="260" height="110" rx="4"/>`,
  label(200, 218, "前台 App / 非 Home Surface", "state-title", "middle"),
  label(200, 241, "display_on = true", "state-detail", "middle"),
  label(200, 261, "navigation state preserved", "state-detail", "middle"),
  `<rect class="state product" x="470" y="180" width="260" height="110" rx="4"/>`,
  label(600, 218, "Watch Face", "state-title", "middle"),
  label(600, 241, "HOME · display_on = true", "state-detail", "middle"),
  label(600, 261, "PWR 再按一次 → Off", "state-detail", "middle"),
  `<rect class="state platform" x="870" y="180" width="260" height="110" rx="4"/>`,
  label(1000, 218, "Screen Off", "state-title", "middle"),
  label(1000, 241, "touch disabled · backlight off", "state-detail", "middle"),
  label(1000, 261, "resume_app_id retained", "state-detail", "middle"),
  edge("M330 235H470", "PWR Home", 360, 224, "strong"),
  edge("M730 235H870", "PWR / timeout", 752, 224, "strong"),
  edge("M1000 290V355H600V290", "PWR wake · target valid", 720, 346, "event"),
  edge("M1000 290V400H470V290", "target invalid → Watch Face", 684, 391, "fail"),
  label(70, 455, "不变量", "caption-strong"),
  label(130, 455, "息屏不触发 Back/Home；唤醒时只有 Running 的 resume_app_id 可恢复，否则降级到 Watch Face。", "caption"),
].join(""), "显示开关与导航正交；PWR 在显示开启时逐步执行 App Home、Shell Home、Screen Off，在关闭时唤醒。"),

// 05c · 应用运行模型：同一接口，两类 Adapter。
write("app-runtime", 1200, 650, "ESPocket 应用运行模型", "Native 与 Runtime 使用不同 Adapter，跨越同一个 System Core seam", [
  node(55, 235, 210, 100, "Launch Source", ["Launcher · Card", "Quick Settings"], "product", "SHELL"),
  node(325, 220, 250, 130, "espocket::System", ["manifest → app_id", "source · foreground · restore"], "focus-product", "PRODUCT POLICY"),
  node(635, 195, 300, 180, "System Core", ["single AppState machine"], "focus-framework", "RUNTIME SEAM"),
  chip(660, 255, 120, "App Manager", "lifecycle", "framework"),
  chip(790, 255, 120, "AppContext", "GUI · Timer", "framework"),
  chip(660, 305, 250, "Keyboard request", "System hook → Shell overlay", "framework"),
  band(985, 125, 180, 150, "Native path", "IApp", "neutral"),
  chip(1005, 178, 140, "Hello Native", "product", "product"),
  chip(1005, 222, 140, "Settings / Store", "official", "neutral"),
  band(985, 330, 180, 190, "Runtime path", "PACKAGE", "platform"),
  chip(1005, 382, 140, "Package Manager", "LittleFS /apps", "platform"),
  chip(1005, 426, 140, "Runtime JS", "QuickJS backend", "platform"),
  chip(1005, 470, 140, "Hello Runtime", "manifest + JS", "platform"),
  edge("M265 285H325", "launch", 273, 275, "strong"),
  edge("M575 285H635", "start / stop", 581, 275, "strong"),
  edge("M935 245H985", "IApp", 945, 235, "direct"),
  edge("M935 340H955V425H985", "", 0, 0, "package"),
  edge("M985 470H945V360H935", "", 0, 0, "event"),
  band(325, 430, 610, 102, "共同契约", "SAME PRODUCT BEHAVIOR", "framework"),
  chip(350, 475, 170, "统一生命周期", "Installed → Running → Stopped", "framework"),
  chip(535, 475, 170, "统一导航", "Back · Home · restore", "framework"),
  chip(720, 475, 190, "统一 GUI / Keyboard", "AppContext interface", "framework"),
  edge("M785 375V430", "shared contract", 797, 420, "safe"),
  label(325, 575, "包信任决定 Runtime 是否可安装；安装后不再维护第二套产品导航。", "caption-strong"),
].join(""), "Native IApp 与 Runtime JS package 通过不同 Adapter 接入同一个 System Core 生命周期、导航与 AppContext 契约。"),

// 06 · 设备能力：每一行是一条可追溯能力路径。
write("device-capabilities", 1200, 840, "ESPocket 设备能力映射", "调用者 → 框架接口 → Adapter → 硬件落点", [
  label(170, 128, "调用者", "section", "middle"),
  label(450, 128, "框架接口 / seam", "section", "middle"),
  label(760, 128, "Adapter / 实现", "section", "middle"),
  label(1050, 128, "硬件落点", "section", "middle"),
  ...[
    { y: 155, caller: ["espocket::System", "CircularShell"], iface: ["Display Helper", "DisplaySource / GUI backend"], adapter: ["Display Service", "GUI LVGL · ESP LVGL Adapter"], hardware: ["AMOLED", "Touch controller"] },
    { y: 275, caller: ["PowerKeyMonitor", "short press task"], iface: ["Board Manager", "I2C device handle"], adapter: ["ESP-IDF I2C", "board configuration"], hardware: ["TCA9554", "EXIO4 · PWR"] },
    { y: 395, caller: ["CircularShell", "status refresh"], iface: ["Device Helper", "battery event"], adapter: ["Device Service", "HAL adaptor"], hardware: ["PMIC / Battery", "capacity state"] },
    { y: 515, caller: ["CircularShell / Settings", "toggle + status"], iface: ["Wi-Fi / SNTP Helper", "service events"], adapter: ["Wi-Fi / SNTP Service", "ESP-IDF netif"], hardware: ["Wi-Fi Radio", "system clock"] },
    { y: 635, caller: ["System Core", "package install"], iface: ["Package / Runtime", "IRuntimeBackend"], adapter: ["LittleFS", "Runtime JS · QuickJS"], hardware: ["Flash / PSRAM", "/apps packages"] },
  ].flatMap((row) => [
    node(45, row.y, 250, 82, row.caller[0], [row.caller[1]], "product"),
    node(325, row.y, 250, 82, row.iface[0], [row.iface[1]], "framework"),
    node(605, row.y, 300, 82, row.adapter[0], [row.adapter[1]], "platform"),
    node(935, row.y, 220, 82, row.hardware[0], [row.hardware[1]], "neutral"),
    edge(`M295 ${row.y + 41}H325`, "", 0, 0, "direct"),
    edge(`M575 ${row.y + 41}H605`, "", 0, 0, "safe"),
    edge(`M905 ${row.y + 41}H935`, "", 0, 0, "direct"),
  ]).join(""),
  band(45, 760, 520, 54, "启动关键路径", "Display · Touch · System Core · Shell failure → fatal", "danger"),
  band(585, 760, 570, 54, "可降级能力", "Time · Wi-Fi · Battery unavailable → Shell continues", "framework"),
].join(""), "显示、PWR、电池、网络时间和 Runtime 存储能力从产品调用者到硬件的实际映射。"),

console.log(`generated 9 architecture SVGs in ${OUT}`);
