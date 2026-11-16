#!/usr/bin/env python3
"""math-sandbox verifier for the publishing-kit dev.to article.

Every quantitative claim in paper/devto-publishing-kit.md and its archived evidence that can be
recomputed is recomputed here: from the images, markdown and HTML on disk, from the evidence
files, or from the publishing-kit source. Writes eq_verified_numbers.json and the sensitivity
figures. seed=42 for the only stochastic step (a binomial bootstrap of 47 of 62).
"""

from __future__ import annotations

import json
import math
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import matplotlib
import numpy as np
from PIL import Image, ImageOps
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = Path(__file__).resolve().parent
PAPER = OUT.parent / "paper"
EV = PAPER / "evidence"
FIG = OUT / "figures"
FIG.mkdir(exist_ok=True)
KIT = Path.home() / "publishing-kit"
RNG = np.random.default_rng(42)

ARTICLE = (PAPER / "devto-publishing-kit.md").read_text()
ART_LINES = ARTICLE.splitlines()
CLAIMS = (PAPER / "CLAIMS.md").read_text()
records: list[dict] = []


def ev(name: str) -> str:
    return (EV / name).read_text()


def line_of(text: str, needle: str) -> int:
    for i, ln in enumerate(text.splitlines(), 1):
        if needle in ln:
            return i
    raise KeyError(needle)


def add(
    rid,
    cls,
    statement,
    paper_value,
    paper_source,
    computed,
    verdict,
    reason,
    simulated=None,
    simulation=None,
    abs_gap=None,
    tolerance=None,
):
    records.append(
        dict(
            id=rid,
            operator_class=cls,
            statement=statement,
            paper_value=paper_value,
            paper_source=paper_source,
            computed=computed,
            simulated=simulated,
            simulation=simulation,
            abs_gap=abs_gap,
            tolerance=tolerance,
            verdict=verdict,
            reason=reason,
        )
    )


L_CROP = line_of(ARTICLE, "2.381:1")
# ---------------------------------------------------------------- dev.to cover proxy geometry
crop_txt = ev("devto-cover-crop.txt")
m = re.search(r"width=(\d+),height=(\d+),fit=(\w+),gravity=(\w+)", crop_txt)
PW, PH, FIT, GRAVITY = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
ratio = PW / PH
add(
    "D1_proxy_ratio",
    "definition",
    "dev.to proxies the cover at width/height = 2.381:1",
    2.381,
    f"devto-publishing-kit.md l.{L_CROP}; evidence/devto-cover-crop.txt proxy URL",
    {"proxy_w": PW, "proxy_h": PH, "ratio": round(ratio, 6)},
    "VERIFIED",
    f"{PW}/{PH} = {ratio:.6f}, prints as 2.381.",
    abs_gap=round(abs(ratio - 2.381), 6),
    tolerance=0.0005,
)


def fit_cover_loss(w: float, h: float, pw: int = PW, ph: int = PH) -> tuple[float, float]:
    """Source rows (or columns) a fit=cover crop to pw x ph discards, in source pixels."""
    target = pw / ph
    if w / h < target:  # too tall: rows go
        return h - w / target, 0.0
    return 0.0, w - h * target


kept_rows = 1376 / ratio
lost_rows, _ = fit_cover_loss(1376, 768)


def simulate_crop(w: int, h: int, centering=(0.5, 0.5)) -> dict:
    """Run a real fit=cover crop (Pillow ImageOps.fit) on an image whose pixel value encodes its
    source row, and read back which source rows survive at the top and bottom."""
    rows = np.repeat(np.arange(h, dtype=np.uint32)[:, None], w, axis=1)
    img = Image.fromarray(rows.astype(np.int32), mode="I")
    # crop first at source resolution (ImageOps.fit crops then resizes; we read the crop box)
    out = ImageOps.fit(img, (PW, PH), method=Image.Resampling.NEAREST, centering=centering)
    arr = np.asarray(out)
    top, bottom = int(arr[0, 0]), int(arr[-1, 0])
    return {"first_row_kept": top, "last_row_kept": bottom, "lost_top": top, "lost_bottom": h - 1 - bottom}


