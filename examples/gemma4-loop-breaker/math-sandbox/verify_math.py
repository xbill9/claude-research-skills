#!/usr/bin/env python3
"""Deterministic numerical sandbox for the Gemma 4 LoopBreaker paper.

Paper: examples/gemma4-loop-breaker/paper/ (PDF = primary source, PAPER.md = companion).
Every value written to eq_verified_numbers.json is computed here. seed = 42.

    python3 verify_math.py            # writes eq_verified_numbers.json and figures/*.png
"""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

import numpy as np
from scipy import stats
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
RNG = np.random.default_rng(SEED)
OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"
FIG.mkdir(exist_ok=True)
Z95 = stats.norm.ppf(0.975)

records: list[dict] = []


def rec(id_, cls, statement, source, paper_value, computed, simulated=None, sim_info=None,
        tolerance=None, verdict=None, reason=""):
    abs_gap = None
    if isinstance(paper_value, (int, float)) and isinstance(computed, (int, float)):
        abs_gap = abs(float(paper_value) - float(computed))
    if verdict is None:
        verdict = "VERIFIED" if (abs_gap is not None and tolerance is not None and abs_gap <= tolerance) else "MISMATCH"
    records.append(dict(id=id_, operator_class=cls, statement=statement,
                        paper_value=paper_value, paper_source=source,
                        computed=computed, simulated=simulated, simulation=sim_info,
                        abs_gap=abs_gap, tolerance=tolerance, verdict=verdict, reason=reason))


def wilson(k, n, z=Z95):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def mc_rate(k, n, draws=200_000):
    """Parametric bootstrap of a k/n rate: mean and its Monte Carlo standard error."""
    sims = RNG.binomial(n, k / n, size=draws) / n
    return float(sims.mean()), float(sims.std(ddof=1) / math.sqrt(draws)), float(sims.std(ddof=1))


# ---------------------------------------------------------------- E1 Proposition 1 (identity)
def softmax_attn(logits, values):
    w = np.exp(logits - logits.max())
    w /= w.sum()
    return w @ values, w


def block_form(logits, values, A, B):
    LA = np.log(np.exp(logits[A]).sum())  # log-sum-exp over block A
    LB = np.log(np.exp(logits[B]).sum())
    wA = np.exp(logits[A] - LA)
    wB = np.exp(logits[B] - LB)
    ZA, ZB = wA @ values[A], wB @ values[B]  # within-block softmax averages
    out = (ZA * np.exp(LA) + ZB * np.exp(LB)) / (np.exp(LA) + np.exp(LB))
    massA = np.exp(LA) / (np.exp(LA) + np.exp(LB))
    return out, massA


trials, max_err = 2000, 0.0
for _ in range(trials):
    N = int(RNG.integers(8, 200))
    nA = int(RNG.integers(1, N))
    logits = RNG.normal(0, 2, N)
    values = RNG.normal(0, 1, (N, 16))
    perm = RNG.permutation(N)
    A, B = perm[:nA], perm[nA:]
    full, w = softmax_attn(logits, values)
    blk, mA = block_form(logits, values, A, B)
    max_err = max(max_err, float(np.abs(full - blk).max()), abs(float(w[A].sum()) - float(mA)))
rec("E1_prop1_block_identity", "definition",
    "Attn_h(X)_N = [Z_A e^{L_A} + Z_B e^{L_B}] / [e^{L_A} + e^{L_B}] equals full softmax attention, "
    "with L = log-sum-exp of block logits and Z = within-block softmax average",
    "PDF p.2 Sec 3.1 (Lemma 39 of [3]); PAPER.md Sec 3.1 display equation",
    0.0, max_err, simulated=max_err,
    sim_info=f"{trials} random (N, partition, logits, values) draws; max |full - block| over outputs and A-mass",
    tolerance=1e-10,
    reason="Exact identity once L and Z are read as log-sum-exp and within-block averages; the paper does not define L or Z.")

# ---------------------------------------------------------------- E2 dilution growth with |B_t|
# A-mass = 1 / (1 + (|B|/|A|) * exp(mean-logit gap)) for equal within-block logits.
nA_tok, gap = 512, 0.0  # issue contract + slice, equal per-token logits (illustrative)
B_sizes = np.array([0, 512, 2048, 8192, 13824])
massA_closed = nA_tok / (nA_tok + B_sizes * math.exp(gap))
# simulate with noisy logits (sigma = 1 per token) to show the trend survives noise
sim_mass, sim_se = [], []
for nb in B_sizes:
    vals = []
    for _ in range(400):
        la = RNG.normal(0, 1, nA_tok)
        lb = RNG.normal(gap, 1, nb) if nb else np.array([])
        ea, eb = np.exp(la).sum(), np.exp(lb).sum() if nb else 0.0
        vals.append(ea / (ea + eb))
    sim_mass.append(float(np.mean(vals)))
    sim_se.append(float(np.std(vals, ddof=1) / math.sqrt(400)))
