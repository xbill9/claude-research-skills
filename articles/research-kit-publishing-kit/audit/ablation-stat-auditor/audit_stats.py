# ruff: noqa: E501, UP031
"""ablation-stat-auditor run on articles/research-kit-publishing-kit/devto-research-kit-publishing-kit.md.

Every number is computed here: tests and intervals through the research-audit MCP server over stdio
JSON-RPC, counts from the files the article cites. Each record names the article line, and the script
stops if the quoted text is missing from that line. Writes stat_audit.json beside this script.

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


def at(line: int, text: str) -> str:
    if text not in LINES[line - 1]:
        raise SystemExit(f"{text!r} is not on article line {line}")
    return f"devto-research-kit-publishing-kit.md:{line}"


class Mcp:
    def __init__(self):
        self.p = subprocess.Popen([sys.executable, str(MCP)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.i = 0
        self.log = []
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "audit"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.p.stdin.flush()

    def _rpc(self, method, params):
        self.i += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.i, "method": method, "params": params}) + "\n")
        self.p.stdin.flush()
        return json.loads(self.p.stdout.readline())

    def call(self, name, **args):
        out = json.loads(self._rpc("tools/call", {"name": name, "arguments": args})["result"]["content"][0]["text"])
        self.log.append({"tool": name, "arguments": args, "result": out})
        return out

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def wilson(k, n, z=1.959963984540054):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * p, 100 * (c - h), 100 * (c + h)


claims = []


def rec(id, line, text, paper_value, computed, verdict, reason, conclusion, kind):
    claims.append(
        {
            "id": id,
            "statement": text,
            "paper_value": paper_value,
            "paper_source": at(line, text),
            "computed": computed,
            "verdict": verdict,
            "reason": reason,
            "conclusion": conclusion,
            "kind": kind,
        }
    )


def ok(cond):
    return "VERIFIED" if cond else "MISMATCH"


mcp = Mcp()

# ------------------------------------------------------------ audit record counts (census of files)
ms = json.loads((EX / "math-sandbox/eq_verified_numbers.json").read_text())["equations"]
ms_c = collections.Counter(r["verdict"] for r in ms)
st = json.loads((EX / "ablation-stat-auditor/stat_audit.json").read_text())["claims"]
st_c = collections.Counter(r["verdict"] for r in st)
ms_v = {
    "total": len(ms),
    "VERIFIED": ms_c["VERIFIED"],
    "MISMATCH": ms_c["MISMATCH"],
    "NOT CHECKABLE": ms_c["NOT CHECKABLE"],
}
st_v = {
    "total": len(st),
    "VERIFIED": st_c["VERIFIED"],
    "MISMATCH": st_c["MISMATCH"],
    "NOT CHECKABLE": st_c["NOT CHECKABLE"],
}
p_ms = {"total": 26, "VERIFIED": 15, "MISMATCH": 6, "NOT CHECKABLE": 5}
p_st = {"total": 16, "VERIFIED": 7, "MISMATCH": 6, "NOT CHECKABLE": 3}
src_ms = "examples/publishing-kit-article/math-sandbox/eq_verified_numbers.json"
src_st = "examples/publishing-kit-article/ablation-stat-auditor/stat_audit.json"
for _i, (ln, t) in enumerate(
    [
        (146, "math-sandbox claims: 26 {'VERIFIED': 15, 'NOT CHECKABLE': 5, 'MISMATCH': 6}"),
        (397, "26 claims checked: 15 verified, 6 mismatches, 5 not checkable"),
    ]
):
    rec(f"ms-counts-{ln}", ln, t, p_ms, ms_v, ok(ms_v == p_ms), f"full count of records in {src_ms}", "HOLDS", "census")
rec(
    "ms-counts-378",
    378,
    "6 mismatches, 5 not checkable",
    {"MISMATCH": 6, "NOT CHECKABLE": 5},
    {"MISMATCH": ms_v["MISMATCH"], "NOT CHECKABLE": ms_v["NOT CHECKABLE"]},
    ok((ms_v["MISMATCH"], ms_v["NOT CHECKABLE"]) == (6, 5)),
    f"full count of records in {src_ms}",
    "HOLDS",
    "census",
)
rec(
    "st-counts-161",
    161,
    "ablation-stat-auditor claim records: 16 {'VERIFIED': 7, 'MISMATCH': 6, 'NOT CHECKABLE': 3}",
    p_st,
    st_v,
    ok(st_v == p_st),
    f"full count of records in {src_st}",
    "HOLDS",
    "census",
)
rec(
    "st-counts-379",
    379,
    "6 mismatches, 3 not checkable",
    {"MISMATCH": 6, "NOT CHECKABLE": 3},
    {"MISMATCH": st_v["MISMATCH"], "NOT CHECKABLE": st_v["NOT CHECKABLE"]},
    ok((st_v["MISMATCH"], st_v["NOT CHECKABLE"]) == (6, 3)),
    f"full count of records in {src_st}",
    "HOLDS",
    "census",
)
disputed_records = ms_v["MISMATCH"] + ms_v["NOT CHECKABLE"] + st_v["MISMATCH"] + st_v["NOT CHECKABLE"]
rec(
    "disputed-records-20",
    351,
    "audit: 2 file(s), 20 disputed record(s)",
    {"disputed_records": 20},
    {"disputed_records": disputed_records},
    ok(disputed_records == 20),
    "MISMATCH + NOT CHECKABLE summed over the two audit files",
    "HOLDS",
    "census",
)

# ------------------------------------------------------------ 47 of 62 (the one sampled rate)
hw = (EX / "paper/evidence/devto-hardwrap.txt").read_text()
n = int(re.search(r"=\s*(\d+)\s*$", re.search(r"paragraph-level blocks.*", hw).group(0)).group(1))
k = int(re.search(r"blocks containing <br>:\s*(\d+)", hw).group(1))
w_mcp = mcp.call("verify_wilson_ci", successes=k, total=n)
rate, lo, hi = wilson(k, n)
assert abs(round(lo, 2) - w_mcp["wilson_low_pct"]) < 0.006 and abs(round(hi, 2) - w_mcp["wilson_high_pct"]) < 0.006
comp = {"k": k, "n": n, "rate_pct": round(rate, 3), "ci": [round(lo, 3), round(hi, 3)]}
good = (k, n, round(rate, 1), round(lo, 1), round(hi, 1)) == (47, 62, 75.8, 63.8, 84.8)
why = (
    "devto-hardwrap.txt: 62 blocks (58 <p> + 4 <li>), 47 with <br>; Wilson at full precision, MCP agrees to 2 dp. "
    "The 62 are every block of one article (a full count); the interval describes dev.to's behaviour only if "
    "these blocks are read as a sample of the paragraphs it renders."
)
paper = {"k": 47, "n": 62, "rate_pct": 75.8, "ci": [63.8, 84.8]}
rec(
    "hardwrap-47-62-165",
    165,
    "75.8%, with a 95% interval of 63.8% to 84.8%",
    paper,
    comp,
    ok(good),
    why,
    "HOLDS",
    "sample",
)
rec(
    "hardwrap-47-62-398",
    398,
    "47 of 62 matches its evidence: 75.8%, 95% interval 63.8% to 84.8%",
    paper,
    comp,
    ok(good),
    why,
    "HOLDS",
    "sample",
)
rec(
    "hardwrap-none-15",
    165,
    "15 of the 62 had none",
    {"k": 15, "n": 62},
    {"k": n - k, "n": n},
    ok(n - k == 15),
    "62 - 47 from devto-hardwrap.txt",
    "HOLDS",
    "census",
)

# ------------------------------------------------------------ Medium 0 of 4 vs 4 of 4
mc = mcp.call("verify_mcnemar_exact", b=4, c=0)
fi = mcp.call("verify_fisher_exact", k_method=4, n_method=4, k_baseline=0, n_baseline=4)
first = None
sweep = {}
for m in range(1, 11):
    sweep[m] = mcp.call("verify_mcnemar_exact", b=m, c=0)["p_value"]
    if first is None and sweep[m] < 0.05:
        first = m
rec(
    "medium-mcnemar-0.125",
    167,
    "If the same four images went into both, the paired test gives p = 0.125",
    {"p": 0.125, "b": 4, "c": 0},
    {"p": mc["p_value"], "b": 4, "c": 0},
    ok(round(mc["p_value"], 3) == 0.125),
    "exact McNemar with all four discordant one way; conditional on a pairing no file records",
    "WITHIN NOISE",
    "sample",
)
rec(
    "medium-first-below-05",
    167,
    "first drops below 0.05 at six images",
    {"images": 6},
    {"images": first, "p_at_5": sweep[5], "p_at_6": sweep[6]},
    ok(first == 6),
    "exact McNemar b = m, c = 0 for m = 1..10",
    "HOLDS",
    "sample",
)
rec(
    "medium-fisher-0.0286",
    167,
    "Fisher's test gives p = 0.0286",
    {"p": 0.0286},
    {"p": fi["p_value"]},
    ok(round(fi["p_value"], 4) == 0.0286),
    "two-sided Fisher on [[4,0],[0,4]] (hosted 4/4 vs embed 0/4)",
    "HOLDS",
    "sample",
)
ev_txt = {f.name: f.read_text(errors="ignore") for f in (EX / "paper/evidence").iterdir()}
medium_files = sorted(nm for nm, t in ev_txt.items() if re.search(r"data:|0 of 4|4 of 4", t) and "edium" in t)
rec(
    "medium-no-file",
    167,
    "No file records which images were pasted.",
    {"files_recording_images": 0},
    {"files_recording_images": len(medium_files), "matched": medium_files},
    ok(not medium_files),
    "paper/evidence searched for a Medium file mentioning data: URIs or the 0 of 4 / 4 of 4 counts",
    "HOLDS",
    "census",
)
log_row = next(
    (i + 1, ln) for i, ln in enumerate((EX / "paper/CLAIMS.md").read_text().split("\n")) if "0 of 4 embed" in ln
)
rec(
    "medium-log-date",
    167,
    "the ledger carries it from a log dated 2026-08-30 with no artifact",
    {"date": "2026-08-30"},
    {"date": re.search(r"\d{4}-\d\d-\d\d", log_row[1]).group(0), "row": f"paper/CLAIMS.md:{log_row[0]}"},
    ok("2026-08-30" in log_row[1]),
    "row sits under '## LOG — carried from the kit's log, dated, not re-measured'",
    "HOLDS",
    "census",
)
rec(
    "medium-one-paste-suffices",
    167,
    "The claim describes fixed editor behaviour, so one archived paste would support it",
    {"pastes_needed": 1},
    None,
    "NOT CHECKABLE",
    "a premise about the editor being deterministic; no test applies, and no archived paste exists to try it",
    "CANNOT CHECK",
    "premise",
)

# ------------------------------------------------------------ links
rep = (EX / "citation-doi-verifier/REPORT.md").read_text()
rows = [ln for ln in rep.splitlines() if re.match(r"\| L\d+ \|", ln)]
ident = sum("RESOLVES+IDENTIFIED" in ln for ln in rows)
blocked = [ln.split("|")[1].strip() for ln in rows if "403" in ln]
lk = {"identified": ident, "links": len(rows)}
for ln, t in [(194, "citation links: 10 of 11 resolving and identified"), (382, "10 of 11 links confirmed")]:
    rec(
        f"links-{ln}",
        ln,
        t,
        {"identified": 10, "links": 11},
        lk,
        ok(lk == {"identified": 10, "links": 11}),
        "rows L1..L11 of citation-doi-verifier/REPORT.md",
        "HOLDS",
        "census",
    )
rec(
    "links-197",
    197,
    "All 11 links were fetched, and 10 were matched to a second source",
    {"fetched": 11, "matched": 10},
    {"fetched": len(rows), "matched": ident, "http_403": blocked},
    ok((len(rows), ident) == (11, 10)),
    "every row has a web status; the unmatched one is the Medium copy, HTTP 403",
    "HOLDS",
    "census",
)
paper_txt = [f for f in (EX / "paper").rglob("*") if f.suffix in (".md", ".txt")]
dois = sum(len(re.findall(r"10\.\d{4,}/|arxiv\.org/abs", f.read_text(errors="ignore"))) for f in paper_txt)
rec(
    "dois-0",
    193,
    "citation dois/arxiv in paper text: 0",
    {"count": 0},
    {"count": dois},
    ok(dois == 0),
    "regex over paper/**/*.md and *.txt",
    "HOLDS",
    "census",
)

# ------------------------------------------------------------ studio check, comic pages, images, skills
sc = (EX / "interactive-paper-studio/check_js_output.txt").read_text().strip().splitlines()[-1]
sv = re.match(r"(\d+) values, (\d+) mismatches", sc)
rec(
    "studio-130",
    206,
    "studio check: 130 values, 0 mismatches",
    {"values": 130, "mismatches": 0},
    {"values": int(sv.group(1)), "mismatches": int(sv.group(2))},
    ok(sv.groups() == ("130", "0")),
    "last line of interactive-paper-studio/check_js_output.txt; a full comparison, no sampling",
    "HOLDS",
    "census",
)
pages = pymupdf.open(EX / "graphic-story/PublishingKit_Comic_v1.pdf").page_count
rec(
    "comic-pages-5",
    215,
    "draws a 5-page comic",
    {"pages": 5},
    {"pages": pages},
    ok(pages == 5),
    "page count of graphic-story/PublishingKit_Comic_v1.pdf",
    "HOLDS",
    "census",
)
skills = sorted(d.name for d in (REPO / "plugin/skills").iterdir() if (d / "SKILL.md").exists())
rec(
    "skills-9",
    21,
    "nine skills",
    {"skills": 9},
    {"skills": len(skills)},
    ok(len(skills) == 9),
    "directories with a SKILL.md under plugin/skills",
    "HOLDS",
    "census",
)
devto = {
    f.name: "%dx%d" % Image.open(f).size
    for f in sorted((EX / "paper").iterdir())
    if f.name.startswith(("cover.", "advocu-")) and f.suffix in (".jpg", ".webp")
}
rec(
    "covers-1376x578",
    182,
    "Every dev.to cover in the article's directory is 1376x578",
    {"size": "1376x578"},
    devto,
    ok(set(devto.values()) == {"1376x578"}),
    "cover.*.jpg and the advocu copy of the dev.to cover, measured with PIL; builder and linkedin covers excluded",
    "HOLDS",
    "census",
)


# ------------------------------------------------------------ pre-flight before / after, exit codes
def tally(path):
    t = (EV / path).read_text()
    marks = collections.Counter(m for m in re.findall(r"^  (DISPUTED|NOTED|ok)\s+\S+\s+.*<-", t, re.M))
    nfiles = int(re.search(r"against (\d+) evidence file", t).group(1)) if "evidence file" in t else None
    logrows = int(re.search(r"(\d+) dated log row", t).group(1)) if "dated log row" in t else None
    code = int(re.search(r"^exit (\d+)", t, re.M).group(1))
    return {
        "disputed": marks["DISPUTED"],
        "noted": marks["NOTED"],
        "traced": marks["ok"],
        "evidence_files": nfiles,
        "log_rows": logrows,
        "exit": code,
    }


before, after, refuse = (
    tally("staged-preflight-before.txt"),
    tally("staged-preflight-after.txt"),
    tally("publish-devto-refuses.txt"),
)
rec(
    "preflight-before",
    252,
    "4 traced, 0 cited from the log, 0 untraced, 3 disputed",
    {"traced": 4, "disputed": 3},
    {"traced": before["traced"], "disputed": before["disputed"]},
    ok((before["traced"], before["disputed"]) == (4, 3)),
    "status lines counted in evidence/staged-preflight-before.txt",
    "HOLDS",
    "census",
)
rec(
    "exit-1",
    258,
    "It exits 1.",
    {"exit": 1},
    {"exit": before["exit"]},
    ok(before["exit"] == 1),
    "'exit 1' recorded in staged-preflight-before.txt",
    "HOLDS",
    "census",
)
rec(
    "preflight-after",
    296,
    "5 traced, 0 cited from the log, 0 untraced, 0 disputed, 3 disputed with a caveat",
    {"traced": 5, "disputed": 0, "noted": 3},
    {"traced": after["traced"], "disputed": after["disputed"], "noted": after["noted"]},
    ok((after["traced"], after["disputed"], after["noted"]) == (5, 0, 3)),
    "status lines counted in evidence/staged-preflight-after.txt",
    "HOLDS",
    "census",
)
rec(
    "exit-0",
    306,
    "It exits 0.",
    {"exit": 0},
    {"exit": after["exit"]},
    ok(after["exit"] == 0),
    "'exit 0' recorded in staged-preflight-after.txt",
    "HOLDS",
    "census",
)
rec(
    "summary-3-to-0",
    401,
    "pre-flight went from 3 disputed numbers to 0, with all 3 explained in the ledger",
    {"before": 3, "after": 0, "noted": 3},
    {"before": before["disputed"], "after": after["disputed"], "noted": after["noted"]},
    ok((before["disputed"], after["disputed"], after["noted"]) == (3, 0, 3)),
    "before is a copy of the article as published, after is the corrected article with three ledger rows; both runs on kit 0.36.1",
    "HOLDS",
    "census",
)
rec(
    "publish-refuses",
    318,
    "4 traced, 0 cited from the log, 0 untraced, 3 disputed",
    {"disputed": 3},
    {"disputed": refuse["disputed"], "exit": refuse["exit"]},
    ok(refuse["disputed"] == 3 and refuse["exit"] == 1),
    "evidence/publish-devto-refuses.txt (kit 0.36.2), exit 1, no draft created",
    "HOLDS",
    "census",
)
had = sorted(f.name for f in (EX / "paper/evidence").iterdir())
stated = int(re.search(r"before staging: (\d+)", (EV / "walkthrough-evidence-count.txt").read_text()).group(1))
rec(
    "evidence-15",
    258,
    "The 15 evidence files are the 13 the article already had plus the two audit records",
    {"total": 15, "had": 13, "added": 2},
    {"total_in_preflight": before["evidence_files"], "had_in_paper_copy": len(had), "had_recorded": stated, "added": 2},
    ok(before["evidence_files"] == 15 and len(had) == stated == 13),
    "paper/evidence listed now (13), walkthrough-evidence-count.txt (13), preflight header (15)",
    "HOLDS",
    "census",
)
log_lines = (EX / "paper/CLAIMS.md").read_text().split("\n")
s0 = next(i for i, ln in enumerate(log_lines) if ln.startswith("## LOG"))
s1 = next(i for i in range(s0 + 1, len(log_lines)) if log_lines[i].startswith("## "))
dated = [ln for ln in log_lines[s0:s1] if ln.startswith("| ") and re.search(r"\| [^|]*\d{4}-\d\d-\d\d[^|]*\|\s*$", ln)]
rec(
    "log-rows-15",
    242,
    "7 claim(s) against 15 evidence file(s), 15 dated log row(s)",
    {"claims": 7, "evidence_files": 15, "log_rows": 15},
    {
        "claims_listed": before["traced"] + before["disputed"],
        "evidence_files": before["evidence_files"],
        "log_rows_preflight": before["log_rows"],
        "log_rows_with_a_date_in_paper_CLAIMS": len(dated),
    },
    ok(before["traced"] + before["disputed"] == 7 and before["evidence_files"] == 15 and len(dated) == 15),
    "dated rows counted in the ## LOG section of paper/CLAIMS.md (date column holds a YYYY-MM-DD)",
    "HOLDS",
    "census",
)

# ------------------------------------------------------------ 34 -> 12 flags, 0.36.0 vs 0.36.1
fl = {}
for ln in (EV / "check-facts-0.36.0-vs-0.36.1.txt").read_text().splitlines():
    if ln.startswith("#") or not ln.strip():
        continue
    parts = ln.split()
    fl[(parts[0], parts[1])] = parts[2:]
old = sum(len(v) for (o, s), v in fl.items() if s == "check_facts_old_tmp")
new_toks = [t for (o, s), v in fl.items() if s == "check-facts" for t in v]
outputs = sorted({o for o, s in fl})
kinds = collections.Counter(
    "medium count" if t in ("0", "4") else "card width" if t.startswith("320") else "other" for t in new_toks
)
rec(
    "flags-34-12",
    364,
    "Over the five outputs in this run that took the flags from 34 to 12",
    {"outputs": 5, "before": 34, "after": 12},
    {"outputs": len(outputs), "before": old, "after": len(new_toks)},
    ok((len(outputs), old, len(new_toks)) == (5, 34, 12)),
    "flag tokens counted per output and version in evidence/check-facts-0.36.0-vs-0.36.1.txt; a full count, empty ledger",
    "HOLDS",
    "census",
)
rec(
    "flags-12-kinds",
    364,
    "the 12 are the Medium counts and the 320px card width",
    {"other": 0},
    dict(kinds),
    ok(kinds["other"] == 0),
    "0 and 4 are the Medium counts by the file's own key; 320 and 320px are the card width",
    "HOLDS",
    "census",
)


# ------------------------------------------------------------ paper-number-check (0.36.0 file vs 0.36.2 file)
def pnc(path):
    t = (EV / path).read_text()
    return {
        m.group(1): dict(zip(("disputed", "noted", "traced", "untraced"), map(int, m.groups()[1:]), strict=True))
        for m in re.finditer(r"^(\S+): (\d+) disputed, (\d+) noted, (\d+) traced, (\d+) untraced", t, re.M)
    }


p36, p362 = pnc("paper-number-check.txt"), pnc("paper-number-check-0.36.2.txt")
studio, comic = "interactive-paper-studio/index.html", "graphic-story/Story.html"
FLAG_NAME = {studio: "studio-index.html", comic: "comic-Story.html"}
want = {
    studio: {"disputed": 0, "noted": 4, "traced": 7, "untraced": 15},
    comic: {"disputed": 0, "noted": 2, "traced": 8, "untraced": 4},
}
for out, ln, txt in [
    (studio, 352, "0 disputed, 4 noted, 7 traced, 15 untraced"),
    (comic, 353, "0 disputed, 2 noted, 8 traced, 4 untraced"),
]:
    rec(
        f"pnc-{out.split('/')[0]}",
        ln,
        txt,
        want[out],
        {
            **p362[out],
            "noted_with_0.36.0": p36[out]["noted"],
            "flags_0.36.0": len(fl[(FLAG_NAME[out], "check_facts_old_tmp")]),
        },
        ok(p362[out] == want[out]),
        "evidence/paper-number-check-0.36.2.txt; the 0.36.0 run noted 11 (studio) and 9 (comic), equal to the 0.36.0 flag counts",
        "HOLDS",
        "census",
    )
rows_beside = {}
for d in ("interactive-paper-studio", "graphic-story"):
    t = (EX / d / "CLAIMS.md").read_text().split("\n")
    a = next(i for i, ln in enumerate(t) if ln.startswith("## DISPUTED"))
    b = next((i for i in range(a + 1, len(t)) if t[i].startswith("## ")), len(t))
    rows_beside[d] = sorted(ln.split("|")[1].strip() for ln in t[a:b] if "NOT CHECKABLE" in ln or "MISMATCH" in ln)
need = {"interactive-paper-studio": ["0 of 4", "4 of 4", "320", "320px"], "graphic-story": ["0 of 4", "4 of 4"]}
cover_ok = all(
    any(r.replace(" ", "") == n.replace(" ", "") or (n == "320" and r.startswith("320")) for r in rows_beside[d])
    for d in need
    for n in need[d]
)
rec(
    "noted-rows-beside",
    358,
    "Each noted number has a row in a `CLAIMS.md` beside its output.",
    {"noted": {"interactive-paper-studio": 4, "graphic-story": 2}},
    {"disputed_rows": rows_beside, "noted_tokens_from_0.36.1_flags": need},
    ok(cover_ok),
    "noted numbers taken from the 0.36.1 flags for each output; bare '320' is covered by the '320 px' row only if check-facts treats them as one claim, which its NOTED status implies",
    "HOLDS",
    "census",
)

# ------------------------------------------------------------ process claims
readme = (EX / "README.md").read_text()
rec(
    "ran-separately",
    137,
    "each skill ran as a separate agent given only its `SKILL.md`, the paper and that folder",
    {"agents_per_skill": 1},
    {
        "readme": "each skill was run on 2026-11-16 by a separate agent given only that skill's `SKILL.md`, the paper and an output folder"
        in readme
    },
    ok("by a separate agent given only that skill's `SKILL.md`, the paper and an output folder" in readme),
    "examples/publishing-kit-article/README.md:5",
    "HOLDS",
    "process",
)
rec(
    "ran-once",
    403,
    "Each skill ran once, as a separate agent, as the example's README records.",
    {"runs_per_skill": 1},
    {"readme_mentions_once": bool(re.search(r"\bonce\b", readme))},
    "NOT CHECKABLE",
    "the README records one separate agent per skill but no run count; nothing in the repo shows a skill was not rerun",
    "CANNOT CHECK",
    "process",
)
rec(
    "comic-stopped",
    403,
    "The comic run stopped before its final page review.",
    {"stopped": True},
    {"readme": "the run was stopped before its final page-by-page review" in readme},
    ok("the run was stopped before its final page-by-page review" in readme),
    "examples/publishing-kit-article/README.md:22",
    "HOLDS",
    "process",
)

mcp.close()
tally_v = dict(collections.Counter(c["verdict"] for c in claims))
out = {
    "paper": "articles/research-kit-publishing-kit/devto-research-kit-publishing-kit.md",
    "verdict_counts": tally_v,
    "claims": claims,
    "tests": {
        "hardwrap_wilson": {"k": k, "n": n, "full_precision": comp, "mcp": w_mcp},
        "medium_mcnemar_paired": mc,
        "medium_fisher_unpaired": fi,
        "mcnemar_all_or_none_sweep": sweep,
    },
    "raw_mcp_calls": mcp.log,
}
(HERE / "stat_audit.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
print("records:", len(claims), tally_v)
for c in claims:
    if c["verdict"] != "VERIFIED":
        print(c["verdict"], c["paper_source"], repr(c["statement"]), "->", c["computed"], "|", c["reason"])
print("wilson 47/62:", comp, "mcp:", w_mcp["formatted"])
print(
    "mcnemar b=4 c=0:",
    mc["p_value"],
    "fisher:",
    fi["p_value"],
    "first m with p<0.05:",
    first,
    "p5/p6:",
    sweep[5],
    sweep[6],
)
print("flags:", old, "->", len(new_toks), dict(kinds), "| pnc 0.36.0:", p36, "| 0.36.2:", p362)
print(
    "before:", before, "after:", after, "refuse:", refuse, "| evidence had:", len(had), "| dated log rows:", len(dated)
)
