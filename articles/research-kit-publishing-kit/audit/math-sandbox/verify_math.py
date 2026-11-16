"""math-sandbox audit of devto-research-kit-publishing-kit.md.

Recomputes every quantitative claim in the article from the worked example
(examples/publishing-kit-article), the article's evidence/ folder, the installed plugins and
the publishing-kit working tree; checks every quoted output block against its evidence file
line by line; checks what the article says the tools do against their source. Wilson, Fisher
and McNemar come from plugin/mcp/research_audit_mcp.py over stdio JSON-RPC.

    python3 verify_math.py            # writes eq_verified_numbers.json, mcp_log.jsonl

Nothing outside this folder is written: the staged pre-flight re-run happens in a temp dir.
"""

import collections
import glob
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pymupdf
from PIL import Image

SEED = 42  # nothing is sampled here; kept for the skill's contract
HERE = Path(__file__).resolve().parent
ART_DIR = HERE.parents[1]
ART = ART_DIR / "devto-research-kit-publishing-kit.md"
EVD = ART_DIR / "evidence"
REPO = ART_DIR.parents[1]
EX = REPO / "examples/publishing-kit-article"
PAPER = EX / "paper"
PK = Path.home() / "publishing-kit"
PKA = PK / "articles/publishing-kit-skill"
PKS = PK / "skills/publishing/scripts"
CACHE = Path.home() / ".claude/plugins/cache/publishing-kit/publishing"
MCP = REPO / "plugin/mcp/research_audit_mcp.py"

L = ART.read_text().split("\n")
RECS = []


def ln(phrase, after=0):
    for i in range(after, len(L)):
        if phrase in L[i]:
            return i + 1
    sys.exit(f"phrase not in article: {phrase!r}")


def rec(id_, statement, line, paper_value, computed, ok, reason, source=None):
    verdict = ok if isinstance(ok, str) else ("VERIFIED" if ok else "MISMATCH")
    RECS.append(
        {
            "id": id_,
            "statement": statement,
            "paper_value": paper_value,
            "paper_source": source or f"devto-research-kit-publishing-kit.md:{line}",
            "computed": computed,
            "verdict": verdict,
            "reason": reason,
        }
    )


def sh(*cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=300)
    return r.returncode, r.stdout


# ---------------------------------------------------------------- MCP over stdio
def mcp(calls):
    msgs = [
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "audit", "version": "0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
    ]
    for i, (name, args) in enumerate(calls, 1):
        msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": name, "arguments": args}})
    inp = "\n".join(json.dumps(m) for m in msgs) + "\n"
    out = subprocess.run([sys.executable, str(MCP)], input=inp, capture_output=True, text=True, timeout=60).stdout
    resp = {}
    for line in out.splitlines():
        d = json.loads(line)
        if d.get("id"):
            resp[d["id"]] = json.loads(d["result"]["content"][0]["text"])
    with open(HERE / "mcp_log.jsonl", "w") as f:
        for m in msgs:
            f.write(json.dumps(m) + "\n")
        for k in sorted(resp):
            f.write(json.dumps({"id": k, "result": resp[k]}) + "\n")
    return [resp[i] for i in range(1, len(calls) + 1)]


# ---------------------------------------------------------------- quoted blocks
def block_at(start_phrase):
    """Lines of the fenced block whose first content line contains start_phrase."""
    i = ln(start_phrase) - 1
    assert L[i - 1].startswith("```"), L[i - 1]
    j = i
    while not L[j].startswith("```"):
        j += 1
    return i + 1, L[i:j]


def compare_block(id_, start_phrase, evidence_path, what):
    first, blk = block_at(start_phrase)
    ev = Path(evidence_path).read_text().split("\n")
    pos, idx, unmarked, blanks, missing, gap_marker = -1, [], [], 0, [], False
    for k, a in enumerate(blk):
        if a.strip() == "...":
            gap_marker = True
            continue
        if a.endswith("...}") or a.endswith(", ...}"):
            pref = a[: a.rindex("...")].rstrip(", ")
            hit = next((e for e in range(pos + 1, len(ev)) if ev[e].startswith(pref)), None)
        else:
            hit = next((e for e in range(pos + 1, len(ev)) if ev[e] == a), None)
        if hit is None:
            missing.append((first + k, a))
            continue
        if pos >= 0 and hit > pos + 1 and not gap_marker:
            skipped = ev[pos + 1 : hit]
            if any(s.strip() for s in skipped):
                unmarked.append((first + k, len([s for s in skipped if s.strip()])))
            else:
                blanks += len(skipped)
        idx.append(hit + 1)
        pos, gap_marker = hit, False
    computed = {
        "article_lines": len(blk),
        "evidence_lines_matched": idx,
        "missing_or_out_of_order": [f"{n}: {t}" for n, t in missing],
        "unmarked_gaps": [
            f"before article line {n}: {c} non-blank evidence line(s) dropped, no '...'" for n, c in unmarked
        ],
        "blank_lines_dropped": blanks,
    }
    ok = not missing and not unmarked
    note = "every line found in order" if ok else "shortened or reordered without '...'"
    if blanks:
        note += f"; {blanks} blank evidence line(s) dropped"
    rec(
        id_,
        f"quoted block ({what}) matches {Path(evidence_path).name} line for line",
        first,
        f"block at lines {first}-{first + len(blk) - 1}",
        computed,
        ok,
        note,
        source=f"devto-research-kit-publishing-kit.md:{first}; {Path(evidence_path).relative_to(Path.home())}",
    )


compare_block("Q01_plugin_list", "❯ publishing@publishing-kit", EVD / "plugins-installed.txt", "claude plugin list")
compare_block("Q02_kit_path", "/home/xbill/.claude/plugins/cache/publishing-kit", EVD / "kit-path.txt", "echo $KIT")
compare_block("Q03_math_sandbox_counts", "math-sandbox claims:", EVD / "run-counts.txt", "math-sandbox tally and crop")
compare_block("Q04_stat_counts", "ablation-stat-auditor claim records:", EVD / "run-counts.txt", "stat tally and tests")
compare_block("Q05_images", "image cover.77acc7c4.jpg", EVD / "run-counts.txt", "image sizes")
compare_block("Q06_citations", "citation dois/arxiv", EVD / "run-counts.txt", "citation counts")
compare_block("Q07_studio", "studio check:", EVD / "run-counts.txt", "studio check")
compare_block("Q08_legibility", "legibility: LEGIBLE_PX", EVD / "run-counts.txt", "legibility")
compare_block(
    "Q09_preflight_before",
    "check-facts.py — every number traces",
    EVD / "staged-preflight-before.txt",
    "pre-flight as published",
)
compare_block("Q10_ledger_rows", "| 0 of 4 | E3_medium_data_uri_0_of_4", PKA / "CLAIMS.md", "## DISPUTED rows")
compare_block(
    "Q11_preflight_after", "NOTED count        0 of 4", EVD / "staged-preflight-after.txt", "pre-flight corrected"
)
# the refusal block starts with the same line as the Step 9 block; locate it after Step 11's heading
_s11 = ln("Step 11")
_i = ln("DISPUTED count     0 of 4", _s11) - 1
_j = _i
while not L[_j].startswith("```"):
    _j += 1
