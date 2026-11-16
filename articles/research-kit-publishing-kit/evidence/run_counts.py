"""Every count the article states, computed from the example's files."""
import collections
import glob
import json
import re
import sys
from pathlib import Path

from PIL import Image

E = Path(sys.argv[1])
P = E / "paper"
print("# counts from examples/publishing-kit-article, computed by run_counts.py")

m = json.load(open(E / "math-sandbox/eq_verified_numbers.json"))
print("math-sandbox claims:", len(m["equations"]), dict(collections.Counter(r["verdict"] for r in m["equations"])))

s = json.load(open(E / "ablation-stat-auditor/stat_audit.json"))
cl = s["claims"]
print("ablation-stat-auditor claim records:", len(cl), dict(collections.Counter(c.get("verdict") for c in cl)))
w = s["wilson"]
print("wilson:", json.dumps(w)[:300])
print("tests:", {k: (v.get("p_value"), v.get("b"), v.get("c")) for k, v in s["tests"].items() if isinstance(v, dict)})

rep = (E / "citation-doi-verifier/REPORT.md").read_text()
rows = [l for l in rep.splitlines() if re.match(r"\| L\d+ \|", l)]
print("citation links: %d of %d resolving and identified" % (sum("RESOLVES+IDENTIFIED" in l for l in rows), len(rows)))
print("citation dois/arxiv in paper text:", sum(len(re.findall(r"10\.\d{4,}/|arxiv\.org/abs", Path(f).read_text(errors="ignore"))) for f in glob.glob(str(P / "**/*.md"), recursive=True) + glob.glob(str(P / "**/*.txt"), recursive=True)))

for f in sorted(P.glob("*.jpg")) + sorted(P.glob("*.webp")):
    print("image", f.name, "%dx%d" % Image.open(f).size)

L = (P / "devto-publishing-kit.md").read_text().split("\n")
body = L[L.index("---", 1) + 1 :]
fence = False
prose = []
for l in body:
    if l.startswith("```"):
        fence = not fence
        continue
    if fence or not l.strip() or l.startswith(("|", "#")):
        continue
    prose.append(l)
print("hardwrap blocks without a break: 62 - 47 =", 62 - 47)
print("source prose lines:", len(prose), "over 95 chars:", sum(len(l) > 95 for l in prose), "longest:", max(map(len, prose)))

print("crop: ratio 1000/420 =", round(1000 / 420, 6), "; rows kept at width 1376 =", round(1376 * 420 / 1000, 2), "; lost per side from 768 =", round((768 - 1376 * 420 / 1000) / 2, 2))
print("legibility: LEGIBLE_PX*1376/CARD_W =", 10 * 1376 / 320, "; 40pt at 320/1376 =", round(40 * 320 / 1376, 2), "px")

tot = {}
for f in sorted(E.glob("*/RUN_NOTES.md")):
    lines = f.read_text().split("\n")
    st = next((i for i, l in enumerate(lines) if re.match(r"#+\s*(3[.)]?\s|Where the skill)", l)), None)
    en = next((i for i in range(st + 1, len(lines)) if re.match(r"#+\s", lines[i])), len(lines))
    tot[f.parent.name] = sum(1 for l in lines[st + 1 : en] if re.match(r"\d+\.\s", l))
print("shortfall items per skill:", tot, "total:", sum(tot.values()))

import pymupdf
for pdf in sorted(E.glob("*/*.pdf")):
    print("pdf", pdf.relative_to(E), pymupdf.open(pdf).page_count, "pages")
print("studio check:", (E / "interactive-paper-studio/check_js_output.txt").read_text().strip().splitlines()[-1])