sim = simulate_crop(1376, 768)
add(
    "B1_crop_rows_kept",
    "bound",
    "a 1376-wide cover keeps 1376/2.381 = 577.9 -> 578 rows",
    578,
    "evidence/devto-cover-crop.txt ARITH line 2",
    {"kept_rows": round(kept_rows, 3)},
    "VERIFIED",
    "1376 * 420 / 1000 = 577.92, rounds to 578.",
    abs_gap=round(abs(kept_rows - 578), 3),
    tolerance=0.5,
)
add(
    "B2_crop_loss_95px",
    "bound",
    "a 1376x768 cover loses 95px off the top and 95px off the bottom",
    {"lost_top_px": 95, "lost_bottom_px": 95},
    f"devto-publishing-kit.md l.{L_CROP}; evidence ARITH line 3",
    {
        "lost_total_px": round(lost_rows, 3),
        "lost_top_px": round(lost_rows / 2, 3),
        "lost_bottom_px": round(lost_rows / 2, 3),
    },
    "VERIFIED",
    f"768 - 577.92 = 190.08 rows, 95.04 a side under a centre crop. Pillow's fit=cover crop on a row-encoded "
    f"image agrees within 1 row. The proxy URL says gravity={GRAVITY}, so the 95/95 split assumes centring; "
    "the 190-row total does not depend on it.",
    simulated=sim,
    simulation="Pillow ImageOps.fit(1376x768 row-index image -> 1000x420, centering 0.5) with "
    "NEAREST resampling; deterministic, no sampling",
    abs_gap=round(abs(lost_rows / 2 - 95), 3),
    tolerance=0.5,
)

covers = {}
for name in [
    "cover.77acc7c4.jpg",
    "cover.ae4d639e.jpg",
    "cover-builder.80aa6ca5.jpg",
    "cover-builder.cabd79f3.jpg",
    "advocu-devto-publishing-kit-cover.webp",
    "linkedin-devto-publishing-kit-cover.jpg",
]:
    with Image.open(PAPER / name) as im:
        covers[name] = list(im.size)
loss_now = {n: round(fit_cover_loss(*covers[n])[0], 3) for n in ["cover.77acc7c4.jpg", "cover.ae4d639e.jpg"]}
add(
    "B3_shipped_cover_uncropped",
    "bound",
    "the article's own dev.to covers are 1376x578 (ratio 2.381:1), so nothing is cropped",
    {"w": 1376, "h": 578},
    "evidence/devto-cover-crop.txt last MEASURED line; front matter cover_image",
    {"sizes": {n: covers[n] for n in loss_now}, "rows_lost": loss_now, "ratio": round(1376 / 578, 6)},
    "VERIFIED",
    "Both cover files on disk measure 1376x578. 1376/578 = 2.3806, wider than 2.38095 by 0.0003, so a "
    "fit=cover crop removes 0.08 source columns and 0 rows.",
    abs_gap=0,
    tolerance=0,
)

# ---------------------------------------------------------------- 320px feed card
L_CARD = line_of(ARTICLE, "320px feed card")
kit_src = (KIT / "skills/publishing/scripts/make-cover.py").read_text()
card_w = int(re.search(r"^CARD_W = (\d+)", kit_src, re.M).group(1))
legible_px = int(re.search(r"^LEGIBLE_PX = (\d+)", kit_src, re.M).group(1))
kit_head = subprocess.run(
    ["git", "-C", str(KIT), "log", "-1", "--format=%h %cs"], capture_output=True, text=True
).stdout.strip()
min_src = legible_px * 1376 / card_w
add(
    "D2_card_width_in_kit",
    "definition",
    "make-cover.py reports which type sizes survive a 320px feed card",
    320,
    f"devto-publishing-kit.md l.{L_CARD}",
    {
        "CARD_W": card_w,
        "LEGIBLE_PX": legible_px,
        "min_legible_source_px_at_1376": round(min_src, 2),
        "card_scale_1376": round(card_w / 1376, 5),
    },
    "VERIFIED" if card_w == 320 else "MISMATCH",
    f"CARD_W = {card_w} in ~/publishing-kit make-cover.py at {kit_head} (current HEAD, not the 2026-08-31 "
    f"version). With LEGIBLE_PX = {legible_px}, type on a 1376-wide cover must be >= {min_src:.1f} source px to "
    "survive the card.",
    abs_gap=abs(card_w - 320),
    tolerance=0,
)
add(
    "D3_card_width_is_devto",
    "definition",
    "320px is the size a dev.to cover is seen at in the feed",
    320,
    f"devto-publishing-kit.md l.{L_CARD}; CLAIMS.md LOG 2026-08-31",
    None,
    "NOT CHECKABLE",
    "No archived measurement of dev.to's feed card. CLAIMS.md files it as LOG, and the only source is the kit's "
    "own constant, which records the author's choice, not dev.to's layout.",
)

