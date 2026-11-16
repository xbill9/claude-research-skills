"""math-sandbox audit of devto-research-kit-publishing-kit.md.

Every quantitative claim in the article is recomputed here from the example's files, the article's
evidence/ folder, the research-kit plugin and the publishing-kit working tree, and written to
eq_verified_numbers.json. Wilson, Fisher and McNemar come from the plugin's MCP server over stdio.

    python3 verify_math.py
"""

import collections
import json
import re
import subprocess
import sys
from pathlib import Path

import pymupdf
from PIL import Image

HERE = Path(__file__).resolve().parent
ART_DIR = HERE.parents[1]
ART = ART_DIR / "devto-research-kit-publishing-kit.md"
EVD = ART_DIR / "evidence"
REPO = ART_DIR.parents[1]
EX = REPO / "examples/publishing-kit-article"
PAPER = EX / "paper"
PK = Path.home() / "publishing-kit"
MCP = REPO / "plugin/mcp/research_audit_mcp.py"
SEED = 42  # no sampling in this audit; kept for the skill's contract

LINES = ART.read_text().split("\n")


def line_of(phrase):
    hits = [i + 1 for i, l in enumerate(LINES) if phrase in l]
    if not hits:
        sys.exit(f"phrase not found in article: {phrase!r}")
    return hits[0]