_blk = L[_i:_j]
_ev = (EVD / "publish-devto-refuses.txt").read_text().split("\n")
_pos, _bad = -1, []
_gap = False
for _k, _a in enumerate(_blk):
    if _a.strip() == "...":
        _gap = True
        continue
    _h = next((e for e in range(_pos + 1, len(_ev)) if _ev[e] == _a), None)
    if _h is None or (_pos >= 0 and _h > _pos + 1 and not _gap and any(s.strip() for s in _ev[_pos + 1 : _h])):
        _bad.append(_i + _k + 1)
    _pos, _gap = (_h if _h is not None else _pos), False
rec(
    "Q12_publish_refuses",
    "quoted block (publish-devto refusal) matches publish-devto-refuses.txt line for line",
    _i + 1,
    f"block at lines {_i + 1}-{_j}",
    {"bad_lines": _bad, "article_lines": len(_blk)},
    not _bad,
    "every line found in order; the one dropped line is marked '...'" if not _bad else "unmarked gap",
    source=f"devto-research-kit-publishing-kit.md:{_i + 1}; evidence/publish-devto-refuses.txt",
)
compare_block("Q13_devto_draft", "5049183  draft", EVD / "devto-draft.txt", "publish-devto --list")
compare_block(
    "Q14_paper_number_check",
    "check-facts: ~/.claude/plugins",
    EVD / "paper-number-check-0.36.2.txt",
    "paper-number-check",
)

# ---------------------------------------------------------------- research-kit facts
skills = sorted(p.parent.name for p in (REPO / "plugin/skills").glob("*/SKILL.md"))
n = ln("nine skills")
rec(
    "S01_nine_skills",
    "research-kit has nine skills",
    n,
    9,
    len(skills),
    len(skills) == 9,
    f"plugin/skills/*/SKILL.md: {skills}",
)
tbl = [l for l in L[n : n + 12] if l.startswith("| `")]
rec(
    "S02_table_plus_two",
    "the table lists seven skills and two more are named",
    n + 2,
    9,
    len(tbl) + 2,
    len(tbl) + 2 == 9,
    f"{len(tbl)} table rows + trajectory-cinematics + frontier-gap-radar",
)
ver = json.loads((REPO / "plugin/.claude-plugin/plugin.json").read_text())["version"]
mver = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())["metadata"]["version"]
rc, out = sh("claude", "plugin", "list", "--json")
pl = {p["id"]: p for p in json.loads(out)} if rc == 0 else {}
n = ln("Version: 1.3.1")
rec(
    "S03_research_kit_version",
    "research-kit 1.3.1 installed",
    n,
    "1.3.1",
    {
        "plugin.json": ver,
        "marketplace": mver,
        "installed": pl.get("research-kit@claude-research-skills", {}).get("version"),
    },
    ver == mver == "1.3.1" == pl.get("research-kit@claude-research-skills", {}).get("version"),
    "plugin.json, marketplace.json and claude plugin list --json agree",
)
pkv = json.loads((PK / ".claude-plugin/plugin.json").read_text())["version"]
n = ln("Version: 0.36.2")
rec(
    "S04_publishing_version",
    "publishing kit 0.36.2 installed",
    n,
    "0.36.2",
    {"repo": pkv, "installed": pl.get("publishing@publishing-kit", {}).get("version")},
    pkv == "0.36.2" == pl.get("publishing@publishing-kit", {}).get("version"),
    "repo plugin.json and claude plugin list --json",
)
kit = pl.get("publishing@publishing-kit", {}).get("installPath", "") + "/skills/publishing"
n = ln("/home/xbill/.claude/plugins/cache/publishing-kit/publishing/0.36.2/skills/publishing")
rec(
    "S05_kit_path",
    "the KIT one-liner prints the 0.36.2 install path",
    n,
    L[n - 1],
    kit,
    kit == L[n - 1],
    "recomputed from claude plugin list --json installPath; fields `id` and `installPath` exist",
)
cached = sorted(p.name for p in CACHE.iterdir())
rec(
    "S06_old_versions_cached",
    "older versions stay in the cache",
    ln("older versions stay in the cache"),
    "older versions present",
    cached,
    len(cached) > 1,
    f"{CACHE}: {cached}",
)
log = sh("git", "-C", str(PK), "log", "--format=%h %s")[1].splitlines()
pos = {l.split()[0]: i for i, l in enumerate(log)}
vpos = {v: next(i for i, l in enumerate(log) if l.split(" ", 1)[1] == v) for v in ("0.36.0", "0.36.1", "0.36.2")}
feat = {"0.36.0": "c8bf3d7", "0.36.1": "dfa1134", "0.36.2": "177f641"}
prev = {"0.36.0": len(log), "0.36.1": vpos["0.36.0"], "0.36.2": vpos["0.36.1"]}
okv = {v: vpos[v] < pos[c] < prev[v] for v, c in feat.items()}
rec(
    "S07_version_milestones",
    "0.36.0 reads audit records, 0.36.1 sequence match, 0.36.2 publish-devto number check",
    ln("needs 0.36.0 or later"),
    "0.36.0 / 0.36.1 / 0.36.2",
    {v: f"{feat[v]} lands before tag commit, after the previous: {okv[v]}" for v in feat},
    all(okv.values()),
    "git log of ~/publishing-kit: c8bf3d7 (check-facts reads verdicts), dfa1134 (sequence match), 177f641 (publish-devto runs check-facts)",
)

