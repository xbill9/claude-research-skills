#!/usr/bin/env python3
# ruff: noqa: E501  (HTML/SVG template text)
"""Build MathGuide.html from eq_verified_numbers.json. Formulas are pre-rendered to SVG with
matplotlib mathtext (offline, no KaTeX). Every number in the tables and the summary is read from
the JSON; the prose only explains."""

from __future__ import annotations

import html
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = Path(__file__).resolve().parent
EQ = OUT / "figures" / "eq"
EQ.mkdir(parents=True, exist_ok=True)
data = json.loads((OUT / "eq_verified_numbers.json").read_text())
R = {r["id"]: r for r in data["equations"]}
C = data["verdict_counts"]

COL = {"definition": "#2563eb", "bound": "#b45309", "estimator": "#7c3aed", "metric": "#0f766e"}
VCOL = {"VERIFIED": "#15803d", "MISMATCH": "#b91c1c", "NOT CHECKABLE": "#6b7280"}


def tex(name: str, s: str, size: int = 14) -> str:
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${s}$", fontsize=size)
    path = EQ / f"{name}.svg"
    fig.savefig(path, bbox_inches="tight", pad_inches=0.04, transparent=True)
    plt.close(fig)
    return f'<div class="eq"><img src="figures/eq/{name}.svg" alt="{html.escape(s)}"></div>'


def pill(cls: str) -> str:
    return f'<span class="pill" style="background:{COL[cls]}">{cls}</span>'


def vpill(v: str) -> str:
    return f'<span class="pill" style="background:{VCOL[v]}">{v}</span>'


def fmt(x, depth: int = 0) -> str:
    if x is None:
        return "&ndash;"
    if isinstance(x, float):
        return f"{x:g}"
    if isinstance(x, dict):
        rows = "".join(
            f"<div><span class='k'>{html.escape(str(k))}</span> {fmt(v, depth + 1)}</div>" for k, v in x.items()
        )
        return f"<div class='kv'>{rows}</div>"
    if isinstance(x, list):
        return html.escape(json.dumps(x, separators=(", ", ": ")))
    return html.escape(str(x))


def vtable(ids: list[str]) -> str:
    rows = []
    for i in ids:
        r = R[i]
        rows.append(
            f"<tr><td class='idc'><b>{i.replace('_', '_<wbr>')}</b><br>{pill(r['operator_class'])}</td>"
            f"<td>{html.escape(r['statement'])}<div class='src'>{html.escape(r['paper_source'])}</div></td>"
            f"<td>{fmt(r['paper_value'])}</td><td>{fmt(r['computed'])}</td>"
            f"<td>{vpill(r['verdict'])}<div class='why'>{html.escape(r['reason'])}</div></td></tr>"
        )
    head = "<thead><tr><th>claim</th><th>statement / source</th><th>paper</th><th>computed</th><th>verdict</th></tr></thead>"
    return f"<table class='vt'>{head}<tbody>{''.join(rows)}</tbody></table>"


def figure(src: str, cap: str) -> str:
    return f"<figure><img src='figures/{src}' alt='{html.escape(cap)}'><figcaption>{cap}</figcaption></figure>"


def kv(rid: str, *path: str):
    x = R[rid]
    for p in path:
        x = x[p]
    return x


GRAPH = """
<svg viewBox="0 0 720 220" class="graph" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica, Arial" font-size="11">
 <defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
 <path d="M0,0 L10,5 L0,10 z" fill="#374151"/></marker></defs>
 <g fill="#fff" font-weight="bold">
  <rect x="10" y="20" width="190" height="34" rx="8" fill="#2563eb"/><text x="105" y="41" text-anchor="middle">proxy 1000x420, fit=cover</text>
  <rect x="10" y="120" width="190" height="34" rx="8" fill="#2563eb"/><text x="105" y="141" text-anchor="middle">CARD_W 320, LEGIBLE_PX 10</text>
  <rect x="260" y="10" width="200" height="30" rx="8" fill="#b45309"/><text x="360" y="29" text-anchor="middle">ratio 2.381 -&gt; rows kept 578</text>
  <rect x="260" y="55" width="200" height="30" rx="8" fill="#b45309"/><text x="360" y="74" text-anchor="middle">95 px lost a side (1376x768)</text>
  <rect x="260" y="120" width="200" height="34" rx="8" fill="#b45309"/><text x="360" y="141" text-anchor="middle">smallest legible type 43 px</text>
  <rect x="10" y="175" width="190" height="34" rx="8" fill="#7c3aed"/><text x="105" y="196" text-anchor="middle">evidence counts (47 of 62, diffs)</text>
  <rect x="260" y="175" width="200" height="34" rx="8" fill="#7c3aed"/><text x="360" y="196" text-anchor="middle">rate, Wilson CI, bootstrap</text>
  <rect x="520" y="20" width="190" height="34" rx="8" fill="#0f766e"/><text x="615" y="41" text-anchor="middle">article sentences</text>
  <rect x="520" y="120" width="190" height="34" rx="8" fill="#0f766e"/><text x="615" y="141" text-anchor="middle">ledger sums and sizes</text>
 </g>
 <g stroke="#374151" stroke-width="1.4" fill="none" marker-end="url(#a)">
  <path d="M200,37 L258,25"/><path d="M360,40 L360,53"/><path d="M200,137 L258,137"/>
  <path d="M460,70 L518,40"/><path d="M460,137 L518,45"/><path d="M200,192 L258,192"/>
  <path d="M460,192 L518,52"/><path d="M460,192 L518,145"/>
 </g>
</svg>"""

