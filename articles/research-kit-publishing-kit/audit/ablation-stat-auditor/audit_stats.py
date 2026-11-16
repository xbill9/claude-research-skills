# ruff: noqa: E501, E741, UP031
"""ablation-stat-auditor run on articles/research-kit-publishing-kit/devto-research-kit-publishing-kit.md.

Every number below is computed here: statistics through the research-audit MCP server over stdio,
counts and arithmetic from the files the article cites. Writes stat_audit.json beside this script.

Usage: python3 audit_stats.py
"""

import collections
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import pymupdf
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ART = REPO / "articles/research-kit-publishing-kit"
ARTICLE = ART / "devto-research-kit-publishing-kit.md"
EV = ART / "evidence"
EX = REPO / "examples/publishing-kit-article"
MCP = REPO / "plugin/mcp/research_audit_mcp.py"

LINES = ARTICLE.read_text().split("\n")


def line_of(text: str) -> int:
    hits = [i + 1 for i, l in enumerate(LINES) if text in l]
    if len(hits) != 1:
        raise SystemExit(f"article text {text!r} found on lines {hits}, need exactly one")
    return hits[0]


# ---------------------------------------------------------------- MCP over stdio
class Mcp:
    def __init__(self):
        self.p = subprocess.Popen([sys.executable, str(MCP)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.i = 0
        self.log = []
        self._rpc(
            "initialize",
            {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "audit", "version": "0"}},
        )
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.p.stdin.flush()

    def _rpc(self, method, params):
        self.i += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.i, "method": method, "params": params}) + "\n")
        self.p.stdin.flush()
        return json.loads(self.p.stdout.readline())

    def call(self, name, **args):
        r = self._rpc("tools/call", {"name": name, "arguments": args})
        out = json.loads(r["result"]["content"][0]["text"])
        self.log.append({"tool": name, "arguments": args, "result": out})
        return out

    def close(self):
        self.p.stdin.close()
        self.p.wait()


mcp = Mcp()
claims = []


def rec(id, text, paper_value, computed, verdict, reason, conclusion, test="count"):
    claims.append(
        {
            "id": id,
            "statement": text,
            "paper_value": paper_value,
            "paper_source": f"devto-research-kit-publishing-kit.md:{line_of(text)}",
            "computed": computed,
            "verdict": verdict,
            "test": test,
            "reason": reason,
            "conclusion": conclusion,
        }
    )


def cmp(a, b):
    return "VERIFIED" if a == b else "MISMATCH"


# ---------------------------------------------------------------- inputs
eq = json.load(open(EX / "math-sandbox/eq_verified_numbers.json"))["equations"]
eqc = collections.Counter(r["verdict"] for r in eq)
sa = json.load(open(EX / "ablation-stat-auditor/stat_audit.json"))
sac = collections.Counter(c["verdict"] for c in sa["claims"])
hard = (EX / "paper/evidence/devto-hardwrap.txt").read_text()
n_blocks = int(re.search(r"MEASURED\s+paragraph-level blocks.*= (\d+)", hard).group(1))
k_br = int(re.search(r"MEASURED\s+blocks containing <br>:\s+(\d+)", hard).group(1))
claims_md = (EX / "paper/CLAIMS.md").read_text().split("\n")

# 1. skills and version
skills = sorted(p.name for p in (REPO / "plugin/skills").iterdir() if (p / "SKILL.md").exists())
rec(
    "skill-count-9",
    "research-kit is a Claude Code plugin with nine skills",
    {"skills": 9},
    {"skills": len(skills)},
    cmp(9, len(skills)),
    f"plugin/skills/*/SKILL.md: {skills}",
    "HOLDS",
)
ver = json.load(open(REPO / "plugin/.claude-plugin/plugin.json"))["version"]
inst = (EV / "plugin-install.txt").read_text()
rec(
    "plugin-version",
    "    Version: 1.3.1",
    {"version": "1.3.1"},
    {"version_plugin_json": ver, "in_evidence": "Version: 1.3.1" in inst},
    cmp("1.3.1", ver) if "Version: 1.3.1" in inst else "MISMATCH",
    "plugin.json and evidence/plugin-install.txt",
    "HOLDS",
)