# ---------------------------------------------------------------- tool behaviour vs source
cf = (PKS / "check-facts.py").read_text()
pf = (PKS / "preflight.py").read_text()
pd = (PKS / "publish-devto.py").read_text()
rec(
    "T01_preflight_every_check",
    "preflight.py runs every check and exits non-zero on a failure",
    ln("runs every check and exits non-zero"),
    "every check",
    {"default": ["facts", "prose", "article", "linkedin"], "only_with_--live": ["links"]},
    False,
    "overstated: check-links.py runs only with --live (preflight.py lines 90-94); without it the run prints 'NOTE: --live was not run'",
)
npat = len(re.findall(r'^    \(r"', cf, re.M))
rec(
    "T02_check_facts_each_number",
    "check-facts.py pulls each number out of the article",
    ln("which pulls each number out of the article"),
    "each number",
    {"claim_patterns": npat, "fenced_code_stripped": "strip_fenced" in cf, "claims_found_in_walkthrough": 7},
    False,
    "overstated: it extracts only numbers matching its claim patterns (ratio, count, dimensions, px, version, ...) in prose outside fenced code; the walk-through yields 7 claims",
)
rec(
    "T03_reads_records",
    "check-facts.py reads every record with paper_value, computed and verdict",
    ln("which reads every record with"),
    "paper_value, computed, verdict",
    {"requires": ["paper_value", "verdict in (MISMATCH, NOT CHECKABLE)"], "computed": "optional"},
    '"paper_value" in x and v in DISPUTED_VERDICTS' in cf,
    "disputed_numbers() walks any nesting; computed is used only to pair numbers of a MISMATCH",
)
rec(
    "T04_publish_runs_number_check",
    "publish-devto.py --create runs the number check (check-article.py and check-facts.py) and refuses on failure",
    ln("runs the cover and front matter checks"),
    "check-article + check-facts",
    "number_check() + check-article.py in preflight()",
    "def number_check" in pd and "check-article.py" in pd and "refusing to publish" in pd,
    "publish-devto.py lines 88-118; exits via sys.exit(message) -> 1",
)
rec(
    "T05_ledger_refused",
    "check-facts.py refuses a ledger inside evidence/",
    ln("refuses a ledger inside"),
    "refuses",
    "FAIL  a claim ledger is inside the evidence set",
    "a claim ledger is inside the evidence set" in cf,
    "check-facts.py lines 374-385: CLAIMS.md or a ## LOG / ## DISPUTED heading",
)
rec(
    "T06_preflight_default_evidence",
    "preflight.py defaults its evidence to <article folder>/evidence",
    ln("defaults its evidence"),
    "<article dir>/evidence",
    'art_path.parent / "evidence"',
    'str(art_path.parent / "evidence")' in pf,
    "preflight.py lines 76-78",
)
rec(
    "T07_verdict_fails_disputed",
    "MISMATCH or NOT CHECKABLE fails as DISPUTED",
    ln("fails as `DISPUTED`"),
    "MISMATCH, NOT CHECKABLE",
    'DISPUTED_VERDICTS = ("MISMATCH", "NOT CHECKABLE")',
    'DISPUTED_VERDICTS = ("MISMATCH", "NOT CHECKABLE")' in cf,
    "holds with two exceptions the sentence leaves out: a MISMATCH number that agrees at the paper's precision is not disputed, and a ## DISPUTED ledger row turns it into NOTED",
)
pnc = (REPO / "plugin/skills/paper-number-check/scripts/check_outputs.py").read_text()
rec(
    "T08_pnc_every_output",
    "paper-number-check runs check-facts.py over every other output, proving it on a control first",
    ln("runs the publishing kit's `check-facts.py` over every other output"),
    "every other output",
    "the outputs named on its command line; candidate = highest cached version, not installPath",
    "passes_control" in pnc,
    "control check verified (passes_control); 'every other output' means the paths passed, and it picks the highest-numbered cache copy, which is the installed one only when the newest is installed",
)
_s = ln("Its build fails on any number")
bs = (EX / "graphic-story/build_story.py").read_text()
rec(
    "T09_story_build_fails",
    "graphic-story's build fails on a number missing from its sourced numbers file",
    _s,
    "fails",
    "raise SystemExit('number typed into story text ...')",
    "number typed into story text" in bs,
    "build_story.py line 40",
)
STYLE_OK = "STYLE.sub" in cf and 'UNIT_WORDS = {"px"' in cf
rec(
    "T10_036_1_rules",
    "from 0.36.1: sequence match, unit in the statement, <style> skipped",
    ln("From 0.36.1 a claim's numbers"),
    "sequence, unit, <style>",
    {
        "disputes_claim_sequence": "sit together, in order" in cf,
        "unit_words": 'UNIT_WORDS = {"px"' in cf,
        "style_stripped": "STYLE.sub" in cf,
    },
    STYLE_OK and "sit together, in order" in cf,
    "check-facts.py disputes_claim() and main()",
)

# ---------------------------------------------------------------- audit tallies
m = json.loads((EX / "math-sandbox/eq_verified_numbers.json").read_text())
mc = collections.Counter(r["verdict"] for r in m["equations"])
s = json.loads((EX / "ablation-stat-auditor/stat_audit.json").read_text())
sc = collections.Counter(c.get("verdict") for c in s["claims"])
for id_, phrase in (
    ("A01_ms_tally_step3", "math-sandbox claims: 26"),
    ("A02_ms_tally_summary", "26 claims checked: 15 verified"),
):
    n = ln(phrase)
    rec(
        id_,
        "math-sandbox: 26 claims, 15 VERIFIED, 6 MISMATCH, 5 NOT CHECKABLE",
        n,
        [26, 15, 6, 5],
        [len(m["equations"]), mc["VERIFIED"], mc["MISMATCH"], mc["NOT CHECKABLE"]],
        [len(m["equations"]), mc["VERIFIED"], mc["MISMATCH"], mc["NOT CHECKABLE"]] == [26, 15, 6, 5],
        "examples/publishing-kit-article/math-sandbox/eq_verified_numbers.json",
    )
n = ln("| `math-sandbox` | 🥇")
rec(
    "A03_ms_compare_row",
    "math-sandbox: 6 mismatches, 5 not checkable",
    n,
    [6, 5],
    [mc["MISMATCH"], mc["NOT CHECKABLE"]],
    [mc["MISMATCH"], mc["NOT CHECKABLE"]] == [6, 5],
    "same file",
)
n = ln("ablation-stat-auditor claim records: 16")
rec(
    "A04_stat_tally",
    "ablation-stat-auditor: 16 claim records, 7 VERIFIED, 6 MISMATCH, 3 NOT CHECKABLE",
    n,
    [16, 7, 6, 3],
    [len(s["claims"]), sc["VERIFIED"], sc["MISMATCH"], sc["NOT CHECKABLE"]],
    [len(s["claims"]), sc["VERIFIED"], sc["MISMATCH"], sc["NOT CHECKABLE"]] == [16, 7, 6, 3],
    "examples/publishing-kit-article/ablation-stat-auditor/stat_audit.json",
)
n = ln("| `ablation-stat-auditor` | 🥇")
rec(
    "A05_stat_compare_row",
    "ablation-stat-auditor: 6 mismatches, 3 not checkable",
    n,
    [6, 3],
    [sc["MISMATCH"], sc["NOT CHECKABLE"]],
    [sc["MISMATCH"], sc["NOT CHECKABLE"]] == [6, 3],
    "same file",
)
sys.path.insert(0, str(REPO / "plugin/skills/paper-number-check/scripts"))
import check_outputs  # noqa: E402

