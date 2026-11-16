#!/usr/bin/env python3
"""Statistical audit of devto-publishing-kit.md (the paper of record) and its archived evidence.

Every k and n is read out of the paper or an evidence file by regex here, so a changed source
changes the audit. Exact tests go through the research-audit MCP server over stdio; plain
arithmetic (sums, ratios, unit conversions, date gaps) is done in this script.
Writes stat_audit.json next to this file; console output is saved as audit_stats_output.txt.
"""

import ast
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
PAPER_DIR = OUT.parent / "paper"
EV = PAPER_DIR / "evidence"
ARTICLE = PAPER_DIR / "devto-publishing-kit.md"
CLAIMS = PAPER_DIR / "CLAIMS.md"
MCP = OUT.parents[2] / "plugin" / "mcp" / "research_audit_mcp.py"

_calls = []


def mcp_batch(calls):
    """One server process; one JSON-RPC tools/call line per (tool, args)."""
    lines = [
        json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": t, "arguments": a}})
        for i, (t, a) in enumerate(calls)
    ]
    proc = subprocess.run(
        [sys.executable, "-I", str(MCP)],
        input="\n".join(lines) + "\n",
        capture_output=True,
        text=True,
        check=True,
        cwd="/tmp",
    )
    res = {}
    for line in proc.stdout.splitlines():
        d = json.loads(line)
        r = d["result"]
        if r.get("isError"):
            raise RuntimeError(r)
        res[d["id"]] = json.loads(r["content"][0]["text"])
    out = [res[i] for i in range(len(calls))]
    for (t, a), o in zip(calls, out, strict=True):
        _calls.append({"tool": t, "arguments": a, "output": o})
    return out


def grep(path, pattern, flags=0):
    """Return (line_no, match) for the first line matching pattern; fail loudly if absent."""
    rx = re.compile(pattern, flags)
    for i, line in enumerate(path.read_text().splitlines(), 1):
        m = rx.search(line)
        if m:
            return i, m
    raise SystemExit(f"pattern not found in {path.name}: {pattern}")


def src(path, line):
    return f"{path.relative_to(PAPER_DIR)}:{line}"


audit = {"inputs": {}, "wilson": {}, "tests": {}, "noise_floor": {}, "arithmetic": {}, "dates": {}}
claims = []

# ------------------------------------------------------------------ 1. extract k, n from files
L_art_hw, m = grep(ARTICLE, r"\*\*(\d+) of (\d+)\*\* in a published article")
art_hw_k, art_hw_n = int(m[1]), int(m[2])
L_art_med, m = grep(ARTICLE, r"\*\*(\d+) of (\d+)\*\* survived; from real URLs, (\d+) of (\d+)")
med_embed_k, med_embed_n, med_host_k, med_host_n = map(int, m.groups())
L_art_every, _ = grep(ARTICLE, r"stray break in every paragraph")
L_art_crop, m = grep(ARTICLE, r"proxies it at ([\d.]+):1")
art_ratio = float(m[1])
L_art_crop2, m = grep(ARTICLE, r"a (\d+)x(\d+) cover loses (\d+)px off the top and bottom")
art_w, art_h, art_loss = map(int, m.groups())
L_art_faults, _ = grep(ARTICLE, r"found five faults in the kit itself")
L_art_date, m = grep(ARTICLE, r"^(\d{4}-\d{2}-\d{2}), so check them again")
art_measured_date = m[1]

L_ev_blocks, m = grep(EV / "devto-hardwrap.txt", r"(\d+) <p> \+ (\d+) <li> = (\d+)")
ev_p, ev_li, ev_blocks = map(int, m.groups())
L_ev_br, m = grep(EV / "devto-hardwrap.txt", r"blocks containing <br>:\s+(\d+)")
ev_br_blocks = int(m[1])
L_ev_brtot, m = grep(EV / "devto-hardwrap.txt", r"total <br> in body_html:\s+(\d+)")
ev_br_total = int(m[1])
L_ev_bt, m = grep(EV / "devto-hardwrap.txt", r"reports (\d+) multi-line")
ev_bodytext = int(m[1])
L_ev_hwdate, m = grep(EV / "devto-hardwrap.txt", r"re-measured (\d{4}-\d{2}-\d{2})")
ev_hw_date = m[1]

