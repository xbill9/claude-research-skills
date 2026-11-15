// Run the page's own model script in node and compare every preset readout with preset_values.json.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url));
const html = fs.readFileSync(path.join(here, "index.html"), "utf8");
const model = html.match(/<script id="model">([\s\S]*?)<\/script>/)[1];
const data = JSON.parse(html.match(/<script id="presets-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const py = JSON.parse(fs.readFileSync(path.join(here, "preset_values.json"), "utf8"));
const module = { exports: {} };
new Function("module", model)(module);
const M = module.exports;
const { rows, worst } = M.selfCheck(py);
console.log("embedded JSON identical to preset_values.json:", JSON.stringify(data) === JSON.stringify(py));
console.log("preset".padEnd(10), "key".padEnd(28), "python".padStart(16), "javascript".padStart(16), "abs diff".padStart(10), "ok");
for (const r of rows) console.log(r.preset.padEnd(10), r.key.padEnd(28), r.py.toPrecision(10).padStart(16), r.js.toPrecision(10).padStart(16), r.abs.toExponential(1).padStart(10), r.ok);
// entropy table
for (const [k, v] of Object.entries(py.entropy_patterns_W4)) { const j = M.windowEntropy(k.split("")); if (Math.abs(j - v) > 1e-12) console.log("ENTROPY MISMATCH", k, j, v); }
const bad = rows.filter(r => !r.ok).length;
console.log(`${rows.length} values, ${bad} mismatches, worst error ${worst.toExponential(2)}, max abs diff ${Math.max(...rows.map(r => r.abs)).toExponential(2)}`);
process.exit(bad ? 1 : 0);