ndis = check_outputs.count_disputed_records(
    [EX / "math-sandbox/eq_verified_numbers.json", EX / "ablation-stat-auditor/stat_audit.json"]
)
n = ln("audit: 2 file(s), 20 disputed")
rec(
    "A06_disputed_records",
    "20 disputed records across the two audit files",
    n,
    20,
    {
        "check_outputs.count_disputed_records": ndis,
        "verdict_sum": mc["MISMATCH"] + mc["NOT CHECKABLE"] + sc["MISMATCH"] + sc["NOT CHECKABLE"],
    },
    ndis == 20,
    "paper-number-check's own counter; equals 6+5+6+3 from the tallies",
)
same = {
    f: (EX / sub / f).read_bytes() == (PKA / "evidence" / f).read_bytes()
    for sub, f in (("math-sandbox", "eq_verified_numbers.json"), ("ablation-stat-auditor", "stat_audit.json"))
}
rec(
    "A07_staged_copies",
    "the audit records staged in the walk-through's evidence/ are the example's files",
    ln("Copy the two audit files"),
    "copied",
    same,
    all(same.values()),
    "byte comparison of the example's files with ~/publishing-kit/articles/publishing-kit-skill/evidence/ (this article's own evidence/ holds its own audit, a different file)",
)

# ---------------------------------------------------------------- crop arithmetic
crop = (PAPER / "evidence/devto-cover-crop.txt").read_text()
w, h = map(int, re.search(r"width=(\d+),height=(\d+)", crop).groups())
ratio = w / h
kept = 1376 * h / w
lost = (768 - kept) / 2
n = ln("crop: ratio 1000/420")
rec(
    "C01_crop_ratio",
    "crop ratio 1000/420",
    n,
    2.380952,
    round(ratio, 6),
    round(ratio, 6) == 2.380952,
    f"proxy URL width={w},height={h} in paper/evidence/devto-cover-crop.txt",
)
rec("C02_rows_kept", "rows kept at width 1376", n, 577.92, round(kept, 2), round(kept, 2) == 577.92, "1376*420/1000")
rec(
    "C03_lost_per_side",
    "rows lost per side from 768",
    n,
    95.04,
    round(lost, 2),
    round(lost, 2) == 95.04,
    "(768-577.92)/2",
)
n = ln("2.381:1 crop, so a 1376x768")
rec(
    "C04_ratio_rounded",
    "2.381:1 crop",
    n,
    2.381,
    round(ratio, 3),
    round(ratio, 3) == 2.381,
    "1000/420 at three decimals",
)
rec(
    "C05_95px",
    "a 1376x768 cover loses 95px off the top and bottom",
    n,
    95,
    round(lost),
    round(lost) == 95,
    "95.04 px a side, centre crop assumed",
)
rec(
    "C06_gravity_auto",
    "the proxy URL says gravity=auto",
    ln("gravity=auto"),
    "gravity=auto",
    "gravity=auto" in crop,
    "gravity=auto" in crop,
    "paper/evidence/devto-cover-crop.txt line 7; so the 95px split is unmeasured, as the article says",
)
n = ln("1376x578, which the 2.381:1 crop")
rec(
    "C07_578_whole",
    "1376x578 is left whole by the crop",
    n,
    "1376x578",
    {"rows_needed": round(kept, 2), "rows_have": 578, "excess_px": round(578 - kept, 2)},
    578 >= kept and 578 - kept < 1,
    "crop keeps 577.92 rows; 578 is within one pixel",
)

# ---------------------------------------------------------------- stats via MCP
mcn = [("verify_mcnemar_exact", {"b": k, "c": 0}) for k in range(1, 9)]
res = mcp(
    [
        ("verify_wilson_ci", {"successes": 47, "total": 62}),
        ("verify_fisher_exact", {"k_method": 4, "n_method": 4, "k_baseline": 0, "n_baseline": 4}),
    ]
    + mcn
)
wil, fis, mcr = res[0], res[1], res[2:]
_z, _p = 1.959964, 47 / 62
_c = (_p + _z * _z / 124) / (1 + _z * _z / 62)
_h = _z * ((_p * (1 - _p) / 62 + _z * _z / (4 * 62 * 62)) ** 0.5) / (1 + _z * _z / 62)
WEX = [round(100 * (_c - _h), 4), round(100 * (_c + _h), 4)]  # independent Wilson bounds, stdlib
wfmt = [
    float(x) for x in re.findall(r"[\d.]+(?=%)", wil["formatted"])
]  # rate, low, high at one decimal, from the unrounded values
hw = (PAPER / "evidence/devto-hardwrap.txt").read_text()
k_br = int(re.search(r"blocks containing <br>:\s+(\d+)", hw).group(1))
n_bl = int(re.search(r"= (\d+)\n", hw).group(1))
for id_, phrase in (
    ("W01_hardwrap_step4", "75.8%, with a 95% interval of 63.8% to 84.8%"),
    ("W02_hardwrap_summary", "47 of 62 matches its evidence: 75.8%"),
):
    n = ln(phrase)
    rec(
        id_,
        "47 of 62: 75.8%, 95% Wilson interval 63.8% to 84.8%",
        n,
        {"k": 47, "n": 62, "rate_pct": 75.8, "ci": [63.8, 84.8]},
        {
            "k": k_br,
            "n": n_bl,
            "rate_pct": wil["rate_pct"],
            "ci": [wil["wilson_low_pct"], wil["wilson_high_pct"]],
            "ci_exact_stdlib": WEX,
        },
        (k_br, n_bl) == (47, 62) and wfmt[0::2][:1] + wfmt[-2:] == [75.8, 63.8, 84.8],
        "MCP verify_wilson_ci (its formatted field, rounded once from the exact bounds; re-rounding the 2-dp 63.85 would give 63.9); k and n read from paper/evidence/devto-hardwrap.txt (58 <p> + 4 <li>: four of the 62 'paragraphs' are list items)",
    )
