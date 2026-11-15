#!/usr/bin/env python3
"""Build MathGuide.html from eq_verified_numbers.json. Equations are pre-rendered with
matplotlib mathtext (offline, no KaTeX download). Every number in the verdict tables is read
from the JSON; the prose only explains."""

from __future__ import annotations

import html
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
EQ = OUT / "figures" / "eq"
EQ.mkdir(parents=True, exist_ok=True)
data = json.loads((OUT / "eq_verified_numbers.json").read_text())
R = {r["id"]: r for r in data["equations"]}

COL = {"definition": "#2563eb", "bound": "#b45309", "estimator": "#7c3aed", "metric": "#0f766e"}
VCOL = {"VERIFIED": "#15803d", "MISMATCH": "#b91c1c", "NOT CHECKABLE": "#6b7280"}


def tex(name: str, s: str, size: int = 15) -> str:
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


def fmt(x) -> str:
    if x is None:
        return "&ndash;"
    if isinstance(x, float):
        return f"{x:.4g}"
    if isinstance(x, (dict, list)):
        return f"<code>{html.escape(json.dumps(x, separators=(', ', ': ')))}</code>"
    return html.escape(str(x))


def vtable(ids: list[str]) -> str:
    rows = []
    for i in ids:
        r = R[i]
        rows.append(
            f"<tr><td><b>{i}</b><br>{pill(r['operator_class'])}</td><td>{fmt(r['paper_value'])}<div class='src'>{html.escape(r['paper_source'])}</div></td>"
            f"<td>{fmt(r['computed'])}</td><td>{fmt(r['simulated'])}"
            + (f"<div class='src'>{html.escape(r['simulation'])}</div>" if r["simulation"] else "")
            + f"</td><td>{fmt(r['abs_gap'])}<br><span class='src'>tol {fmt(r['tolerance'])}</span></td>"
            f"<td>{vpill(r['verdict'])}<div class='src'>{html.escape(r['reason'])}</div></td></tr>")
    return ("<table class='vt'><tr><th>id</th><th>paper value (source)</th><th>computed</th><th>simulated</th>"
            "<th>|gap|</th><th>verdict / reason</th></tr>" + "".join(rows) + "</table>")


def card(title, cls, body, ids=None, fig=None, cap=""):
    s = f"<section class='card'><div class='keep'><h2>{title} {pill(cls)}</h2>{body}"
    if fig:
        s += f"<figure><img src='figures/{fig}' alt='{html.escape(cap)}'><figcaption>{cap}</figcaption></figure>"
    s += "</div>"
    if ids:
        s += vtable(ids)
    return s + "</section>"


vc = data["verdict_counts"]
legend = " ".join(pill(c) for c in COL)
rate_ids = [i for i in R if i.startswith("E6_rate_")] + ["E6b_md_M6_24.1"]
rate_rows = "".join(
    f"<tr><td>{i.replace('E6_rate_', '')}</td><td>{R[i]['statement'] if not i.startswith('E6b') else R[i]['statement']}</td>"
    f"<td>{fmt(R[i]['computed'])}</td><td>{vpill(R[i]['verdict'])}</td></tr>" for i in rate_ids)

