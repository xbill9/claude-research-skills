"""Build story_numbers.json: every number the comic shows, quoted from the paper PDF with its source.

Primary source: paper/Robina_Mirbahar_Gemma4_SWE_Agent_Paper_2026.pdf (5 pages).
Derived entries are computed here from quoted inputs, and each quoted percentage is
re-checked against its own fraction, so the story never relies on arithmetic done by hand.

    python3 story_numbers_build.py      -> writes story_numbers.json, prints checks
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PDF = "Robina_Mirbahar_Gemma4_SWE_Agent_Paper_2026.pdf"

N: dict[str, dict] = {}


def q(key, value, display, source, quote):
    """A number quoted from the paper."""
    assert key not in N, key
    N[key] = {"value": value, "display": display, "source": f"{PDF} {source}", "quote": quote, "derived": False}


def d(key, value, display, formula, inputs):
    """A number computed in code from quoted inputs."""
    assert key not in N, key
    for i in inputs:
        assert i in N, i
    N[key] = {"value": value, "display": display, "formula": formula, "inputs": inputs, "derived": True,
              "source": "computed in story_numbers_build.py from " + ", ".join(inputs)}


# ---- Setup: p.1 abstract and Section 1 -------------------------------------------------------
q("tasks", 129, "129", "p.1 Abstract", "Across the 129-task two-container swegemma benchmark")
q("traps", 25, "25", "p.1 Abstract", "a controlled 25-task fault-injection suite (Trap-25)")
q("repo_fastapi", 67, "67", "p.1 Section 1", "fastapi/fastapi: 67")
q("repo_rich", 48, "48", "p.1 Section 1", "Textualize/rich: 48")
q("repo_requests", 13, "13", "p.1 Section 1", "psf/requests: 13")
q("repo_httpx", 1, "1", "p.1 Section 1", "encode/httpx: 1")
q("gpus", 4, "4", "p.1 Section 1", "runs on four NVIDIA L4 GPUs (96 GB total VRAM)")
q("vram_gb", 96, "96 GB", "p.1 Section 1", "four NVIDIA L4 GPUs (96 GB total VRAM)")
q("max_model_len", 32768, "32,768", "p.1 Section 1", "vLLM (max_model_len = 32,768)")
q("turns", 937, "937", "p.1 Section 1", "Auditing 937 turns of live trajectory telemetry")
q("compaction_cliff", 14336, "14,336", "p.1 Section 1 item 1", "once dialogue history exceeds 14,336 tokens")
q("output_reserve", 8192, "8,192", "p.1 Section 1 item 1", "(reserving 8,192 output tokens)")
q("call_cap", 28, "28", "p.1 Section 1 item 2", "Each episode is capped at 28 tool calls")
q("time_cap_lo", 240, "240", "p.1 Section 1 item 2", "240 to 480 seconds")
q("time_cap_hi", 480, "480", "p.1 Section 1 item 2", "240 to 480 seconds")
q("global_hours", 12, "12-hour", "p.1 Section 1 item 2", "under a 12-hour global wall-clock budget")
q("file_reads_trip", 2, "Two", "p.1 Section 1 item 1", "Two unwindowed file reads trip lossy summarization")

# ---- Section 3.1, p.2 -------------------------------------------------------------------------
q("dilution_before", 0.72, "0.72", "p.2 Section 3.1", "cuts softmax dilution from 0.72 to 0.06")
q("dilution_after", 0.06, "0.06", "p.2 Section 3.1", "cuts softmax dilution from 0.72 to 0.06")
q("bits_gain", 4.51, "+4.51 bits", "p.2 Section 3.1", "(+4.51 bits effective attention)")
q("serializations", 90, "90", "p.2 Section 3.1", "Across 90 controlled serializations")
q("window_lines", 120, "120-line", "p.2 Section 3.1", "retaining a 120-line 1-hop incidence window")
q("budget_full", 4096, "4096", "p.2 Section 3.1", "cuts D1 file-read budgets by 87.5% (4096 to 512)")
q("budget_d1", 512, "512", "p.2 Section 3.1", "cuts D1 file-read budgets by 87.5% (4096 to 512)")
q("budget_cut_pct", 87.5, "87.5%", "p.2 Section 3.1", "cuts D1 file-read budgets by 87.5%")
q("budget_ldp_lo", 2048, "2048", "p.2 Section 3.1", "reserves 2048 to 4096 tokens for LDP co-change edits")
q("budget_ldw", 6144, "6144", "p.2 Section 3.1", "allocates a 6144-token LDW burst after context reset")

# ---- Table 1, p.2 -----------------------------------------------------------------------------
for k, solved, pct, ci, cfg, tk in [
    ("t1_base", 23, 17.8, "[12.2%, 25.3%]", "0 (Off) / false", "0.20 / 40"),
    ("t1_hidden", 35, 27.1, "[20.2%, 35.4%]", "4096 / false", "0.25 / 40"),
    ("t1_calib", 51, 39.5, "[31.5%, 48.1%]", "4096 / true", "1.00 / 64"),
]:
    q(f"{k}_solved", solved, f"{solved}/129", "p.2 Table 1", f"{solved} / 129")
    q(f"{k}_rate", pct, f"{pct}%", "p.2 Table 1", f"{pct}% {ci}")
    q(f"{k}_ci", ci, ci, "p.2 Table 1", f"{pct}% {ci}")
    q(f"{k}_tempk", tk, tk, "p.2 Table 1", f"Temp / top-k = {tk}")
    q(f"{k}_think", cfg, cfg, "p.2 Table 1", f"Think Budget / Thoughts = {cfg}")
q("calib_T", 1.0, "1.0", "p.2 Section 3.2", "Calibrating tau = 1.0, top-p = 0.95, top-k = 64")
q("calib_top_p", 0.95, "0.95", "p.2 Section 3.2", "top-p = 0.95")
q("calib_top_k", 64, "64", "p.2 Section 3.2", "top-k = 64")
q("greedy_tau", 0.2, "0.2", "p.2 Section 3.2", "Under greedy/low-temperature decoding (tau = 0.2)")
q("t1_mcnemar", 1.8e-6, "1.8×10⁻⁶", "p.2 Section 3.2 / Table 1 caption", "McNemar paired p = 1.8x10-6")
q("t1_gain_pts_quoted", 21.7, "+21.7 pts", "p.4 Section 4", "(+21.7 pts Stage-1 synthesis)")

# ---- Section 3.3 / Table 2, p.3 ---------------------------------------------------------------
q("turns_1_4", "1-4", "Turns 1 to 4", "p.3 Section 3.3", "(Turn 1-4 Recall@3 = 0.448)")
q("turn_1_fix", 1, "Turn 1", "p.4 Section 5", "running pytest -vv --tb=short on Turn 1 decomposes compound assertions")
q("tax_pts", 22.4, "22.4-point", "p.3 Section 3.3", "exposes a 22.4-point Localization-Trajectory Tax")
q("tax_tasks", 29, "29", "p.3 Section 3.3", "29 solvable tasks are lost")
q("recall_before", 0.448, "0.448", "p.3 Section 3.3", "(Turn 1-4 Recall@3 = 0.448)")
q("recall_after", 0.931, "0.931", "p.3 Section 3.3", "(M3, Recall@3 = 0.931 [7])")
q("t2_mcnemar", 4.6e-5, "4.6×10⁻⁵", "p.3 Section 3.3 / Table 2 caption", "McNemar paired p = 4.6x10-5")
q("compaction_cut_quoted", 93, "-93%", "p.1 Abstract", "cutting context compaction from 68.2% to 4.7% (-93%)")
T2 = [
    ("M0", "Default starter (T=0.2, 9 tools)", 24.6, 28400, 68.2, 15, 11.6, 0.121),
    ("M1", "+ Lean-6 toolset", 21.2, 22100, 44.0, 18, 14.0, 0.138),
    ("M2", "+ Calibrated thinking", 18.9, 18600, 31.0, 22, 17.1, 0.172),
    ("M3", "+ Turn-1 contract parser + 120-line reads", 15.4, 11200, 8.5, 25, 19.4, 0.190),
    ("M4", "+ Call-12 edit deadline", 13.8, 10400, 6.2, 27, 20.9, 0.207),
    ("M5", "+ Co-change coupling", 13.1, 9850, 5.4, 29, 22.5, 0.224),
    ("M6", "+ Graph backtrack + red-test", 12.4, 9420, 4.7, 31, 24.0, 0.241),
]
for m, label, calls, kv, comp, solved, pct, held in T2:
    src = f"p.3 Table 2 row {m}"
    q(f"t2_{m}_label", label, label, src, "row label (shortened)")
    q(f"t2_{m}_calls", calls, f"{calls}", src, f"Calls = {calls}")
    q(f"t2_{m}_kv", kv, f"{kv:,}", src, f"Peak KV = {kv:,}")
    q(f"t2_{m}_comp", comp, f"{comp}%", src, f"Compacted = {comp}%")
    q(f"t2_{m}_solved", solved, f"{solved}/129", src, f"Solved = {solved}/129 ({pct}% ...)")
    q(f"t2_{m}_rate", pct, f"{pct}%", src, f"Solved = {solved}/129 ({pct}% ...)")
    q(f"t2_{m}_held", held, f"{held:.3f}", src, f"Held-Out = {held:.3f}")
q("peak_active_k", 10.6, "10.6k", "p.3 Figure 2 caption", "keeping active context (peak 10.6k) strictly below the 14,336-token compaction cliff")

# ---- Section 3.4 / Table 3, p.3-4 -------------------------------------------------------------
q("det_err", 2, "≥ 2", "p.3 Section 3.4", "(1) Repeated Error Signature Cerr(t) >= 2")
q("det_lcs", 0.82, "≥ 0.82", "p.3 Section 3.4", "(2) Oscillating Diff LCS Similarity Sdiff(t) >= 0.82")
q("det_entropy", 0.55, "< 0.55 bits", "p.3 Section 3.4", "(3) Low Action Entropy HW(t) < 0.55 bits (W = 4)")
q("det_window", 4, "W = 4", "p.3 Section 3.4", "(W = 4)")
q("ledger_tokens", 150, "150-token", "p.3 Section 3.4", "injects a 150-token <NEGATIVE_CONSTRAINT_LEDGER>")
q("burst_tau", 0.75, "τ = 0.75", "p.3 Section 3.4", "triggers a 6144-token LDW burst (tau = 0.75)")
q("episodes", 100, "100", "p.3 Section 3.4", "Across 100 AST-verified episodes")
q("sandbox_states", 75, "75", "p.3 Section 3.4", "(75 verified exec() sandbox states ...)")
q("fisher_p", 4.2e-9, "4.2×10⁻⁹", "p.4 Section 3.4", "(Fisher's Exact p = 4.2x10-9")
q("wilcoxon", "p < 10^-6", "p < 10⁻⁶", "p.1 Abstract", "(Wilcoxon p < 10-6)")
T3 = [
    ("baseline_static", "Unpruned", 4, 16.0, "[6.4, 34.7]", 11.04, "45,220 (0.0%)", 159816, "0.0%", 24821),
    ("naive_subagent", "Full Handoff", 5, 20.0, "[8.9, 39.1]", 10.72, "51,118 (+13.0%)", 190410, "+19.1%", 31067),
    ("ccr_only", "Pruning + Ledger", 18, 72.0, "[52.4, 85.7]", 8.76, "35,881 (-20.7%)", 85148, "-46.7%", 14488),
    ("ccr_adaptive", "My Method", 24, 96.0, "[80.5, 99.3]", 6.96, "24,842 (-45.1%)", 46689, "-70.8%", 10563),
]
for cfg, tag, solved, esc, ci, turns, think, kv, kvpct, peak in T3:
    src = f"p.4 Table 3 row {cfg}"
    q(f"t3_{cfg}_tag", tag, tag, src, f"{cfg} ({tag})")
    q(f"t3_{cfg}_solved", solved, f"{solved}/25", src, f"Solved = {solved} / 25")
    q(f"t3_{cfg}_esc", esc, f"{esc}%", src, f"Escape Rate = {esc}% {ci}")
    q(f"t3_{cfg}_ci", ci, ci, src, f"Escape Rate = {esc}% {ci}")
    q(f"t3_{cfg}_turns", turns, f"{turns:.2f}", src, f"Avg Turns = {turns:.2f}")
    q(f"t3_{cfg}_think", think, think, src, f"Avg Think Tok = {think}")
    q(f"t3_{cfg}_kv", kv, f"{kv:,}", src, f"Post-Reset KV = {kv:,} ({kvpct})")
    q(f"t3_{cfg}_kvpct", kvpct, kvpct, src, f"Post-Reset KV = {kv:,} ({kvpct})")
    q(f"t3_{cfg}_peak", peak, f"{peak:,}", src, f"Peak KV = {peak:,}")
q("trap_gain_pts_quoted", 80.0, "+80.0 pts", "p.4 Section 4", "(+80.0 pts Trap-25 escape)")

# ---- Section 4 and 5, p.4 ---------------------------------------------------------------------
q("sci_ccr", 5, "5/5", "p.4 Section 4", "G-CCR achieves 100% recovery (5/5 vs. 1/5 baseline)")
q("sci_base", 1, "1/5", "p.4 Section 4", "(5/5 vs. 1/5 baseline)")
q("lora_adapters", 3, "3", "p.4 Section 4", "hot-swapping 3 rank-16 QLoRA adapters")
q("lora_vram", 64.5, "+64.5 MB", "p.4 Section 4", "(+64.5 MB VRAM, 1.42 ms swap latency)")
q("lora_swap_ms", 1.42, "1.42 ms", "p.4 Section 4", "(+64.5 MB VRAM, 1.42 ms swap latency)")
q("lora_mem_cut", 66.3, "66.3%", "p.4 Section 4", "cuts GPU memory by 66.3%")
q("lora_pass_before", 0.33, "0.33", "p.4 Section 4", "raising gated task pass rates from 0.33 to 1.00")
q("lora_pass_after", 1.00, "1.00", "p.4 Section 4", "raising gated task pass rates from 0.33 to 1.00")
q("fail_invariants", 3, "three", "p.4 Section 5", "bundles three distinct proxy invariants ... behind a bare AssertionError")
q("tests_passed", 20, "20 passed", "p.4 Section 5", "20 passed in 4.82s")
q("tests_time", 4.82, "4.82s", "p.4 Section 5", "20 passed in 4.82s")
q("verify_budget_s", 15, "15 seconds", "p.4 Section 5", "exact p-values offline in under 15 seconds")
q("tables_count", 12, "12", "p.4 Section 5", "verifies all 12 CSV/JSONL tables")

# ---- Derived (computed here) -------------------------------------------------------------------
v = lambda k: N[k]["value"]
d("repo_sum", v("repo_fastapi") + v("repo_rich") + v("repo_requests") + v("repo_httpx"),
  str(v("repo_fastapi") + v("repo_rich") + v("repo_requests") + v("repo_httpx")),
  "fastapi + rich + requests + httpx", ["repo_fastapi", "repo_rich", "repo_requests", "repo_httpx"])
g1 = round(v("t1_calib_rate") - v("t1_base_rate"), 1)
d("t1_gain_pts", g1, f"+{g1} pts", "t1_calib_rate - t1_base_rate", ["t1_calib_rate", "t1_base_rate"])
tax = round(v("t1_calib_rate") - v("t2_M2_rate"), 1)
d("tax_pts_calc", tax, f"{tax} pts", "t1_calib_rate - t2_M2_rate", ["t1_calib_rate", "t2_M2_rate"])
d("tax_tasks_calc", v("t1_calib_solved") - v("t2_M2_solved"), str(v("t1_calib_solved") - v("t2_M2_solved")),
  "t1_calib_solved - t2_M2_solved", ["t1_calib_solved", "t2_M2_solved"])
gain_tasks = v("t2_M6_solved") - v("t2_M0_solved")
d("t2_gain_tasks", gain_tasks, f"+{gain_tasks} tasks", "t2_M6_solved - t2_M0_solved", ["t2_M6_solved", "t2_M0_solved"])
cut = round(100 * (1 - v("t2_M6_comp") / v("t2_M0_comp")), 1)
d("compaction_cut_calc", cut, f"-{cut}%", "1 - M6_comp / M0_comp", ["t2_M6_comp", "t2_M0_comp"])
kvcut = round(100 * (1 - v("t3_ccr_adaptive_kv") / v("t3_baseline_static_kv")), 1)
d("kv_cut_calc", kvcut, f"-{kvcut}%", "1 - ccr_adaptive_kv / baseline_static_kv", ["t3_ccr_adaptive_kv", "t3_baseline_static_kv"])
tg = round(v("t3_ccr_adaptive_esc") - v("t3_baseline_static_esc"), 1)
d("trap_gain_pts", tg, f"+{tg} pts", "ccr_adaptive_esc - baseline_static_esc", ["t3_ccr_adaptive_esc", "t3_baseline_static_esc"])
bc = round(100 * (1 - v("budget_d1") / v("budget_full")), 1)
d("budget_cut_calc", bc, f"{bc}%", "1 - budget_d1 / budget_full", ["budget_d1", "budget_full"])
ratio = round(v("t2_M6_solved") / v("t2_M0_solved"), 2)
d("t2_ratio", ratio, f"{ratio}x", "t2_M6_solved / t2_M0_solved", ["t2_M6_solved", "t2_M0_solved"])

# ---- Checks: quoted percentages against their own fractions ----------------------------------
checks = []


def chk(name, got, want, tol=0.05):
    ok = abs(got - want) <= tol
    checks.append((name, round(got, 3), want, ok))


chk("repo sum == tasks", v("repo_sum"), v("tasks"), 0)
for k in ("t1_base", "t1_hidden", "t1_calib"):
    chk(f"{k} {v(k + '_solved')}/129", 100 * v(k + "_solved") / 129, v(k + "_rate"))
for m, *_ in T2:
    chk(f"t2 {m} {v(f't2_{m}_solved')}/129", 100 * v(f"t2_{m}_solved") / 129, v(f"t2_{m}_rate"))
for cfg, *_ in T3:
    chk(f"t3 {cfg} {v(f't3_{cfg}_solved')}/25", 100 * v(f"t3_{cfg}_solved") / 25, v(f"t3_{cfg}_esc"))
for cfg, *_ in T3:
    pct = 100 * (v(f"t3_{cfg}_kv") / v("t3_baseline_static_kv") - 1)
    chk(f"t3 {cfg} KV vs baseline", pct, float(v(f"t3_{cfg}_kvpct").rstrip("%")))
chk("t1 gain quoted vs computed", v("t1_gain_pts"), v("t1_gain_pts_quoted"))
chk("tax pts quoted vs computed", v("tax_pts_calc"), v("tax_pts"))
chk("tax tasks quoted vs computed", v("tax_tasks_calc"), v("tax_tasks"), 0)
chk("compaction cut quoted vs computed", v("compaction_cut_calc"), v("compaction_cut_quoted"), 0.5)
chk("KV cut quoted vs computed", v("kv_cut_calc"), 70.8)
chk("trap gain quoted vs computed", v("trap_gain_pts"), v("trap_gain_pts_quoted"))
chk("D1 budget cut quoted vs computed", v("budget_cut_calc"), v("budget_cut_pct"))

out = {"_about": "Every number shown in the comic. Quoted entries carry the PDF page/section/table and the verbatim "
                  "fragment; derived entries carry the formula and inputs. Built by story_numbers_build.py.",
       "_checks": [{"check": c[0], "computed": c[1], "paper": c[2], "ok": c[3]} for c in checks],
       "numbers": N}
(HERE / "story_numbers.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
bad = [c for c in checks if not c[3]]
for c in checks:
    print(("OK  " if c[3] else "BAD ") + f"{c[0]}: computed {c[1]} vs paper {c[2]}")
print(f"{len(N)} numbers, {len(checks)} checks, {len(bad)} failed")