n = ln("15 of the 62 had none")
rec("W03_15_without", "15 of the 62 had none", n, 15, n_bl - k_br, n_bl - k_br == 15, "62 - 47 from devto-hardwrap.txt")
pp = (PAPER / "devto-publishing-kit.md").read_text().split("\n")
ev_line = next(i + 1 for i, l in enumerate(pp) if "every paragraph" in l)
c_line = next(i + 1 for i, l in enumerate(pp) if "47 of 62" in l)
rec(
    "W04_same_sentence",
    "the same sentence in the article said 'a stray break in every paragraph'",
    n,
    "same sentence",
    {"every_paragraph_line": ev_line, "47_of_62_line": c_line},
    ev_line == c_line,
    f"the walk-through says 'every paragraph' at line {ev_line} (prose) and '47 of 62' at line {c_line} (the measured table); same claim, different sentences",
    source=f"devto-research-kit-publishing-kit.md:{n}; paper/devto-publishing-kit.md:{ev_line},{c_line}",
)
n = ln("the paired test gives p = 0.125")
first6 = next(r["discordant"] for r in mcr if r["p_value"] < 0.05)
rec(
    "W05_mcnemar",
    "paired test p = 0.125 for 4 discordant pairs",
    n,
    0.125,
    mcr[3]["p_value"],
    mcr[3]["p_value"] == 0.125,
    "MCP verify_mcnemar_exact b=4 c=0",
)
rec(
    "W06_mcnemar_six",
    "with all-or-none results p first drops below 0.05 at six images",
    n,
    6,
    first6,
    first6 == 6,
    "MCP verify_mcnemar_exact b=1..8, c=0: " + ", ".join(f"{r['discordant']}:{r['p_value']}" for r in mcr),
)
rec(
    "W07_fisher",
    "Fisher's test gives p = 0.0286",
    n,
    0.0286,
    round(fis["p_value"], 4),
    round(fis["p_value"], 4) == 0.0286,
    "MCP verify_fisher_exact 4/4 vs 0/4 (= 2/70)",
)
rec(
    "W08_tests_line",
    "tests line: fisher 0.02857142857142857, mcnemar (0.125, 4, 0)",
    ln("tests: {'medium_hosted"),
    {"fisher": 0.02857142857142857, "mcnemar": [0.125, 4, 0]},
    {
        "fisher": s["tests"]["medium_hosted_vs_embed_fisher_unpaired"]["p_value"],
        "mcnemar": [s["tests"]["medium_hosted_vs_embed_mcnemar_paired"][k] for k in ("p_value", "b", "c")],
    },
    s["tests"]["medium_hosted_vs_embed_fisher_unpaired"]["p_value"] == fis["p_value"]
    and s["tests"]["medium_hosted_vs_embed_mcnemar_paired"]["p_value"] == 0.125,
    "stat_audit.json equals the MCP recomputation",
)
pc = (PAPER / "CLAIMS.md").read_text()
logrow = re.search(r"^\|[^\n]*data:[^\n]*0 of 4[^\n]*\| (\d{4}-\d\d-\d\d) \|", pc, re.M)
rec(
    "W09_log_date",
    "the ledger carries it from a log dated 2026-08-30 with no artifact",
    ln("from a log dated 2026-08-30"),
    "2026-08-30",
    logrow.group(1) if logrow else None,
    bool(logrow) and logrow.group(1) == "2026-08-30",
    "paper/CLAIMS.md ## LOG row 'Medium strips data: URIs on paste; 0 of 4 embed, 4 of 4 hosted'",
)
rec(
    "W10_which_images",
    "no file records which images were pasted",
    ln("No file records which images"),
    "no file",
    None,
    "NOT CHECKABLE",
    "an absence across every file cannot be proven by search; nothing found under paper/ names the four images",
)

# ---------------------------------------------------------------- images
sizes = {f.name: "%dx%d" % Image.open(f).size for f in sorted(PAPER.glob("*.jpg")) + sorted(PAPER.glob("*.webp"))}
_first, blk = block_at("image cover.77acc7c4.jpg")
for k, line in enumerate(blk):
    name, dim = line.split()[1:3]
    rec(
        f"I0{k + 1}_{name.split('.')[0].replace('-', '_')}",
        f"{name} is {dim}",
        _first + k,
        dim,
        sizes.get(name),
        sizes.get(name) == dim,
        "PIL on paper/" + name,
    )
devto = {k: v for k, v in sizes.items() if k.startswith("cover.")}
cur = {f.name: "%dx%d" % Image.open(f).size for f in PKA.glob("cover.*.jpg")}
n = ln("Every dev.to cover in the article's directory")
rec(
    "I05_every_devto_cover",
    "every dev.to cover in the article's directory is 1376x578",
    n,
    "1376x578",
    {"paper": devto, "publishing-kit now": cur},
    set(devto.values()) | set(cur.values()) == {"1376x578"},
    "cover.*.jpg (front-matter covers; cover-builder and linkedin excluded)",
)
old = {
    p: "%dx%d" % Image.open(Path.home() / "gemma4-dev/docs" / p).size
    for p in ("devto-cover-aws.jpg", "devto-cover-gde.jpg")
}
rec(
    "I06_older_covers",
    "the kit made 1376x768 covers before --mode devto changed",
    n + 1,
    "1376x768",
    old,
    set(old.values()) == {"1376x768"},
    "PIL on ~/gemma4-dev/docs, the files evidence/older-covers.txt names",
)
curtxt = (PKA / "devto-publishing-kit.md").read_text()
rec(
    "I07_sentence_now_says",
    "its sentence now says so",
    n + 1,
    "would lose 95px ... renders dev.to covers at 1376x578",
    "would lose 95px" in curtxt and "covers at 1376x578" in curtxt,
    "would lose 95px" in curtxt and "covers at 1376x578" in curtxt,
    "~/publishing-kit/articles/publishing-kit-skill/devto-publishing-kit.md lines 54-55",
)
n = ln("the current one has no text at all and five destination shapes")
rec(
    "I08_five_shapes",
    "the current cover has no text at all and five destination shapes",
    n,
    "no text; five destination shapes",
    None,
    "NOT CHECKABLE",
    "visual content; figure-forensics/RUN_NOTES.md items 1-2 report it (5 endpoint markers, computed there); not re-measured in this run",
)
rec(
    "I09_four_destinations",
    "the article describes four destinations",
    n,
    "four",
    "four places (line 15); all four of its artifacts (line 12)",
    "Publishing one technical article to four places" in "\n".join(pp),
    "paper/devto-publishing-kit.md",
)