graph = """
<svg viewBox="0 0 700 170" class="graph" role="img" aria-label="operator dependency graph">
<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8z" fill="#475569"/></marker></defs>
<g font-size="11" font-family="sans-serif" fill="#fff">
<rect x="5" y="15" width="150" height="34" rx="17" fill="#2563eb"/><text x="80" y="36" text-anchor="middle">G_repo, A / B_t split</text>
<rect x="5" y="70" width="150" height="34" rx="17" fill="#2563eb"/><text x="80" y="91" text-anchor="middle">Prop 1 block softmax</text>
<rect x="5" y="125" width="150" height="34" rx="17" fill="#2563eb"/><text x="80" y="146" text-anchor="middle">Prop 2 budget map</text>
<rect x="200" y="42" width="150" height="34" rx="17" fill="#b45309"/><text x="275" y="63" text-anchor="middle">dilution bound (|B_t| up)</text>
<rect x="200" y="98" width="150" height="34" rx="17" fill="#b45309"/><text x="275" y="119" text-anchor="middle">Law 1 noise vs tau</text>
<rect x="395" y="15" width="140" height="34" rx="17" fill="#7c3aed"/><text x="465" y="36" text-anchor="middle">loop detectors</text>
<rect x="395" y="70" width="140" height="34" rx="17" fill="#7c3aed"/><text x="465" y="91" text-anchor="middle">Fisher / McNemar</text>
<rect x="395" y="125" width="140" height="34" rx="17" fill="#7c3aed"/><text x="465" y="146" text-anchor="middle">Wilson CI, SE</text>
<rect x="575" y="42" width="120" height="34" rx="17" fill="#0f766e"/><text x="635" y="63" text-anchor="middle">Tables 1-3 rates</text>
<rect x="575" y="98" width="120" height="34" rx="17" fill="#0f766e"/><text x="635" y="119" text-anchor="middle">deltas, totals</text>
</g>
<g stroke="#475569" stroke-width="1.3" marker-end="url(#a)" fill="none">
<path d="M155,32 L200,55"/><path d="M155,87 L200,62"/><path d="M155,142 L200,118"/>
<path d="M350,59 L395,35"/><path d="M350,115 L395,87"/><path d="M535,87 L575,62"/><path d="M535,142 L575,118"/><path d="M535,32 L575,55"/>
</g></svg>"""

body = []
body.append(f"""
<header><h1>Mathematical Verification Guide</h1>
<p class="sub">{html.escape(data['paper'])}<br>Source: {html.escape(data['primary_source'])}. Sandbox: <code>verify_math.py</code>, seed {data['seed']}, numpy {data['numpy']}, scipy {data['scipy']}.</p>
<p class="counts">{' '.join(f"{vpill(k)} <b>{v}</b>" for k, v in vc.items())}</p>
<p>Operator classes: {legend}</p>
{graph}
<p class="note">Every value in the tables below is read from <code>eq_verified_numbers.json</code>. MISMATCH means the paper's
number differs from the recomputation beyond the stated tolerance; NOT CHECKABLE means the paper lacks a definition or the data needed.</p>
</header>""")

body.append(card("Proposition 1 &mdash; softmax dilution from failed-turn accumulation", "definition",
    tex("prop1", r"\mathrm{Attn}_h(X)_N=\frac{Z_{h,A}\,e^{L_{h,A}}+Z_{h,B_t}\,e^{L_{h,B_t}}}{e^{L_{h,A}}+e^{L_{h,B_t}}}")
    + "<p><b>Intuition.</b> Split the context into the issue contract <i>A</i> and the failed-turn tail <i>B<sub>t</sub></i>. "
      "Attention output is a weighted average of the two block summaries, weighted by each block's total exponentiated score.</p>"
      "<p><b>Derivation.</b> (1) Full softmax: weight on token <i>j</i> is e<sup>s<sub>j</sub></sup>/&Sigma;e<sup>s</sup>. "
      "(2) Define L<sub>A</sub> = log&Sigma;<sub>j&isin;A</sub>e<sup>s<sub>j</sub></sup> and Z<sub>A</sub> = within-A softmax average of values; same for B. "
      "(3) Grouping the sum by block gives the display equation exactly. The paper never defines L or Z; the sandbox uses this reading.</p>"
    + tex("massA", r"w_A=\frac{1}{1+e^{L_{B_t}-L_A}}\approx\frac{|A|}{|A|+|B_t|\,e^{\Delta}}", 13) + "<p class='src' style='text-align:center'>approximation assumes equal per-token logits within each block, gap &Delta; between blocks</p>",
    ["E1_prop1_block_identity", "E2_prop1_dilution_monotone"], "sens_prop1_dilution.png",
    "Attention mass on B_t versus |B_t| with |A| = 512 tokens, for three per-token logit gaps; shaded region lies past the 14,336-token compaction point."))