monotone = bool(np.all(np.diff(sim_mass) < 0))
rec("E2_prop1_dilution_monotone", "bound",
    "As |B_t| grows, exp(L_B) dominates the denominator and attention mass on A falls",
    "PDF p.2 Sec 3.1 Proposition 1", "monotone decrease (qualitative)",
    {"B_sizes": B_sizes.tolist(), "A_mass_closed_form_equal_logits": massA_closed.round(4).tolist()},
    simulated={"A_mass_mean": [round(x, 4) for x in sim_mass], "mc_se": [round(x, 5) for x in sim_se],
               "strictly_decreasing": monotone},
    sim_info="400 draws per |B| with per-token logits ~ N(0,1) in both blocks, |A| = 512 (illustrative, not from paper)",
    verdict="VERIFIED" if monotone else "MISMATCH",
    reason="Direction verified. The Omega(r / log N) threshold is NOT CHECKABLE: r is never defined in the paper.")

# ---------------------------------------------------------------- E3 "dilution 0.72 -> 0.06 = +4.51 bits"
d0, d1 = 0.72, 0.06
cands = {
    "log2(d0/d1)": math.log2(d0 / d1),
    "log2((1-d1)/(1-d0))": math.log2((1 - d1) / (1 - d0)),
    "-log2(d1)": -math.log2(d1),
    "-log2(d1)+log2(d0)": -math.log2(d1) + math.log2(d0),
    "H2(d0)-H2(d1) binary entropy": (lambda h: h(d0) - h(d1))(lambda p: -p * math.log2(p) - (1 - p) * math.log2(1 - p)),
    "log2(d0/(1-d0)) - log2(d1/(1-d1)) (log-odds)": math.log2(d0 / (1 - d0)) - math.log2(d1 / (1 - d1)),
}
best = min(cands, key=lambda k: abs(cands[k] - 4.51))
rec("E3_dilution_bits", "metric",
    "Pruning B_t cuts softmax dilution from 0.72 to 0.06, recovering 4.51 bits of effective attention",
    "PDF p.2 Sec 3.1; PAPER.md Sec 3.1", 4.51,
    {k: round(v, 4) for k, v in cands.items()},
    tolerance=0.01, verdict="NOT CHECKABLE",
    reason=f"'Dilution' and 'bits of effective attention' are undefined. Of six natural readings the closest is "
           f"{best} = {cands[best]:.4f} bits; none reproduces 4.51. Source CSV graph_encoding_ablation_90.csv not provided.")

# ---------------------------------------------------------------- E4 Proposition 2 budget cut
cut = (4096 - 512) / 4096
rec("E4_prop2_budget_cut", "definition", "thinking_budget 4096 -> 512 on D1 reads is an 87.5% cut",
    "PDF p.2 Sec 3.1 Proposition 2", 0.875, cut, tolerance=1e-9,
    reason="Arithmetic only. Proposition 2 itself is never stated formally, so the budget mapping is NOT CHECKABLE.")

# ---------------------------------------------------------------- E5 Law 1 quantization noise vs temperature
V, sigma_q, draws = 256_000 // 1000, 0.05, 4000  # 256-token toy vocab; sigma_q illustrative (paper gives none)
z = RNG.normal(0, 2.0, V)
taus = np.array([0.1, 0.2, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0])
tv_mean, tv_se = [], []
for tau in taus:
    p = np.exp((z - z.max()) / tau); p /= p.sum()
    eps = RNG.normal(0, sigma_q, (draws, V))
    q = np.exp(((z + eps) - (z + eps).max(axis=1, keepdims=True)) / tau); q /= q.sum(axis=1, keepdims=True)
    tv = 0.5 * np.abs(q - p).sum(axis=1)
    tv_mean.append(float(tv.mean())); tv_se.append(float(tv.std(ddof=1) / math.sqrt(draws)))
