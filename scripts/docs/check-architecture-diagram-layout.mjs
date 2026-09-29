import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const assetsDir = process.argv[2]
  ? resolve(process.argv[2])
  : resolve(scriptDir, "..", "..", "docs", "design", "architecture", "assets");
const files = readdirSync(assetsDir).filter((name) => name.endsWith(".svg")).sort();
const candidates = [
  process.env.CHROME_PATH,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
].filter(Boolean);
const chrome = candidates.find((path) => existsSync(path));

if (!chrome) {
  console.error("No Chrome/Chromium executable found. Set CHROME_PATH and retry.");
  process.exit(2);
}

const evaluator = String.raw`
(() => {
  const svg = document.querySelector("svg");
  const overlap = (a, b, pad = 0) =>
    a.x + pad < b.x + b.width && a.x + a.width - pad > b.x &&
    a.y + pad < b.y + b.height && a.y + a.height - pad > b.y;
  const contains = (box, point, pad = 0) =>
    point.x > box.x + pad && point.x < box.x + box.width - pad &&
    point.y > box.y + pad && point.y < box.y + box.height - pad;
  const describe = (element) => {
    const value = element.textContent?.replace(/\s+/g, " ").trim();
    return value ? "“" + value + "”" : element.getAttribute("d")?.slice(0, 48) || element.tagName;
  };
  const results = [];
  const texts = [...svg.querySelectorAll("text")].map((element) => ({
    box: element.getBBox(),
    text: describe(element),
  })).filter(({ box }) => box.width > 0 && box.height > 0);
  for (let a = 0; a < texts.length; a += 1) {
    for (let b = a + 1; b < texts.length; b += 1) {
      if (overlap(texts[a].box, texts[b].box, 1.5)) {
        results.push("文字重叠：" + texts[a].text + " ↔ " + texts[b].text);
      }
    }
  }
  const rectangles = [...svg.querySelectorAll(".node > rect, .chip > rect, .step > rect, .state")]
    .map((element) => ({ box: element.getBBox(), owner: describe(element.parentElement || element) }));
  for (const path of svg.querySelectorAll("path.edge")) {
    const length = path.getTotalLength();
    const points = [];
    for (let offset = 4; offset < length - 4; offset += 3) points.push(path.getPointAtLength(offset));
    for (const item of texts) {
      if (points.some((point) => contains(item.box, point))) {
        results.push("连线穿字：" + describe(path) + " ↔ " + item.text);
      }
    }
    for (const rect of rectangles) {
      if (points.filter((point) => contains(rect.box, point, 4)).length >= 4) {
        results.push("连线穿模块：" + describe(path) + " ↔ " + rect.owner);
      }
    }
  }
  document.body.dataset.result = btoa(unescape(encodeURIComponent(JSON.stringify([...new Set(results)]))));
})();`;

const tempDir = mkdtempSync(join(tmpdir(), "espocket-architecture-layout-"));
let failures = 0;

try {
  for (const file of files) {
    const svg = readFileSync(join(assetsDir, file), "utf8");
    const harness = join(tempDir, `${file}.html`);
    writeFileSync(harness, `<!doctype html><meta charset="utf-8"><body>${svg}<script>${evaluator}</script></body>`);
    const output = execFileSync(chrome, [
      "--headless=new",
      "--disable-gpu",
      "--no-sandbox",
      "--allow-file-access-from-files",
      "--dump-dom",
      pathToFileURL(harness).href,
    ], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
    const encoded = output.match(/data-result="([^"]*)"/)?.[1];
    if (!encoded) throw new Error(`Layout harness did not return a result for ${file}`);
    const issues = JSON.parse(Buffer.from(encoded, "base64").toString("utf8"));
    if (issues.length) {
      failures += issues.length;
      console.log(`\n${file}`);
      for (const issue of issues) console.log(`  - ${issue}`);
    }
  }
} finally {
  rmSync(tempDir, { recursive: true, force: true });
}

if (failures) {
  console.error(`\nlayout check failed: ${failures} issue(s)`);
  process.exit(1);
}
console.log(`layout check passed: ${files.length} SVG files`);
