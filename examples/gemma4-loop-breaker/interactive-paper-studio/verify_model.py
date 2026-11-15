#!/usr/bin/env python3
"""Reference implementation of every quantity the interactive page computes.

Sources are cited as [PDF §x / Table y]. The PDF is the authoritative text; PAPER.md is the
markdown companion. Writes preset_values.json, which index.html embeds and the node check compares.

Quantities with no closed form in the paper (per-turn token growth, the A/B logit gap, sigma_q) are
free inputs, labelled as illustrative; nothing here back-fits them to a published number.
"""
import json
import math
import os
import sys

Z95 = 1.959963984540054  # two-sided 95% normal quantile, used by the Wilson interval

# ---------------------------------------------------------------- published data
# Table 1 (PDF §3.2): Stage-1 isolated patch synthesis, 129 tasks.
TABLE1 = [
    {"id": "t1_baseline", "label": "Non-thinking low-temp baseline", "tau": 0.20, "topk": 40,
     "budget": 0, "k": 23, "n": 129, "pub_rate": 17.8, "pub_ci": [12.2, 25.3]},
    {"id": "t1_hidden", "label": "Low-temp thinking (hidden thoughts)", "tau": 0.25, "topk": 40,
     "budget": 4096, "k": 35, "n": 129, "pub_rate": 27.1, "pub_ci": [20.2, 35.4]},
    {"id": "t1_calibrated", "label": "Calibrated thinking mode", "tau": 1.00, "topk": 64,
     "budget": 4096, "k": 51, "n": 129, "pub_rate": 39.5, "pub_ci": [31.5, 48.1]},
]
# Table 2 (PDF §3.3): cumulative end-to-end ablation, 129 tasks.
TABLE2 = [
    {"id": "M0", "label": "Default starter template (T=0.2, 9 tools)", "calls": 24.6, "peak_kv": 28400, "compact": 68.2, "k": 15, "pub_rate": 11.6, "pub_ci": [7.2, 18.3], "heldout": 0.121},
    {"id": "M1", "label": "+ Lean-6 workspace toolset", "calls": 21.2, "peak_kv": 22100, "compact": 44.0, "k": 18, "pub_rate": 14.0, "pub_ci": [9.0, 21.0], "heldout": 0.138},
    {"id": "M2", "label": "+ Calibrated thinking sampling (T=1.0)", "calls": 18.9, "peak_kv": 18600, "compact": 31.0, "k": 22, "pub_rate": 17.1, "pub_ci": [11.5, 24.5], "heldout": 0.172},
    {"id": "M3", "label": "+ Turn-1 6-relation parser + 120-line reads", "calls": 15.4, "peak_kv": 11200, "compact": 8.5, "k": 25, "pub_rate": 19.4, "pub_ci": [13.5, 27.0], "heldout": 0.190},
    {"id": "M4", "label": "+ Call-12 source-edit deadline", "calls": 13.8, "peak_kv": 10400, "compact": 6.2, "k": 27, "pub_rate": 20.9, "pub_ci": [14.8, 28.7], "heldout": 0.207},
    {"id": "M5", "label": "+ Structural co-change coupling", "calls": 13.1, "peak_kv": 9850, "compact": 5.4, "k": 29, "pub_rate": 22.5, "pub_ci": [16.1, 30.4], "heldout": 0.224},
    {"id": "M6", "label": "+ Graph backtrack + red-test submit", "calls": 12.4, "peak_kv": 9420, "compact": 4.7, "k": 31, "pub_rate": 24.0, "pub_ci": [17.5, 32.1], "heldout": 0.241},
]
# Table 3 (PDF §3.4): Trap-25 loop recovery.
TABLE3 = [
    {"id": "baseline_static", "label": "baseline_static (unpruned)", "reset": False, "k": 4, "n": 25, "pub_rate": 16.0, "pub_ci": [6.4, 34.7], "turns": 11.04, "think": 45220, "pub_think_pct": 0.0, "post_kv": 159816, "pub_kv_pct": 0.0, "peak_kv": 24821},
    {"id": "naive_subagent", "label": "naive_subagent (full handoff)", "reset": False, "k": 5, "n": 25, "pub_rate": 20.0, "pub_ci": [8.9, 39.1], "turns": 10.72, "think": 51118, "pub_think_pct": 13.0, "post_kv": 190410, "pub_kv_pct": 19.1, "peak_kv": 31067},
    {"id": "ccr_only", "label": "ccr_only (pruning + ledger)", "reset": True, "k": 18, "n": 25, "pub_rate": 72.0, "pub_ci": [52.4, 85.7], "turns": 8.76, "think": 35881, "pub_think_pct": -20.7, "post_kv": 85148, "pub_kv_pct": -46.7, "peak_kv": 14488},
    {"id": "ccr_adaptive", "label": "ccr_adaptive (G-CCR + adaptive thinking)", "reset": True, "k": 24, "n": 25, "pub_rate": 96.0, "pub_ci": [80.5, 99.3], "turns": 6.96, "think": 24842, "pub_think_pct": -45.1, "post_kv": 46689, "pub_kv_pct": -70.8, "peak_kv": 10563},
]
COMPACTION_CLIFF = 14336      # PDF §1 item 1
LEDGER_TOKENS = 150           # PDF §3.4
THRESH = {"c_err": 2, "s_diff": 0.82, "h_w": 0.55, "W": 4}  # PDF §3.4