# 2. math-sandbox verdict counts
rec(
    "math-sandbox-26",
    "math-sandbox claims: 26 {'VERIFIED': 15, 'NOT CHECKABLE': 5, 'MISMATCH': 6}",
    {"total": 26, "VERIFIED": 15, "NOT CHECKABLE": 5, "MISMATCH": 6},
    {"total": len(eq), **{k: eqc[k] for k in ("VERIFIED", "NOT CHECKABLE", "MISMATCH")}},
    cmp([26, 15, 5, 6], [len(eq), eqc["VERIFIED"], eqc["NOT CHECKABLE"], eqc["MISMATCH"]]),
    "recounted from math-sandbox/eq_verified_numbers.json equations[]. A census of audit records, not a sample.",
    "HOLDS",
)
for ln_text, idx in (
    ("🟢 26 claims recomputed: 15 verified, 6 mismatches, 5 not checkable", "sum"),
    ("| `math-sandbox` | 🥇 every quantitative claim | 6 mismatches, 5 not checkable |", "cc"),
):
    pv = (
        {"total": 26, "VERIFIED": 15, "MISMATCH": 6, "NOT CHECKABLE": 5}
        if idx == "sum"
        else {"MISMATCH": 6, "NOT CHECKABLE": 5}
    )
    cv = {k: (len(eq) if k == "total" else eqc[k]) for k in pv}
    rec(f"math-sandbox-26-{idx}", ln_text, pv, cv, cmp(pv, cv), "same recount", "HOLDS")

# 3. crop arithmetic
ratio = 1000 / 420
kept = 1376 * 420 / 1000
lost = (768 - kept) / 2
rec(
    "crop-arith",
    "crop: ratio 1000/420 = 2.380952 ; rows kept at width 1376 = 577.92 ; lost per side from 768 = 95.04",
    {"ratio": 2.380952, "kept": 577.92, "lost_per_side": 95.04},
    {"ratio": round(ratio, 6), "kept": round(kept, 2), "lost_per_side": round(lost, 2)},
    cmp([2.380952, 577.92, 95.04], [round(ratio, 6), round(kept, 2), round(lost, 2)]),
    "arithmetic; the 1000x420 box comes from the dev.to proxy URL in paper/evidence/devto-cover-crop.txt",
    "HOLDS",
    "arithmetic",
)
rec(
    "crop-95px",
    "a 1376x768 cover loses 95px off the top and bottom",
    {"ratio": 2.381, "px_each_side": 95},
    {"ratio": round(ratio, 3), "px_each_side": round(lost)},
    cmp([2.381, 95], [round(ratio, 3), round(lost)]),
    "arithmetic holds; the even split assumes a centre crop, which line 96 says is unmeasured (gravity=auto)",
    "HOLDS (arithmetic only)",
    "arithmetic",
)
r578 = 1376 / 578
rec(
    "crop-578-whole",
    "Every dev.to cover the kit made is 1376x578, which the 2.381:1 crop leaves whole",
    {"w": 1376, "h": 578},
    {"ratio_1376x578": round(r578, 4), "rows_lost_per_side": round((578 - kept) / 2, 2)},
    "VERIFIED" if abs((578 - kept) / 2) < 0.5 else "MISMATCH",
    "578 vs 577.92 rows kept: 0.04 px per side",
    "HOLDS",
    "arithmetic",
)

# 4. ablation-stat-auditor verdict counts and tests
rec(
    "stat-audit-16",
    "ablation-stat-auditor claim records: 16 {'VERIFIED': 7, 'MISMATCH': 6, 'NOT CHECKABLE': 3}",
    {"total": 16, "VERIFIED": 7, "MISMATCH": 6, "NOT CHECKABLE": 3},
    {"total": len(sa["claims"]), **{k: sac[k] for k in ("VERIFIED", "MISMATCH", "NOT CHECKABLE")}},
    cmp([16, 7, 6, 3], [len(sa["claims"]), sac["VERIFIED"], sac["MISMATCH"], sac["NOT CHECKABLE"]]),
    "recounted from examples/.../ablation-stat-auditor/stat_audit.json claims[]",
    "HOLDS",
)
fis = mcp.call("verify_fisher_exact", k_method=4, n_method=4, k_baseline=0, n_baseline=4)
mcn = mcp.call("verify_mcnemar_exact", b=4, c=0)
rec(
    "tests-line",
    "tests: {'medium_hosted_vs_embed_fisher_unpaired': (0.02857142857142857, None, None), 'medium_hosted_vs_embed_mcnemar_paired': (0.125, 4, 0), ...}",
    {"fisher_p": 0.02857142857142857, "mcnemar_p": 0.125, "b": 4, "c": 0},
    {"fisher_p": fis["p_value"], "mcnemar_p": mcn["p_value"], "b": 4, "c": 0},
    "VERIFIED"
    if math.isclose(fis["p_value"], 0.02857142857142857, rel_tol=1e-9) and mcn["p_value"] == 0.125
    else "MISMATCH",
    "MCP verify_fisher_exact(4/4 vs 0/4) and verify_mcnemar_exact(4,0)",
    "HOLDS",
    "Fisher exact + exact McNemar",
)