L_ev_fence, m = grep(EV / "devto-roundtrip.txt", r"opening fences: (\d+)\s+closing fences: (\d+)")
fence_open, fence_close = int(m[1]), int(m[2])
L_ev_bare, m = grep(EV / "devto-roundtrip.txt", r"bare \(unlabelled\) opening fences: (\d+)")
fence_bare = int(m[1])
L_ev_fdict, m = grep(EV / "devto-roundtrip.txt", r"^(\{.*\})$")
fence_dict = ast.literal_eval(m[1])  # literal dict printed by the capture
L_ev_crop, m = grep(EV / "devto-cover-crop.txt", r"width=(\d+),height=(\d+),fit=cover")
crop_w, crop_h = int(m[1]), int(m[2])
L_ev_coverfit, m = grep(EV / "devto-cover-crop.txt", r"is (\d+)x(\d+), ratio")
cov_w, cov_h = int(m[1]), int(m[2])

orgs_txt = (EV / "devto-orgs.txt").read_text()
orgs_total = int(re.search(r"articles listed: (\d+)", orgs_txt)[1])
orgs_parts = {k: int(v) for k, v in re.findall(r"^\s+(\w[\w-]*): (\d+)$", orgs_txt, re.M)}

tc = (EV / "toolchain-run.txt").read_text()
cover_bytes = {name: int(b) for name, b in re.findall(r"^(\S+\.jpg) (\d+) bytes$", tc, re.M)}
bp = (EV / "builder-payload.txt").read_text()
bp_chars = int(re.search(r"chars : (\d+)", bp)[1])
bp_lines = tuple(map(int, re.search(r"lines : (\d+) before unwrap, (\d+) after", bp).groups()))

sf = (EV / "skill-footprint.txt").read_text()
sf_skill = int(re.search(r"SKILL\.md: (\d+) lines", sf)[1])
sf_desc = int(re.search(r"description (\d+) chars", sf)[1])
sf_files = [int(n) for n in re.findall(r"^\s+(\d+)\s+\S+\.(?:md|txt|py)$", sf, re.M)]
sf_total = int(re.search(r"total: ([\d,]+) lines", sf)[1].replace(",", ""))
sf_ver = re.search(r"publishing ([\d.]+)", sf)[1]
sf_counts = {k: int(v) for k, v in re.findall(r"^(\w+) \((\d+)\):", sf, re.M)}

li = (EV / "linkedin-run.txt").read_text()
li_post, li_max = map(int, re.search(r"post is (\d+) chars of (\d+)", li).groups())
li_hook = int(re.search(r"hook fits the fold: (\d+) chars", li)[1])
li_fold = int(re.search(r"above the fold \((\d+) chars\)", li)[1])
li_fail_lines = re.findall(r"^\s+FAIL\s+(.*)$", li, re.M)
li_warn_lines = re.findall(r"^\s+WARN\s+(.*)$", li, re.M)

ss = (EV / "substack-paste.txt").read_text()
ss_src_links = int(re.search(r"link targets\s+(\d+) distinct", ss)[1])
ss_first_links = int(re.search(r"First paste.*?link targets\s+(\d+):", ss, re.S)[1])
ss_second_links = len(
    re.findall(r"^\s*(?:link targets\s+)?(https://\S+)$", ss.split("## Second paste")[1].split("##")[0], re.M)
)
ss_src_imgs = int(re.search(r"<img>\s+(\d+)", ss)[1])
ss_img_after = int(re.search(r"images\s+(\d+) rehosted", ss)[1])
ss_pre_lines = [int(x) for x in re.search(r"<pre> blocks\s+\d+, lines ([\d/]+)", ss)[1].split("/")]
ss_code_lines_after = [int(x) for x in re.search(r"code lines\s+([\d/]+)", ss)[1].split("/")]

audit["inputs"] = {
    "article_hardwrap": {"k": art_hw_k, "n": art_hw_n, "src": src(ARTICLE, L_art_hw)},
    "evidence_hardwrap": {
        "p": ev_p,
        "li": ev_li,
        "blocks": ev_blocks,
        "br_blocks": ev_br_blocks,
        "br_total": ev_br_total,
        "bodytext_multiline": ev_bodytext,
        "src": [src(EV / "devto-hardwrap.txt", x) for x in (L_ev_blocks, L_ev_br, L_ev_brtot, L_ev_bt)],
    },
    "article_medium": {
        "embed": [med_embed_k, med_embed_n],
        "hosted": [med_host_k, med_host_n],
        "src": src(ARTICLE, L_art_med),
    },
    "fences": {
        "open": fence_open,
        "close": fence_close,
        "bare": fence_bare,
        "by_label": fence_dict,
        "src": src(EV / "devto-roundtrip.txt", L_ev_fence),
    },
}