# ---------------------------------------------------------------- model functions (mirrored in JS)
def rate(k, n):
    return 100.0 * k / n


def wilson(k, n, z=Z95):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [100 * (c - h), 100 * (c + h)]


def pct_change(new, old):
    return 100.0 * (new - old) / old


def log_fact(n):
    return sum(math.log(i) for i in range(2, n + 1))


def hyper_logp(a, r1, c1, n):
    # P(X=a) for the 2x2 table with row-1 total r1, column-1 total c1, grand total n
    return (log_fact(r1) + log_fact(n - r1) + log_fact(c1) + log_fact(n - c1)
            - log_fact(n) - log_fact(a) - log_fact(r1 - a) - log_fact(c1 - a) - log_fact(n - r1 - c1 + a))


def fisher(k1, n1, k2, n2):
    """Fisher's exact test on [[k1, n1-k1], [k2, n2-k2]]. Returns (two_sided, one_sided_greater)."""
    n = n1 + n2
    c1 = k1 + k2
    lo, hi = max(0, c1 - n2), min(n1, c1)
    lp_obs = hyper_logp(k1, n1, c1, n)
    two = 0.0
    greater = 0.0
    for a in range(lo, hi + 1):
        lp = hyper_logp(a, n1, c1, n)
        if lp <= lp_obs + 1e-7:
            two += math.exp(lp)
        if a >= k1:
            greater += math.exp(lp)
    return min(1.0, two), min(1.0, greater)


def window_entropy(actions):
    """Shannon entropy (bits) of the action distribution in the window (PDF §3.4 detector 3)."""
    counts = {}
    for a in actions:
        counts[a] = counts.get(a, 0) + 1
    w = len(actions)
    return -sum((c / w) * math.log2(c / w) for c in counts.values())


def noise_logodds_sd(tau, sigma_q):
    """Std of the log-odds shift between two tokens under exp((z+eps)/tau), eps~N(0,sigma_q^2) iid.
    Follows directly from the expression in PDF §3.2: (eps_v - eps_w)/tau has sd sqrt(2)*sigma_q/tau."""
    return math.sqrt(2.0) * sigma_q / tau


def dilution(a_tok, b_tok, gap):
    """Share of attention on B under Proposition 1 with an ILLUSTRATIVE assumption:
    exp(L_S) = |S| * exp(l_S), i.e. uniform per-token logits within each block, gap = l_B - l_A.
    The paper gives the two-block softmax form but no closed form for L_{h,B_t} as |B_t| grows."""
    eb = b_tok * math.exp(gap)
    return eb / (a_tok + eb)