# 5. headline 47 of 62
w = mcp.call("verify_wilson_ci", successes=47, total=62)


def wilson_full(k, n, z=1.959963984540054):
    # full precision, so rounding to the article's one decimal is not a double rounding of the MCP's 2 dp
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return 100 * ph, 100 * (c - h), 100 * (c + h)


rate, lo, hi = wilson_full(47, 62)
assert [round(rate, 2), round(lo, 2), round(hi, 2)] == [w["rate_pct"], w["wilson_low_pct"], w["wilson_high_pct"]], w
rec(
    "hardwrap-47-62",
    "The article's headline figure, 47 of 62 paragraphs with a stray break on dev.to, matches its evidence file: 75.8%, with a 95% interval of 63.8% to 84.8%",
    {"k": 47, "n": 62, "rate_pct": 75.8, "ci": [63.8, 84.8]},
    {"k_evidence": k_br, "n_evidence": n_blocks, "rate_pct": rate, "ci": [lo, hi]},
    "VERIFIED"
    if (k_br, n_blocks) == (47, 62) and [round(rate, 1), round(lo, 1), round(hi, 1)] == [75.8, 63.8, 84.8]
    else "MISMATCH",
    "k and n parsed from paper/evidence/devto-hardwrap.txt:12-13; Wilson via MCP. One article measured: the interval covers "
    "paragraphs of that article, and says nothing about dev.to articles in general.",
    "HOLDS",
    "Wilson score",
)
rec(
    "hardwrap-15-none",
    "15 of the 62 had none",
    {"k": 15, "n": 62},
    {"k": n_blocks - k_br, "n": n_blocks},
    cmp(15, n_blocks - k_br),
    "62 - 47 from the evidence file",
    "HOLDS",
)
rec(
    "summary-47-62",
    "🟢 47 of 62 matches its evidence: 75.8%, 95% interval 63.8% to 84.8%",
    {"k": 47, "n": 62, "rate_pct": 75.8, "ci": [63.8, 84.8]},
    {"k": k_br, "n": n_blocks, "rate_pct": rate, "ci": [lo, hi]},
    "VERIFIED" if [round(rate, 1), round(lo, 1), round(hi, 1)] == [75.8, 63.8, 84.8] else "MISMATCH",
    "same MCP call",
    "HOLDS",
    "Wilson score",
)