# ------------------------------------------------------------------ 2. Wilson intervals (MCP)
wil_rows = [
    ("hardwrap_47_62", art_hw_k, art_hw_n, src(ARTICLE, L_art_hw) + "; " + src(EV / "devto-hardwrap.txt", L_ev_br)),
    ("medium_embed_0_4", med_embed_k, med_embed_n, src(ARTICLE, L_art_med) + " (no evidence file; CLAIMS.md LOG)"),
    ("medium_hosted_4_4", med_host_k, med_host_n, src(ARTICLE, L_art_med) + " (no evidence file; CLAIMS.md LOG)"),
    ("fences_labelled_23_23", fence_open - fence_bare, fence_open, src(EV / "devto-roundtrip.txt", L_ev_bare)),
    ("substack_links_first_paste", ss_first_links, ss_src_links, "evidence/substack-paste.txt (First paste)"),
    ("substack_links_after_prepare", ss_second_links, ss_src_links, "evidence/substack-paste.txt (Second paste)"),
    ("substack_images", ss_img_after, ss_src_imgs, "evidence/substack-paste.txt"),
]
res = mcp_batch([("verify_wilson_ci", {"successes": k, "total": n}) for _, k, n, _ in wil_rows])
for (label, k, n, s), r in zip(wil_rows, res, strict=True):
    audit["wilson"][label] = {"k": k, "n": n, "source": s, **r}

# ------------------------------------------------------------------ 3. comparisons (MCP)
# Medium: the same four images went through both builds -> paired. b = only hosted keeps, c = only embed keeps.
med_b = med_host_k - med_embed_k  # only valid because embed kept 0: every hosted success is discordant
med_c = 0
ss_b = ss_second_links - ss_first_links
fis_med, mcn_med, mcn_ss, fis_ss = mcp_batch(
    [
        (
            "verify_fisher_exact",
            {"k_method": med_host_k, "n_method": med_host_n, "k_baseline": med_embed_k, "n_baseline": med_embed_n},
        ),
        ("verify_mcnemar_exact", {"b": med_b, "c": med_c}),
        ("verify_mcnemar_exact", {"b": ss_b, "c": 0}),
        (
            "verify_fisher_exact",
            {
                "k_method": ss_second_links,
                "n_method": ss_src_links,
                "k_baseline": ss_first_links,
                "n_baseline": ss_src_links,
            },
        ),
    ]
)
audit["tests"] = {
    "medium_hosted_vs_embed_fisher_unpaired": fis_med,
    "medium_hosted_vs_embed_mcnemar_paired": {"b": med_b, "c": med_c, **mcn_med},
    "substack_links_prepare_vs_first_mcnemar_paired": {"b": ss_b, "c": 0, **mcn_ss},
    "substack_links_prepare_vs_first_fisher_unpaired": fis_ss,
    "wilcoxon": "not run: the paper and evidence contain no paired resource metric (no per-run latency, "
    "token or size series); every size figure is a single measurement",
}

# smallest n at which an all-vs-none paired result reaches two-sided p < 0.05
min_b = None
for b in range(1, 20):
    if mcp_batch([("verify_mcnemar_exact", {"b": b, "c": 0})])[0]["p_value"] < 0.05:
        min_b = b
        break
audit["tests"]["mcnemar_min_discordant_for_p_lt_0.05"] = min_b

# ------------------------------------------------------------------ 4. noise floor (MCP)
nf = mcp_batch([("leaderboard_noise_floor", {"num_tasks": art_hw_n, "baseline_rate": art_hw_k / art_hw_n})])[0]
audit["noise_floor"]["hardwrap_62_blocks"] = nf