body.append(card("Dilution 0.72 &rarr; 0.06 and the 4.51-bit claim", "metric",
    "<p><b>Claim.</b> G-CCR pruning cuts dilution from 0.72 to 0.06, recovering 4.51 bits (PDF Sec 3.1). "
    "Neither 'dilution' nor 'bits of effective attention' is defined. The sandbox evaluates six natural readings; none gives 4.51.</p>",
    ["E3_dilution_bits"]))

body.append(card("Proposition 2 &mdash; phase-adaptive thinking budget", "definition",
    tex("prop2", r"\frac{4096-512}{4096}=0.875")
    + "<p>Proposition 2 appears only as a sentence (budgets matched to D1 / LDP / LDW); there is no statement to test beyond the arithmetic.</p>",
    ["E4_prop2_budget_cut"]))

body.append(card("Law 1 &mdash; quantization noise amplified at low temperature", "bound",
    tex("law1", r"p_v(\tau)\propto\exp\!\left(\frac{z_v+\epsilon_v}{\tau}\right),\quad \epsilon_v\sim\mathcal{N}(0,\sigma_q^2)")
    + "<p><b>Intuition.</b> Dividing by &tau; scales the noise term by 1/&tau;: at &tau; = 0.2 a rounding error moves the logit 5&times; further than at &tau; = 1.0. "
      "The simulation measures total-variation shift of the sampling distribution. Under pure greedy decoding the argmax ignores &tau;, so the effect "
      "exists only for sampled decoding. The paper gives no &sigma;<sub>q</sub>; 0.05 is illustrative.</p>",
    ["E5_law1_noise_amplification"], "sens_law1_tau.png",
    "Total-variation distance between clean and noise-perturbed softmax across temperature, with plus or minus 2 Monte Carlo standard errors."))

body.append("<section class='card keep'><h2>Tables 1&ndash;3 &mdash; solve rates and Wilson intervals " + pill("metric") + "</h2>"
    + tex("wilson", r"\mathrm{CI}=\frac{\hat p+\frac{z^2}{2n}\pm z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}}{1+\frac{z^2}{n}}", 13)
    + "<p>Each rate and both interval ends are recomputed from the reported counts (tolerance 0.05 pts for one-decimal rounding). "
      "Each was also bootstrapped with 200,000 binomial draws (values in the JSON).</p>"
    + "<table class='vt'><tr><th>row</th><th>paper</th><th>computed</th><th>verdict</th></tr>" + rate_rows + "</table>"
    + f"<p class='src'>{html.escape(R['E6_rate_T1_row3']['reason'])} (Table 1 row 3: upper end 48.157 prints as 48.1).</p></section>")

body.append(card("Significance tests &mdash; Fisher, McNemar, Wilcoxon", "estimator",
    tex("fisher", r"p=\sum_{k:\,P(k)\leq P(24)}\frac{\binom{28}{k}\binom{22}{25-k}}{\binom{50}{25}}", 13)
    + "<p><b>Fisher (Trap-25).</b> The paper reports p = 4.2&times;10<sup>-9</sup>; scipy and the plugin's research-audit server both give the two-sided value in the table. "
      "Both arms run the same 25 traps, so a paired test is the matched design; its best case is far weaker. "
      "<b>McNemar (Tables 1, 2).</b> Discordant counts are not reported; the sandbox shows which (b, c) pairs reproduce the p-values.</p>",
    ["E8_fisher_trap25", "E8b_paired_alternative", "E7_mcnemar_T1", "E7_mcnemar_T2", "E16_wilcoxon"],
    "sens_trap25_pvalue.png", "Two-sided p versus traps solved by ccr_adaptive with baseline at 4 of 25: unpaired Fisher and best-case paired McNemar."))