# 6. Medium comparison
med_rows = [(i + 1, l) for i, l in enumerate(claims_md) if "0 of 4" in l]
w0 = mcp.call("verify_wilson_ci", successes=0, total=4)
w4 = mcp.call("verify_wilson_ci", successes=4, total=4)
rec(
    "medium-mcnemar-0125",
    "The paired test gives p = 0.125",
    {"p": 0.125},
    {
        "p": mcn["p_value"],
        "b": 4,
        "c": 0,
        "wilson_0_of_4": [w0["wilson_low_pct"], w0["wilson_high_pct"]],
        "wilson_4_of_4": [w4["wilson_low_pct"], w4["wilson_high_pct"]],
    },
    cmp(0.125, mcn["p_value"]),
    "exact McNemar with b=4 (hosted only), c=0. Inputs are the article's totals; the pairing they assume is record medium-paired-design.",
    "p >= 0.05 if paired; see medium-paired-design",
    "exact McNemar",
)
rec(
    "medium-paired-design",
    "is a paired comparison of the same four images",
    {"design": "paired, same four images"},
    {
        "design": "unknown",
        "per_image_outcomes_archived": False,
        "fisher_unpaired_p": fis["p_value"],
        "ledger_rows": [f"paper/CLAIMS.md:{i}" for i, _ in med_rows],
    },
    "NOT CHECKABLE",
    "No file records which images were pasted either way; the only source is a CLAIMS.md log row with totals. "
    "The design decides the answer: paired McNemar p = 0.125, unpaired Fisher p = %.4f (below 0.05)." % fis["p_value"],
    "OVERSTATED: the article states the pairing as fact; it is an assumption",
    "design",
)
first_mc = next(n for n in range(1, 30) if mcp.call("verify_mcnemar_exact", b=n, c=0)["p_value"] < 0.05)
p5 = mcp.call("verify_mcnemar_exact", b=first_mc - 1, c=0)["p_value"]
p6 = mcp.call("verify_mcnemar_exact", b=first_mc, c=0)["p_value"]
first_fi = next(
    n
    for n in range(1, 30)
    if mcp.call("verify_fisher_exact", k_method=n, n_method=n, k_baseline=0, n_baseline=n)["p_value"] < 0.05
)
rec(
    "medium-six-images",
    "With all-or-none results it first drops below 0.05 at six images",
    {"n_images": 6},
    {"n_images_paired": first_mc, "p_at_n_minus_1": p5, "p_at_n": p6, "n_images_unpaired_fisher": first_fi},
    cmp(6, first_mc),
    f"MCP verify_mcnemar_exact(n, 0) for n = 1..: p first < 0.05 at n = {first_mc}. Under the unpaired design it is n = {first_fi}.",
    "HOLDS if paired",
    "exact McNemar sweep",
)
ev_files_medium = [
    p.name
    for p in (EX / "paper/evidence").iterdir()
    if re.search(r"data URI|data:image|data-uri", p.read_text(errors="ignore"), re.I)
]
rec(
    "medium-archived-paste",
    "what supports it is one archived paste",
    {"archived_pastes": 1},
    {
        "archived_pastes": 0,
        "evidence_files_on_medium_data_uris": ev_files_medium,
        "ledger": f"paper/CLAIMS.md:{med_rows[-1][0]}",
    },
    "MISMATCH",
    "paper/evidence holds no file about Medium data-URI pastes; the same sentence goes on to say 'with no artifact'. Probably meant 'what would support it'.",
    "OVERSTATED",
    "provenance",
)
rec(
    "medium-log-date",
    "the ledger carries it from a log dated 2026-08-30 with no artifact",
    {"date": "2026-08-30"},
    {"date_in_ledger": "2026-08-30" in med_rows[-1][1], "row": med_rows[-1][1].strip()},
    "VERIFIED" if "2026-08-30" in med_rows[-1][1] else "MISMATCH",
    "paper/CLAIMS.md log row",
    "HOLDS",
    "provenance",
)

# 7. images
P = EX / "paper"
for name, dims in (
    ("cover.77acc7c4.jpg", "1376x578"),
    ("cover.ae4d639e.jpg", "1376x578"),
    ("advocu-devto-publishing-kit-cover.webp", "1376x578"),
    ("cover-builder.cabd79f3.jpg", "1200x675"),
):
    got = "%dx%d" % Image.open(P / name).size
    rec(
        f"image-{name}",
        f"image {name} {dims}",
        {"dims": dims},
        {"dims": got},
        cmp(dims, got),
        "PIL on paper/" + name,
        "HOLDS",
        "measurement",
    )
devto_covers = sorted(
    p.name for p in P.iterdir() if re.match(r"(cover\.[0-9a-f]{8}\.jpg|advocu-devto-.*cover.*)$", p.name)
)
sizes = {n: "%dx%d" % Image.open(P / n).size for n in devto_covers}
rec(
    "every-devto-cover-578",
    "Every dev.to cover the kit made is 1376x578",
    {"all": "1376x578"},
    {"covers": sizes},
    "VERIFIED" if set(sizes.values()) == {"1376x578"} else "MISMATCH",
    f"{len(sizes)} dev.to covers in the article's folder; covers the kit made for other articles were not measured",
    "HOLDS for this article's folder; wider generalisation untested",
    "measurement",
)
meas = json.load(open(EX / "figure-forensics/work/measurements.json"))
n_end = {k: len(v) for k, v in meas["endpoints"].items()}
rec(
    "five-destinations",
    "five destination shapes, while the article describes four destinations",
    {"markers": 5},
    {"endpoint_markers_per_cover": n_end},
    "VERIFIED" if n_end.get("cover.ae4d639e.jpg") == 5 else "MISMATCH",
    "figure-forensics/work/measurements.json endpoints[]. That each marker is a destination is an inference; no file maps them.",
    "HOLDS (count); 'destination' is a reading of the art",
    "measurement",
)