# ------------------------------------------------------------------ 5. arithmetic
A = audit["arithmetic"]
A["hardwrap_blocks_sum"] = {"p_plus_li": ev_p + ev_li, "stated": ev_blocks, "ok": ev_p + ev_li == ev_blocks}
A["hardwrap_blocks_without_br"] = ev_blocks - ev_br_blocks
A["hardwrap_pct"] = round(100 * ev_br_blocks / ev_blocks, 3)
A["br_per_affected_block"] = round(ev_br_total / ev_br_blocks, 3)
A["article_matches_evidence_hardwrap"] = (art_hw_k, art_hw_n) == (ev_br_blocks, ev_blocks)
A["published_minus_bodytext"] = ev_br_blocks - ev_bodytext
A["fence_labels_sum"] = {
    "sum": sum(fence_dict.values()),
    "opening": fence_open,
    "ok": sum(fence_dict.values()) == fence_open == fence_close,
}
A["orgs_sum"] = {
    "parts": orgs_parts,
    "sum": sum(orgs_parts.values()),
    "stated": orgs_total,
    "ok": sum(orgs_parts.values()) == orgs_total,
}
ratio = crop_w / crop_h
kept_rows_exact = art_w / ratio
kept_rows_from_rounded = art_w / round(ratio, 3)
A["crop"] = {
    "ratio_exact": ratio,
    "ratio_3dp": round(ratio, 3),
    "article_ratio": art_ratio,
    "ratio_matches_article": round(ratio, 3) == art_ratio,
    "kept_rows_exact": kept_rows_exact,
    "kept_rows_from_rounded_ratio": kept_rows_from_rounded,
    "lost_each_side_exact": (art_h - kept_rows_exact) / 2,
    "lost_each_side_rounded_rows": (art_h - round(kept_rows_exact)) / 2,
    "article_loss": art_loss,
    "this_cover_ratio": cov_w / cov_h,
}
A["cover_kb"] = {
    name: {"bytes": b, "KiB": round(b / 1024, 2), "kB": round(b / 1000, 2)} for name, b in cover_bytes.items()
}
A["builder_payload"] = {
    "chars": bp_chars,
    "KiB": round(bp_chars / 1024, 3),
    "kB": round(bp_chars / 1000, 3),
    "lines_before_after": bp_lines,
    "lines_removed": bp_lines[0] - bp_lines[1],
}
A["skill_footprint"] = {
    "version_in_file": sf_ver,
    "skill_md_lines": sf_skill,
    "description_chars": sf_desc,
    "file_count_by_section": sf_counts,
    "files_listed": len(sf_files),
    "sum_listed_files": sum(sf_files),
    "sum_plus_skill_md": sum(sf_files) + sf_skill,
    "stated_total": sf_total,
    "total_ok": sum(sf_files) + sf_skill == sf_total,
    "listed_matches_section_counts": len(sf_files) == sum(sf_counts.values()),
}
A["linkedin"] = {
    "post": li_post,
    "limit": li_max,
    "post_share_of_limit": round(li_post / li_max, 4),
    "hook": li_hook,
    "fold_chars": li_fold,
    "hook_within_fold": li_hook <= li_fold,
    "distinct_FAIL_lines": len(set(li_fail_lines)),
    "distinct_WARN_lines": len(set(li_warn_lines)),
    "distinct_fail_plus_warn": len(set(li_fail_lines)) + len(set(li_warn_lines)),
}
A["substack_code_lines_preserved"] = ss_pre_lines == ss_code_lines_after
# five faults: count the semicolon-separated items after the colon in that paragraph
para = ARTICLE.read_text().split("found five faults in the kit itself")[1].split("\n\n")[0]
# "TL;DR" inside the last item carries a semicolon that is not a list separator
items = [x for x in para.split(":", 1)[1].replace("TL;DR", "TLDR").split(";") if x.strip()]
A["five_faults_listed"] = len(items)

