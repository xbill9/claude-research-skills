#!/usr/bin/env python3
"""Statistical audit of the Gemma 4 LoopBreaker paper (PAPER.md + PDF).

Exact tests go through the skill's research-audit MCP server (called over stdio);
scipy is used only for checks the server does not offer (Wilcoxon feasibility,
one-sided / chi-square variants used to trace where a reported p-value came from).
Writes stat_audit.json next to this file.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

from scipy import stats

OUT = Path(__file__).resolve().parent
MCP = "/home/xbill/claude-research-skills/plugin/mcp/research_audit_mcp.py"

_calls = []


def mcp_batch(calls):
    """calls: list of (tool, args). One server process, one JSON-RPC line per call."""
    lines = [json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                         "params": {"name": t, "arguments": a}}) for i, (t, a) in enumerate(calls)]
    proc = subprocess.run([sys.executable, "-I", MCP], input="\n".join(lines) + "\n",
                          capture_output=True, text=True, check=True, cwd="/tmp")
    res = {}
    for line in proc.stdout.splitlines():
        d = json.loads(line)
        r = d["result"]
        if r.get("isError"):
            raise RuntimeError(r)
        res[d["id"]] = json.loads(r["content"][0]["text"])
    out = [res[i] for i in range(len(calls))]
    for (t, a), o in zip(calls, out):
        _calls.append({"tool": t, "arguments": a, "output": o})
    return out


def one(tool, **args):
    return mcp_batch([(tool, args)])[0]


audit = {}

# ---------------------------------------------------------------- 1. claim rows
# (label, k, n, source, paper-reported CI from PDF if any)
rows = [
    ("T1.1 Non-thinking baseline (Stage-1)", 23, 129, "PDF p2 Table 1; PAPER.md Table 1 L61", (12.2, 25.3)),
    ("T1.2 Low-temp thinking hidden (Stage-1)", 35, 129, "PDF p2 Table 1; PAPER.md L62", (20.2, 35.4)),
    ("T1.3 Calibrated thinking (Stage-1)", 51, 129, "PDF p2 Table 1; PAPER.md L63", (31.5, 48.1)),
    ("T2.M0 Default starter", 15, 129, "PDF p3 Table 2; PAPER.md L71", (7.2, 18.3)),
    ("T2.M1 Lean-6", 18, 129, "PDF p3 Table 2; PAPER.md L72", (9.0, 21.0)),
    ("T2.M2 Calibrated sampling", 22, 129, "PDF p3 Table 2; PAPER.md L73", (11.5, 24.5)),
    ("T2.M3 Contract parser", 25, 129, "PDF p3 Table 2; PAPER.md L74", (13.5, 27.0)),
    ("T2.M4 Call-12 deadline", 27, 129, "PDF p3 Table 2; PAPER.md L75", (14.8, 28.7)),
    ("T2.M5 Co-change", 29, 129, "PDF p3 Table 2; PAPER.md L76", (16.1, 30.4)),
    ("T2.M6 Backtrack (end-to-end method)", 31, 129, "PDF p3 Table 2; PAPER.md L77", (17.5, 32.1)),
    ("T3 baseline_static", 4, 25, "PDF p4 Table 3; PAPER.md L92", (6.4, 34.7)),
    ("T3 naive_subagent", 5, 25, "PDF p4 Table 3; PAPER.md L93", (8.9, 39.1)),
    ("T3 ccr_only", 18, 25, "PDF p4 Table 3; PAPER.md L94", (52.4, 85.7)),
    ("T3 ccr_adaptive (method)", 24, 25, "PDF p4 Table 3; PAPER.md L95", (80.5, 99.3)),
    ("sci-trap G-CCR", 5, 5, "PDF p4 Sec 4 '5/5 vs. 1/5'", None),
    ("sci-trap baseline", 1, 5, "PDF p4 Sec 4 '5/5 vs. 1/5'", None),
]

# per-repo counts recovered from percentages (PDF p3 text + Figure 3a)
repos = {"fastapi": 67, "rich": 48, "requests": 13, "httpx": 1}
repo_pct = {  # (M0, M6, Stage-1) in %, Figure 3a / PDF p3
    "fastapi": (10.4, 22.4, 37.3), "rich": (12.5, 25.0, 41.7),
    "requests": (15.4, 23.1, 38.5), "httpx": (0.0, 100.0, 100.0)}
recovered = {}
for r, n in repos.items():
    ks = [round(p / 100 * n) for p in repo_pct[r]]
    back = [round(100 * k / n, 1) for k in ks]
    recovered[r] = {"n": n, "k_M0_M6_Stage1": ks, "pct_back": back,
                    "matches_reported": back == list(repo_pct[r])}
sums = [sum(recovered[r]["k_M0_M6_Stage1"][i] for r in repos) for i in range(3)]
audit["per_repo_recovered"] = {"repos": recovered, "n_total": sum(repos.values()),
                               "sum_k_M0_M6_Stage1": sums, "expected": [15, 31, 51]}
for r, n in repos.items():
    k0, k6, ks = recovered[r]["k_M0_M6_Stage1"]
    rows.append((f"repo {r} M0 (recovered)", k0, n, "PDF p3 / Fig 3a pct", None))
    rows.append((f"repo {r} M6 (recovered)", k6, n, "PDF p3 / Fig 3a pct", None))

w = mcp_batch([("verify_wilson_ci", {"successes": k, "total": n}) for _, k, n, _, _ in rows])
audit["wilson"] = []
for (lab, k, n, src, rep), o in zip(rows, w):
    entry = {"claim": lab, "k": k, "n": n, "source": src, **o}
    if rep:
        entry["paper_ci"] = rep
        entry["ci_matches_paper_1dp"] = (round(o["wilson_low_pct"], 1), round(o["wilson_high_pct"], 1)) == rep
    audit["wilson"].append(entry)

# ---------------------------------------------------------------- 2. tests
# Unpaired Fisher (fallback: per-task outcomes are not published)
fisher_pairs = [
    ("T1 calibrated vs baseline", 51, 129, 23, 129),
    ("T1 hidden-thinking vs baseline", 35, 129, 23, 129),
    ("T1 calibrated vs hidden-thinking", 51, 129, 35, 129),
    ("T2 M6 vs M0", 31, 129, 15, 129),
    ("T2 M1 vs M0", 18, 129, 15, 129),
    ("T2 M2 vs M1", 22, 129, 18, 129),
    ("T2 M3 vs M2", 25, 129, 22, 129),
    ("T2 M4 vs M3", 27, 129, 25, 129),
    ("T2 M5 vs M4", 29, 129, 27, 129),
    ("T2 M6 vs M5", 31, 129, 29, 129),
    ("T2 M6 vs M2 (same sampling)", 31, 129, 22, 129),
    ("T3 ccr_adaptive vs baseline_static", 24, 25, 4, 25),
    ("T3 ccr_only vs baseline_static", 18, 25, 4, 25),
    ("T3 ccr_adaptive vs ccr_only", 24, 25, 18, 25),
    ("T3 naive_subagent vs baseline_static", 5, 25, 4, 25),
    ("sci-trap 5/5 vs 1/5", 5, 5, 1, 5),
    ("Trap-25 as 100 episodes? 96/100 vs 16/100 (hypothesis)", 96, 100, 16, 100),
]
f = mcp_batch([("verify_fisher_exact", {"k_method": a, "n_method": b, "k_baseline": c, "n_baseline": d})
               for _, a, b, c, d in fisher_pairs])
audit["fisher"] = [{"comparison": lab, **o} for (lab, *_), o in zip(fisher_pairs, f)]

# where could Trap-25 p = 4.2e-9 come from?
tbl = [[24, 1], [4, 21]]
audit["trap25_p_trace"] = {
    "paper_p": 4.2e-9,
    "fisher_two_sided_scipy": stats.fisher_exact(tbl, alternative="two-sided").pvalue,
    "fisher_one_sided_greater_scipy": stats.fisher_exact(tbl, alternative="greater").pvalue,
    "chi2_yates": stats.chi2_contingency(tbl, correction=True)[1],
    "chi2_no_yates": stats.chi2_contingency(tbl, correction=False)[1],
}

# Exact McNemar feasibility: given only marginals, which (b, c) are possible and
# which p-values could result? b - c = k_method - k_base; c <= min(k_base, n - k_method).
def mcnemar_range(label, km, kb, n, paper_p=None):
    d = km - kb
    cmax = min(kb, n - km)
    calls = [("verify_mcnemar_exact", {"b": d + c, "c": c}) for c in range(cmax + 1)]
    res = mcp_batch(calls)
    ps = [(c + d, c, r["p_value"]) for c, r in enumerate(res)]
    out = {"comparison": label, "k_method": km, "k_baseline": kb, "n": n,
           "feasible_c_range": [0, cmax],
           "p_min": ps[0][2], "p_at_c_max": ps[-1][2],
           "p_by_bc": [{"b": b, "c": c, "p": p} for b, c, p in ps]}
    if paper_p is not None:
        best = min(ps, key=lambda t: abs(math.log10(t[2]) - math.log10(paper_p)))
        out["paper_p"] = paper_p
        out["closest_bc_to_paper_p"] = {"b": best[0], "c": best[1], "p": best[2]}
    return out

audit["mcnemar_feasibility"] = [
    mcnemar_range("T1 calibrated vs baseline", 51, 23, 129, 1.8e-6),
    mcnemar_range("T2 M6 vs M0", 31, 15, 129, 4.6e-5),
    mcnemar_range("T3 ccr_adaptive vs baseline_static (paired by trap)", 24, 4, 25, 4.2e-9),
]

# ---------------------------------------------------------------- 3. noise floor
nf_args = [(129, 0.178), (129, 0.116), (129, 0.171), (129, 0.209), (25, 0.16), (25, 0.72), (58, 0.20)]
nf = mcp_batch([("leaderboard_noise_floor", {"num_tasks": n, "baseline_rate": p}) for n, p in nf_args])
audit["noise_floor"] = nf
# PDF p1: "58-task ... true p = 0.20 ... SE = 5.25% (95% Wilson CI width ±9.8 pts)"
k58 = round(0.20 * 58)
w58 = one("verify_wilson_ci", successes=k58, total=58)
audit["pdf_58task_claim"] = {
    "paper": "SE = 5.25%, 95% Wilson CI width +/-9.8 pts (PDF p1, item 2)",
    "se_pct": 100 * math.sqrt(0.2 * 0.8 / 58),
    "wald_half_width_pct": 196 * math.sqrt(0.2 * 0.8 / 58) / 1,
    "k_recovered": k58, "wilson": w58,
    "wilson_half_widths_pts": [round(100 * k58 / 58 - w58["wilson_low_pct"], 2),
                               round(w58["wilson_high_pct"] - 100 * k58 / 58, 2)],
    "pts_per_task": 100 / 58,
}

# ---------------------------------------------------------------- 4. Wilcoxon feasibility
def wilcoxon_bounds(n):
    # smallest two-sided p attainable by exact signed-rank (all differences same sign, no ties)
    exact_min = 2 * 0.5 ** n
    mu = n * (n + 1) / 4
    sd = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    zmax = (n * (n + 1) / 2 - mu) / sd
    return {"n_pairs": n, "exact_min_two_sided_p": exact_min,
            "normal_approx_max_z": zmax, "normal_approx_min_p": 2 * stats.norm.sf(zmax)}

audit["wilcoxon_feasibility"] = {
    "paper": "Active post-reset KV 46.7K vs 159.8K, Wilcoxon p = 8.91e-07 (PAPER.md L117); p < 1e-6 (PAPER.md L13, PDF p1)",
    "per_episode_data_published": False,
    "bounds": [wilcoxon_bounds(n) for n in (25, 100)],
}

# ---------------------------------------------------------------- 5. arithmetic checks
avg_turns = {"baseline_static": 11.04, "naive_subagent": 10.72, "ccr_only": 8.76, "ccr_adaptive": 6.96}
think = {"baseline_static": 45220, "naive_subagent": 51118, "ccr_only": 35881, "ccr_adaptive": 24842}
kv = {"baseline_static": 159816, "naive_subagent": 190410, "ccr_only": 85148, "ccr_adaptive": 46689}
rel = lambda a, b: round(100 * (a - b) / b, 1)
arith = {
    "pct_from_k_n": {lab: round(100 * k / n, 2) for lab, k, n, *_ in rows},
    "PAPER.md abstract 24.1% vs 31/129": round(100 * 31 / 129, 2),
    "2.1x gain = 31/15": round(31 / 15, 3),
    "'double' 11.6->24.x ratio of rates": round((31 / 129) / (15 / 129), 3),
    "-93% compaction = 1 - 4.7/68.2": round(100 * (1 - 4.7 / 68.2), 1),
    "-24.2 pts compaction M0->M1": round(68.2 - 44.0, 1),
    "+21.7 pts Stage-1": round(100 * (51 - 23) / 129, 1),
    "+80 pts Trap-25": round(100 * (24 - 4) / 25, 1),
    "22.4-pt tax = 39.5-17.1 (k)": round(100 * (51 - 22) / 129, 1),
    "29 solvable tasks lost = 51-22": 51 - 22,
    "'recovers half that 29-task gap': M6-M2 tasks": 31 - 22,
    "fraction of 29-task gap recovered (M6-M2)/29": round((31 - 22) / 29, 3),
    "fraction of M0->Stage1 gap recovered (31-15)/(51-15)": round((31 - 15) / (51 - 15), 3),
    "Table 3 think-token rel %": {k: rel(v, think["baseline_static"]) for k, v in think.items()},
    "Table 3 post-reset KV rel %": {k: rel(v, kv["baseline_static"]) for k, v in kv.items()},
    "937 turns = 25 * sum(avg turns)": round(25 * sum(avg_turns.values()), 2),
    "100 episodes = 4 configs * 25 traps": 4 * 25,
    "87.5% = 1 - 512/4096": 100 * (1 - 512 / 4096),
    "-66.3% VRAM = 1 - 18.4/54.6": round(100 * (1 - 18.4 / 54.6), 1),
    "4.51 bits? log2(0.72/0.06)": round(math.log2(0.72 / 0.06), 3),
    "1-of-3 adapters pass = 0.33?": round(1 / 3, 2),
}
audit["arithmetic"] = arith

# ---------------------------------------------------------------- 6. follow-ups
# 6a. full-precision Wilson for the rows whose 2-dp tool output double-rounds ambiguously
def wilson_full(k, n, z=stats.norm.ppf(0.975)):
    ph = k / n
    c = (ph + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return 100 * (c - h), 100 * (c + h)
audit["wilson_full_precision"] = {f"{k}/{n}": wilson_full(k, n) for k, n in [(51, 129), (25, 129), (4, 25)]}
# Wilson half-width at exactly p=0.20, n=58 (PDF p1 says +/-9.8)
z = stats.norm.ppf(0.975); n = 58; ph = 0.2
audit["pdf_58task_claim"]["wilson_half_width_at_p0.20_pts"] = 100 * z * math.sqrt(ph*(1-ph)/n + z*z/(4*n*n)) / (1 + z*z/n)

# 6b. best case paired test for every single ablation step: even if c = 0, b = k_i - k_{i-1}
steps = [("M1 vs M0", 3), ("M2 vs M1", 4), ("M3 vs M2", 3), ("M4 vs M3", 2), ("M5 vs M4", 2), ("M6 vs M5", 2),
         ("M6 vs M2 (tooling modules only)", 9), ("sci-trap 5/5 vs 1/5 paired", 4),
         ("T3 ccr_adaptive vs ccr_only paired", 6), ("T1 calibrated vs hidden-thinking paired", 16)]
r = mcp_batch([("verify_mcnemar_exact", {"b": b, "c": 0}) for _, b in steps])
audit["mcnemar_best_case_steps"] = [{"comparison": l, "b": b, "c": 0, "best_case_p": o["p_value"]} for (l, b), o in zip(steps, r)]

# 6c. can any common McNemar variant produce the reported p-values?
def variants(b, c):
    d = (b - c) ** 2 / (b + c)
    dcc = (abs(b - c) - 1) ** 2 / (b + c)
    exact = min(1.0, 2 * stats.binom.cdf(min(b, c), b + c, 0.5))
    mid = exact - stats.binom.pmf(min(b, c), b + c, 0.5)
    return {"b": b, "c": c, "exact": exact, "mid_p": mid,
            "chi2": stats.chi2.sf(d, 1), "chi2_cc": stats.chi2.sf(dcc, 1)}
audit["mcnemar_variants"] = {
    "T2 M6 vs M0 (paper 4.6e-5)": [variants(16 + c, c) for c in range(0, 4)],
    "T1 calibrated vs baseline (paper 1.8e-6)": [variants(28 + c, c) for c in range(2, 7)],
}

audit["raw_mcp_calls"] = _calls

(OUT / "stat_audit.json").write_text(json.dumps(audit, indent=2))

# ---------------------------------------------------------------- console summary
print("== Wilson")
for e in audit["wilson"]:
    print(f"{e['claim']:<42} {e['k']:>3}/{e['n']:<3} {e['formatted']:<40} paper={e.get('paper_ci')} match={e.get('ci_matches_paper_1dp')}")
print("== per-repo recovered", json.dumps(audit["per_repo_recovered"]["sum_k_M0_M6_Stage1"]),
      {r: v["k_M0_M6_Stage1"] for r, v in recovered.items()},
      {r: v["matches_reported"] for r, v in recovered.items()})
print("== Fisher (two-sided, unpaired)")
for e in audit["fisher"]:
    print(f"{e['comparison']:<58} diff={e['difference_pts']:>6} p={e['p_value']:.3g}")
print("== Trap-25 p trace", json.dumps({k: (f'{v:.3g}' if isinstance(v, float) else v) for k, v in audit['trap25_p_trace'].items()}))
print("== McNemar feasibility")
for e in audit["mcnemar_feasibility"]:
    print(e["comparison"], "c in", e["feasible_c_range"], f"p_min={e['p_min']:.3g} p_cmax={e['p_at_c_max']:.3g}",
          "paper", e.get("paper_p"), "closest", e.get("closest_bc_to_paper_p"))
print("== Noise floor")
for e in nf:
    print(e)
print("== 58-task", json.dumps(audit["pdf_58task_claim"], default=str))
print("== Wilcoxon", json.dumps(audit["wilcoxon_feasibility"]["bounds"]))
print("== Wilson full precision", audit["wilson_full_precision"])
print("== 58-task Wilson half-width at p=.2", audit["pdf_58task_claim"]["wilson_half_width_at_p0.20_pts"])
print("== McNemar best case per step")
for e in audit["mcnemar_best_case_steps"]: print("  ", e)
print("== McNemar variants")
for k, v in audit["mcnemar_variants"].items():
    print("  ", k)
    for e in v: print("     ", {a: (f"{x:.3g}" if isinstance(x, float) else x) for a, x in e.items()})
print("== Arithmetic")
for k, v in arith.items():
    if k != "pct_from_k_n":
        print(f"  {k}: {v}")