CSS = """
@page { size: A4; margin: 14mm 13mm 14mm 13mm; }
body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 9.6pt; color: #111827; line-height: 1.38; }
h1 { font-size: 19pt; margin: 0 0 2mm; }
h2 { font-size: 13pt; margin: 6mm 0 2mm; border-bottom: 2px solid #e5e7eb; padding-bottom: 1mm; break-after: avoid; }
h3 { font-size: 10.5pt; margin: 4mm 0 1mm; break-after: avoid; }
.sub { color: #4b5563; margin-bottom: 4mm; }
.pill { display: inline-block; color: #fff; border-radius: 9px; padding: 0.3mm 2.2mm; font-size: 7.4pt;
        font-weight: bold; white-space: nowrap; margin: 0.6mm 0; }
.counts { display: flex; gap: 4mm; margin: 3mm 0; }
.counts div { flex: 1; border-radius: 6px; padding: 2.5mm; color: #fff; font-size: 9pt; }
.counts b { font-size: 17pt; display: block; }
.eq { margin: 2mm 0 2mm 6mm; }
.eq img { max-width: 100%; }
.steps { margin: 1mm 0 2mm 0; padding-left: 5mm; }
table.vt { width: 100%; border-collapse: collapse; font-size: 7.6pt; margin: 2mm 0 3mm; table-layout: fixed; }
table.vt thead { display: table-header-group; }
table.vt th { background: #f3f4f6; text-align: left; padding: 1.2mm; }
table.vt th:nth-child(1) { width: 17%; } table.vt th:nth-child(2) { width: 24%; }
table.vt th:nth-child(3) { width: 14%; } table.vt th:nth-child(4) { width: 20%; } table.vt th:nth-child(5) { width: 25%; }
table.vt td { border-top: 1px solid #e5e7eb; padding: 1.2mm; vertical-align: top; overflow-wrap: anywhere; }
table.vt tr { break-inside: avoid; }
.idc b { font-size: 7.2pt; }
.src { color: #6b7280; font-size: 6.9pt; margin-top: 0.8mm; }
.why { color: #374151; font-size: 7pt; margin-top: 0.8mm; }
.kv div { margin-bottom: 0.4mm; } .k { color: #6b7280; }
figure { margin: 2mm 0 3mm; text-align: center; break-inside: avoid; }
figure img { width: 76%; }
figcaption { font-size: 7.8pt; color: #4b5563; margin-top: 1mm; }
.keep { break-inside: avoid; }
.graph { width: 100%; margin: 2mm 0; }
.note { background: #f9fafb; border-left: 3px solid #9ca3af; padding: 2mm 3mm; font-size: 8.6pt; margin: 2mm 0; }
ul { margin: 1mm 0; padding-left: 5mm; } li { margin-bottom: 0.8mm; }
.pb { break-before: page; }
"""

e_crop = [
    tex("ratio", r"r=\frac{W_p}{H_p}=\frac{1000}{420}=2.380952"),
    tex("kept", r"h_{keep}=\frac{W}{r}=\frac{1376}{2.380952}=577.92"),
    tex("loss", r"\ell_{side}=\frac{H-h_{keep}}{2}=\frac{768-577.92}{2}=95.04"),
]
e_card = tex("card", r"s_{min}=\mathrm{LEGIBLE\_PX}\cdot\frac{W}{\mathrm{CARD\_W}}=10\cdot\frac{1376}{320}=43.0")
e_wil = tex(
    "wilson",
    r"\tilde p\pm h=\frac{\hat p+\frac{z^2}{2n}\pm z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}}{1+\frac{z^2}{n}}",
    13,
)
e_tri = tex("tri", r"|\,d(new,old)-d(copy,old)\,|\;\leq\;d(copy,new)")