i02, i10 = int(np.where(taus == 0.2)[0][0]), int(np.where(taus == 1.0)[0][0])
ratio = tv_mean[i02] / tv_mean[i10]
rec("E5_law1_noise_amplification", "bound",
    "exp((z_v + eps_v)/tau) amplifies eps ~ N(0, sigma_q^2) at tau = 0.2 relative to tau = 1.0",
    "PDF p.2 Sec 3.2; PAPER.md Sec 3.2", "amplified at low tau (qualitative); logit-scale factor 1/tau = 5",
    {"logit_noise_scale_tau0.2_over_tau1.0": 1.0 / 0.2},
    simulated={"taus": taus.tolist(), "TV_mean": [round(x, 5) for x in tv_mean],
               "mc_se": [round(x, 6) for x in tv_se], "TV_ratio_tau0.2_over_tau1.0": round(ratio, 3)},
    sim_info=f"{draws} noise draws per tau, V = {V} toy vocab, z ~ N(0, 2^2), sigma_q = {sigma_q} (illustrative)",
    verdict="VERIFIED" if ratio > 1 else "MISMATCH",
    reason="Direction verified for the sampled distribution. Caveat: under greedy decoding the argmax is "
           "tau-invariant, so the claim only bites when sampling. Link to the 17.8% -> 39.5% gain is empirical, not derived.")

# ---------------------------------------------------------------- E6 Tables 1-3 rates and Wilson CIs
tables = {
    "T1_row1": (23, 129, 17.8, (12.2, 25.3), "PDF p.2 Table 1"),
    "T1_row2": (35, 129, 27.1, (20.2, 35.4), "PDF p.2 Table 1"),
    "T1_row3": (51, 129, 39.5, (31.5, 48.1), "PDF p.2 Table 1"),
    "T2_M0": (15, 129, 11.6, (7.2, 18.3), "PDF p.3 Table 2"),
    "T2_M1": (18, 129, 14.0, (9.0, 21.0), "PDF p.3 Table 2"),
    "T2_M2": (22, 129, 17.1, (11.5, 24.5), "PDF p.3 Table 2"),
    "T2_M3": (25, 129, 19.4, (13.5, 27.0), "PDF p.3 Table 2"),
    "T2_M4": (27, 129, 20.9, (14.8, 28.7), "PDF p.3 Table 2"),
    "T2_M5": (29, 129, 22.5, (16.1, 30.4), "PDF p.3 Table 2"),
    "T2_M6": (31, 129, 24.0, (17.5, 32.1), "PDF p.3 Table 2"),
    "T3_baseline_static": (4, 25, 16.0, (6.4, 34.7), "PDF p.4 Table 3"),
    "T3_naive_subagent": (5, 25, 20.0, (8.9, 39.1), "PDF p.4 Table 3"),
    "T3_ccr_only": (18, 25, 72.0, (52.4, 85.7), "PDF p.4 Table 3"),
    "T3_ccr_adaptive": (24, 25, 96.0, (80.5, 99.3), "PDF p.4 Table 3"),
}
for key, (k, n, pct, ci, src) in tables.items():
    rate = 100 * k / n
    lo, hi = (100 * x for x in wilson(k, n))
    m, se, _ = mc_rate(k, n)
    gap = max(abs(rate - pct), abs(lo - ci[0]), abs(hi - ci[1]))
    rec(f"E6_rate_{key}", "metric", f"{k}/{n} = {pct}% with 95% Wilson CI [{ci[0]}, {ci[1]}]", src,
        {"rate_pct": pct, "ci": list(ci)},
        {"rate_pct": round(rate, 3), "wilson_ci": [round(lo, 3), round(hi, 3)]},
        simulated={"bootstrap_mean_pct": round(100 * m, 3), "mc_se_pct": round(100 * se, 4)},
        sim_info="200,000 binomial draws at p = k/n",
        tolerance=0.05, verdict="VERIFIED" if gap <= 0.051 else "MISMATCH",
        reason=f"max abs gap across rate and both CI ends = {gap:.3f} pts (rounding tolerance 0.05 pts)")

# PAPER.md says M6 = 24.1% in abstract
rec("E6b_md_M6_24.1", "metric", "PAPER.md abstract: multi-module repair rises to 24.1%",
    "PAPER.md Abstract item 2", 24.1, round(100 * 31 / 129, 3), tolerance=0.05,
    reason="PAPER.md Table 2 and the PDF both give 31/129 = 24.0%; abstract figure 24.1% is a rounding error.")

# ---------------------------------------------------------------- E7 McNemar feasibility
def mcnemar_exact(b, c):
    n = b + c
    return min(1.0, 2 * stats.binom.cdf(min(b, c), n, 0.5))


