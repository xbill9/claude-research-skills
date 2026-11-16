// True 390 px mobile emulation over the Chrome DevTools Protocol: per tab, report innerWidth vs
// scrollWidth (horizontal scroll), capture full-height screenshots, and collect console messages.
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url));
const url = pathToFileURL(path.join(here, "index.html")).href;
const prof = fs.mkdtempSync("/tmp/pc-");
const chrome = spawn("google-chrome", ["--headless=new", "--remote-debugging-port=9333", `--user-data-dir=${prof}`, "about:blank"], { stdio: "ignore" });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let targets;
for (let i = 0; i < 50; i++) { try { targets = await (await fetch("http://127.0.0.1:9333/json")).json(); break; } catch { await sleep(200); } }
const ws = new WebSocket(targets.find(t => t.type === "page").webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0; const pending = new Map(), logs = [];
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id); } else if (m.method === "Runtime.consoleAPICalled") logs.push(`${m.params.type}: ${m.params.args.map(a => a.value).join(" ")}`); };
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
await send("Runtime.enable"); await send("Page.enable");
const W = +(process.argv[2] || 390);
await send("Emulation.setDeviceMetricsOverride", { width: W, height: 844, deviceScaleFactor: 1, mobile: true });
for (const tab of ["sim", "arch", "abl", "repro"]) {
  await send("Page.navigate", { url: `${url}#${tab}` }); await sleep(1200);
  await send("Page.reload"); await sleep(1500);
  const r = await send("Runtime.evaluate", { expression: "JSON.stringify({iw: innerWidth, sw: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight})", returnByValue: true });
  const m = JSON.parse(r.result.value);
  console.log(`${tab}: innerWidth=${m.iw} scrollWidth=${m.sw} height=${m.h} -> ${m.sw > m.iw ? "HORIZONTAL SCROLL" : "no horizontal scroll"}`);
  if (tab === "sim" || tab === "repro") {
    await send("Emulation.setDeviceMetricsOverride", { width: W, height: Math.min(m.h, 6000), deviceScaleFactor: 1, mobile: true }); await sleep(500);
    const shot = await send("Page.captureScreenshot", { format: "png" });
    fs.writeFileSync(path.join(here, `phone${W}_${tab}.png`), Buffer.from(shot.data, "base64"));
    await send("Emulation.setDeviceMetricsOverride", { width: W, height: 844, deviceScaleFactor: 1, mobile: true });
  }
}
for (const l of [...new Set(logs)]) console.log("console:", l);
ws.close(); chrome.kill(); fs.rmSync(prof, { recursive: true, force: true });