# CLAIMS.md ledger rows vs the archived files they cite
cl = CLAIMS.read_text()
ledger_skill = re.search(r"SKILL\.md (\d+) lines, ([\d,]+) chars", cl)
ledger_total = re.search(r"([\d,]+) total \|", cl)
ledger_bp = re.findall(r"Builder payload ([\d,]+) chars / ([\d.]+) KB, (\d+) lines before unwrap, (\d+) after", cl)
# ledger order is 1376x768, 1376x768, 1200x675; toolchain-run.txt lists aws and gde (1376x768) and builder (1200x675)
COVER_ORDER = sorted(cover_bytes, key=lambda f: ("builder" in f, f))
ledger_cov = re.search(r"1376x768 (\d+) KB / 1376x768 (\d+) KB / 1200x675 (\d+) KB", cl)
A["ledger_vs_evidence"] = {
    "skill_md_lines": {"ledger": int(ledger_skill[1]), "evidence": sf_skill},
    "footprint_total": {"ledger": int(ledger_total[1].replace(",", "")), "evidence": sf_total},
    "builder_payload_rows": [
        {
            "ledger_chars": int(c.replace(",", "")),
            "ledger_kb": float(kb),
            "ledger_lines": (int(a), int(b)),
            "evidence_chars": bp_chars,
            "evidence_lines": bp_lines,
            "match": int(c.replace(",", "")) == bp_chars and (int(a), int(b)) == bp_lines,
        }
        for c, kb, a, b in ledger_bp
    ],
    "cover_kb": {
        "ledger": [int(x) for x in ledger_cov.groups()],
        "evidence_KiB_rounded": [round(cover_bytes[f] / 1024) for f in COVER_ORDER],
        "evidence_kB_rounded": [round(cover_bytes[f] / 1000) for f in COVER_ORDER],
        "evidence_order": COVER_ORDER,
    },
}

# ------------------------------------------------------------------ 6. dates
d_art = dt.date.fromisoformat(art_measured_date)
d_hw = dt.date.fromisoformat(ev_hw_date)
audit["dates"] = {
    "article_says_measured": art_measured_date,
    "hardwrap_measured": ev_hw_date,
    "hardwrap_days_after_article_date": (d_hw - d_art).days,
    "medium_0_of_4_log_date": re.search(r"0 of 4 embed, 4 of 4 hosted \| (\S+)", cl)[1],
}

# ------------------------------------------------------------------ 7. claim records
W = audit["wilson"]


def rec(id_, statement, paper_value, paper_source, computed, verdict, conclusion, reason):
    claims.append(
        {
            "id": id_,
            "statement": statement,
            "paper_value": paper_value,
            "paper_source": paper_source,
            "computed": computed,
            "verdict": verdict,
            "conclusion": conclusion,
            "reason": reason,
        }
    )


