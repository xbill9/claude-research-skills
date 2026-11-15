// True 390px mobile emulation via the Chrome DevTools Protocol (node >= 22 has a global WebSocket).
// Usage: node phone_check.mjs [out_prefix]. Reports scrollWidth per tab and saves full-page PNGs.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url));
const prefix = process.argv[2] || path.join(here, "phone390");
const port = 9333, prof = fs.mkdtempSync(path.join(os.tmpdir(), "ips-chrome-"));
const chrome = spawn("google-chrome", ["--headless=new", "--disable-gpu", `--remote-debugging-port=${port}`, `--user-data-dir=${prof}`, "about:blank"], { stdio: "ignore" });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let targets;
for (let i = 0; i < 50; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); break; } catch { await sleep(200); } }
const page = targets.find(t => t.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener("open", r));
let id = 0; const waiting = new Map(); const logs = [];
ws.addEventListener("message", e => { const m = JSON.parse(e.data); if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id); }
  if (m.method === "Runtime.consoleAPICalled") logs.push(m.params.type + ": " + m.params.args.map(a => a.value ?? a.description).join(" "));
  if (m.method === "Runtime.exceptionThrown") logs.push("EXCEPTION: " + m.params.exceptionDetails.exception?.description); });
const send = (method, params = {}) => new Promise(r => { const i = ++id; waiting.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
await send("Runtime.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
const url = pathToFileURL(path.join(here, "index.html")).href;
for (const tab of ["sim", "arch", "abl", "repro"]) {
  await send("Page.navigate", { url: url + "#" + tab }); await sleep(1200);
  const r = await send("Runtime.evaluate", { expression: "JSON.stringify({iw: innerWidth, sw: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight})", returnByValue: true });
  const m = JSON.parse(r.result.result.value);
  console.log(`${tab}: innerWidth=${m.iw} scrollWidth=${m.sw} height=${m.h} ${m.sw > m.iw ? "HORIZONTAL OVERFLOW" : "no horizontal scroll"}`);
  if (tab === "sim" || tab === "abl") {
    const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: 390, height: Math.min(m.h, 4000), scale: 1 } });
    fs.writeFileSync(`${prefix}_${tab}.png`, Buffer.from(shot.result.data, "base64"));
  }
}
console.log("console:", logs.length ? logs.join(" | ") : "(none)");
ws.close(); chrome.kill(); fs.rmSync(prof, { recursive: true, force: true });