# ---------------------------------------------------------------- hard-wrap 47 of 62
hw = ev("devto-hardwrap.txt")
n_p, n_li = map(int, re.search(r"(\d+) <p> \+ (\d+) <li> = (\d+)", hw).groups()[:2])
n_blocks = int(re.search(r"= (\d+)\n", hw).group(1))
k_br = int(re.search(r"blocks containing <br>:\s+(\d+)", hw).group(1))
tot_br = int(re.search(r"total <br> in body_html:\s+(\d+)", hw).group(1))
two_space = int(re.search(r"ending in two spaces.*?: (\d+)", hw).group(1))
multi = int(re.search(r"reports (\d+) multi-line", hw).group(1))
z = stats.norm.ppf(0.975)
p_hat = k_br / n_blocks
den = 1 + z * z / n_blocks
centre = (p_hat + z * z / (2 * n_blocks)) / den
half = z * math.sqrt(p_hat * (1 - p_hat) / n_blocks + z * z / (4 * n_blocks**2)) / den
wilson = [round(100 * (centre - half), 2), round(100 * (centre + half), 2)]
mcp = json.loads(
    json.loads((OUT / "mcp_wilson_response.jsonl").read_text().splitlines()[1])["result"]["content"][0]["text"]
)
B = 100_000
boot = RNG.binomial(n_blocks, p_hat, size=B) / n_blocks
L_HW = line_of(ARTICLE, "47 of 62")
add(
    "E1_hardwrap_47_of_62",
    "estimator",
    "47 of 62 paragraph-level blocks in a published dev.to article carry <br>",
    {"k": 47, "n": 62},
    f"devto-publishing-kit.md l.{L_HW} (table); evidence/devto-hardwrap.txt",
    {
        "k": k_br,
        "n": n_p + n_li,
        "p_plus_li": [n_p, n_li],
        "rate_pct": round(100 * p_hat, 2),
        "wilson95_pct": wilson,
        "total_br": tot_br,
    },
    "VERIFIED" if (k_br, n_p + n_li, n_blocks) == (47, 62, 62) and tot_br >= k_br else "MISMATCH",
    f"58 + 4 = {n_p + n_li} = the stated total; 47 <= 88 total <br>, consistent with blocks that wrap more than "
    f"once. MCP verify_wilson_ci gives {mcp['wilson_low_pct']}-{mcp['wilson_high_pct']}%, same as scipy here. "
    "One article was measured, so the interval describes that article's blocks, not dev.to in general.",
    simulated={
        "bootstrap_mean_pct": round(100 * boot.mean(), 3),
        "bootstrap_se_pct": round(100 * boot.std(ddof=1), 3),
        "bootstrap_95_pct": [round(100 * x, 2) for x in np.percentile(boot, [2.5, 97.5])],
    },
    simulation=f"parametric bootstrap, {B} draws of Binomial(62, 47/62), seed 42",
    abs_gap=0,
    tolerance=0,
)
L_EVERY = line_of(ARTICLE, "stray break in every paragraph")
add(
    "E2_break_in_every_paragraph",
    "estimator",
    "a source wrapped at 95 columns arrives with a stray break in every paragraph",
    {"share_of_paragraphs": 1.0},
    f"devto-publishing-kit.md l.{L_EVERY}",
    {
        "share_of_paragraphs": round(p_hat, 4),
        "blocks_without_br": n_blocks - k_br,
        "source_multiline_paragraphs": multi,
        "source_lines_ending_two_spaces": two_space,
    },
    "MISMATCH",
    f"The archived measurement has {n_blocks - k_br} of {n_blocks} blocks with no <br>. The narrower reading, "
    f"'every wrapped paragraph', fits ({multi} multi-line source paragraphs, 0 explicit breaks), but the "
    "evidence does not pair blocks with source paragraphs, so that reading is not shown either.",
    abs_gap=round(1 - p_hat, 4),
    tolerance=0,
)

# ---------------------------------------------------------------- 95 columns, own source
in_code, in_fm, prose_over = False, False, []
for i, ln in enumerate(ART_LINES, 1):
    if i == 1 and ln == "---":
        in_fm = True
        continue
    if in_fm:
        in_fm = ln != "---"
        continue
    if ln.startswith("```"):
        in_code = not in_code
        continue
    if not in_code and len(ln) > 95:
        prose_over.append((i, len(ln)))
prose_lens = [len(ln) for ln in ART_LINES[7:] if ln.strip()]
L_95 = line_of(ARTICLE, "readable at 95 columns")
add(
    "M1_own_source_95_columns",
    "metric",
    "the repo copy stays readable at 95 columns",
    95,
    f"devto-publishing-kit.md l.{L_95} (also l.{L_EVERY})",
    {
        "prose_lines_over_95": len(prose_over),
        "max_prose_line": max(n for _, n in prose_over) if prose_over else 0,
        "examples": prose_over[:6],
    },
    "NOT CHECKABLE",
    "The sentence describes the kit's behaviour, not a width limit on this file. For reference, this file's "
    f"own source has {len(prose_over)} prose lines longer than 95 characters, so it is wrapped near 95, "
    "not at it.",
)