hw = W["hardwrap_47_62"]
rec(
    "hardwrap-47-of-62",
    "47 of 62 paragraph-level blocks in a published dev.to article carried a stray <br>",
    {"k": art_hw_k, "n": art_hw_n},
    src(ARTICLE, L_art_hw),
    {
        "k": ev_br_blocks,
        "n": ev_blocks,
        "rate_pct": A["hardwrap_pct"],
        "wilson_ci_pct": [hw["wilson_low_pct"], hw["wilson_high_pct"]],
    },
    "VERIFIED",
    "HOLDS",
    f"Matches devto-hardwrap.txt lines {L_ev_blocks}-{L_ev_br} ({ev_p} <p> + {ev_li} <li>). One article; the "
    "interval is over blocks of that article and does not generalise to other articles.",
)
rec(
    "hardwrap-every-paragraph",
    "a source wrapped at 95 columns arrives with a stray break in every paragraph",
    {"blocks_with_break": "every"},
    src(ARTICLE, L_art_every),
    {"blocks_with_break": ev_br_blocks, "blocks": ev_blocks, "blocks_without": A["hardwrap_blocks_without_br"]},
    "MISMATCH",
    "OVERSTATED",
    f"The article's own measurement has {A['hardwrap_blocks_without_br']} of {ev_blocks} blocks with no break. "
    "The evidence's mechanism claim ('a break at every wrap') would need the count of source blocks that were "
    "actually wrapped, which is not archived (bodytext reports 43 multi-line paragraphs but skips list items "
    "and quotes), so 'every wrap' is NOT CHECKABLE; 'every paragraph' is contradicted.",
)
rec(
    "medium-0-of-4",
    "Medium images pasted as data URIs: 0 of 4 survived",
    {"k": med_embed_k, "n": med_embed_n},
    src(ARTICLE, L_art_med),
    {"wilson_ci_pct": [W["medium_embed_0_4"]["wilson_low_pct"], W["medium_embed_0_4"]["wilson_high_pct"]]},
    "NOT CHECKABLE",
    "CANNOT CHECK",
    "No evidence file in the archive. CLAIMS.md files it as LOG dated "
    f"{audit['dates']['medium_0_of_4_log_date']}, not re-measured.",
)
rec(
    "medium-4-of-4",
    "Medium images from real URLs: 4 of 4 survived",
    {"k": med_host_k, "n": med_host_n},
    src(ARTICLE, L_art_med),
    {"wilson_ci_pct": [W["medium_hosted_4_4"]["wilson_low_pct"], W["medium_hosted_4_4"]["wilson_high_pct"]]},
    "NOT CHECKABLE",
    "CANNOT CHECK",
    "Same as medium-0-of-4: LOG entry only, no archived artifact.",
)
rec(
    "medium-comparison",
    "Medium drops data: URI images on paste (0 of 4 vs 4 of 4 hosted)",
    {"embed": [med_embed_k, med_embed_n], "hosted": [med_host_k, med_host_n]},
    src(ARTICLE, L_art_med) + "; line 54",
    {"mcnemar_exact_p": mcn_med["p_value"], "fisher_exact_p": fis_med["p_value"]},
    "NOT CHECKABLE",
    "CANNOT CHECK",
    "Paired design (same four images, two builds): exact McNemar b=4, c=0 gives p above 0.05; Fisher, which "
    "wrongly treats the builds as independent, gives p below 0.05. The claim is a deterministic mechanism "
    "(the editor strips data: URIs); a significance test on four images is the wrong instrument and neither "
    "p-value supports or refutes it. Inputs not archived.",
)
c = A["crop"]
rec(
    "devto-crop-ratio",
    "dev.to proxies the cover at 2.381:1",
    {"ratio": art_ratio},
    src(ARTICLE, L_art_crop),
    {"ratio": round(c["ratio_exact"], 6)},
    "VERIFIED" if c["ratio_matches_article"] else "MISMATCH",
    "HOLDS",
    f"width={crop_w},height={crop_h} in the proxied URL (devto-cover-crop.txt:{L_ev_crop}); a single fetch.",
)
rec(
    "devto-crop-95px",
    "a 1376x768 cover loses 95px off the top and bottom",
    {"px_each_side": art_loss},
    src(ARTICLE, L_art_crop2),
    {
        "px_each_side_exact": round(c["lost_each_side_exact"], 3),
        "px_each_side_rounded_rows": c["lost_each_side_rounded_rows"],
    },
    "VERIFIED" if c["lost_each_side_rounded_rows"] == art_loss else "MISMATCH",
    "HOLDS",
    "Arithmetic from one measured display size; assumes a centre crop, "
    "which the URL's gravity=auto does not guarantee.",
)
rec(
    "five-faults",
    "The run also found five faults in the kit itself",
    {"count": 5},
    src(ARTICLE, L_art_faults),
    {"count": A["five_faults_listed"]},
    "VERIFIED" if A["five_faults_listed"] == 5 else "MISMATCH",
    "HOLDS",
    "Count of semicolon-separated items listed in the same paragraph; the faults themselves have no archived "
    "artifact apart from toolchain-run.txt evidence for some (CLAIMS.md).",
)
rec(
    "measured-date",
    "the destination behaviours described here were measured on 2026-08-31",
    {"date": art_measured_date},
    src(ARTICLE, L_art_date),
    {"hardwrap_measured": ev_hw_date, "medium_log_date": audit["dates"]["medium_0_of_4_log_date"]},
    "MISMATCH",
    "OVERSTATED",
    f"The 47-of-62 figure was measured {audit['dates']['hardwrap_days_after_article_date']} days later "
    f"({ev_hw_date}); the 0-of-4 figure is a log entry dated {audit['dates']['medium_0_of_4_log_date']}. "
    "Neither of the article's two headline numbers was measured on the date the footer gives.",
)
rec(
    "fences-23-of-23",
    "23 of 23 opening fences carry a language label in a stored body (CLAIMS.md; not in the article)",
    {"k": fence_open - fence_bare, "n": fence_open},
    src(CLAIMS, 29),
    {
        "labels_sum": A["fence_labels_sum"]["sum"],
        "wilson_ci_pct": [W["fences_labelled_23_23"]["wilson_low_pct"], W["fences_labelled_23_23"]["wilson_high_pct"]],
    },
    "VERIFIED" if A["fence_labels_sum"]["ok"] else "MISMATCH",
    "HOLDS",
    "Per-label counts sum to the opening-fence count; one article.",
)
rec(
    "orgs-40",
    "40 articles listed: gde 24, aws-builders 13, none 3 (CLAIMS.md)",
    {"total": 40, "parts": [24, 13, 3]},
    src(CLAIMS, 32),
    {"total": orgs_total, "sum_parts": A["orgs_sum"]["sum"]},
    "VERIFIED" if A["orgs_sum"]["ok"] else "MISMATCH",
    "HOLDS",
    "Parts sum to total; per_page=40 means the listing may be truncated at 40.",
)
lv = A["ledger_vs_evidence"]
rec(
    "ledger-footprint",
    "SKILL.md 446 lines; 2,370 total lines (CLAIMS.md, cites skill-footprint.txt)",
    {"skill_md_lines": lv["skill_md_lines"]["ledger"], "total": lv["footprint_total"]["ledger"]},
    src(CLAIMS, 21) + "-22",
    {"skill_md_lines": sf_skill, "total": sf_total, "evidence_version": sf_ver},
    "MISMATCH",
    "CANNOT CHECK",
    f"The archived skill-footprint.txt is at publishing {sf_ver}, the ledger row is 'at 0.2.0'; the file was "
    "overwritten by a later capture, so the ledger row has no surviving artifact. The later file is internally "
    f"consistent (sum of listed files + SKILL.md = {A['skill_footprint']['sum_plus_skill_md']}, stated {sf_total}).",
)
for i, r in enumerate(lv["builder_payload_rows"]):
    rec(
        f"ledger-builder-payload-{i}",
        f"Builder payload {r['ledger_chars']} chars, lines {r['ledger_lines']} (CLAIMS.md)",
        {"chars": r["ledger_chars"], "lines": list(r["ledger_lines"])},
        "CLAIMS.md",
        {"chars": bp_chars, "lines": list(bp_lines)},
        "VERIFIED" if r["match"] else "MISMATCH",
        "HOLDS" if r["match"] else "CANNOT CHECK",
        "Compared with evidence/builder-payload.txt serve-body.py payload line.",
    )