def trajectory(a_tok, per_turn, gap, turns, reset, c_thr=THRESH["c_err"], ledger=LEDGER_TOKENS):
    """Toy worst-case loop: every turn fails with the same error signature and appends per_turn
    tokens to B. With reset on, when the repeat count reaches c_thr, B is pruned and a ledger of
    `ledger` tokens joins A (PDF §3.4). Returns per-turn lists."""
    a, b, rep = float(a_tok), 0.0, 0
    out = {"ctx": [], "dil": [], "reset_at": []}
    for t in range(1, turns + 1):
        b += per_turn
        rep += 1
        if reset and rep >= c_thr:
            b = 0.0
            a += ledger
            rep = 0
            out["reset_at"].append(t)
        out["ctx"].append(a + b)
        out["dil"].append(dilution(a, b, gap))
    return out


def first_cross(ctx, cliff=COMPACTION_CLIFF):
    for i, v in enumerate(ctx):
        if v > cliff:
            return i + 1
    return 0


# ---------------------------------------------------------------- presets
# Slider defaults: tau from the paper; the rest are illustrative (paper gives no value).
SLIDER_DEFAULTS = {"a_tok": 2000, "per_turn": 1500, "gap": 0.0, "turns": 12, "sigma_q": 1.0}

PRESETS = [
    {"id": "baseline", "name": "Unpruned greedy baseline", "tau": 0.20, "reset": False,
     "t1": "t1_baseline", "t2": "M0", "t3": "baseline_static",
     "cite": "Table 1 row 1 (tau 0.20), Table 2 M0, Table 3 baseline_static"},
    {"id": "hidden", "name": "Low-temp hidden thinking", "tau": 0.25, "reset": False,
     "t1": "t1_hidden", "t2": "M1", "t3": "naive_subagent",
     "cite": "Table 1 row 2 (tau 0.25), Table 2 M1, Table 3 naive_subagent"},
    {"id": "ccr_only", "name": "CCR pruning only", "tau": 1.00, "reset": True,
     "t1": "t1_calibrated", "t2": "M3", "t3": "ccr_only",
     "cite": "Table 1 row 3 (tau 1.00), Table 2 M3, Table 3 ccr_only"},
    {"id": "optimum", "name": "Calibrated optimum (G-CCR)", "tau": 1.00, "reset": True,
     "t1": "t1_calibrated", "t2": "M6", "t3": "ccr_adaptive",
     "cite": "Table 1 row 3 (tau 1.00), Table 2 M6, Table 3 ccr_adaptive"},
]


def by_id(rows, i):
    return next(r for r in rows if r["id"] == i)


def preset_readout(p, s=SLIDER_DEFAULTS):
    t1, t2, t3 = by_id(TABLE1, p["t1"]), by_id(TABLE2, p["t2"]), by_id(TABLE3, p["t3"])
    b3 = TABLE3[0]
    two, one = fisher(t3["k"], t3["n"], b3["k"], b3["n"])
    tr = trajectory(s["a_tok"], s["per_turn"], s["gap"], s["turns"], p["reset"])
    return {
        "t1_rate": rate(t1["k"], t1["n"]),
        "t1_ci_lo": wilson(t1["k"], t1["n"])[0], "t1_ci_hi": wilson(t1["k"], t1["n"])[1],
        "t1_delta_pts": rate(t1["k"], t1["n"]) - rate(TABLE1[0]["k"], TABLE1[0]["n"]),
        "t2_rate": rate(t2["k"], 129),
        "t2_ci_lo": wilson(t2["k"], 129)[0], "t2_ci_hi": wilson(t2["k"], 129)[1],
        "t2_compaction_change_pct": pct_change(t2["compact"], TABLE2[0]["compact"]),
        "t3_rate": rate(t3["k"], t3["n"]),
        "t3_ci_lo": wilson(t3["k"], t3["n"])[0], "t3_ci_hi": wilson(t3["k"], t3["n"])[1],
        "t3_fisher_two_sided": two, "t3_fisher_one_sided": one,
        "t3_kv_pct": pct_change(t3["post_kv"], b3["post_kv"]),
        "t3_think_pct": pct_change(t3["think"], b3["think"]),
        "noise_sd_over_sigma": noise_logodds_sd(p["tau"], s["sigma_q"]),
        "toy_peak_dilution": max(tr["dil"]),
        "toy_peak_ctx": max(tr["ctx"]),
        "toy_cliff_turn": first_cross(tr["ctx"]),
        "toy_resets": len(tr["reset_at"]),
    }