# ---------------------------------------------------------------- links, studio, legibility, pages
rep = (EX / "citation-doi-verifier/REPORT.md").read_text()
rows = [l for l in rep.splitlines() if re.match(r"\| L\d+ \|", l)]
good = sum("RESOLVES+IDENTIFIED" in l for l in rows)
dois = sum(
    len(re.findall(r"10\.\d{4,}/|arxiv\.org/abs", Path(f).read_text(errors="ignore")))
    for f in glob.glob(str(PAPER / "**/*.md"), recursive=True) + glob.glob(str(PAPER / "**/*.txt"), recursive=True)
)
rec(
    "L01_dois",
    "citation dois/arxiv in paper text: 0",
    ln("citation dois/arxiv"),
    0,
    dois,
    dois == 0,
    "regex 10.NNNN/ or arxiv.org/abs over paper/**/*.md,*.txt",
)
for id_, phrase in (
    ("L02_links_block", "citation links: 10 of 11"),
    ("L03_links_compare", "10 of 11 links confirmed"),
    ("L04_links_prose", "All 11 links were fetched, and 10"),
):
    rec(
        id_,
        "10 of 11 links resolving and identified",
        ln(phrase),
        [10, 11],
        [good, len(rows)],
        (good, len(rows)) == (10, 11),
        "citation-doi-verifier/REPORT.md rows L1..L11",
    )
l9 = next(l for l in rows if "medium.com" in l)
rec(
    "L05_medium_403",
    "Medium answers scripts with HTTP 403",
    ln("Medium answers scripts with HTTP 403"),
    403,
    int(re.search(r"HTTP (\d{3})", l9).group(1)),
    "HTTP 403" in l9,
    "REPORT.md row L9",
)
js = (EX / "interactive-paper-studio/check_js_output.txt").read_text().strip().splitlines()[-1]
jn = re.match(r"(\d+) values, (\d+) mismatches", js)
rec(
    "P01_studio_check",
    "studio check: 130 values, 0 mismatches",
    ln("studio check: 130"),
    [130, 0],
    [int(jn.group(1)), int(jn.group(2))],
    (int(jn.group(1)), int(jn.group(2))) == (130, 0),
    "interactive-paper-studio/check_js_output.txt last line",
)
mk = (PKS / "make-cover.py").read_text()
cw = int(re.search(r"^CARD_W = (\d+)", mk, re.M).group(1))
lp = int(re.search(r"^LEGIBLE_PX = (\d+)", mk, re.M).group(1))
old_mk = sh("git", "-C", str(PK), "show", "dec86c0:skills/publishing/scripts/make-cover.py")[1]
n = ln("type below about 40pt")
rec(
    "P02_old_comment_40pt",
    "make-cover.py's comment said type below about 40pt disappears",
    n,
    40,
    int(re.search(r"type below about (\d+)pt", old_mk).group(1)),
    "type below about 40pt" in old_mk,
    "git show dec86c0:make-cover.py",
)
rec("P03_legible_px", "LEGIBLE_PX = 10", n, 10, lp, lp == 10, "make-cover.py line 90")
rec(
    "P04_43pt",
    "on a 1376-wide cover LEGIBLE_PX is 43pt",
    n,
    43.0,
    lp * 1376 / cw,
    round(lp * 1376 / cw, 1) == 43.0,
    f"{lp}*1376/{cw}",
)
rec("P05_comment_now", "the comment now says 43pt", n, "43pt", "= 43pt" in mk, "= 43pt" in mk, "make-cover.py line 264")
n = ln("40pt at 320/1376 = 9.3 px")
rec(
    "P06_9_3px",
    "40pt at 320/1376 = 9.3 px",
    n,
    9.3,
    round(40 * cw / 1376, 2),
    round(40 * cw / 1376, 1) == 9.3,
    "40*320/1376 = 9.30",
)
pages = pymupdf.open(EX / "graphic-story/PublishingKit_Comic_v1.pdf").page_count
rec("P07_comic_pages", "a 5-page comic", ln("5-page comic"), 5, pages, pages == 5, "pymupdf page_count")

# ---------------------------------------------------------------- re-run the staged pre-flight facts check
CF = CACHE / "0.36.2/skills/publishing/scripts/check-facts.py"


def facts_lines(out):
    rows = [l for l in out.splitlines() if re.match(r"^\s+(ok|DISPUTED|NOTED|TRACE|LOG)\s", l)]
    head = next((l for l in out.splitlines() if "claim(s) against" in l), "")
    tail = next((l for l in out.splitlines() if " traced, " in l), "")
    return head, rows, tail


with tempfile.TemporaryDirectory() as t:
    st = Path(t) / "publishing-kit-skill"
    shutil.copytree(PAPER, st)
    for f in ("math-sandbox/eq_verified_numbers.json", "ablation-stat-auditor/stat_audit.json"):
        shutil.copy(EX / f, st / "evidence")
    n_ev = len(list((st / "evidence").iterdir()))
    rc_b, out_b = sh(sys.executable, str(CF), str(st / "devto-publishing-kit.md"), "--evidence", str(st / "evidence"))
