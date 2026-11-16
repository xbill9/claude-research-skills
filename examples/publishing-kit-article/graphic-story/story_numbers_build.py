"""Build story_numbers.json: every number the comic may show, quoted from the article or its evidence.

Paper of record: ../paper/devto-publishing-kit.md. Evidence: ../paper/evidence/*.txt.
Each quoted entry names its file and section and carries a verbatim fragment; the build checks that
the fragment really occurs in that file (whitespace collapsed), so a mistyped quote fails here.
Derived entries are computed in this script from quoted inputs. Internal-consistency checks
(sums, ratios, the article against its evidence) are computed here too and must all pass.

Some numbers are in the article but have no measurement archived in evidence/ (CLAIMS.md files them
under LOG or DOCUMENTED). They carry a `caveat`, and the comic prints that caveat next to them.

CLAIMS.md is read for comparison only. Where its rows disagree with the evidence files, the
disagreement is recorded under `_ledger_vs_evidence`; none of those figures are shown in the comic.

    python3 story_numbers_build.py   -> writes story_numbers.json; exit 1 on any failed check
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent / "paper"
ARTICLE = "devto-publishing-kit.md"

N: dict[str, dict] = {}
CHECKS: list[dict] = []
FAILS: list[str] = []


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


_TEXT_CACHE: dict[str, str] = {}


def _text(rel: str) -> str:
    if rel not in _TEXT_CACHE:
        _TEXT_CACHE[rel] = _norm((PAPER / rel).read_text(encoding="utf-8"))
    return _TEXT_CACHE[rel]


def q(key, value, display, file, where, quote, caveat=None):
    """A number quoted from the article or an evidence file. The quote must occur in that file."""
    assert key not in N, key
    if _norm(quote) not in _text(file):
        FAILS.append(f"quote for {key!r} not found in {file}: {quote!r}")
    bare = str(display).strip("~%").replace(",", "")
    if bare not in _norm(quote).replace(",", "") and display not in _norm(quote):
        FAILS.append(f"display {display!r} for {key!r} does not occur in its quote {quote!r}")
    N[key] = {"value": value, "display": display, "source": f"{file} ({where})", "quote": _norm(quote),
              "derived": False}
    if caveat:
        N[key]["caveat"] = caveat


def d(key, value, display, formula, inputs):
    """A number computed here from quoted inputs."""
    assert key not in N, key
    for i in inputs:
        assert i in N, i
    N[key] = {"value": value, "display": display, "formula": formula, "inputs": inputs, "derived": True,
              "source": "computed in story_numbers_build.py from " + ", ".join(inputs)}


def check(name, computed, paper, ok):
    CHECKS.append({"check": name, "computed": computed, "paper": paper, "ok": bool(ok)})
    if not ok:
        FAILS.append(f"check failed: {name}: computed {computed!r} vs paper {paper!r}")


LOG = "CLAIMS.md files this under LOG: carried from the kit's log, not re-measured in this run"
DOC = "CLAIMS.md files this under DOCUMENTED: LinkedIn's own developer docs, not measured"

# ---- The article: setup -------------------------------------------------------------------------
A = ARTICLE
q("dest_count", 4, "four", A, "opening", "Publishing one technical article to four places")
q("artifact_count", 4, "four", A, "TL;DR", "all four of its artifacts")
q("wrap_cols", 95, "95", A, "What it does", "a source wrapped at 95 columns")
q("card_px", 320, "320px", A, "What it does", "which type sizes survive a 320px feed card", caveat=LOG)
q("crop_ratio", 2.381, "2.381:1", A, "What it does", "proxies it at 2.381:1")
q("cover_dims", "1376x768", "1376x768", A, "What it does", "a 1376x768 cover loses 95px off the top and bottom")
q("crop_px", 95, "95px", A, "What it does", "loses 95px off the top and bottom")
q("untraced_kinds", 3, "three", A, "Debugging", "untraced claim is one of three things")
q("http_ok", 200, "HTTP 200", A, "Debugging", "HTTP 200, bytes match disk")
q("checklinks_block",
  "devto-publishing-kit.md (branch URLs)",
  "devto-publishing-kit.md (branch URLs)", A, "Debugging, check-links.py output",
  "devto-publishing-kit.md (branch URLs)")
q("checklinks_cover", "cover.77acc7c4.jpg", "cover.77acc7c4.jpg: HTTP 200, bytes match disk", A,
  "Debugging, check-links.py output", "ok cover.77acc7c4.jpg: HTTP 200, bytes match disk")
q("checklinks_imgcover", "img/cover.77acc7c4.jpg", "img/cover.77acc7c4.jpg: HTTP 200, bytes match disk", A,
  "Debugging, check-links.py output", "ok img/cover.77acc7c4.jpg: HTTP 200, bytes match disk")
q("checklinks_table", "img/devto-publishing-kit-table-1.png",
  "img/devto-publishing-kit-table-1.png: HTTP 200, bytes match disk", A, "Debugging, check-links.py output",
  "ok img/devto-publishing-kit-table-1.png: HTTP 200, bytes match disk")
q("cover_numbers", 2, "two", A, "Dogfooding", "The two numbers on the cover are real")
q("hw_blocks", 47, "47", A, "Dogfooding table", "**47 of 62** in a published article carried a stray break")
q("hw_total", 62, "62", A, "Dogfooding table", "**47 of 62** in a published article carried a stray break")
q("med_embed_ok", 0, "0", A, "Dogfooding table", "**0 of 4** survived; from real URLs, 4 of 4", caveat=LOG)
q("med_embed_n", 4, "4", A, "Dogfooding table", "**0 of 4** survived; from real URLs, 4 of 4", caveat=LOG)
q("med_hosted_ok", 4, "4", A, "Dogfooding table", "from real URLs, 4 of 4", caveat=LOG)
q("faults", 5, "five", A, "Dogfooding", "The run also found five faults in the kit itself")
q("localhost", "127.0.0.1", "127.0.0.1", A, "Dogfooding", "`check-facts.py` read `127.0.0.1` as a version number")
q("tldr_lines", 5, "five", A, "Dogfooding", "this article's own TL;DR posted as five separate lines")
q("measured_on", "2026-08-31", "2026-08-31", A, "closing note", "measured on 2026-08-31")

# ---- Evidence files -----------------------------------------------------------------------------
E = "evidence/devto-hardwrap.txt"
q("hw_p", 58, "58", E, "MEASURED", "paragraph-level blocks in body_html: 58 <p> + 4 <li> = 62")
q("hw_li", 4, "4", E, "MEASURED", "paragraph-level blocks in body_html: 58 <p> + 4 <li> = 62")
q("hw_total_ev", 62, "62", E, "MEASURED", "58 <p> + 4 <li> = 62")
q("hw_blocks_ev", 47, "47", E, "MEASURED", "blocks containing <br>: 47")
q("hw_br", 88, "88", E, "MEASURED", "total <br> in body_html: 88")
q("hw_twospace", 0, "0", E, "CONTROL", "source lines ending in two spaces (an explicit markdown break): 0")
q("two_spaces", 2, "two", E, "CONTROL", "source lines ending in two spaces")
q("hw_bodytext", 43, "43", E, "CONTROL", "reports 43 multi-line")
q("hw_date", "2026-09-16", "2026-09-16", E, "header", "re-measured 2026-09-16")

E = "evidence/devto-cover-crop.txt"
q("crop_display", "1000x420", "1000x420", E, "MEASURED", "dev.to displays the cover at 1000x420, fit=cover")
q("crop_rows", 578, "578", E, "ARITH", "1376/2.381 = 577.9 -> 578 rows")
q("crop_fixed", "1376x578", "1376x578", E, "MEASURED", "cover.77acc7c4.jpg is 1376x578, ratio 2.381:1 -- nothing cropped")

E = "evidence/builder-payload.txt"
q("payload_chars", 23234, "23,234", E, "serve-body.py payload", "chars : 23234")
q("payload_lines_before", 531, "531", E, "serve-body.py payload", "lines : 531 before unwrap, 411 after")
q("payload_lines_after", 411, "411", E, "serve-body.py payload", "lines : 531 before unwrap, 411 after")
N["payload_chars"]["quote_display_note"] = "file prints 23234; shown with a thousands separator"

E = "evidence/linkedin-run.txt"
q("li_post", 1269, "1269", E, "default template", "ok post is 1269 chars of 3000")
q("li_limit", 3000, "3000", E, "default template", "ok post is 1269 chars of 3000",
  caveat="CLAIMS.md: 3,000 is third-party consensus; LinkedIn documents only FIELD_LENGTH_TOO_LONG")
q("li_hook", 80, "80", E, "default template", "ok hook fits the fold: 80 chars")
q("li_fold", 140, "140", E, "default template", "--- above the fold (140 chars) ---",
  caveat="CLAIMS.md: the fold is third-party, and moves with screen and font size")
q("li_pending", 4, "4", E, "default template", "FAIL 4 link(s) still PENDING")

E = "evidence/devto-orgs.txt"
q("orgs_listed", 40, "40", E, "orgs seen", "articles listed: 40")
q("orgs_gde", 24, "24", E, "orgs seen", "gde: 24")
q("orgs_aws", 13, "13", E, "orgs seen", "aws-builders: 13")
q("orgs_none", 3, "3", E, "orgs seen", "None: 3")

E = "evidence/devto-roundtrip.txt"
q("fences_open", 23, "23", E, "fence labelling", "opening fences: 23")
q("fences_bare", 0, "0", E, "fence labelling", "bare (unlabelled) opening fences: 0")

E = "evidence/toolchain-run.txt"
q("med_tables", 5, "5", E, "make-medium", "devto-publishing-kit-gde.md: 5 tables, 1 diagrams")
q("med_h4", 19, "19", E, "make-medium", "19 <h4")
q("med_embed_kb", 497, "497 KB", E, "make-medium", "embed: 497 KB")

E = "evidence/skill-footprint.txt"
q("fp_version", "0.18.0", "0.18.0", E, "header", "publishing 0.18.0")
q("fp_scripts", 14, "14", E, "scripts", "scripts (14):")
q("fp_lines", 4580, "4,580", E, "total", "total: 4,580 lines")
q("fp_always", 190, "~190", E, "installed snapshot", "~190 always-on")
q("fp_invoke", "11.8k", "~11.8k", E, "installed snapshot", "~11.8k on-invoke")

E = "evidence/install-is-a-snapshot.txt"
q("snap_version", "0.6.0", "0.6.0", E, "header", "re-captured 2026-08-31T16:46:33-04:00 at 0.6.0")

# ---- Derived ------------------------------------------------------------------------------------
d("hw_pct", round(100 * 47 / 62), "76%", "round(100 * hw_blocks / hw_total)", ["hw_blocks", "hw_total"])
d("unwrap_removed", 531 - 411, "120", "payload_lines_before - payload_lines_after",
  ["payload_lines_before", "payload_lines_after"])
d("li_room", 3000 - 1269, "1731", "li_limit - li_post", ["li_post", "li_limit"])

# ---- Audit lookup -------------------------------------------------------------------------------
# The skill: look up every number in an existing audit first; a MISMATCH or NOT CHECKABLE value never
# appears alone. Audits sit beside this folder (../math-sandbox, ../ablation-stat-auditor).
AUDIT_FILES = {"math": HERE.parent / "math-sandbox" / "eq_verified_numbers.json",
               "stat": HERE.parent / "ablation-stat-auditor" / "stat_audit.json"}
AUD: dict[tuple[str, str], dict] = {}
for tag, f in AUDIT_FILES.items():
    if f.exists():
        j = json.loads(f.read_text(encoding="utf-8"))
        for r in j.get("equations", []) + j.get("claims", []):
            AUD[(tag, r["id"])] = r
AUDIT_MAP = {
    "crop_ratio": [("math", "D1_proxy_ratio"), ("stat", "devto-crop-ratio")],
    "crop_rows": [("math", "B1_crop_rows_kept")],
    "crop_px": [("math", "B2_crop_loss_95px"), ("stat", "devto-crop-95px")],
    "crop_fixed": [("math", "B3_shipped_cover_uncropped")],
    "card_px": [("math", "D3_card_width_is_devto")],
    "wrap_cols": [("math", "M1_own_source_95_columns")],
    "hw_blocks": [("math", "E1_hardwrap_47_of_62"), ("stat", "hardwrap-47-of-62")],
    "hw_total": [("math", "E1_hardwrap_47_of_62"), ("stat", "hardwrap-47-of-62")],
    "med_embed_ok": [("math", "E3_medium_data_uri_0_of_4"), ("stat", "medium-0-of-4")],
    "med_embed_n": [("math", "E3_medium_data_uri_0_of_4"), ("stat", "medium-0-of-4")],
    "med_hosted_ok": [("math", "E3_medium_data_uri_0_of_4"), ("stat", "medium-4-of-4")],
    "tldr_lines": [("math", "M2_tldr_five_lines")],
    "faults": [("math", "M3_five_faults"), ("stat", "five-faults")],
    "orgs_listed": [("math", "M6_org_split_sums"), ("stat", "orgs-40")],
    "fences_open": [("math", "M7_fences_23_of_23"), ("stat", "fences-23-of-23")],
    "li_post": [("stat", "linkedin-1269")],
    "li_hook": [("math", "M15_linkedin_hook_80"), ("stat", "linkedin-1269")],
    "measured_on": [("stat", "measured-date")],
}
# Caveats written from the disputed audit records; they replace the CLAIMS.md-only caveat.
AUDIT_CAVEAT = {
    "med_embed_ok": "Kit log, 2026-08-30, not re-measured: no artifact is archived (audit: NOT CHECKABLE), and "
                    "this article's own Medium builds hold different images",
    "measured_on": "The audit dates the headline counts differently: 47 of 62 was measured 2026-09-16, "
                   "the Medium count is a kit-log entry from 2026-08-30",
    "wrap_cols": "Audit: NOT CHECKABLE; the article's own source has prose lines longer than this",
    "card_px": "Audit: NOT CHECKABLE; the only source is the kit's own constant",
}
AUDIT_CAVEAT["med_embed_n"] = AUDIT_CAVEAT["med_hosted_ok"] = AUDIT_CAVEAT["med_embed_ok"]
# Worded claims in the article the audit contradicts; build_story.py fails if the story repeats one.
AUDIT_PHRASES = [
    {"phrase": "every paragraph", "record": "E2_break_in_every_paragraph / hardwrap-every-paragraph (MISMATCH)",
     "why": "15 of 62 blocks carried no break"},
    {"phrase": "numbers on the cover", "record": "../README.md, 'What the runs found' (no audit record)",
     "why": "neither number is on any cover; they appear in the table image"},
]
DISPUTED = ("MISMATCH", "NOT CHECKABLE")
if not AUD:
    print("WARN  no audit file found; numbers not checked against an audit")
for key, refs in AUDIT_MAP.items():
    recs = []
    for tag, rid in refs:
        r = AUD.get((tag, rid))
        if r is None:
            if AUD:
                FAILS.append(f"audit record {rid!r} for {key!r} not found in {AUDIT_FILES[tag].name}")
            continue
        recs.append({"file": AUDIT_FILES[tag].name, "id": rid, "verdict": r["verdict"],
                     "reason": r.get("reason", "")})
    N[key]["audit"] = recs
    if any(x["verdict"] in DISPUTED for x in recs):
        if key not in AUDIT_CAVEAT:
            FAILS.append(f"{key!r} is disputed by the audit and has no audit caveat")
        else:
            N[key]["caveat"] = AUDIT_CAVEAT[key]
            N[key]["disputed"] = True

# ---- Consistency checks -------------------------------------------------------------------------
V = {k: v["value"] for k, v in N.items()}
check("hard-wrap: <p> + <li> == total", V["hw_p"] + V["hw_li"], V["hw_total_ev"], V["hw_p"] + V["hw_li"] == 62)
check("hard-wrap: article 47 of 62 == evidence", (V["hw_blocks_ev"], V["hw_total_ev"]),
      (V["hw_blocks"], V["hw_total"]), (V["hw_blocks_ev"], V["hw_total_ev"]) == (V["hw_blocks"], V["hw_total"]))
check("hw_pct == round(47/62*100)", round(100 * V["hw_blocks"] / V["hw_total"]), V["hw_pct"],
      round(100 * V["hw_blocks"] / V["hw_total"]) == V["hw_pct"])
w, h = (int(x) for x in V["crop_display"].split("x"))
ratio = round(w / h, 3)
check("crop ratio 1000/420 == 2.381", ratio, V["crop_ratio"], ratio == V["crop_ratio"])
cw, ch = (int(x) for x in V["cover_dims"].split("x"))
rows = round(cw / V["crop_ratio"])
check("rows kept round(1376/2.381) == 578", rows, V["crop_rows"], rows == V["crop_rows"])
lost = (ch - rows) / 2
check("(768 - 578) / 2 == 95", lost, V["crop_px"], lost == V["crop_px"])
fw, fh = (int(x) for x in V["crop_fixed"].split("x"))
check("fixed cover 1376x578 has ratio 2.381", round(fw / fh, 3), V["crop_ratio"], round(fw / fh, 3) == V["crop_ratio"])
s = V["orgs_gde"] + V["orgs_aws"] + V["orgs_none"]
check("orgs gde + aws-builders + none == listed", s, V["orgs_listed"], s == V["orgs_listed"])
check("LinkedIn post under limit", V["li_post"], V["li_limit"], V["li_post"] < V["li_limit"])
check("LinkedIn hook under fold", V["li_hook"], V["li_fold"], V["li_hook"] < V["li_fold"])
art = (PAPER / ARTICLE).read_text(encoding="utf-8")
m = re.search(r"also found five faults in the kit itself.*?:(.*?)\n\n", art, re.S)
named = [x for x in re.split(r";\s", m.group(1)) if x.strip()] if m else []
check("five faults: semicolon-separated items in the article's list", len(named), V["faults"],
      len(named) == V["faults"])
check("article measured date equals evidence/devto-orgs.txt capture date",
      "2026-08-31" in (PAPER / "evidence/devto-orgs.txt").read_text(), V["measured_on"],
      "2026-08-31" in (PAPER / "evidence/devto-orgs.txt").read_text())

# ---- CLAIMS.md rows compared with the evidence files (recorded, not shown in the comic) ---------
claims = _norm((PAPER / "CLAIMS.md").read_text(encoding="utf-8"))
LEDGER = []


def ledger(row_fragment, ledger_value, evidence_file, evidence_value):
    present = _norm(row_fragment) in claims
    LEDGER.append({"claims_row": _norm(row_fragment), "row_found_in_CLAIMS.md": present,
                   "claims_value": ledger_value, "evidence_file": evidence_file,
                   "evidence_value": evidence_value, "agree": ledger_value == evidence_value})


ledger("Builder payload 22,542 chars / 22.0 KB, 521 lines before unwrap, 408 after", (22542, 521, 408),
       "evidence/builder-payload.txt", (V["payload_chars"], V["payload_lines_before"], V["payload_lines_after"]))
ledger("Builder payload 23,214 chars / 22.7 KB, 531 lines before unwrap, 411 after", (23214, 531, 411),
       "evidence/builder-payload.txt", (V["payload_chars"], V["payload_lines_before"], V["payload_lines_after"]))
ledger("~187 tokens always-on, ~8k on-invoke, at 0.2.0", ("~187", "~8k", "0.2.0"),
       "evidence/skill-footprint.txt", ("~190", "~11.8k", V["fp_version"]))
ledger("description 528 chars; SKILL.md 446 lines, 22,602 chars", 446, "evidence/skill-footprint.txt", 649)
ledger("install pinned at commit f7eaac2, equal to HEAD", "f7eaac2",
       "evidence/install-is-a-snapshot.txt", "920fe6c2c54ada449b13a31221dd8f0fdceb3acf"[:7])
ledger("references 226 / 148 / 86 / 66 lines; six scripts 1,389 lines; 2,370 total", 2370,
       "evidence/skill-footprint.txt", V["fp_lines"])
for row in LEDGER:
    if not row["row_found_in_CLAIMS.md"]:
        FAILS.append(f"ledger row not found in CLAIMS.md: {row['claims_row']}")

out = {
    "_about": ("Every number the comic may show. Quoted entries carry file, section and a verbatim fragment "
               "checked against that file; derived entries carry formula and inputs. Built by "
               "story_numbers_build.py. Entries with `caveat` have no archived measurement in evidence/."),
    "_checks": CHECKS,
    "_ledger_vs_evidence": LEDGER,
    "_audit_phrases": AUDIT_PHRASES,
    **N,
}
(HERE / "story_numbers.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
for c in CHECKS:
    print(("OK   " if c["ok"] else "FAIL ") + c["check"])
for row in LEDGER:
    tag = "agree   " if row["agree"] else "DIFFERS "
    print(f"ledger {tag} CLAIMS.md {row['claims_value']} vs {row['evidence_file']} {row['evidence_value']}")
n_aud = sum(bool(v.get("audit")) for v in N.values())
n_dis = sum(bool(v.get("disputed")) for v in N.values())
print(f"audit: {len(AUD)} records read, {n_aud} numbers looked up, {n_dis} disputed (carry the audit caveat)")
print(f"{len(N)} numbers, {len(CHECKS)} checks, {sum(not c['ok'] for c in CHECKS)} failed, "
      f"{sum(not r['agree'] for r in LEDGER)} of {len(LEDGER)} CLAIMS.md rows differ from evidence")
for f in FAILS:
    print("ERROR", f)
sys.exit(1 if FAILS else 0)