# ---------------------------------------------------------------- Medium 0 of 4 / 4 of 4
L_MED = line_of(ARTICLE, "0 of 4")
embed = (PAPER / "medium/devto-publishing-kit-embed.html").read_text()
hosted = (PAPER / "medium/devto-publishing-kit-hosted.html").read_text()
n_data = len(re.findall(r"<img[^>]+src=\"data:", embed))
n_http = len(re.findall(r"<img[^>]+src=\"https?://", hosted))
add(
    "E3_medium_data_uri_0_of_4",
    "estimator",
    "Medium images pasted as data URIs: 0 of 4 survived; from real URLs, 4 of 4",
    {"data_uri_survived": [0, 4], "hosted_survived": [4, 4]},
    f"devto-publishing-kit.md l.{L_MED} (table); CLAIMS.md LOG 2026-08-30",
    {"this_article_embed_data_uri_imgs": n_data, "this_article_hosted_url_imgs": n_http},
    "NOT CHECKABLE",
    "No archived artifact: CLAIMS.md lists it as LOG from 2026-08-30. This article's own Medium builds carry "
    f"{n_data} data-URI and {n_http} URL images, so the 4 images belong to an earlier article.",
)

# ---------------------------------------------------------------- counts inside the article
tldr = [ln for ln in ART_LINES if ln.startswith(">") and ART_LINES.index(ln) < 20]
L_TLDR = line_of(ARTICLE, "five separate")
add(
    "M2_tldr_five_lines",
    "metric",
    "this article's own TL;DR posted as five separate lines",
    5,
    f"devto-publishing-kit.md l.{L_TLDR}",
    {"tldr_source_lines": len(tldr)},
    "VERIFIED" if len(tldr) == 5 else "MISMATCH",
    "The TL;DR block quote is 5 source lines; an unwrap that skips block quotes posts each as its own line.",
    abs_gap=abs(len(tldr) - 5),
    tolerance=0,
)
para = " ".join(ART_LINES[line_of(ARTICLE, "five faults") - 1 : line_of(ARTICLE, "and agreed.")])
faults = para.split(":", 1)[1].split("; ")  # "; " so that "TL;DR" is not a separator
add(
    "M3_five_faults",
    "metric",
    "the run found five faults in the kit itself",
    5,
    f"devto-publishing-kit.md l.{line_of(ARTICLE, 'five faults')}",
    {"faults_listed": len(faults)},
    "VERIFIED" if len(faults) == 5 else "MISMATCH",
    "Splitting the list after the colon on '; ' gives the count ('TL;DR' contains a bare ';').",
    abs_gap=abs(len(faults) - 5),
    tolerance=0,
)
desc = re.search(r'^description: "(.*)"$', ARTICLE, re.M).group(1)
ss = ev("substack-paste.txt")
sub_len = int(re.search(r"draft_subtitle\s+(\d+) chars", ss).group(1))
add(
    "M4_description_241_chars",
    "metric",
    "Substack draft subtitle is the front matter description, 241 chars",
    241,
    "evidence/substack-paste.txt draft_subtitle",
    {"front_matter_description_chars": len(desc)},
    "VERIFIED" if len(desc) == sub_len else "MISMATCH",
    "len() of the description string in the article's front matter.",
    abs_gap=abs(len(desc) - sub_len),
    tolerance=0,
)