rec(
    "ledger-cover-kb",
    "covers 105 KB / 104 KB / 15 KB (CLAIMS.md, cites toolchain-run.txt)",
    {"kb": lv["cover_kb"]["ledger"]},
    src(CLAIMS, 30),
    {"KiB_rounded": lv["cover_kb"]["evidence_KiB_rounded"], "kB_rounded": lv["cover_kb"]["evidence_kB_rounded"]},
    "VERIFIED"
    if lv["cover_kb"]["ledger"] in (lv["cover_kb"]["evidence_KiB_rounded"], lv["cover_kb"]["evidence_kB_rounded"])
    else "MISMATCH",
    "HOLDS",
    "Byte counts in toolchain-run.txt converted both ways (1024 and 1000); the file was re-captured "
    "after the ledger row, so the 105 KB value has no surviving artifact. "
    "The size class (about 100 KB vs 15 KB) holds.",
)
rec(
    "linkedin-1269",
    "LinkedIn post 1,269 chars, hook 80 chars (CLAIMS.md)",
    {"post": 1269, "hook": 80},
    src(CLAIMS, 36),
    {"post": li_post, "hook": li_hook, "fold": li_fold},
    "VERIFIED" if (li_post, li_hook) == (1269, 80) else "MISMATCH",
    "HOLDS",
    "Read from linkedin-run.txt.",
)

audit["claims"] = claims
audit["raw_mcp_calls"] = _calls
(OUT / "stat_audit.json").write_text(json.dumps(audit, indent=1, default=list) + "\n")

# ------------------------------------------------------------------ console summary
print("== inputs")
print(json.dumps(audit["inputs"], indent=1))
print("== Wilson (MCP)")
for k, v in W.items():
    print(f"  {k:32s} {v['formatted']}")
print("== tests (MCP)")
for k, v in audit["tests"].items():
    print(f"  {k}: {v}")
print("== noise floor (MCP)")
print(f"  {nf}")
print("== arithmetic")
for k, v in A.items():
    print(f"  {k}: {v}")
print("== dates")
print(f"  {audit['dates']}")
print("== claim verdicts")
for r in claims:
    print(f"  {r['id']:28s} {r['verdict']:14s} {r['conclusion']}")
from collections import Counter  # noqa: E402

print("  verdict counts:", dict(Counter(r["verdict"] for r in claims)))
print("  conclusion counts:", dict(Counter(r["conclusion"] for r in claims)))