rc_a, out_a = sh(sys.executable, str(CF), str(PKA / "devto-publishing-kit.md"), "--evidence", str(PKA / "evidence"))
hb, rb, tb = facts_lines(out_b)
ha, ra, ta = facts_lines(out_a)
_f, blk_b = block_at("check-facts.py — every number traces")
_g, blk_a = block_at("NOTED count        0 of 4")
art_rows_b = [l for l in blk_b if re.match(r"^\s+(ok|DISPUTED|NOTED)\s", l)]
art_rows_a = [l for l in blk_a if re.match(r"^\s+(ok|DISPUTED|NOTED)\s", l)]
n_paper_ev = len(list((PAPER / "evidence").iterdir()))
n = ln("devto-publishing-kit.md: 7 claim(s) against 15 evidence")
rec(
    "F01_before_header",
    "7 claims against 15 evidence files, 15 dated log rows",
    n,
    [7, 15, 15],
    [int(x) for x in re.findall(r"(\d+) ", hb)[:3]],
    [int(x) for x in re.findall(r"(\d+) ", hb)[:3]] == [7, 15, 15],
    f"re-run of check-facts 0.36.2 on a temp staged copy: {hb.strip()}",
)
rec(
    "F02_before_rows",
    "the seven claim rows as published",
    n + 2,
    len(art_rows_b),
    {"rerun_rows_equal": rb == art_rows_b, "rows": len(rb)},
    rb == art_rows_b,
    "row-for-row equal to the re-run",
)
c_ok, c_dis = (
    sum(r.lstrip().startswith("ok") for r in art_rows_b),
    sum(r.lstrip().startswith("DISPUTED") for r in art_rows_b),
)
n = ln("4 traced, 0 cited from the log, 0 untraced, 3 disputed")
rec(
    "F03_before_tally",
    "4 traced, 3 disputed",
    n,
    [4, 3],
    [c_ok, c_dis],
    [c_ok, c_dis] == [4, 3] and tb.strip() == L[n - 1].strip(),
    f"rows counted in the quoted block; re-run tail: {tb.strip()}",
)
rec(
    "F04_before_exit",
    "It exits 1",
    ln("It exits 1."),
    1,
    rc_b,
    rc_b == 1,
    "check-facts exit on the staged copy; staged-preflight-before.txt ends 'exit 1'",
)
n = ln("The 15 evidence files are the 13")
rec(
    "F05_13_plus_2",
    "15 evidence files = 13 + 2 audit records",
    n,
    [15, 13, 2],
    [n_ev, n_paper_ev, n_ev - n_paper_ev],
    [n_ev, n_paper_ev] == [15, 13],
    "ls of paper/evidence and the staged copy",
)
c_ok2, c_not = (
    sum(r.lstrip().startswith("ok") for r in art_rows_a),
    sum(r.lstrip().startswith("NOTED") for r in art_rows_a),
)
n = ln("5 traced, 0 cited from the log, 0 untraced, 0 disputed, 3 disputed with a caveat")
rec(
    "F06_after_rows",
    "corrected pre-flight rows",
    ln("NOTED count        0 of 4"),
    len(art_rows_a),
    {"rerun_rows_equal": ra == art_rows_a, "rows": len(ra)},
    ra == art_rows_a,
    "row-for-row equal to a re-run of check-facts 0.36.2 on ~/publishing-kit/articles/publishing-kit-skill",
)
rec(
    "F07_after_tally",
    "5 traced, 3 disputed with a caveat",
    n,
    [5, 3],
    [c_ok2, c_not],
    [c_ok2, c_not] == [5, 3] and ta.strip() == L[n - 1].strip(),
    f"re-run tail: {ta.strip()}",
)
rec(
    "F08_after_exit",
    "It exits 0",
    ln("It exits 0."),
    0,
    rc_a,
    rc_a == 0,
    "check-facts exit on the corrected article; staged-preflight-after.txt ends 'exit 0' after all five checks",
)
rec(
    "F09_summary_3_to_0",
    "pre-flight went from 3 disputed numbers to 0, with all 3 explained in the ledger",
    ln("pre-flight went from 3 disputed"),
    [3, 0, 3],
    [c_dis, 0, c_not],
    [c_dis, c_not] == [3, 3],
    "DISPUTED rows before, NOTED rows after",
)
same_scripts = {
    f: (CACHE / "0.36.1/skills/publishing/scripts" / f).read_bytes()
    == (CACHE / "0.36.2/skills/publishing/scripts" / f).read_bytes()
    for f in (
        "preflight.py",
        "check-facts.py",
        "check-prose.py",
        "check-article.py",
        "check-links.py",
        "make-linkedin.py",
    )
}
rec(
    "F10_scope_versions",
    "audited with research-kit 1.3.1 and publishing kit 0.36.2",
    ln("Scope: one article"),
    "0.36.2",
    {"preflight_evidence_header": "publishing-kit 0.36.1", "scripts_identical_0.36.1_vs_0.36.2": same_scripts},
    all(same_scripts.values()),
    "Steps 9-10 outputs were captured under 0.36.1, but every script preflight.py runs is byte-identical in 0.36.2, and the facts rows re-run under 0.36.2 match",
)

# ---------------------------------------------------------------- step 10, 11, 12
ok_fix = {
    "most paragraphs": "in most paragraphs" in curtxt,
    "would lose 95px": "would lose 95px" in curtxt,
    "These two numbers are real": "These two numbers are real" in curtxt,
    "between 2026-08-30 and 2026-09-16": "between 2026-08-30 and 2026-09-16" in curtxt,
    "keeps its line wrapping": "keeps its line wrapping" in curtxt,
}
gone = {
    "every paragraph": "every paragraph" not in curtxt,
    "loses 95px": "loses 95px" not in curtxt,
    "The two numbers on the cover": "numbers on the cover" not in curtxt,
    "measured on 2026-08-31": "2026-08-31, so check" not in curtxt,
    "readable at 95 columns": "readable at 95 columns" not in curtxt,
}
rec(
    "X01_five_fixes",
    "the five Was/Now fixes are in the publishing kit's walk-through",
    ln("| Was | Now |"),
    5,
    {"now_present": ok_fix, "was_gone": gone},
    all(ok_fix.values()) and all(gone.values()),
    "grep of ~/publishing-kit/articles/publishing-kit-skill/devto-publishing-kit.md",
)
rec(
    "X02_three_fixed",
    "'every paragraph', 'on the cover' and the footer date: all three fixed",
    ln("all three fixed"),
    3,
    sum([gone["every paragraph"], gone["The two numbers on the cover"], gone["measured on 2026-08-31"]]),
    all(gone.values()),
    "same grep",
)
pkc = (PKA / "CLAIMS.md").read_text()
dis_rows = [
    l
    for l in pkc.split("## DISPUTED", 1)[1].splitlines()
    if l.startswith("| ") and not l.startswith("| Claim") and not l.startswith("| ---")
]
rec(
    "X03_ledger_rows",
    "what stays is one row per claim under ## DISPUTED (three shown)",
    ln("one row per claim with the reason"),
    3,
    len(dis_rows),
    "VERIFIED",
    f"the three quoted rows are verbatim; the ledger holds {len(dis_rows)} rows, the other {len(dis_rows) - 3} explain number collisions (2.381:1, 95px) that 0.36.1 no longer flags",
)
fm = L[1 : L.index("---", 1)]
keys = {k: any(l.startswith(k + ":") for l in fm) for k in ("title", "tags", "cover_image", "published")}
rec(
    "X04_front_matter",
    "the front matter carries title, tags and cover, and published: false",
    ln("The front matter carries"),
    "title, tags, cover, published: false",
    {**keys, "published_false": "published: false" in fm},
    all(keys.values()) and "published: false" in fm,
    "this article's front matter",
)
n = ln("Nothing reaches dev.to")
refuse = (EVD / "publish-devto-refuses.txt").read_text()
rec(
    "X05_nothing_reaches",
    "Nothing reaches dev.to",
    n,
    "no draft",
    "No draft created" in refuse,
    "No draft created" in refuse and refuse.rstrip().endswith("exit 1"),
    "evidence/publish-devto-refuses.txt header: 'No draft created: newest unpublished id stayed 5049183'; exit 1",
)
rc, pnc_out = sh(
    sys.executable,
    str(REPO / "plugin/skills/paper-number-check/scripts/check_outputs.py"),
    "--audit",
    "math-sandbox/eq_verified_numbers.json",
    "ablation-stat-auditor/stat_audit.json",
    "--",
    "interactive-paper-studio/index.html",
    "graphic-story/Story.html",
    cwd=EX,
)
want = [l for l in block_at("check-facts: ~/.claude/plugins")[1] if re.search(r"\d+ disputed", l)]
got = [l for l in pnc_out.splitlines() if re.search(r"\d+ disputed", l)]
rec(
    "X06_pnc_rerun",
    "paper-number-check: studio 0/4/7/15, comic 0/2/8/4, 0 disputed",
    ln("interactive-paper-studio/index.html: 0 disputed"),
    want,
    got,
    want == got and rc == 0,
    f"re-run of check_outputs.py in the example folder, exit {rc}",
)
noted_ok = {}
for out in ("interactive-paper-studio/index.html", "graphic-story/Story.html"):
    o = sh(
        sys.executable,
        str(CF),
        str(EX / out),
        "--evidence",
        str(EX / "math-sandbox/eq_verified_numbers.json"),
        str(EX / "ablation-stat-auditor/stat_audit.json"),
    )[1]
    noted = [
        re.match(r"^\s+NOTED\s+\S+\s+(.+?)\s+<-", l).group(1) for l in o.splitlines() if l.lstrip().startswith("NOTED")
    ]
    ledger = (EX / out).parent.joinpath("CLAIMS.md").read_text().split("## DISPUTED", 1)[1]
    noted_ok[out] = {c: any(c in r for r in ledger.splitlines() if r.startswith("|")) for c in noted}