# ---------------------------------------------------------------- grounding checks
def grounding():
    rows = []

    def add(quantity, sim, pub, cite, tol=0.05, note=""):
        ok = None if pub is None else abs(sim - pub) <= tol
        rows.append({"quantity": quantity, "sim": sim, "pub": pub, "cite": cite, "match": ok, "note": note})

    for r in TABLE1:
        add(f"Table 1 {r['label']}: rate %", rate(r["k"], r["n"]), r["pub_rate"], "PDF Table 1")
        lo, hi = wilson(r["k"], r["n"])
        add(f"Table 1 {r['label']}: Wilson lo %", lo, r["pub_ci"][0], "PDF Table 1")
        add(f"Table 1 {r['label']}: Wilson hi %", hi, r["pub_ci"][1], "PDF Table 1",
            note="48.157 rounds to 48.2; paper prints 48.1" if r["id"] == "t1_calibrated" else "")
    for r in TABLE2:
        add(f"Table 2 {r['id']}: rate %", rate(r["k"], 129), r["pub_rate"], "PDF Table 2")
        lo, hi = wilson(r["k"], 129)
        add(f"Table 2 {r['id']}: Wilson lo %", lo, r["pub_ci"][0], "PDF Table 2")
        add(f"Table 2 {r['id']}: Wilson hi %", hi, r["pub_ci"][1], "PDF Table 2")
    for r in TABLE3:
        add(f"Table 3 {r['id']}: escape %", rate(r["k"], r["n"]), r["pub_rate"], "PDF Table 3")
        lo, hi = wilson(r["k"], r["n"])
        add(f"Table 3 {r['id']}: Wilson lo %", lo, r["pub_ci"][0], "PDF Table 3")
        add(f"Table 3 {r['id']}: Wilson hi %", hi, r["pub_ci"][1], "PDF Table 3")
        add(f"Table 3 {r['id']}: think-token change %", pct_change(r["think"], TABLE3[0]["think"]), r["pub_think_pct"], "PDF Table 3")
        add(f"Table 3 {r['id']}: post-reset KV change %", pct_change(r["post_kv"], TABLE3[0]["post_kv"]), r["pub_kv_pct"], "PDF Table 3")
    two, one = fisher(24, 25, 4, 25)
    add("Fisher exact p, 24/25 vs 4/25 (two-sided) x1e9", two * 1e9, 4.2, "Abstract, §3.4, §5",
        note="Paper value matches neither tail; one-sided = %.3g" % one)
    add("Fisher exact p, 24/25 vs 4/25 (one-sided) x1e9", one * 1e9, 4.2, "Abstract, §3.4, §5")
    add("Compaction change M0 -> M6 %", pct_change(4.7, 68.2), -93.0, "Abstract (-93%)", tol=0.5)
    add("M0 -> M1 compaction drop, points", 68.2 - 44.0, 24.2, "§4 (-24.2 pts)")
    add("M6 / M0 solved ratio", 31 / 15, 2.1, "PAPER.md §3.3 (2.1x)", tol=0.05)
    add("Stage-1 gain, points", rate(51, 129) - rate(23, 129), 21.7, "§4 (+21.7 pts)")
    add("Localization-Trajectory Tax, points (Table 1 row 3 - M2)", rate(51, 129) - rate(22, 129), 22.4, "§3.3", tol=0.1,
        note="paper subtracts the rounded rates 39.5 - 17.1")
    add("Tasks lost, Table 1 row 3 - M2", 51 - 22, 29, "§3.3", tol=0)
    add("Fraction of 29-task gap recovered by M2 -> M6", (31 - 22) / 29, 0.5, "§3.3 ('recovers half')", tol=0.05,
        note="M0->M6 gains 16 tasks, M2->M6 gains 9; neither is half of 29 (16/29 = 0.552 is closest)")
    add("Fraction of 29-task gap: M0 -> M6 gain / 29", (31 - 15) / 29, 0.5, "§3.3 ('recovers half')")
    add("Trap-25 gain, points", rate(24, 25) - rate(4, 25), 80.0, "§4 (+80.0 pts)")
    add("D1 thinking-budget cut %", pct_change(512, 4096), -87.5, "§3.1")
    add("Multi-LoRA memory change % (18.4 vs 54.6 GB)", pct_change(18.4, 54.6), -66.3, "PAPER.md §4")
    add("Binomial SE, p=0.20, n=58, %", 100 * math.sqrt(0.2 * 0.8 / 58), 5.25, "PDF §1 item 2")
    lo, hi = wilson(0.2 * 58, 58)
    add("Wilson 95% half-width, p=0.20, n=58, points", (hi - lo) / 2, 9.8, "PDF §1 item 2",
        note="Normal-approx half-width is %.2f; neither gives 9.8" % (100 * Z95 * math.sqrt(0.16 / 58)))
    add("Per-repo M0 solved sum (7+6+2+0)", 7 + 6 + 2 + 0, 15, "§3.3 per-repo rates x repo sizes", tol=0)
    add("Per-repo M6 solved sum (15+12+3+1)", 15 + 12 + 3 + 1, 31, "§3.3 per-repo rates x repo sizes", tol=0)
    for repo, n, k0, k6, p0, p6 in [("fastapi", 67, 7, 15, 10.4, 22.4), ("rich", 48, 6, 12, 12.5, 25.0),
                                     ("requests", 13, 2, 3, 15.4, 23.1)]:
        add(f"{repo} M0 rate % ({k0}/{n})", rate(k0, n), p0, "§3.3")
        add(f"{repo} M6 rate % ({k6}/{n})", rate(k6, n), p6, "§3.3")
    # 0.72 -> 0.06 "+4.51 bits": try the obvious readings
    cands = {"log2(0.72/0.06)": math.log2(0.72 / 0.06),
             "-log2(0.06)": -math.log2(0.06),
             "log2 odds ratio": math.log2((0.72 / 0.28) / (0.06 / 0.94)),
             "log2(0.94/0.28)": math.log2(0.94 / 0.28)}
    for k, v in cands.items():
        add(f"Dilution 0.72 -> 0.06 as bits: {k}", v, 4.51, "§3.1", note="no stated reading reproduces 4.51")
    return rows