delta_ids = [i for i in R if i.startswith("E9_")]
body.append(card("Derived percentages and point gaps", "metric",
    tex("delta", r"\Delta\%=100\left(\frac{x_{\mathrm{new}}}{x_{\mathrm{base}}}-1\right)", 13), delta_ids))

body.append(card("Internal consistency checks", "metric",
    "<p>Per-repository counts, turn totals and context-window arithmetic, recovered from the reported figures.</p>",
    ["E10_repo_breakdown", "E11_turn_total", "E12_kv_vs_context", "E15_context_budget"]))

body.append(card("Leaderboard noise on a 58-task board (Sec 1)", "estimator",
    tex("se", r"\mathrm{SE}=\sqrt{\frac{p(1-p)}{n}},\quad p=0.20,\ n=58", 13),
    ["E13_leaderboard_SE", "E13_leaderboard_wilson_halfwidth", "E13_pts_per_task", "E13_swing"],
    "sens_binomial_noise.png", "Normal-approximation 95 percent half-width versus number of tasks for p = 0.2 and 0.4, with the paper's three benchmark sizes marked."))

body.append(card("Loop detector &mdash; low action entropy", "estimator",
    tex("ent", r"H_W(t)=-\sum_a \hat p_a\log_2\hat p_a<0.55,\quad W=4", 13)
    + "<p>With four actions in the window only five entropy values are possible. The threshold 0.55 separates 'all four identical' from everything else, "
      "so it is equivalent to any threshold in (0, 0.811].</p>",
    ["E14_entropy_detector"], "sens_entropy_detector.png", "All achievable action-entropy values for a window of four actions, with the paper's 0.55-bit threshold."))

CSS = """
@page{size:A4;margin:13mm 12mm}
:root{--fg:#0f172a;--mut:#475569;--bd:#cbd5e1}
body{font-family:'DejaVu Sans',Arial,sans-serif;color:var(--fg);font-size:9.6pt;line-height:1.38;background:#fff;margin:0}
h1{font-size:19pt;margin:0 0 4px} h2{font-size:12.5pt;margin:0 0 6px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.sub{color:var(--mut);margin:0 0 6px}.note{color:var(--mut);font-size:8.6pt}
.pill{display:inline-block;color:#fff;border-radius:999px;padding:1px 8px;font-size:7.6pt;font-weight:600;white-space:nowrap;letter-spacing:.02em}
.card{border:1px solid var(--bd);border-radius:8px;padding:10px 12px;margin:10px 0}
.card h2,.card .eq{break-after:avoid}
.eq{text-align:center;margin:6px 0}.eq img{max-width:100%;max-height:70px}
figure{margin:6px 0;text-align:center;break-inside:avoid}figure img{width:62%}
figcaption{font-size:8pt;color:var(--mut)}
table.vt{width:100%;border-collapse:collapse;font-size:7.6pt;margin-top:6px;table-layout:fixed}
table.vt td,table.vt th{border:1px solid var(--bd);padding:3px 4px;vertical-align:top;word-wrap:break-word;overflow-wrap:anywhere}
table.vt th{background:#f1f5f9;text-align:left}
table.vt .pill{font-size:6.6pt;padding:1px 5px;white-space:normal}
table.vt tr{break-inside:avoid}
table.vt{break-inside:avoid}
.keep{break-inside:avoid}
figure{break-after:avoid}
.src{color:var(--mut);font-size:7pt;margin-top:2px}
code{font-size:7pt;font-family:'DejaVu Sans Mono',monospace;word-break:break-all}
.graph{width:100%;height:auto;margin:4px 0}.counts .pill{font-size:8.6pt}
"""
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Gemma 4 Equation Guide</title>
<style>{CSS}</style></head><body>{''.join(body)}</body></html>"""
(OUT / "MathGuide.html").write_text(page)
print("wrote", OUT / "MathGuide.html")