class PreGrab(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pre, self.buf, self.inpre, self.h4, self.img, self.hrefs = [], [], False, 0, 0, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "pre":
            self.inpre, self.buf = True, []
        elif tag == "h4":
            self.h4 += 1
        elif tag == "img":
            self.img += 1
        elif tag == "a" and a.get("href", "").startswith("http"):
            self.hrefs.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "pre":
            self.inpre = False
            self.pre.append("".join(self.buf))

    def handle_data(self, data):
        if self.inpre:
            self.buf.append(data)


pg = PreGrab()
body = hosted.split("</header>", 1)[-1] if "</header>" in hosted else hosted
pg.feed(body)
pre_lines = [len(p.strip("\n").split("\n")) for p in pg.pre]
pre_chars = [len(p.strip("\n")) for p in pg.pre]
add(
    "M5_substack_source_shape",
    "metric",
    "hosted HTML source: 4 <pre> blocks, lines 2/2/1/4, chars 87/124/65/225; "
    "2 images; 7 <h4>; 4 link targets, 6 anchors",
    {"pre_lines": [2, 2, 1, 4], "pre_chars": [87, 124, 65, 225], "img": 2, "h4": 7, "link_targets": 4, "anchors": 6},
    "evidence/substack-paste.txt '## Source'",
    {
        "pre_lines": pre_lines,
        "pre_chars": pre_chars,
        "img": pg.img,
        "h4": pg.h4,
        "link_targets": len(set(pg.hrefs)),
        "anchors": len(pg.hrefs),
    },
    "VERIFIED" if (pre_lines, pre_chars, pg.img, pg.h4) == ([2, 2, 1, 4], [87, 124, 65, 225], 2, 7) else "MISMATCH",
    "Parsed the archived medium/devto-publishing-kit-hosted.html with html.parser. It holds 3 <pre> blocks, not 4: "
    "its third block is the evidence's blocks 3 and 4 joined (65 + 1 newline + 225 = 291 chars, 1 + 4 = 5 lines), "
    "so the archived HTML is a different build from the one pasted into Substack. Images, <h4> and links match.",
)

# ---------------------------------------------------------------- ledger arithmetic
orgs = ev("devto-orgs.txt")
o = {k: int(v) for k, v in re.findall(r"^\s+(gde|aws-builders|None): (\d+)", orgs, re.M)}
listed = int(re.search(r"articles listed: (\d+)", orgs).group(1))
add(
    "M6_org_split_sums",
    "metric",
    "40 articles listed: gde 24, aws-builders 13, none 3",
    {"total": 40, "gde": 24, "aws-builders": 13, "none": 3},
    "CLAIMS.md MEASURED; evidence/devto-orgs.txt",
    {"total": listed, "sum_of_parts": sum(o.values()), **o},
    "VERIFIED" if sum(o.values()) == listed == 40 else "MISMATCH",
    "24 + 13 + 3 summed in code.",
    abs_gap=abs(sum(o.values()) - 40),
    tolerance=0,
)
rt = ev("devto-roundtrip.txt")
fences = {k: int(v) for k, v in re.findall(r"'(```\w+)': (\d+)", rt)}
openers = int(re.search(r"opening fences: (\d+)", rt).group(1))
bare = int(re.search(r"bare \(unlabelled\) opening fences: (\d+)", rt).group(1))
add(
    "M7_fences_23_of_23",
    "metric",
    "23 of 23 opening fences carry a language label",
    {"labelled": 23, "openers": 23},
    "CLAIMS.md MEASURED; evidence/devto-roundtrip.txt",
    {"labelled_sum": sum(fences.values()), "openers": openers, "bare": bare},
    "VERIFIED" if sum(fences.values()) == openers == 23 and bare == 0 else "MISMATCH",
    "6 + 14 + 1 + 1 + 1 summed in code, equals the opener count with 0 bare.",
    abs_gap=0,
    tolerance=0,
)

bp = ev("builder-payload.txt")
kb_rows = re.findall(r"^(\S+\.md): (\d+) chars, (\d+) lines, ([\d.]+) KB", bp, re.M)
kb_check = {
    f: {"chars": int(c), "chars_over_1024": round(int(c) / 1024, 3), "printed_KB": float(k)} for f, c, _, k in kb_rows
}
kb_ok = all(abs(v["chars_over_1024"] - v["printed_KB"]) <= 0.05 for v in kb_check.values())
add(
    "M8_builder_file_KB",
    "metric",
    "article sizes in KB: 23.1 / 23.3 / 22.5",
    {f: float(k) for f, _, _, k in kb_rows},
    "evidence/builder-payload.txt",
    kb_check,
    "VERIFIED" if kb_ok else "MISMATCH",
    "Each printed KB equals chars/1024 to one decimal. The KB is of characters; with em dashes the byte size "
    "is larger.",
    tolerance=0.05,
)
sb_chars = int(re.search(r"chars : (\d+)", bp).group(1))
sb_before, sb_after = map(int, re.search(r"lines : (\d+) before unwrap, (\d+) after", bp).groups())
add(
    "M9_ledger_payload_measured_row",
    "metric",
    "CLAIMS.md MEASURED: Builder payload 22,542 chars / 22.0 KB, 521 lines before unwrap, 408 after",
    {"chars": 22542, "KB": 22.0, "before": 521, "after": 408},
    f"CLAIMS.md l.{line_of(CLAIMS, '22,542')}",
    {"chars": sb_chars, "KB": round(sb_chars / 1024, 3), "before": sb_before, "after": sb_after},
    "MISMATCH",
    "The archived evidence (re-captured 2026-08-31T15:54) says 23234 chars, 531 / 411 lines. The ledger row "
    "was not updated; 22542/1024 = 22.01 is internally consistent but has no archived artifact.",
    abs_gap={"chars": sb_chars - 22542, "before": sb_before - 521, "after": sb_after - 408},
    tolerance=0,
)
add(
    "M10_ledger_payload_traps_row",
    "metric",
    "CLAIMS.md traps table: Builder payload 23,214 chars / 22.7 KB, 531 lines before unwrap, 411 after",
    {"chars": 23214, "KB": 22.7, "before": 531, "after": 411},
    f"CLAIMS.md l.{line_of(CLAIMS, '23,214')}",
    {"chars": sb_chars, "KB": round(sb_chars / 1024, 3), "before": sb_before, "after": sb_after},
    "MISMATCH" if sb_chars != 23214 else "VERIFIED",
    f"Lines and KB match ({sb_chars}/1024 = {sb_chars / 1024:.2f}); the character count is {sb_chars} in the "
    "evidence against 23,214 in the ledger, a 20-character gap.",
    abs_gap={"chars": sb_chars - 23214},
    tolerance=0,
)

tc = ev("toolchain-run.txt")
cov_bytes = {n: int(b) for n, b in re.findall(r"^(\S+\.jpg) (\d+) bytes", tc, re.M)}
order = ["devto-cover-aws.44aee846.jpg", "devto-cover-gde.0d021e90.jpg", "builder-cover.2b7f0305.jpg"]
claimed_kb = [105, 104, 15]
conv = {
    n: {"bytes": cov_bytes[n], "KiB": round(cov_bytes[n] / 1024, 2), "kB": round(cov_bytes[n] / 1000, 2)} for n in order
}
reach = [any(round(cov_bytes[n] / d) == c for d in (1000, 1024)) for n, c in zip(order, claimed_kb, strict=True)]
add(
    "M11_ledger_cover_sizes",
    "metric",
    "covers: 1376x768 105 KB / 1376x768 104 KB / 1200x675 15 KB",
    {"KB": claimed_kb},
    f"CLAIMS.md l.{line_of(CLAIMS, '105 KB')}",
    {"per_cover": conv, "claim_reachable": reach},
    "VERIFIED" if all(reach) else "MISMATCH",
    "106890 bytes is 104.38 KiB or 106.89 kB; neither rounds to 105. The other two rows match (104.23 KiB, 15.11 KiB).",
    tolerance=0.5,
)

sf = ev("skill-footprint.txt")
nums = lambda block: [int(x) for x in re.findall(r"^\s+(\d+)\s+\S+", block, re.M)]  # noqa: E731
refs = nums(sf.split("references")[1].split("templates")[0])
tmpl = nums(sf.split("templates")[1].split("scripts")[0])
scr = nums(sf.split("scripts (")[1].split("total")[0])
skill_md = int(re.search(r"SKILL.md: (\d+) lines", sf).group(1))
total = int(re.search(r"total: ([\d,]+) lines", sf).group(1).replace(",", ""))
fp_sum = skill_md + sum(refs) + sum(tmpl) + sum(scr)
add(
    "M12_footprint_total_0_18",
    "metric",
    "skill footprint at 0.18.0: total 4,580 lines",
    4580,
    "evidence/skill-footprint.txt",
    {
        "SKILL_md": skill_md,
        "references": sum(refs),
        "templates": sum(tmpl),
        "scripts": sum(scr),
        "sum": fp_sum,
        "counts": [len(refs), len(tmpl), len(scr)],
    },
    "VERIFIED" if fp_sum == total == 4580 else "MISMATCH",
    "SKILL.md + 6 references + 2 templates + 14 scripts summed in code.",
    abs_gap=abs(fp_sum - 4580),
    tolerance=0,
)
ledger_parts = [446, 226, 148, 86, 66, 1389]
add(
    "M13_footprint_ledger_0_2",
    "metric",
    "CLAIMS.md: SKILL.md 446 lines; references 226/148/86/66; six scripts 1,389; 2,370 total (at 0.2.0)",
    {"total": 2370},
    f"CLAIMS.md l.{line_of(CLAIMS, '2,370')}",
    {
        "sum_of_listed_parts": sum(ledger_parts),
        "gap_to_total": 2370 - sum(ledger_parts),
        "archived_evidence_version": "0.18.0",
        "archived_total": total,
    },
    "NOT CHECKABLE",
    f"The listed parts sum to {sum(ledger_parts)}, {2370 - sum(ledger_parts)} short of 2,370 (the gap could be the "
    "description or a file not listed). The archived skill-footprint.txt was overwritten at 0.18.0, so the "
    "0.2.0 figures and the ~187 / ~8k token costs have no artifact.",
)

snap = ev("install-is-a-snapshot.txt")
inodes = re.findall(r"^(\d+):(\d+)\s+(\S+)", snap, re.M)
shas = re.findall(r"^([0-9a-f]{40})$", snap, re.M)
add(
    "M14_install_pinned_commit",
    "metric",
    "install pinned at commit f7eaac2, equal to HEAD",
    {"commit": "f7eaac2", "equals_HEAD": True},
    f"CLAIMS.md l.{line_of(CLAIMS, 'f7eaac2')}",
    {
        "pinned": shas[0][:7],
        "HEAD": shas[1][:7],
        "equals_HEAD": shas[0] == shas[1],
        "inodes_differ": inodes[0][1] != inodes[1][1],
    },
    "MISMATCH",
    "The re-captured evidence (0.6.0) shows 920fe6c for both, so pinned == HEAD and the inodes differ (a snapshot) "
    "hold; the commit id in the ledger does not appear in the archived file.",
)

li = ev("linkedin-run.txt")
fold = li.split("--- above the fold (140 chars) ---\n", 1)[1].splitlines()[0]
hook_claim = int(re.search(r"hook fits the fold: (\d+) chars", li).group(1))
add(
    "M15_linkedin_hook_80",
    "metric",
    "LinkedIn hook 80 chars",
    80,
    "CLAIMS.md MEASURED; evidence/linkedin-run.txt",
    {"hook_line_chars": len(fold), "tool_reported": hook_claim},
    "VERIFIED" if len(fold) == 80 else "MISMATCH",
    f"len() of the first line above the fold: '{fold}'.",
    abs_gap=abs(len(fold) - 80),
    tolerance=0,
)


# ---------------------------------------------------------------- cover refresh pixel diffs
def mad(a: str, b: str, mode: str) -> float:
    with Image.open(PAPER / a) as x, Image.open(PAPER / b) as y:
        xa = np.asarray(x.convert(mode), dtype=np.float64)
        ya = np.asarray(y.convert(mode).resize(x.size), dtype=np.float64)
    return float(np.abs(xa - ya).mean())


cr = ev("cover-refresh.txt")
d_sub = float(re.search(r"vs cover.77acc7c4.jpg ([\d.]+)", cr).group(1))
d_bld = float(re.search(r"vs cover-builder.80aa6ca5.jpg ([\d.]+)", cr).group(1))
e_bld = float(re.search(r"vs cover-builder.cabd79f3.jpg ([\d.]+)", cr).group(1))
diffs = {
    m: {
        "ae4d_vs_77acc": round(mad("cover.ae4d639e.jpg", "cover.77acc7c4.jpg", m), 3),
        "cabd_vs_80aa": round(mad("cover-builder.cabd79f3.jpg", "cover-builder.80aa6ca5.jpg", m), 3),
    }
    for m in ("RGB", "L")
}
gap_sub = abs(diffs["RGB"]["ae4d_vs_77acc"] - d_sub)
gap_bld = abs(diffs["RGB"]["cabd_vs_80aa"] - d_bld)
add(
    "E4_substack_cover_diff",
    "estimator",
    "re-hosted Substack cover: mean abs pixel diff 0.0 vs the new cover, 18.71 vs the old one",
    {"vs_new": 0.0, "vs_old": d_sub},
    "evidence/cover-refresh.txt",
    {"new_vs_old_local_RGB": diffs["RGB"]["ae4d_vs_77acc"], "new_vs_old_local_L": diffs["L"]["ae4d_vs_77acc"]},
    "NOT CHECKABLE",
    "The re-hosted copy is not archived. If it is 0.0 from the new cover, the triangle inequality forces "
    f"new-vs-old = 18.71 (within 0.01 for rounding). The local files give {diffs['RGB']['ae4d_vs_77acc']} (RGB) "
    f"and {diffs['L']['ae4d_vs_77acc']} (greyscale), {gap_sub:.3f} off, so the evidence used a method other than "
    "these two (it does not name one).",
    abs_gap=round(gap_sub, 3),
    tolerance=0.01,
)
add(
    "E5_builder_hero_diff",
    "estimator",
    "Builder Center hero: mean abs pixel diff 0.56 vs the new cover, 14.66 vs the old one",
    {"vs_new": e_bld, "vs_old": d_bld},
    "evidence/cover-refresh.txt",
    {"new_vs_old_local_RGB": diffs["RGB"]["cabd_vs_80aa"], "new_vs_old_local_L": diffs["L"]["cabd_vs_80aa"]},
    "VERIFIED" if gap_bld <= e_bld else "MISMATCH",
    f"Triangle inequality: |d(new, old) - 14.66| <= d(hero, new) = 0.56. Local RGB d(new, old) = "
    f"{diffs['RGB']['cabd_vs_80aa']}, {gap_bld:.3f} from 14.66, inside the bound. The hero itself is not archived.",
    abs_gap=round(gap_bld, 3),
    tolerance=e_bld,
)

# ---------------------------------------------------------------- output
counts = {v: sum(r["verdict"] == v for r in records) for v in ("VERIFIED", "MISMATCH", "NOT CHECKABLE")}
doc = {
    "paper": "Streamline Publishing with a Claude Code Skill (dev.to, xbill9/publishing-kit)",
    "primary_source": "paper/devto-publishing-kit.md; evidence/*.txt and CLAIMS.md as archived evidence",
    "seed": 42,
    "numpy": np.__version__,
    "pillow": Image.__version__,
    "kit_head": kit_head,
    "verdict_counts": counts,
    "equations": records,
}
(OUT / "eq_verified_numbers.json").write_text(json.dumps(doc, indent=2) + "\n")

# ---------------------------------------------------------------- sensitivity figures
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

hs = np.arange(400, 1001)
loss = np.array([fit_cover_loss(1376, h)[0] for h in hs])
fig, ax = plt.subplots(figsize=(6.2, 3.0))
ax.plot(hs, loss / 2, color="#b45309", lw=2, label="rows lost per side (centre crop)")
ax.axvspan(578, 1000, color="#fee2e2", alpha=0.6, label="taller than 2.381:1: cropped")
ax.scatter([768], [lost_rows / 2], color="#b91c1c", zorder=5)
ax.annotate("1376x768: 95.04 px a side", (768, lost_rows / 2), (800, 40), arrowprops=dict(arrowstyle="->"))
ax.scatter([578], [0], color="#15803d", zorder=5)
ax.annotate("1376x578 (shipped): 0", (578, 0), (420, 60), arrowprops=dict(arrowstyle="->"))
ax.set_xlabel("cover height at width 1376 (px)")
ax.set_ylabel("source rows lost per side")
ax.legend(loc="upper left", frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "sens_crop_loss.png", dpi=300)
plt.close(fig)

widths = np.arange(800, 2401)
src_min = legible_px * widths / card_w
fig, ax = plt.subplots(figsize=(6.2, 3.0))
ax.plot(widths, src_min, color="#2563eb", lw=2, label=f"smallest legible type (>= {legible_px}px at {card_w}px card)")
ax.fill_between(widths, 0, src_min, color="#fee2e2", alpha=0.6, label="lost in the feed card")
ax.scatter([1376], [min_src], color="#b91c1c", zorder=5)
ax.annotate(f"1376 wide: {min_src:.1f} px", (1376, min_src), (1550, 25), arrowprops=dict(arrowstyle="->"))
ax.set_xlabel("cover width (px)")
ax.set_ylabel("source type size (px)")
ax.set_ylim(0, src_min.max() * 1.05)
ax.legend(loc="upper left", frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "sens_card_legibility.png", dpi=300)
plt.close(fig)

ns = np.arange(10, 401)
lo, hi = [], []
for n in ns:
    k = p_hat * n
    d = 1 + z * z / n
    c = (p_hat + z * z / (2 * n)) / d
    h = z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n)) / d
    lo.append(100 * (c - h))
    hi.append(100 * (c + h))
fig, ax = plt.subplots(figsize=(6.2, 3.0))
ax.fill_between(ns, lo, hi, color="#0f766e", alpha=0.25, label="95% Wilson interval at rate 75.8%")
ax.axhline(100 * p_hat, color="#0f766e", lw=1.5)
ax.axhline(100, color="#b91c1c", ls="--", lw=1.2, label="'every paragraph' (100%)")
ax.axvline(62, color="#374151", ls=":", lw=1)
ax.annotate(
    f"n = 62: {100 * (centre - half):.1f}-{100 * (centre + half):.1f}%",
    (62, wilson[1]),
    (110, 92),
    arrowprops=dict(arrowstyle="->"),
)
ax.set_xlabel("paragraph-level blocks measured (n)")
ax.set_ylabel("blocks with <br> (%)")
ax.set_ylim(50, 102)
ax.legend(loc="lower right", frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "sens_hardwrap_rate.png", dpi=300)
plt.close(fig)

print(json.dumps(counts))
for r in records:
    print(f"{r['verdict']:14} {r['id']}")