def mcnemar_variants(b, c):
    n, k = b + c, min(b, c)
    return {"exact": mcnemar_exact(b, c),
            "mid-p": min(1.0, 2 * (stats.binom.cdf(k, n, 0.5) - 0.5 * stats.binom.pmf(k, n, 0.5))),
            "chi2": float(stats.chi2.sf((b - c) ** 2 / n, 1)),
            "chi2_cc": float(stats.chi2.sf((abs(b - c) - 1) ** 2 / n, 1))}


for id_, diff, target, src in [("E7_mcnemar_T1", 51 - 23, 1.8e-6, "PDF p.2 Table 1 caption"),
                               ("E7_mcnemar_T2", 31 - 15, 4.6e-5, "PDF p.3 Table 2 caption")]:
    matches, c = [], 0
    while 2 * c + diff <= 129:
        for name, pv in mcnemar_variants(c + diff, c).items():
            if float(f"{pv:.2g}") == target:
                matches.append({"test": name, "b": c + diff, "c": c, "p": pv})
        c += 1
    pmin = mcnemar_exact(diff, 0)
    comp = {"min_possible_exact_p(c=0)": pmin, "exact_p(c=1)": mcnemar_exact(diff + 1, 1),
            "reproducing_(b,c)_to_2_sig_figs": matches}
    if matches:
        verdict = "NOT CHECKABLE"
        reason = (f"b - c must equal {diff}. Discordant counts are not reported, but the value is reproducible: "
                  + "; ".join(f"{m['test']} with b={m['b']}, c={m['c']} gives {m['p']:.3g}" for m in matches)
                  + ". The paper does not say which McNemar variant it used.")
    else:
        verdict = "MISMATCH"
        reason = (f"b - c must equal {diff} (net tasks). Searched every (b, c) with b - c = {diff}, b + c <= 129 under "
                  "two-sided exact, mid-p, chi-square and continuity-corrected chi-square McNemar: none gives "
                  f"{target:g} to two significant figures. Exact p jumps from {pmin:.3g} (c=0) to "
                  f"{mcnemar_exact(diff + 1, 1):.3g} (c=1).")
    rec(id_, "estimator", f"McNemar paired p = {target:g} (net {diff} more tasks solved)", src, target, comp,
        verdict=verdict, reason=reason)

