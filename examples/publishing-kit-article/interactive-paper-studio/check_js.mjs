// Run the page's own <script id="model"> in node and compare every preset value with preset_values.json.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url));
const html = fs.readFileSync(path.join(here, "index.html"), "utf8");
const model = html.match(/<script id="model">([\s\S]*?)<\/script>/)[1];
const embedded = JSON.parse(html.match(/<script id="presets-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const py = JSON.parse(fs.readFileSync(path.join(here, "preset_values.json"), "utf8"));
const module = { exports: {} };
new Function("module", model)(module);
const M = module.exports;
console.log("embedded JSON identical to preset_values.json:", JSON.stringify(embedded) === JSON.stringify(py));
const { rows, worst } = M.selfCheck(py);
console.log("preset".padEnd(12), "key".padEnd(22), "python".padStart(16), "javascript".padStart(16), "abs diff".padStart(10), "ok");
for (const r of rows.filter(r => !r.preset.startsWith("sweep")))
  console.log(r.preset.padEnd(12), r.key.padEnd(22), r.py.toPrecision(10).padStart(16), Number(r.js).toPrecision(10).padStart(16), r.abs.toExponential(1).padStart(10), r.ok);
const sw = rows.filter(r => r.preset.startsWith("sweep"));
console.log(`sweep: ${sw.length} values over ${py.sweep.length} wrap columns, ${sw.filter(r => !r.ok).length} mismatches`);
// stored-line counts: page shows them from JSON; recheck the per-block line totals independently
const bad = rows.filter(r => !r.ok).length;
console.log(`${rows.length} values, ${bad} mismatches, worst abs error ${worst.toExponential(2)}`);
process.exit(bad ? 1 : 0);