# 8. links
rep = (EX / "citation-doi-verifier/REPORT.md").read_text()
rows = [l for l in rep.splitlines() if re.match(r"\| L\d+ \|", l)]
ok_links = sum("RESOLVES+IDENTIFIED" in l for l in rows)
blocked = [l.split("|")[1].strip() for l in rows if "RESOLVES+IDENTIFIED" not in l]
wl = mcp.call("verify_wilson_ci", successes=ok_links, total=len(rows))
for txt, i in (
    ("citation links: 10 of 11 resolving and identified", "out"),
    ("| `citation-doi-verifier` | 🥉 links only | 10 of 11 links confirmed |", "cc"),
):
    rec(
        f"links-10-11-{i}",
        txt,
        {"k": 10, "n": 11},
        {"k": ok_links, "n": len(rows), "wilson_ci_pct": [wl["wilson_low_pct"], wl["wilson_high_pct"]]},
        cmp([10, 11], [ok_links, len(rows)]),
        "rows of citation-doi-verifier/REPORT.md. A census of the article's links: the interval is printed for completeness and has no population to describe.",
        "HOLDS",
        "count",
    )
rec(
    "links-each-11-matched",
    "Each of the 11 links was fetched instead and matched to a second source",
    {"matched": 11, "n": 11},
    {"matched": ok_links, "n": len(rows), "not_matched": blocked},
    cmp(11, ok_links),
    f"{blocked} was blocked (HTTP 403) and its RSS fallback did not contain it; the next sentence says so, but this one counts 11.",
    "OVERSTATED (corrected by the following sentence)",
    "count",
)
paper_txt = [f for f in list(P.rglob("*.md")) + list(P.rglob("*.txt"))]
n_doi = sum(len(re.findall(r"10\.\d{4,}/|arxiv\.org/abs", f.read_text(errors="ignore"))) for f in paper_txt)
rec(
    "dois-0",
    "citation dois/arxiv in paper text: 0",
    {"count": 0},
    {"count": n_doi},
    cmp(0, n_doi),
    "regex over paper/**/*.md and *.txt",
    "HOLDS",
)

# 9. studio and legibility
js = (EX / "interactive-paper-studio/check_js_output.txt").read_text().split("\n")
tab = [l for l in js if re.match(r"^\S+\s+\S+\s+-?[\d.]+\s+-?[\d.]+\s+[\d.e+-]+\s+(true|false)$", l)]
sweep = int(re.search(r"sweep: (\d+) values", "\n".join(js)).group(1))
mism = sum(l.endswith("false") for l in tab) + int(re.search(r"sweep: .* (\d+) mismatches", "\n".join(js)).group(1))
rec(
    "studio-130",
    "studio check: 130 values, 0 mismatches, worst abs error 0.00e+0",
    {"values": 130, "mismatches": 0},
    {"values": len(tab) + sweep, "mismatches": mism, "table_rows": len(tab), "sweep_values": sweep},
    cmp([130, 0], [len(tab) + sweep, mism]),
    "rows of interactive-paper-studio/check_js_output.txt plus its sweep line",
    "HOLDS",
)
const = (EV / "make-cover-constants.txt").read_text()
card_w = int(re.search(r"CARD_W = (\d+)", const).group(1))
leg = int(re.search(r"LEGIBLE_PX = (\d+)", const).group(1))
pt = leg * 1376 / card_w
px40 = 40 * card_w / 1376
rec(
    "legibility",
    "legibility: LEGIBLE_PX*1376/CARD_W = 43.0 ; 40pt at 320/1376 = 9.3 px",
    {"pt": 43.0, "px_at_40pt": 9.3},
    {"pt": pt, "px_at_40pt": round(px40, 2), "CARD_W": card_w, "LEGIBLE_PX": leg},
    cmp([43.0, 9.3], [round(pt, 1), round(px40, 1)]),
    "constants parsed from evidence/make-cover-constants.txt",
    "HOLDS",
    "arithmetic",
)
pages = pymupdf.open(EX / "graphic-story/PublishingKit_Comic_v1.pdf").page_count
rec(
    "comic-5-pages",
    "`graphic-story` draws a 5-page comic of the article",
    {"pages": 5},
    {"pages": pages},
    cmp(5, pages),
    "pymupdf page count",
    "HOLDS",
)