# ---------------------------------------------------------------- E8 Fisher exact Trap-25
_, p_f = stats.fisher_exact([[24, 1], [4, 21]], alternative="two-sided")
# Monte Carlo permutation test under H0 (28 successes among 50 tasks, random split)
pool = np.array([1] * 28 + [0] * 22)
obs = 24 - 4
n_perm, hits = 2_000_000, 0
chunk = 200_000
for _ in range(n_perm // chunk):
    idx = np.argsort(RNG.random((chunk, 50)), axis=1)[:, :25]
    s = pool[idx].sum(axis=1)
    hits += int(np.sum(np.abs(s - (28 - s)) >= obs))
p_mc = hits / n_perm
se_mc = math.sqrt(max(p_mc, 1 / n_perm) * (1 - p_mc) / n_perm)
rec("E8_fisher_trap25", "estimator", "Fisher's exact two-sided p for 24/25 vs 4/25", "PDF p.1 Abstract, p.4 Sec 3.4, p.4 Sec 5 log",
    4.2e-9, float(p_f), simulated=p_mc,
    sim_info=f"{n_perm:,} random 25/25 splits of 28 successes; hits = {hits}; MC SE = {se_mc:.2e} "
             "(p is far below MC resolution, so the MC only bounds it)",
    tolerance=0.05e-9, verdict=None,  # cross-checked: research-audit MCP verify_fisher_exact -> 7.1786e-09
    reason="")
r = records[-1]
r["abs_gap"] = abs(4.2e-9 - p_f)
r["verdict"] = "VERIFIED" if r["abs_gap"] <= 0.05e-9 else "MISMATCH"
r["reason"] = (f"scipy fisher_exact two-sided = {p_f:.4g}. "
               + ("Matches." if r["verdict"] == "VERIFIED" else
                  f"Paper value differs by a factor of {p_f / 4.2e-9:.2f}. ")
               + f"One-sided p = {stats.fisher_exact([[24, 1], [4, 21]], alternative='greater')[1]:.3g}, also not 4.2e-9. "
               + "Note: test treats 25 tasks per arm as independent although both arms run the same 25 traps "
                 "(a paired McNemar test would be the matched design).")
# paired alternative: if every baseline-solved trap is also solved by ccr_adaptive, b=20, c=0
p_paired = mcnemar_exact(20, 0)
rec("E8b_paired_alternative", "estimator", "Paired exact McNemar on the same 25 traps (best case b=20, c=0)",
    "derived (design check)", "not reported", p_paired, verdict="NOT CHECKABLE",
    reason=f"Same 25 traps in both arms; with b=20, c=0 the paired exact p is {p_paired:.3g}, "
           f"{math.log10(p_paired / 4.2e-9):.1f} orders of magnitude weaker than the reported unpaired p. "
           "Per-trap pairing not reported.")

# ---------------------------------------------------------------- E9 percentage deltas in tables
deltas = [
    ("T3_think_naive", 51118, 45220, 13.0), ("T3_think_ccr_only", 35881, 45220, -20.7),
    ("T3_think_adaptive", 24842, 45220, -45.1), ("T3_kv_naive", 190410, 159816, 19.1),
    ("T3_kv_ccr_only", 85148, 159816, -46.7), ("T3_kv_adaptive", 46689, 159816, -70.8),
    ("S4_vram_cut", 18.4, 54.6, -66.3),
]
for key, new, base, pct in deltas:
    got = 100 * (new / base - 1)
    rec(f"E9_delta_{key}", "metric", f"({new} / {base} - 1) = {pct}%",
        "PDF p.4 Table 3" if key.startswith("T3") else "PDF p.4 Sec 4; PAPER.md Sec 4",
        pct, round(got, 4), tolerance=0.05)

comp = 100 * (68.2 - 4.7) / 68.2
rec("E9_compaction_cut", "metric", "Compaction 68.2% -> 4.7% is a -93% cut", "PDF p.1 Abstract; Table 2", 93.0,
    round(comp, 4), tolerance=0.5, reason="Paper rounds to integer percent.")
rec("E9_graph_tool_pts", "metric", "Deleting unindexed graph tools: -24.2 pts compaction (M0 -> M1)",
    "PDF p.4 Sec 4", 24.2, round(68.2 - 44.0, 4), tolerance=0.01)
rec("E9_twofold", "metric", "M0 -> M6 is a 2.1x gain", "PAPER.md Sec 3.3", 2.1, round(31 / 15, 4), tolerance=0.05)
rec("E9_stage1_gain_pts", "metric", "+21.7 pts Stage-1 synthesis", "PDF p.4 Sec 4", 21.7,
    round(100 * (51 - 23) / 129, 4), tolerance=0.05)
rec("E9_trap_gain_pts", "metric", "+80.0 pts Trap-25 escape", "PDF p.4 Sec 4", 80.0,
    round(100 * (24 - 4) / 25, 4), tolerance=0.01)
rec("E9_tax_pts", "metric", "22.4-point Localization-Trajectory Tax (39.5% - 17.1%)", "PDF p.3 Sec 3.3", 22.4,
    round(round(100 * 51 / 129, 1) - round(100 * 22 / 129, 1), 4), tolerance=1e-9,
    reason=f"Matches as a difference of the two rounded rates (39.5 - 17.1). From counts the gap is "
           f"{100 * (51 - 22) / 129:.4f} pts, which rounds to 22.5.")
rec("E9_tax_tasks", "metric", "29 solvable tasks lost (51 - 22)", "PDF p.3 Sec 3.3", 29, 51 - 22, tolerance=0)
half = (31 - 22) / 29
rec("E9_half_gap", "metric", "M3..M6 'recovers half that 29-task gap'", "PDF p.3 Sec 3.3", 0.5,
    {"(M6-M2)/29": round(half, 4), "(M6-M0)/29": round((31 - 15) / 29, 4)},
    verdict="NOT CHECKABLE",
    reason=f"Ambiguous baseline. From M2 (the row defining the gap) M6 recovers 9/29 = {half:.3f}, "
           f"not half; from M0 it is 16/29 = {(31 - 15) / 29:.3f}, but the 29-task gap is defined against M2.")

# ---------------------------------------------------------------- E10 per-repo breakdown consistency
repos = {"fastapi": (67, 51.9, 10.4, 22.4), "rich": (48, 37.2, 12.5, 25.0),
         "requests": (13, 10.1, 15.4, 23.1), "httpx": (1, 0.8, 0.0, 100.0)}
recon, ok = {}, True
tot0 = tot6 = 0
for name, (n, share, r0, r6) in repos.items():
    k0 = [k for k in range(n + 1) if abs(100 * k / n - r0) < 0.05]
    k6 = [k for k in range(n + 1) if abs(100 * k / n - r6) < 0.05]
    sh = 100 * n / 129
    ok &= len(k0) == 1 and len(k6) == 1 and abs(sh - share) < 0.05
    recon[name] = {"n": n, "share_pct": round(sh, 3), "M0_k": k0, "M6_k": k6}
    tot0 += k0[0] if k0 else 0
    tot6 += k6[0] if k6 else 0
ok &= sum(v[0] for v in repos.values()) == 129 and tot0 == 15 and tot6 == 31
rec("E10_repo_breakdown", "metric", "Per-repo M0/M6 rates and shares sum to 15/129 and 31/129",
    "PDF p.3 Sec 3.3", {"M0_total": 15, "M6_total": 31, "N": 129},
    {"per_repo": recon, "N": sum(v[0] for v in repos.values()), "M0_total": tot0, "M6_total": tot6},
    verdict="VERIFIED" if ok else "MISMATCH",
    reason="Each reported repo rate maps to exactly one integer count; counts sum to the table totals.")

# ---------------------------------------------------------------- E11 937 turns = sum of avg turns x 25
turns = 25 * (11.04 + 10.72 + 8.76 + 6.96)
rec("E11_turn_total", "metric", "Table 3 covers 100 trajectories and 937 turns", "PDF p.4 Table 3 caption; PAPER.md Abstract",
    937, round(turns, 4), tolerance=0.5,
    reason="25 tasks x 4 configurations = 100 trajectories; sum of Avg Turns x 25. Note the abstract also "
           "attributes the 937 turns to the 129-task swegemma telemetry (PDF p.1 Sec 1), which this identity contradicts.")

# ---------------------------------------------------------------- E12 KV numbers vs max_model_len
rec("E12_kv_vs_context", "bound", "Active Post-Reset KV 159,816 / 190,410 tokens vs max_model_len 32,768",
    "PDF p.4 Table 3; p.1 Sec 1", 32768, {"baseline_over_ctx": round(159816 / 32768, 3),
                                          "naive_over_ctx": round(190410 / 32768, 3)},
    verdict="NOT CHECKABLE",
    reason="Values exceed one context window by ~4.9x and ~5.8x, so the column must be cumulative over turns; "
           "the paper calls it 'active' and does not define the aggregation.")

# ---------------------------------------------------------------- E13 leaderboard noise (Sec 1 item 2)
p0, n58 = 0.20, 58
se = math.sqrt(p0 * (1 - p0) / n58)
lo_e, hi_e = (lambda c, h: (c - h, c + h))(*(lambda den: ((p0 + Z95**2 / (2 * n58)) / den,
                                                       Z95 * math.sqrt(p0 * (1 - p0) / n58 + Z95**2 / (4 * n58**2)) / den))(1 + Z95**2 / n58))
sims = RNG.binomial(n58, p0, size=1_000_000) / n58
se_sim = float(sims.std(ddof=1))
rec("E13_leaderboard_SE", "estimator", "58-task leaderboard at p = 0.20: SE = 5.25%", "PDF p.1 Sec 1 item 2",
    5.25, round(100 * se, 4), simulated=round(100 * se_sim, 4),
    sim_info="1,000,000 binomial(58, 0.2) draws; SE of the SD estimate ~ SD/sqrt(2n) = "
             f"{100 * se_sim / math.sqrt(2e6):.4f} pts", tolerance=0.01)
rec("E13_leaderboard_wilson_halfwidth", "estimator", "95% Wilson CI width +/-9.8 pts at p = 0.20, n = 58",
    "PDF p.1 Sec 1 item 2", 9.8, round(100 * (hi_e - lo_e) / 2, 4), tolerance=0.05,
    reason=f"Wilson interval at p=0.20 exactly: [{100 * lo_e:.2f}, {100 * hi_e:.2f}]; half-width computed. "
           f"Normal-approx half-width 1.96*SE = {100 * Z95 * se:.2f}.")
rec("E13_pts_per_task", "metric", "1.72 pts/task on a 58-task board", "PDF p.1 Sec 1 item 2", 1.72,
    round(100 / 58, 4), tolerance=0.005)
swing = float(np.mean(np.abs(RNG.binomial(n58, p0, 1_000_000) - RNG.binomial(n58, p0, 1_000_000)) / n58 >= 0.05))
rec("E13_swing", "estimator", "Two T=1.0 runs 'routinely swing by 5 to 7 points'", "PDF p.1 Sec 1 item 2",
    "routine (qualitative)", None, simulated={"P(|run1-run2| >= 5 pts)": round(swing, 4)},
    sim_info="1,000,000 pairs of independent binomial(58, 0.2) runs",
    verdict="VERIFIED" if swing > 0.3 else "MISMATCH",
    reason="Under pure binomial noise, a gap of 5 or more points between two independent runs has the simulated probability shown.")

# ---------------------------------------------------------------- E14 low-action-entropy detector
def entropy_bits(counts):
    c = np.array(counts, float); c = c[c > 0]; p = c / c.sum()
    return abs(float(-(p * np.log2(p)).sum()))


W = 4
parts = sorted({tuple(sorted(Counter_vals, reverse=True)) for Counter_vals in
                (tuple(np.bincount(np.array(seq), minlength=W)[np.bincount(np.array(seq), minlength=W) > 0])
                 for seq in itertools.product(range(W), repeat=W))})
levels = sorted({round(entropy_bits(p), 4) for p in parts})
fires = [l for l in levels if l < 0.55]
rec("E14_entropy_detector", "estimator", "H_W(t) < 0.55 bits with W = 4 flags low action entropy",
    "PDF p.3 Sec 3.4; PAPER.md Sec 3.4", 0.55,
    {"achievable_H_values_bits": levels, "values_below_0.55": fires,
     "equivalent_threshold_range": [0.0, levels[1]]},
    verdict="VERIFIED",
    reason=f"With W = 4 the only achievable entropy below 0.55 is 0 (all 4 actions identical); the next level is "
           f"{levels[1]} bits. The detector is therefore 'four identical actions in a row', and any threshold in "
           f"(0, {levels[1]}] behaves identically. Formula well-defined; 0.55 is not a calibrated value.")

# ---------------------------------------------------------------- E15 context budget arithmetic
rec("E15_context_budget", "definition", "Compaction at 14,336 tokens 'reserving 8,192 output tokens' within 32,768",
    "PDF p.1 Sec 1 item 1", 32768, {"14336+8192": 14336 + 8192, "32768-14336": 32768 - 14336},
    verdict="NOT CHECKABLE",
    reason="14,336 + 8,192 = 22,528, which leaves 10,240 of the 32,768 window unexplained; the paper does not "
           "say how the remaining budget is used.")

# ---------------------------------------------------------------- E16 Wilcoxon
rec("E16_wilcoxon", "estimator", "Wilcoxon p = 8.91e-07 (< 1e-6) on post-reset KV", "PDF p.1 Abstract; PAPER.md Sec 5 log",
    8.91e-7, {"min_exact_two_sided_p_n25": 2 / 2**25, "min_exact_two_sided_p_n100": 2 / 2**100},
    verdict="NOT CHECKABLE",
    reason="Per-episode KV values not released; the value lies within the attainable range for n = 25 (minimum exact p = 5.96e-08) and n = 100. "
           "Unclear whether n = 25 tasks or 100 trajectories.")

# ======================================================================= plots (300 DPI)
plt.rcParams.update({"font.size": 9, "figure.dpi": 100})


def save(fig, name):
    fig.tight_layout(); fig.savefig(FIG / name, dpi=300); plt.close(fig)


# P1 dilution vs |B|
nb = np.linspace(0, 20000, 400)
fig, ax = plt.subplots(figsize=(5.2, 3.0))
for g, ls in [(-1.0, ":"), (0.0, "-"), (1.0, "--")]:
    ax.plot(nb, 1 - nA_tok / (nA_tok + nb * math.exp(g)), ls, label=f"logit gap L_B - L_A per token = {g:+.0f}")
ax.axhline(0.72, color="#b91c1c", lw=0.8); ax.text(8000, 0.67, "paper: dilution 0.72 before reset", color="#b91c1c", fontsize=7)
ax.axhline(0.06, color="#15803d", lw=0.8); ax.text(8000, 0.08, "paper: 0.06 after G-CCR", color="#15803d", fontsize=7)
ax.axvspan(14336 - nA_tok, 20000, color="#fecaca", alpha=0.4); ax.text(14200, 0.13, "past 14,336\ncompaction", fontsize=7)
ax.set_xlabel("|B_t| (failed-turn tokens), |A| = 512"); ax.set_ylabel("attention mass on B_t (dilution)")
ax.legend(fontsize=7, loc="center right"); ax.set_ylim(0, 1.02)
save(fig, "sens_prop1_dilution.png")

# P2 TV vs tau
fig, ax = plt.subplots(figsize=(5.2, 3.0))
ax.errorbar(taus, tv_mean, yerr=np.array(tv_se) * 2, marker="o", ms=3, capsize=2)
ax.axvspan(0.05, 0.3, color="#fecaca", alpha=0.5); ax.text(0.07, max(tv_mean) * 0.9, "low-tau regime\n(tau 0.2, 0.25)", fontsize=7)
ax.axvline(1.0, color="#15803d", ls="--"); ax.text(1.03, max(tv_mean) * 0.6, "calibrated tau = 1.0", color="#15803d", fontsize=7)
ax.set_xscale("log"); ax.set_xlabel("temperature tau"); ax.set_ylabel("TV(p, p + quant noise)")
ax.set_title(f"sigma_q = {sigma_q} (illustrative), +/-2 MC SE", fontsize=8)
save(fig, "sens_law1_tau.png")

# P3 binomial SE vs n
ns = np.arange(10, 400)
fig, ax = plt.subplots(figsize=(5.2, 3.0))
for pp in (0.2, 0.4):
    ax.plot(ns, 100 * Z95 * np.sqrt(pp * (1 - pp) / ns), label=f"95% half-width (normal approx.), p = {pp}")
for n_, lab in [(25, "Trap-25"), (58, "58-task board"), (129, "swegemma 129")]:
    ax.axvline(n_, color="grey", ls=":"); ax.text(n_ + 3, 21, lab, fontsize=7, rotation=90)
ax.axhspan(10, 30, color="#fecaca", alpha=0.4); ax.text(250, 12, "CI wider than +/-10 pts", fontsize=7)
ax.set_xlabel("number of tasks n"); ax.set_ylabel("half-width (pts)"); ax.legend(fontsize=7); ax.set_ylim(0, 30)
save(fig, "sens_binomial_noise.png")

# P4 Fisher p vs ccr successes
ks = np.arange(4, 26)
pf = [stats.fisher_exact([[k, 25 - k], [4, 21]])[1] for k in ks]
pm = [mcnemar_exact(k - 4, 0) if k > 4 else 1.0 for k in ks]
fig, ax = plt.subplots(figsize=(5.2, 3.0))
ax.semilogy(ks, pf, "o-", ms=3, label="Fisher exact (unpaired)")
ax.semilogy(ks, pm, "s--", ms=3, label="exact McNemar, best case c = 0 (paired)")
ax.axhline(0.05, color="#b91c1c", lw=0.8); ax.text(4.3, 0.07, "alpha = 0.05", fontsize=7, color="#b91c1c")
ax.axvline(24, color="#15803d", ls="--"); ax.text(22.2, 1e-2, "paper: 24/25", fontsize=7, color="#15803d")
ax.axhline(4.2e-9, color="grey", ls=":"); ax.text(4.3, 6e-9, "paper p = 4.2e-9", fontsize=7)
ax.set_xlabel("ccr_adaptive traps solved (baseline fixed at 4/25)"); ax.set_ylabel("two-sided p"); ax.legend(fontsize=7)
save(fig, "sens_trap25_pvalue.png")

# P5 entropy levels
fig, ax = plt.subplots(figsize=(5.2, 2.6))
part_names = {tuple(p): entropy_bits(p) for p in parts}
for j, (p_, h) in enumerate(sorted(part_names.items(), key=lambda x: x[1])):
    lab = "+".join(str(int(c)) for c in p_) + f"\nH = {h:.3f}"
    ax.plot([h], [0], "o", ms=7)
    ax.annotate(lab, (h, 0), textcoords="offset points", xytext=(0, 12 if j % 2 == 0 else -30), ha="center", fontsize=7)
ax.axvspan(0, 0.55, color="#fecaca", alpha=0.5); ax.axvline(0.55, color="#b91c1c"); ax.text(0.57, 0.7, "paper threshold 0.55", fontsize=7, color="#b91c1c")
ax.set_yticks([]); ax.set_ylim(-1, 1); ax.set_xlabel("H_W (bits), W = 4: action-count patterns")
save(fig, "sens_entropy_detector.png")

# ======================================================================= JSON
summary = {}
for r in records:
    summary[r["verdict"]] = summary.get(r["verdict"], 0) + 1
out = {"paper": "Breaking the 15-Minute Cliff in Quantized Gemma 4 Coding Agents (Mirbahar 2026)",
       "primary_source": "paper/Robina_Mirbahar_Gemma4_SWE_Agent_Paper_2026.pdf (PAPER.md used where noted)",
       "seed": SEED, "numpy": np.__version__, "scipy": __import__("scipy").__version__,
       "verdict_counts": summary, "equations": records}


def _default(o):
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, np.bool_): return bool(o)
    raise TypeError(type(o))


(OUT / "eq_verified_numbers.json").write_text(json.dumps(out, indent=2, default=_default))
print(json.dumps(summary))
for r in records:
    print(f"{r['verdict']:14s} {r['id']:40s} paper={r['paper_value']!s:.40s} computed={r['computed']!s:.70s}")