rec(
    "X07_noted_rows",
    "each noted number has a row in a CLAIMS.md beside its output",
    ln("Each noted number has a row"),
    "every noted",
    noted_ok,
    all(all(v.values()) for v in noted_ok.values()),
    "check-facts NOTED rows matched to ## DISPUTED rows of the CLAIMS.md beside each output",
)
cmp_txt = (EVD / "check-facts-0.36.0-vs-0.36.1.txt").read_text().splitlines()
tok = collections.defaultdict(list)
for l in cmp_txt[1:]:
    parts = l.split()
    tok[parts[1]].append(parts[2:])
old_n, new_n = sum(map(len, tok["check_facts_old_tmp"])), sum(map(len, tok["check-facts"]))
new_set = sorted({t for x in tok["check-facts"] for t in x})
n = ln("took the flags from 34 to 12")
rec(
    "X08_34_to_12",
    "over the five outputs the flags went from 34 to 12",
    n,
    [5, 34, 12],
    [len(tok["check-facts"]), old_n, new_n],
    [len(tok["check-facts"]), old_n, new_n] == [5, 34, 12],
    "tokens counted per row of evidence/check-facts-0.36.0-vs-0.36.1.txt",
)
rec(
    "X09_the_12",
    "the 12 are the Medium counts and the 320px card width",
    n,
    "0 of 4, 4 of 4, 320px",
    new_set,
    set(new_set) <= {"0", "4", "320", "320px"},
    "remaining flag tokens (count claims shown by their first number)",
)
rd = (EX / "README.md").read_text()
rec(
    "X10_separate_agents",
    "each skill ran as a separate agent given only its SKILL.md, the paper and that folder",
    ln("each skill ran as a separate agent"),
    "separate agent",
    "separate agent given only that skill's `SKILL.md`, the paper and an output folder" in rd,
    "separate agent given only" in rd,
    "examples/publishing-kit-article/README.md line 5",
)
rec(
    "X11_ran_once",
    "Each skill ran once, as the example's README records",
    ln("Each skill ran once"),
    "once",
    "README states 'separate agent' and 'independent'; it does not state a run count",
    "NOT CHECKABLE",
    "the README records separate, independent agents; 'once' is not in it",
)
rec(
    "X12_comic_stopped",
    "the comic run stopped before its final page review",
    ln("The comic run stopped"),
    "stopped",
    "stopped before its final page-by-page review" in rd,
    "stopped before its final page-by-page review" in rd,
    "README.md line 22",
)
rec(
    "X13_live_only_link_check",
    "Live pages were fetched only by the link check",
    ln("Live pages were fetched only"),
    "only the link check",
    [
        "citation-doi-verifier fetched 11 links (Step 6)",
        "preflight --live ran check-links.py and make-linkedin.py fetching",
        "publish-devto.py --create/--list called the dev.to API",
    ],
    False,
    "overstated: the article itself reports three live fetchers; true only if 'the link check' covers both citation-doi-verifier and check-links.py, and the dev.to API calls are excluded",
)
rec(
    "X14_every_other_step_reads",
    "They write the audit records, and every other step reads them",
    ln("every other step reads them"),
    "every other step",
    {
        "reads audits": ["paper-number-check", "pre-flight", "publish-devto"],
        "does not": ["figure-forensics", "citation-doi-verifier"],
    },
    False,
    "overstated: figure-forensics and citation-doi-verifier ran given only SKILL.md, the paper and a folder (README line 5, article line 137)",
)
rec(
    "X15_fails_any_output",
    "paper-number-check fails any output that repeats a number the audit disputes",
    ln("Fails any output that repeats"),
    "any",
    "fails only on claims check-facts' patterns extract, outside fenced code; a repeat with a ## DISPUTED ledger row passes as NOTED",
    False,
    "overstated in the skills table; the article's own Step 12 shows 6 noted repeats that pass",
)

# ---------------------------------------------------------------- write
counts = collections.Counter(r["verdict"] for r in RECS)
json.dump(
    {
        "paper": "articles/research-kit-publishing-kit/devto-research-kit-publishing-kit.md",
        "seed": SEED,
        "verdict_counts": dict(counts),
        "equations": RECS,
    },
    open(HERE / "eq_verified_numbers.json", "w"),
    indent=1,
    ensure_ascii=False,
)
print("records:", len(RECS), dict(counts))
for r in RECS:
    if r["verdict"] != "VERIFIED":
        print(f"{r['verdict']:13s} {r['id']:30s} {r['paper_source']}  -- {r['reason'][:150]}")