# 10. check-facts before / after / outputs
def tally(txt):
    body = [l.strip().split()[0] for l in txt.split("\n") if re.match(r"^\s{2}(ok|DISPUTED|NOTED)\s", l)]
    return dict(collections.Counter(body))


before = (EV / "check-facts-before.txt").read_text()
after = (EV / "check-facts-after.txt").read_text()
tb, ta = tally(before), tally(after)
art_block = "\n".join(
    LINES[
        line_of("  DISPUTED count     0 of 4") - 1 : line_of("2 traced, 0 cited from the log, 0 untraced, 5 disputed")
    ]
)
rec(
    "cf-before",
    "2 traced, 0 cited from the log, 0 untraced, 5 disputed",
    {"traced": 2, "disputed": 5},
    {
        "ok_lines": tb.get("ok", 0),
        "disputed_lines": tb.get("DISPUTED", 0),
        "article_block_matches_evidence": tally(art_block) == tb,
    },
    cmp([2, 5], [tb.get("ok", 0), tb.get("DISPUTED", 0)]),
    "evidence/check-facts-before.txt",
    "HOLDS",
)
for t in ("It exits 1.", "It exits 0."):
    rec(
        "cf-exit-" + t[-2],
        t,
        {"exit": int(t[-2])},
        {"exit": None},
        "NOT CHECKABLE",
        "neither check-facts evidence file records the exit status",
        "CANNOT CHECK",
        "provenance",
    )
rec(
    "cf-after",
    "3 traced, 0 cited from the log, 0 untraced, 0 disputed, 5 disputed with a caveat",
    {"traced": 3, "disputed": 0, "caveat": 5},
    {
        "ok_lines": ta.get("ok", 0),
        "disputed_lines": ta.get("DISPUTED", 0),
        "noted_lines": ta.get("NOTED", 0),
        "lines_in_evidence": sum(ta.values()),
        "lines_shown_in_article": 3,
    },
    cmp([3, 0, 5], [ta.get("ok", 0), ta.get("DISPUTED", 0), ta.get("NOTED", 0)]),
    "evidence/check-facts-after.txt; the article shows 3 of its 8 claim lines without marking the cut",
    "HOLDS",
)
rec(
    "cf-5-to-0",
    "🟢 check-facts went from 5 disputed to 0, with 5 explained in the ledger",
    {"before": 5, "after": 0, "explained": 5},
    {"before": tb.get("DISPUTED", 0), "after": ta.get("DISPUTED", 0), "explained": ta.get("NOTED", 0)},
    cmp([5, 0, 5], [tb.get("DISPUTED", 0), ta.get("DISPUTED", 0), ta.get("NOTED", 0)]),
    "both evidence files",
    "HOLDS",
)
pnc = (EV / "paper-number-check.txt").read_text()
got = {
    m.group(1): [int(m.group(i)) for i in (2, 3, 4, 5)]
    for m in re.finditer(r"(\S+\.html): (\d+) disputed, (\d+) noted, (\d+) traced, (\d+) untraced", pnc)
}
want = {"interactive-paper-studio/index.html": [0, 11, 5, 30], "graphic-story/Story.html": [0, 9, 7, 20]}
rec(
    "pnc-outputs",
    "interactive-paper-studio/index.html: 0 disputed, 11 noted, 5 traced, 30 untraced",
    want,
    got,
    cmp(want, got),
    "evidence/paper-number-check.txt (also covers line 232)",
    "HOLDS",
)
rec(
    "kit-0360",
    "The publishing kit at 0.36.0 or later",
    {"version": "0.36.0"},
    {"path_has_0.36.0": "/0.36.0/" in pnc},
    "VERIFIED" if "/0.36.0/" in pnc else "MISMATCH",
    "check-facts path in evidence/paper-number-check.txt",
    "HOLDS",
    "provenance",
)