def mcp(calls):
    msgs = [
        {"jsonrpc": "2.0", "id": 0, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "audit", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
    ]
    for i, (name, args) in enumerate(calls, 1):
        msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": name, "arguments": args}})
    out = subprocess.run([sys.executable, str(MCP)], input="\n".join(json.dumps(m) for m in msgs) + "\n",
                         capture_output=True, text=True, check=True).stdout
    res = {}
    for l in out.splitlines():
        r = json.loads(l)
        if r.get("id"):
            res[r["id"]] = json.loads(r["result"]["content"][0]["text"])
    (HERE / "mcp_calls.jsonl").write_text("\n".join(json.dumps(m) for m in msgs) + "\n")
    (HERE / "mcp_responses.txt").write_text(out)
    return [res[i] for i in range(1, len(calls) + 1)]


records = []


def rec(id_, phrase, statement, paper_value, computed, verdict, reason, source, overstatement=False):
    r = {"id": id_, "statement": statement, "paper_value": paper_value,
         "paper_source": f"devto-research-kit-publishing-kit.md:{line_of(phrase)}", "computed": computed,
         "verdict": verdict, "reason": reason, "evidence": source}
    if overstatement:
        r["overstatement"] = True
    records.append(r)


def cmp(a, b):
    return "VERIFIED" if a == b else "MISMATCH"


# ---------- inputs ----------
m = json.load(open(EX / "math-sandbox/eq_verified_numbers.json"))["equations"]
mid = {r["id"]: r for r in m}
s = json.load(open(EX / "ablation-stat-auditor/stat_audit.json"))
before = (EVD / "check-facts-before.txt").read_text()
after = (EVD / "check-facts-after.txt").read_text()
pnc = (EVD / "paper-number-check.txt").read_text()
report_rows = [l for l in (EX / "citation-doi-verifier/REPORT.md").read_text().splitlines() if re.match(r"\| L\d+ \|", l)]

# ---------- MCP statistics ----------
mc_n = list(range(1, 11))
stats = mcp([("verify_wilson_ci", {"successes": 47, "total": 62}),
             ("verify_fisher_exact", {"k_method": 4, "n_method": 4, "k_baseline": 0, "n_baseline": 4}),
             ("verify_mcnemar_exact", {"b": 4, "c": 0})]
            + [("verify_mcnemar_exact", {"b": n, "c": 0}) for n in mc_n])
wil, fis, mcn = stats[0], stats[1], stats[2]
mc_p = {n: r["p_value"] for n, r in zip(mc_n, stats[3:])}
first_sig = min(n for n, p in mc_p.items() if p < 0.05)

# ---------- C01 skill count ----------
skills = sorted(p.parent.name for p in (REPO / "plugin/skills").glob("*/SKILL.md"))
table_skills = re.findall(r"^\| `([a-z-]+)` \| (?!Fit)", "\n".join(LINES[20:30]), re.M)
rec("C01_nine_skills", "nine skills for research-paper engineering", "research-kit has nine skills; table lists 7, two more named",
    {"skills": 9, "table_rows": 7}, {"skills": len(skills), "table_rows": len(table_skills), "names": skills},
    cmp({"skills": 9, "table_rows": 7}, {"skills": len(skills), "table_rows": len(table_skills)}),
    "counted SKILL.md files under plugin/skills", "plugin/skills/*/SKILL.md")

# ---------- C02 version ----------
pj = json.load(open(REPO / "plugin/.claude-plugin/plugin.json"))["version"]
mk = json.load(open(REPO / ".claude-plugin/marketplace.json"))["metadata"]["version"]
ev = re.search(r"Version: (\S+)", (EVD / "plugin-install.txt").read_text()).group(1)
rec("C02_version_1_3_1", "Version: 1.3.1", "research-kit version 1.3.1 (install output, Scope line)", "1.3.1",
    {"plugin.json": pj, "marketplace.json": mk, "evidence": ev}, "VERIFIED" if pj == mk == ev == "1.3.1" else "MISMATCH",
    "plugin.json, marketplace.json and plugin-install.txt agree", "plugin.json; marketplace.json; evidence/plugin-install.txt")

# ---------- C03 publishing kit 0.36.0 ----------
pkv = re.search(r"publishing/(\d+\.\d+\.\d+)/", pnc).group(1)
rec("C03_publishing_kit_0_36_0", "check-facts.py` from 0.36.0", "check-facts.py from publishing kit 0.36.0", "0.36.0",
    pkv, cmp("0.36.0", pkv), "version in the check-facts.py path recorded by paper-number-check.txt; check-facts-before/after.txt do not name a version",
    "evidence/paper-number-check.txt")

# ---------- C04 math-sandbox tallies ----------
mc = dict(collections.Counter(r["verdict"] for r in m))
pv = {"total": 26, "VERIFIED": 15, "MISMATCH": 6, "NOT CHECKABLE": 5}
cv = {"total": len(m), **{k: mc.get(k, 0) for k in ("VERIFIED", "MISMATCH", "NOT CHECKABLE")}}
for ph, i in (("math-sandbox claims: 26", "a"), ("6 mismatches, 5 not checkable |", "b"), ("26 claims recomputed", "c")):
    rec(f"C04{i}_math_sandbox_tally", ph, "math-sandbox: 26 claims, 15 VERIFIED, 6 MISMATCH, 5 NOT CHECKABLE", pv, cv, cmp(pv, cv),
        "recounted verdicts in eq_verified_numbers.json", "examples/.../math-sandbox/eq_verified_numbers.json")

# ---------- C05 crop arithmetic ----------
crop = {"ratio": round(1000 / 420, 6), "kept": round(1376 * 420 / 1000, 2), "lost_side": round((768 - 1376 * 420 / 1000) / 2, 2)}
rec("C05_crop_arithmetic", "crop: ratio 1000/420", "ratio 1000/420 = 2.380952; rows kept 577.92; lost per side 95.04",
    {"ratio": 2.380952, "kept": 577.92, "lost_side": 95.04}, crop, cmp({"ratio": 2.380952, "kept": 577.92, "lost_side": 95.04}, crop),
    "recomputed from the 1000x420 proxy size", "paper/evidence/devto-cover-crop.txt (width=1000,height=420)")
rec("C06_crop_95px", "so a 1376x768 cover loses 95px off the top and bottom. The arithmetic", "2.381:1 crop; 1376x768 loses 95px top and bottom",
    {"ratio": 2.381, "px_each_side": 95}, {"ratio": round(1000 / 420, 3), "px_each_side": round(crop["lost_side"])},
    cmp({"ratio": 2.381, "px_each_side": 95}, {"ratio": round(1000 / 420, 3), "px_each_side": round(crop["lost_side"])}),
    "95.04 px a side under a centre crop", "computed")
grav = sorted({f.name for f in (PAPER / "evidence").glob("*.txt") if "gravity=auto" in f.read_text()})
rec("C07_gravity_auto", "says `gravity=auto`", "the proxy URL in the evidence says gravity=auto", "gravity=auto", grav,
    "VERIFIED" if grav else "MISMATCH", "found in the paper's evidence files", "paper/evidence/")

# ---------- C08 ablation tallies ----------
ac = collections.Counter(c.get("verdict") for c in s["claims"])
pv = {"total": 16, "VERIFIED": 7, "MISMATCH": 6, "NOT CHECKABLE": 3}
cv = {"total": len(s["claims"]), **{k: ac.get(k, 0) for k in ("VERIFIED", "MISMATCH", "NOT CHECKABLE")}}
rec("C08_ablation_tally", "ablation-stat-auditor claim records: 16", "16 claim records: 7/6/3", pv, cv, cmp(pv, cv),
    "recounted verdicts in stat_audit.json", "examples/.../ablation-stat-auditor/stat_audit.json")

# ---------- C09-C13 statistics ----------
pv = {"fisher_p": 0.02857142857142857, "mcnemar_p": 0.125, "b": 4, "c": 0}
cv = {"fisher_p": fis["p_value"], "mcnemar_p": mcn["p_value"], "b": 4, "c": 0}
ok = abs(pv["fisher_p"] - cv["fisher_p"]) < 1e-12 and abs(pv["mcnemar_p"] - cv["mcnemar_p"]) < 1e-12
rec("C09_tests_line", "'medium_hosted_vs_embed_fisher_unpaired': (0.02857", "Fisher 4/4 vs 0/4 p=0.02857; McNemar b=4 c=0 p=0.125",
    pv, cv, "VERIFIED" if ok else "MISMATCH", "recomputed through the MCP server", "MCP verify_fisher_exact, verify_mcnemar_exact")
wv = {"k": 47, "n": 62, "rate_pct": 75.8, "ci": [63.8, 84.8]}
# The MCP server returns 2-dp values (63.85); rounding those again to 1 dp gives 63.9. Use the full-precision
# Wilson bound for the 1-dp comparison and check it agrees with the server to 2 dp.
_p, _z, _n = 47 / 62, 1.959963984540054, 62
_c = (_p + _z**2 / (2 * _n)) / (1 + _z**2 / _n)
_h = _z * (_p * (1 - _p) / _n + _z**2 / (4 * _n**2)) ** 0.5 / (1 + _z**2 / _n)
full = [100 * _p, 100 * (_c - _h), 100 * (_c + _h)]
assert [round(x, 2) for x in full] == [wil["rate_pct"], wil["wilson_low_pct"], wil["wilson_high_pct"]]
wc = {"k": 47, "n": 62, "rate_pct": round(full[0], 1), "ci": [round(full[1], 1), round(full[2], 1)],
      "full_precision": [round(x, 4) for x in full], "mcp": [wil["rate_pct"], wil["wilson_low_pct"], wil["wilson_high_pct"]]}
for ph, i in (("47 of 62 paragraphs", "a"), ("47 of 62 matches its evidence", "b")):
    rec(f"C10{i}_wilson_47_62", ph, "47 of 62 = 75.8%, 95% Wilson 63.8% to 84.8%", wv, wc,
        cmp(wv, {k: wc[k] for k in wv}), "MCP verify_wilson_ci", "examples/.../paper/evidence/devto-hardwrap.txt via stat_audit.json")
hw = mid["E1_hardwrap_47_of_62"]["computed"]
rec("C11_15_of_62_none", "15 of the 62 had none", "15 of the 62 paragraphs had no stray break", 15, hw["n"] - hw["k"],
    cmp(15, hw["n"] - hw["k"]), "62 - 47 from the E1 record", "eq_verified_numbers.json E1")
rec("C12_mcnemar_0_125", "The paired test gives p = 0.125", "paired test on 0/4 vs 4/4 gives p = 0.125", 0.125, mcn["p_value"],
    cmp(0.125, round(mcn["p_value"], 6)), "exact McNemar, b=4 c=0", "MCP verify_mcnemar_exact")
rec("C13_first_sig_at_six", "first drops below 0.05 at six images", "all-or-none McNemar first below 0.05 at n=6", 6,
    {"first_n": first_sig, "p_by_n": {str(k): round(v, 6) for k, v in mc_p.items()}}, cmp(6, first_sig),
    "smallest n with exact McNemar p<0.05 for b=n, c=0", "MCP verify_mcnemar_exact n=1..10")
row = next(l for l in (PAPER / "CLAIMS.md").read_text().splitlines() if "0 of 4 embed" in l)
d = re.search(r"\d{4}-\d{2}-\d{2}", row).group(0)
rec("C14_log_2026_08_30", "a log dated 2026-08-30", "the ledger carries 0 of 4 from a log dated 2026-08-30", "2026-08-30", d, cmp("2026-08-30", d),
    "paper/CLAIMS.md LOG row", "paper/CLAIMS.md")

# ---------- C15-C17 figures ----------
imgs = ["cover.77acc7c4.jpg", "cover.ae4d639e.jpg", "advocu-devto-publishing-kit-cover.webp", "cover-builder.cabd79f3.jpg"]
pv = {"cover.77acc7c4.jpg": "1376x578", "cover.ae4d639e.jpg": "1376x578", "advocu-devto-publishing-kit-cover.webp": "1376x578",
      "cover-builder.cabd79f3.jpg": "1200x675"}
cv = {f: "%dx%d" % Image.open(PAPER / f).size for f in imgs}
rec("C15_image_sizes", "image cover.77acc7c4.jpg 1376x578", "four measured image sizes", pv, cv, cmp(pv, cv), "PIL", "paper/*.jpg, *.webp")
uncrop = round(578 - 1376 * 420 / 1000, 2)
rec("C16_1376x578_left_whole", "which the 2.381:1 crop leaves whole", "a 1376x578 cover survives the 2.381:1 crop whole",
    {"rows_lost": 0}, {"rows_lost_total": uncrop}, "VERIFIED" if uncrop < 1 else "MISMATCH", "under one source row lost", "computed")
tc = (PAPER / "evidence/toolchain-run.txt").read_text()
kit_devto = re.findall(r"(devto-cover-\w+\.[0-9a-f]+\.jpg) (\d+) bytes", tc)
ledger30 = next(l for l in (PAPER / "CLAIMS.md").read_text().splitlines() if l.startswith("| covers:"))
g = {p.name: "%dx%d" % Image.open(p).size for p in sorted((Path.home() / "gemma4-dev/docs").glob("devto-cover-*.jpg"))}
rec("C17_every_devto_cover_1376x578", "Every dev.to cover the kit made is 1376x578",
    "every dev.to cover the kit made is 1376x578; 1376x768 is a size the kit does not ship", {"size": "1376x578", "scope": "every"},
    {"kit_toolchain_devto_covers": [k for k, _ in kit_devto], "ledger_row": ledger30, "gemma4-dev/docs sizes": g},
    "MISMATCH", "the paper's own toolchain-run.txt (2026-08-31) records the kit writing devto-cover-aws/gde, which CLAIMS.md "
    "line 30 lists as 1376x768 and which measure 1376x768 in ~/gemma4-dev/docs; only the covers in paper/ are 1376x578",
    "paper/evidence/toolchain-run.txt; paper/CLAIMS.md:30; ~/gemma4-dev/docs", overstatement=True)
fm = json.load(open(EX / "figure-forensics/work/measurements.json"))
n_end = len(fm["endpoints"]["cover.ae4d639e.jpg"])
four = [i + 1 for i, l in enumerate((PAPER / "devto-publishing-kit.md").read_text().split("\n")) if re.search(r"\bfour (places|of its)", l)]
rec("C18a_five_shapes_four_destinations", "five destination shapes", "current cover: five destination shapes; article describes four",
    {"shapes": 5, "article_destinations": 4}, {"shapes": n_end, "article_lines_saying_four": four},
    cmp(5, n_end) if four else "MISMATCH", "endpoint markers counted by figure-forensics measure_figures.py; 'four' at paper lines listed",
    "figure-forensics/work/measurements.json; paper/devto-publishing-kit.md")
rec("C18b_covers_no_numbers", "Both covers carry no numbers", "both covers carry no numbers; current one has no text",
    {"numbers_on_covers": 0}, None, "NOT CHECKABLE",
    "figure-forensics read the images visually (RUN_NOTES finding 1); no OCR or computed text measure exists to recompute",
    "figure-forensics/RUN_NOTES.md")

# ---------- C19-C21 links ----------
ok_rows = sum("RESOLVES+IDENTIFIED" in l for l in report_rows)
rec("C19_links_10_of_11", "citation links: 10 of 11", "10 of 11 links resolving and identified", {"k": 10, "n": 11},
    {"k": ok_rows, "n": len(report_rows)}, cmp({"k": 10, "n": 11}, {"k": ok_rows, "n": len(report_rows)}), "REPORT.md rows",
    "citation-doi-verifier/REPORT.md")
rec("C19b_links_compare_table", "10 of 11 links confirmed", "Compare table: 10 of 11 links confirmed", {"k": 10, "n": 11},
    {"k": ok_rows, "n": len(report_rows)}, cmp({"k": 10, "n": 11}, {"k": ok_rows, "n": len(report_rows)}), "REPORT.md rows",
    "citation-doi-verifier/REPORT.md")
blocked = [l.split("|")[1].strip() for l in report_rows if "BLOCKED" in l]
rec("C20_each_of_11_matched", "Each of the 11 links was fetched instead and matched to a second source",
    "each of the 11 links was fetched and matched to a second source", {"matched": 11, "n": 11},
    {"matched": ok_rows, "n": len(report_rows), "blocked": blocked}, "MISMATCH",
    "L9 (Medium) returned HTTP 403 and was not matched; the next sentence of the article says so", "citation-doi-verifier/REPORT.md",
    overstatement=True)
dois = sum(len(re.findall(r"10\.\d{4,}/|arxiv\.org/abs", f.read_text(errors="ignore")))
           for f in list(PAPER.rglob("*.md")) + list(PAPER.rglob("*.txt")))
rec("C21_zero_dois", "citation dois/arxiv in paper text: 0", "0 DOIs or arXiv ids in the paper", 0, dois, cmp(0, dois), "regex over paper/",
    "paper/**/*.md, *.txt")
h403 = [l.split("|")[1].strip() for l in report_rows if "HTTP 403" in l]
rec("C21b_medium_403", "Medium answers scripts with HTTP 403", "Medium answers scripts with HTTP 403", 403, {"rows_with_403": h403},
    "VERIFIED" if h403 == ["L9"] else "MISMATCH", "REPORT.md L9", "citation-doi-verifier/REPORT.md")

# ---------- C22-C24 studio and comic ----------
last = (EX / "interactive-paper-studio/check_js_output.txt").read_text().strip().splitlines()[-1]
nums = re.match(r"(\d+) values, (\d+) mismatches, worst abs error (\S+)", last)
pv = {"values": 130, "mismatches": 0, "worst": 0.0}
cv = {"values": int(nums.group(1)), "mismatches": int(nums.group(2)), "worst": float(nums.group(3))}
rec("C22_studio_check", "studio check: 130 values", "130 values, 0 mismatches, worst error 0", pv, cv, cmp(pv, cv), "last line of check_js_output.txt",
    "interactive-paper-studio/check_js_output.txt")
mcsrc = (PK / "skills/publishing/scripts/make-cover.py").read_text()
card_w = int(re.search(r"^CARD_W = (\d+)", mcsrc, re.M).group(1))
leg = int(re.search(r"^LEGIBLE_PX = (\d+)", mcsrc, re.M).group(1))
pv = {"LEGIBLE_PX": 10, "pt": 43.0, "px_40pt": 9.3, "card": 320, "comment_says_43pt": True, "comment_still_40pt": False}
cv = {"LEGIBLE_PX": leg, "pt": leg * 1376 / card_w, "px_40pt": round(40 * card_w / 1376, 1), "card": card_w,
      "comment_says_43pt": "= 43pt" in mcsrc, "comment_still_40pt": "about 40pt" in mcsrc}
rec("C23_legibility_43pt", "on a 1376-wide cover that is 43pt", "LEGIBLE_PX=10 at a 320px card is 43pt on 1376; 40pt is 9.3px; comment now says 43pt",
    pv, cv, cmp(pv, cv), "constants and comment read from the current make-cover.py", "~/publishing-kit/skills/publishing/scripts/make-cover.py")
pages = pymupdf.open(EX / "graphic-story/PublishingKit_Comic_v1.pdf").page_count
rec("C24_comic_5_pages", "draws a 5-page comic", "5-page comic", 5, pages, cmp(5, pages), "PyMuPDF page count", "graphic-story/PublishingKit_Comic_v1.pdf")


# ---------- C25-C29 check-facts blocks ----------
def block_after(phrase):
    i = line_of(phrase)  # 1-based line of the phrase
    j = next(k for k in range(i, len(LINES)) if LINES[k].startswith("```plaintext"))
    k = next(k for k in range(j + 1, len(LINES)) if LINES[k].startswith("```"))
    return [l for l in LINES[j + 1:k] if l.strip()]


def ev_lines(txt):
    return [l for l in txt.splitlines() if l.strip() and not l.startswith(("#", "$", "A disputed")) and "claim(s) against" not in l]


art_before = block_after("Pass the two audit files as evidence")
ev_before = ev_lines(before)
rec("C25_check_facts_before", "2 traced, 0 cited from the log, 0 untraced, 5 disputed",
    "check-facts on the published article: 7 lines, 2 traced, 5 disputed", {"lines": len(art_before), "summary": art_before[-1]},
    {"lines": len(ev_before), "summary": ev_before[-1], "identical": art_before == ev_before},
    "VERIFIED" if art_before == ev_before else "MISMATCH", "article block compared line by line with the evidence file",
    "evidence/check-facts-before.txt")
art_after = block_after("The same run against the corrected article")
ev_after = ev_lines(after)
missing = [l for l in ev_after if l not in art_after]
rec("C26_check_facts_after", "3 traced, 0 cited from the log, 0 untraced, 0 disputed, 5 disputed with a caveat",
    "check-facts on the corrected article: 3 traced, 0 disputed, 5 with a caveat", {"summary": art_after[-1]},
    {"summary": ev_after[-1], "article_lines_in_evidence": all(l in ev_after for l in art_after),
     "evidence_lines_omitted_from_article": missing},
    "VERIFIED" if all(l in ev_after for l in art_after) else "MISMATCH",
    "every line shown is in the evidence; the article shows 3 of 8 claim lines without marking the cut, so it reads as if only 3 numbers were checked",
    "evidence/check-facts-after.txt")
for ph, i in (("It exits 1.", "a"), ("It exits 0.", "b")):
    rec(f"C27{i}_exit_code", ph, f"check-facts {ph.lower()}", int(ph[-2]), None, "NOT CHECKABLE",
        "the evidence files capture output only, no exit status", "evidence/check-facts-*.txt")
art_pnc = block_after("python3 check_outputs.py --audit")
ev_pnc = [l for l in pnc.splitlines() if l.strip() and not l.startswith(("#", "$", "check-facts:", "audit:"))]
rec("C28_paper_number_check", "0 disputed claim(s) across 2 output(s)", "studio 0/11/5/30, comic 0/9/7/20, 0 disputed across 2",
    art_pnc, ev_pnc, cmp(art_pnc, ev_pnc), "line by line", "evidence/paper-number-check.txt")
rec("C28b_control", "after first proving the copy it found flags a known disputed number", "check_outputs proves its check-facts copy first",
    "control passed", re.search(r"\(control (\w+)\)", pnc).group(0), "VERIFIED" if "(control passed)" in pnc else "MISMATCH",
    "evidence line", "evidence/paper-number-check.txt")

# ---------- C29 ledger and fixes ----------
pk_claims = (PK / "articles/publishing-kit-skill/CLAIMS.md").read_text()
disp = pk_claims.split("## DISPUTED", 1)[1]
drows = [l for l in disp.splitlines() if l.startswith("| ") and not l.startswith(("| Claim", "| ---"))]
shown = block_after("What stays goes under")
rec("C29_ledger_rows", "5 explained in the ledger", "5 disputed numbers explained in the ledger; shown rows are verbatim",
    {"rows": 5, "shown_rows_verbatim": True}, {"rows": len(drows), "shown_rows_verbatim": all(l in drows for l in shown)},
    cmp({"rows": 5, "shown_rows_verbatim": True}, {"rows": len(drows), "shown_rows_verbatim": all(l in drows for l in shown)}),
    "rows under ## DISPUTED in the publishing kit's CLAIMS.md", "~/publishing-kit/articles/publishing-kit-skill/CLAIMS.md")
fixed = (PK / "articles/publishing-kit-skill/devto-publishing-kit.md").read_text()
flat = re.sub(r"\s+", " ", fixed)
fx = {"every paragraph gone": "every paragraph" not in flat, "most paragraphs": "in most paragraphs" in flat,
      "would lose 95px": "would lose 95px" in flat and "1376x578" in flat, "These two numbers": "These two numbers are real" in flat,
      "cover claim gone": "numbers on the cover" not in flat, "date range": "between 2026-08-30 and 2026-09-16" in flat,
      "2026-08-31 gone": "2026-08-31" not in flat, "line wrapping": "keeps its line wrapping" in flat, "95 columns gone": "95 columns" not in flat}
rec("C30_five_fixes_all_three", "all three fixed", "the five Was/Now fixes are in the corrected article; all three overstatements fixed",
    {k: True for k in fx}, fx, "VERIFIED" if all(fx.values()) else "MISMATCH", "string search in the publishing-kit working tree",
    "~/publishing-kit/articles/publishing-kit-skill/devto-publishing-kit.md")
rec("C31_5_to_0", "check-facts went from 5 disputed to 0", "check-facts went from 5 disputed to 0, with 5 explained",
    {"before": 5, "after": 0, "noted": 5},
    {"before": before.count("DISPUTED "), "after": int(re.search(r"(\d+) disputed,", after).group(1)), "noted": after.count("NOTED ")},
    cmp({"before": 5, "after": 0, "noted": 5},
        {"before": before.count("DISPUTED "), "after": int(re.search(r"(\d+) disputed,", after).group(1)), "noted": after.count("NOTED ")}),
    "counted line labels in both evidence files", "evidence/check-facts-before.txt, -after.txt")

# ---------- C32 tip collisions ----------
m5 = mid["M5_substack_source_shape"]["paper_value"]
pv = {"M5_contains_1": True, "M1_value": 95, "D1_verdict": "VERIFIED", "M1_about_columns": True}
cv = {"M5_contains_1": 1 in m5["pre_lines"], "M1_value": mid["M1_own_source_95_columns"]["paper_value"],
      "D1_verdict": mid["D1_proxy_ratio"]["verdict"], "M1_about_columns": "column" in mid["M1_own_source_95_columns"]["id"]}
rec("C32_collisions", "Two of the five disputed claims in Step 8 are number collisions", "2.381:1 matched a 1 in M5 code-block line counts; 95px matched M1",
    pv, cv, cmp(pv, cv), "audit records read directly", "math-sandbox/eq_verified_numbers.json")
style = "".join(re.findall(r"<style[^>]*>(.*?)</style>", (EX / "interactive-paper-studio/index.html").read_text(), re.S))
css = {p: len(re.findall(r"(?<![\d.])" + p, style)) for p in ("1px", "4px")}
rec("C33_css_1px_4px", "so `1px` and `4px` can match", "1px and 4px occur in the studio stylesheet", {"1px": ">0", "4px": ">0"},
    {"counts": css, "evidence": "1px: 6, 4px: 3"}, "VERIFIED" if all(css.values()) else "MISMATCH", "regex inside <style>",
    "interactive-paper-studio/index.html; evidence/studio-css-lengths.txt")

# ---------- C34-C36 scope ----------
dates = sorted(set(re.findall(r"(\d{4}-\d{2}-\d{2})T", before + after + pnc + (EVD / "plugin-install.txt").read_text())))
rec("C34_audit_date", "audited on 2026-11-16", "audited on 2026-11-16", "2026-11-16", dates, cmp(["2026-11-16"], dates),
    "timestamps in the evidence headers", "evidence/*.txt")
readme = (EX / "README.md").read_text()
rec("C35_comic_unfinished", "The comic run stopped before its final page review", "the comic run stopped before its final page review",
    True, "stopped before its final page-by-page review" in readme, "VERIFIED" if "stopped before its final" in readme else "MISMATCH",
    "README states it", "examples/publishing-kit-article/README.md")
runs = sorted(p.parent.name for p in EX.glob("*/RUN_NOTES.md"))
rec("C36_each_skill_once_separate_agent", "Each skill ran once, as a separate agent", "each skill ran once, as a separate agent given only its SKILL.md",
    {"runs_per_skill": 1}, {"run_notes": runs}, "NOT CHECKABLE",
    "one RUN_NOTES.md per skill folder; no session record shows agent separation or run count", "examples/publishing-kit-article/*/RUN_NOTES.md")

# ---------- C37 'every number' wording ----------
nc = sum(r["verdict"] == "NOT CHECKABLE" for r in m)
rec("C37_recompute_every_number", "The research skills recompute every number the article states",
    "the research skills recompute every number the article states", {"recomputed": "every"},
    {"claims": len(m), "not_checkable": nc, "recomputed_to_value": len(m) - nc}, "MISMATCH",
    f"{nc} of {len(m)} math-sandbox records are NOT CHECKABLE, i.e. not recomputed; the same wording recurs at "
    f"lines {line_of('Recomputes each quantitative claim')} and {line_of('26 claims recomputed')}", "math-sandbox/eq_verified_numbers.json",
    overstatement=True)

# ---------- write ----------
counts = dict(collections.Counter(r["verdict"] for r in records))
out = {"paper": str(ART.relative_to(REPO)), "seed": SEED, "verdict_counts": counts, "equations": records}
(HERE / "eq_verified_numbers.json").write_text(json.dumps(out, indent=1) + "\n")
print("records:", len(records), counts)
for r in records:
    if r["verdict"] != "VERIFIED":
        print(f"{r['verdict']:14} {r['id']:40} {r['paper_source']}")