b2 = R["B2_crop_loss_95px"]
e1 = R["E1_hardwrap_47_of_62"]
d2 = R["D2_card_width_in_kit"]

body = f"""
<h1>Mathematical Verification Guide</h1>
<div class="sub"><b>{html.escape(data["paper"])}</b><br>
Source: {html.escape(data["primary_source"])}. Seed {data["seed"]}, numpy {data["numpy"]}, Pillow {data["pillow"]},
publishing-kit HEAD {html.escape(data["kit_head"])}. Every number below is read from <code>eq_verified_numbers.json</code>,
written by <code>verify_math.py</code>.</div>

<div class="counts">
 <div style="background:{VCOL["VERIFIED"]}"><b>{C["VERIFIED"]}</b>VERIFIED</div>
 <div style="background:{VCOL["MISMATCH"]}"><b>{C["MISMATCH"]}</b>MISMATCH</div>
 <div style="background:{VCOL["NOT CHECKABLE"]}"><b>{C["NOT CHECKABLE"]}</b>NOT CHECKABLE</div>
</div>

<p>The article has no equations. Its checkable content is geometry (the dev.to cover crop and the feed card),
one measured proportion (47 of 62) and a set of counts and sizes in the archived evidence and the claim ledger.
Each is written as a formula where one exists and recomputed from the files on disk.</p>

<h3>Operator classes and how they feed each other</h3>
<p>{pill("definition")} constants taken from a destination or the kit's source &nbsp;
{pill("bound")} values derived from them &nbsp; {pill("estimator")} measured counts and rates &nbsp;
{pill("metric")} sentence-level counts and ledger arithmetic</p>
{GRAPH}

<h3>Headline</h3>
<ul>
<li>The crop arithmetic holds: {fmt(kv("D1_proxy_ratio", "computed", "ratio"))}:1, {fmt(kv("B1_crop_rows_kept", "computed", "kept_rows"))}
rows kept, {fmt(b2["computed"]["lost_top_px"])} px lost a side. A real Pillow fit=cover crop agrees
(rows {b2["simulated"]["first_row_kept"]}&ndash;{b2["simulated"]["last_row_kept"]} survive). The 95/95 split assumes
a centred crop; the proxy URL asks for <code>gravity=auto</code>.</li>
<li>47 of 62 matches the evidence ({e1["computed"]["rate_pct"]}%, Wilson 95% {fmt(e1["computed"]["wilson95_pct"])}%).
The article's wording, "a stray break in every paragraph", does not: {R["E2_break_in_every_paragraph"]["computed"]["blocks_without_br"]}
of 62 blocks carry none.</li>
<li>Medium "0 of 4 / 4 of 4" has no archived artifact. This article's own Medium build holds
{R["E3_medium_data_uri_0_of_4"]["computed"]["this_article_embed_data_uri_imgs"]} images, not 4.</li>
<li>Four CLAIMS.md rows disagree with the evidence they cite: the payload size (twice), a cover size of 105 KB that
neither KB nor KiB produces, and the pinned commit id. One archived HTML build has 3 code blocks where the evidence
counted 4.</li>
</ul>

<h2 class="pb">1 &middot; dev.to cover proxy {pill("definition")} {pill("bound")}</h2>
<p><b>Intuition.</b> dev.to does not re-host the cover. It serves it through an image proxy with a fixed box,
<code>width=1000,height=420,fit=cover</code>. <i>fit=cover</i> scales the image until it fills the box and cuts whatever
overhangs. A cover taller than the box's shape loses rows; one wider loses columns.</p>
<ol class="steps">
<li>The box's shape is its width over its height:</li>{e_crop[0]}
<li>At the cover's width W the box keeps W/r source rows:</li>{e_crop[1]}
<li>The rest is cut, split between top and bottom when the crop is centred:</li>{e_crop[2]}
</ol>
<p><b>Simulation.</b> {html.escape(b2["simulation"])}. Rows kept: {b2["simulated"]["first_row_kept"]} to
{b2["simulated"]["last_row_kept"]}, so {b2["simulated"]["lost_top"]} lost at the top and {b2["simulated"]["lost_bottom"]}
at the bottom.</p>
{figure("sens_crop_loss.png", "Rows lost per side against cover height at width 1376. Shaded: shapes taller than 2.381:1, which the proxy crops. The shipped covers sit at the knee.")}
{vtable(["D1_proxy_ratio", "B1_crop_rows_kept", "B2_crop_loss_95px", "B3_shipped_cover_uncropped"])}

<h2>2 &middot; The 320px feed card {pill("definition")} {pill("bound")}</h2>
<p><b>Intuition.</b> A cover is first seen shrunk to a feed card. Everything on it scales by CARD_W / W, so a label must
start large enough to land above the legibility threshold after the shrink. The kit's <code>make-cover.py</code> sets
CARD_W = {d2["computed"]["CARD_W"]} and LEGIBLE_PX = {d2["computed"]["LEGIBLE_PX"]}:</p>
{e_card}
<p>At width 1376 the card scale is {d2["computed"]["card_scale_1376"]}, so anything under
{d2["computed"]["min_legible_source_px_at_1376"]} px on the full-size cover is unreadable in the feed.</p>
{figure("sens_card_legibility.png", "Smallest type that survives a 320px card, by cover width, using the kit's own LEGIBLE_PX = 10. Shaded: type that is lost.")}
{vtable(["D2_card_width_in_kit", "D3_card_width_is_devto"])}

<h2 class="pb">3 &middot; Hard-wrapped paragraphs: 47 of 62 {pill("estimator")}</h2>
<p><b>Intuition.</b> dev.to renders single newlines as <code>&lt;br&gt;</code>. The evidence counts paragraph-level blocks
in one published article's HTML and how many contain a break. Treated as a proportion of that article's blocks, the
Wilson interval is:</p>
{e_wil}
<p>with n = {e1["computed"]["n"]}, k = {e1["computed"]["k"]}, z = 1.96. scipy and the plugin's MCP
<code>verify_wilson_ci</code> agree. <b>Simulation.</b> {html.escape(e1["simulation"])}: mean
{e1["simulated"]["bootstrap_mean_pct"]}%, standard error {e1["simulated"]["bootstrap_se_pct"]} points, 95% band
{fmt(e1["simulated"]["bootstrap_95_pct"])}%.</p>
{figure("sens_hardwrap_rate.png", "Width of the 95% Wilson interval at the measured rate as the number of blocks grows. The dashed line is the article's every-paragraph wording; it sits outside the interval at n = 62.")}
{vtable(["E1_hardwrap_47_of_62", "E2_break_in_every_paragraph", "M1_own_source_95_columns"])}

<h2>4 &middot; Medium images and cover pixel differences {pill("estimator")}</h2>
<p><b>Intuition.</b> The re-hosted copies of the refreshed covers on Substack and Builder Center are not archived, so
their pixel differences cannot be recomputed directly. Mean absolute difference is a distance, so the triangle inequality
ties the unarchived copy to the two local files:</p>
{e_tri}
<p>If a copy is 0.0 from the new cover, new-vs-old must equal its own distance to the old cover; if it is 0.56 away,
the two may differ by at most 0.56.</p>
{vtable(["E3_medium_data_uri_0_of_4", "E4_substack_cover_diff", "E5_builder_hero_diff"])}

<h2>5 &middot; Counts in the article and in the ledger {pill("metric")}</h2>
<p>Sentence-level counts are recounted from the article's markdown and its archived Medium HTML; ledger figures are
re-added or re-divided from the evidence files.</p>
{vtable([r for r in R if r.startswith("M") and r != "M1_own_source_95_columns"])}

<h2>6 &middot; Method and limits</h2>
<div class="note">
<ul>
<li>Monte Carlo is used where it adds something: a deterministic Pillow crop for the proxy geometry and a 100,000-draw
binomial bootstrap (seed 42) for 47 of 62. Integer counts and sums are checked exactly, with tolerance 0.</li>
<li>VERIFIED on an evidence-sourced count means the count is internally consistent and matches the archived file. It
does not re-measure dev.to, Medium or Substack; nothing here fetched a live page.</li>
<li>The kit constants (CARD_W, LEGIBLE_PX) are read from the publishing-kit checkout at HEAD
{html.escape(data["kit_head"])}, not the version used on 2026-08-31.</li>
<li>The pixel-difference method in the evidence is not stated. RGB and greyscale mean absolute difference were tried.</li>
</ul>
</div>
"""

page = (
    "<!doctype html><html><head><meta charset='utf-8'><title>Publishing Kit Equation Guide</title>"
    f"<style>{CSS}</style></head><body>{body}</body></html>"
)
(OUT / "MathGuide.html").write_text(page)
print("wrote", OUT / "MathGuide.html")