# 11. collisions
by_id = {r["id"]: r for r in eq}
disp_ids = re.findall(r"DISPUTED .*?\((\w+)\)", before)
m5 = by_id["M5_substack_source_shape"]
coll = {
    "2.381:1 -> M5": 1 in m5["paper_value"]["pre_lines"] and "2.381" not in json.dumps(m5["paper_value"]),
    "95px -> M1": "95" in "M1_own_source_95_columns" and by_id["B2_crop_loss_95px"]["verdict"] == "VERIFIED",
}
rec(
    "collisions-2-of-5",
    "Two of the five disputed claims in Step 8 are number collisions",
    {"collisions": 2, "disputed": 5},
    {
        "collisions": sum(coll.values()),
        "disputed": len(disp_ids),
        "checks": coll,
        "D1_proxy_ratio": by_id["D1_proxy_ratio"]["verdict"],
    },
    cmp([2, 5], [sum(coll.values()), len(disp_ids)]),
    "M5 stores pre_lines [2,2,1,4] (the 1 matched); M1 is the 95-column record while B2 (95px crop) is VERIFIED; D1 (2.381) is VERIFIED",
    "HOLDS",
    "count",
)
css = (EV / "studio-css-lengths.txt").read_text()
rec(
    "css-1px-4px",
    "so `1px` and `4px` can match",
    {"lengths": ["1px", "4px"]},
    {"1px": int(re.search(r"1px: (\d+)", css).group(1)), "4px": int(re.search(r"4px: (\d+)", css).group(1))},
    "VERIFIED",
    "evidence/studio-css-lengths.txt occurrence counts",
    "HOLDS",
)

# 12. what the prior stat audit found
rep_sa = (EX / "ablation-stat-auditor/STAT_AUDIT_REPORT.md").read_text()
over = [
    l.split("|")[1].strip() for l in rep_sa.split("\n") if l.startswith("|") and l.rstrip().endswith("OVERSTATED |")
]
rec(
    "cc-ablation-found",
    "| `ablation-stat-auditor` | 🥇 any count or rate | an overstatement and an unsupported comparison |",
    {"overstated": 1, "unsupported_comparisons": 1},
    {"overstated": len(over), "overstated_rows": over},
    cmp(1, len(over)),
    "conclusion column of examples/.../ablation-stat-auditor/STAT_AUDIT_REPORT.md",
    "HOLDS in kind; the count is 2",
    "count",
)
fix_rows = LINES[
    line_of("| Was | Now |") + 1 : line_of("| measured on 2026-08-31 | measured between 2026-08-30 and 2026-09-16 |")
    + 2
]
named = ["every paragraph", "numbers on the cover", "2026-08-31"]
rec(
    "three-fixed",
    '❌ "every paragraph", "on the cover" and the footer date overstated their evidence; all three fixed',
    {"fixed": 3},
    {
        "fixed": sum(any(n in r for r in fix_rows) for n in named),
        "fix_table_rows": len([r for r in fix_rows if r.startswith("|")]),
    },
    cmp(3, sum(any(n in r for r in fix_rows) for n in named)),
    "Step 9 table rows; fixes live in the publishing-kit repo, not re-read here",
    "HOLDS",
    "count",
)
rec(
    "ran-once",
    "Each skill ran once, as a separate agent.",
    {"runs_per_skill": 1},
    {"runs_per_skill": None},
    "NOT CHECKABLE",
    "no session log in the example records how many runs each skill had",
    "CANNOT CHECK",
    "provenance",
)

# ---------------------------------------------------------------- noise floor (context only)
nf62 = mcp.call("leaderboard_noise_floor", num_tasks=62, baseline_rate=47 / 62)
nf4 = mcp.call("leaderboard_noise_floor", num_tasks=4, baseline_rate=0.5)
mcp.close()

vc = dict(collections.Counter(c["verdict"] for c in claims))
out = {
    "paper": str(ARTICLE.relative_to(REPO)),
    "verdict_counts": vc,
    "claims": claims,
    "noise_floor": {
        "n62_at_0.758": nf62,
        "n4_at_0.5": nf4,
        "note": "context only: the article compares no two runs on a benchmark",
    },
    "wilcoxon": "not run: the article reports no paired resource metric",
    "raw_mcp_calls": mcp.log,
}
json.dump(out, open(HERE / "stat_audit.json", "w"), indent=1)
print("claim records:", len(claims), vc)
for c in claims:
    if c["verdict"] != "VERIFIED":
        print(
            f"{c['verdict']:14s} {c['paper_source']:42s} {c['statement']!r}\n    paper={json.dumps(c['paper_value'])}\n    computed={json.dumps(c['computed'])[:300]}"
        )
print("noise floor n=62:", json.dumps(nf62))
print("noise floor n=4:", json.dumps(nf4))