def main():
    outdir = os.path.dirname(os.path.abspath(__file__))
    # sanity-check the hand-rolled Fisher and Wilson against scipy where available
    try:
        from scipy.stats import fisher_exact
        sp2 = fisher_exact([[24, 1], [4, 21]]).pvalue
        sp1 = fisher_exact([[24, 1], [4, 21]], alternative="greater").pvalue
        f2, f1 = fisher(24, 25, 4, 25)
        print(f"fisher two-sided ours={f2:.6e} scipy={sp2:.6e}; one-sided ours={f1:.6e} scipy={sp1:.6e}")
        assert abs(f2 - sp2) / sp2 < 1e-9 and abs(f1 - sp1) / sp1 < 1e-9
    except ImportError:
        print("scipy not available; skipped cross-check", file=sys.stderr)

    ent = {}
    for name, w in [("AAAA", "AAAA"), ("AAAB", "AAAB"), ("AABB", "AABB"), ("AABC", "AABC"), ("ABCD", "ABCD")]:
        ent[name] = window_entropy(list(w))

    out = {
        "slider_defaults": SLIDER_DEFAULTS,
        "presets": [{**p, "readout": preset_readout(p)} for p in PRESETS],
        "entropy_patterns_W4": ent,
        "grounding": grounding(),
        "tables": {"t1": TABLE1, "t2": TABLE2, "t3": TABLE3},
        "constants": {"cliff": COMPACTION_CLIFF, "ledger": LEDGER_TOKENS, "thresh": THRESH},
    }
    with open(os.path.join(outdir, "preset_values.json"), "w") as f:
        json.dump(out, f, indent=1)
    for p in out["presets"]:
        print(p["id"], {k: round(v, 6) for k, v in p["readout"].items()})
    print("entropy W=4:", {k: round(v, 4) for k, v in ent.items()})
    g = out["grounding"]
    print(f"grounding: {sum(1 for r in g if r['match'])} match, {sum(1 for r in g if r['match'] is False)} mismatch of {len(g)}")
    for r in g:
        if r["match"] is False:
            print("  MISMATCH", r["quantity"], round(r["sim"], 4), "vs", r["pub"], r["note"])


if __name__ == "__main__":
    main()
