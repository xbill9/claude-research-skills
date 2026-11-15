# Statistical Audit Report: "Breaking the 15-Minute Cliff in Quantized Gemma 4 Coding Agents"

Sources audited: `paper/PAPER.md` (Markdown version) and `paper/Robina_Mirbahar_Gemma4_SWE_Agent_Paper_2026.pdf` (5 pages). The two versions differ; where they do, both are cited. All recomputed numbers come from `audit_stats.py` (output in `audit_stats_output.txt`, raw tool output in `stat_audit.json`). Exact tests were run through the skill's `research-audit` MCP server over stdio; scipy was used for Wilcoxon bounds and McNemar/Fisher variants the server does not offer.

No per-task or per-episode outcomes are published with the paper (the datasets and `pytest` suite the paper names were not available here). Every paired test below is therefore either a feasibility bound computed from the published marginals or an unpaired Fisher fallback.

## 1. Claim extraction

| Claim | k | n | Source |
|---|---|---|---|
| Stage-1 baseline (non-thinking, T=0.2) | 23 | 129 | PDF p2 Table 1; PAPER.md Table 1 |
| Stage-1 hidden-thinking | 35 | 129 | PDF p2 Table 1; PAPER.md Table 1 |
| Stage-1 calibrated thinking (method) | 51 | 129 | PDF p2 Table 1; PAPER.md Table 1 |
| End-to-end M0 ... M6 | 15, 18, 22, 25, 27, 29, 31 | 129 | PDF p3 Table 2; PAPER.md Table 2 |
| Trap-25 baseline_static / naive_subagent / ccr_only / ccr_adaptive | 4, 5, 18, 24 | 25 | PDF p4 Table 3; PAPER.md Table 3 |
| sci-trap G-CCR vs baseline | 5 vs 1 | 5 | PDF p4 Sec. 4 |
| Per-repo M0 / M6 / Stage-1 (recovered: k = round(p·n)) | fastapi 7/15/25 of 67; rich 6/12/20 of 48; requests 2/3/5 of 13; httpx 0/1/1 of 1 | — | PDF p3 text, Figure 3a. Recovered counts sum to 15 / 31 / 51, matching Tables 1–2 |
| 58-task leaderboard, p = 0.20, SE 5.25%, "Wilson ±9.8 pts" | — | 58 | PDF p1, item 2 |
| Post-reset KV 46.7K vs 159.8K, Wilcoxon p = 8.91e-07 | — | not stated | PAPER.md L117; PDF p1 "p < 10^-6" |
| Multi-LoRA pass rate 1.00 vs 0.33; held-out score 0.121 → 0.241; Recall@3 0.448 → 0.931; dilution 0.72 → 0.06 "+4.51 bits" | — | not stated | PDF p1–p4; PAPER.md §3.1, §3.3, §4 |

## 2. Statistical Audit Report

| Claim | Paper value | Recomputed CI / p-value | Test used | Verdict |
|---|---|---|---|---|
| Stage-1 calibrated thinking 51/129 | 39.5% [31.5, 48.1] (PDF Table 1) | 39.5% [31.5, 48.2] (upper bound 48.157) | Wilson | HOLDS (paper's upper bound off by 0.1 in rounding) |
| All other Table 1–3 Wilson CIs (12 rows) | as printed in PDF | identical to 1 dp | Wilson | HOLDS |
| Stage-1: calibrated vs baseline, 51 vs 23 of 129 | McNemar paired p = 1.8e-6 (PDF p2) | Paired data not published. Feasible exact McNemar range p ∈ [7.45e-9, 1.52e-3] (c = 0..23). 1.8e-6 is reproduced by the continuity-corrected chi-square McNemar at b = 30, c = 2 (1.82e-6), and not by the exact test at any feasible (b, c). Unpaired Fisher fallback: p = 1.79e-4 | exact McNemar bounds; Fisher fallback | HOLDS (significant under every feasible pairing). The p-value's test is mislabelled as or approximated by chi-square |
| PAPER.md abstract: calibration "lifts resolved swegemma tasks from 17.8% to 39.5%" | 39.5% framed as swegemma resolution | The PDF says 39.5% is Stage-1 file-isolated synthesis (target file supplied). The same calibration inside the end-to-end harness is M1 → M2: 18 → 22 of 129, Fisher p = 0.606; best-case paired p = 0.125 | Fisher; McNemar best case | OVERSTATED (PAPER.md). The end-to-end effect of calibration is WITHIN NOISE |
| Stage-1: calibrated vs hidden-thinking, 51 vs 35 | not tested | Fisher p = 0.0473; best-case paired p = 3.05e-5. Rows 2→3 change temperature, top-k and include_thoughts at once | Fisher | HOLDS narrowly unpaired; the attribution to any one knob CANNOT CHECK (confounded) |
| End-to-end M6 vs M0, 31 vs 15 of 129 | McNemar paired p = 4.6e-5 (PDF p3) | Smallest feasible exact McNemar p = 3.05e-5 (b = 16, c = 0); next is 1.45e-4 (b = 17, c = 1). 4.6e-5 lies between attainable exact values and matches no mid-p or chi-square variant for c = 0..3. Unpaired Fisher p = 0.0141 | exact McNemar bounds; Fisher fallback | HOLDS for direction (p < 0.05 either way); the reported p-value is not reproducible from the stated counts |
| Each single module M1…M6 (+2 to +4 tasks per step) | Table 2 "cumulative" attribution to each module; PDF §4 "what worked" list | Fisher p = 0.606–0.883 per step; best-case paired p (c = 0) = 0.125 (M2) to 0.5 (M4, M5, M6). Noise floor at N = 129, base 11.6–20.9%: minimum detectable lift 7.9–10.0 pts vs fixed baseline; each step is 1.55–3.10 pts | Fisher; exact McNemar best case; noise floor | WITHIN NOISE. No individual module can reach p < 0.05 even under perfect pairing |
| Tooling modules only, M6 vs M2, 31 vs 22 | implicit | Fisher p = 0.217; best-case paired p = 3.9e-3 | Fisher; McNemar best case | CANNOT CHECK (needs per-task outcomes; significant only if few M2-only solves) |
| "recovers half that 29-task gap" (PDF p3) | half of 29 | M6 − M2 = 9 tasks = 0.31 of 29. Measured from M0, (31 − 15)/(51 − 15) = 0.444 | arithmetic | OVERSTATED |
| "22.4-point Localization-Trajectory Tax" | 39.5 − 17.1 | (51 − 22)/129 = 22.5 pts from counts | arithmetic | HOLDS (0.1 pt rounding) |
| PAPER.md abstract "double ... to 24.1%" | 24.1% | 31/129 = 24.03%; ratio 2.067 | arithmetic | HOLDS for "2.1x"; 24.1% is a typo for 24.0% |
| Trap-25 ccr_adaptive vs baseline_static, 24 vs 4 of 25 | Fisher's exact p = 4.2e-9 | Two-sided Fisher = 7.18e-9; one-sided = 3.59e-9; neither is 4.2e-9. The 25 traps are the same for every config, so the design is paired: exact McNemar feasible range is p ∈ [1.91e-6, 1.10e-5] (c ≤ 1) | Fisher; exact McNemar bounds | HOLDS for significance; p-value OVERSTATED by a factor of 454 to 2,619 (wrong test for a paired design, and the Fisher value itself is misreported) |
| Trap-25 ccr_only vs baseline_static, 18 vs 4 | not tested | Fisher p = 1.47e-4 | Fisher | HOLDS |
| Trap-25 ccr_adaptive vs ccr_only, 24 vs 18 (the "adaptive thinking" increment) | implied | Fisher p = 0.0488; best-case paired p = 0.0313. Noise floor N = 25 at 72%: MDL 25.2 pts vs fixed baseline; observed +24 pts | Fisher; McNemar best case; noise floor | WITHIN NOISE (borderline; below the minimum detectable lift) |
| naive_subagent vs baseline_static, 5 vs 4 | "+19.1% KV bloat" listed under "what hurt" | Fisher p = 1.0 on solve rate | Fisher | WITHIN NOISE for solve rate; KV claim CANNOT CHECK |
| sci-trap 5/5 vs 1/5, "100% recovery" | 100% (PDF p4) | 100% [56.6, 100.0] vs 20% [3.6, 62.4]; Fisher p = 0.0476; paired best case p = 0.125 (sci-traps are 5 of the same Trap-25 traps) | Wilson; Fisher; McNemar best case | WITHIN NOISE under the paired design; Wilson lower bound is 56.6% |
| Post-reset KV −70.8%, Wilcoxon p = 8.91e-07 / p < 1e-6 | 46,689 vs 159,816 | Relative change −70.8% reproduced. n not stated. With 25 paired traps the exact signed-rank minimum is 5.96e-8 and the normal-approximation minimum is 1.23e-5, so 8.91e-7 is only attainable with an exact test (n = 25) or with more pairs | Wilcoxon feasibility | CANNOT CHECK (per-episode KV values not published; n not stated) |
| "100 AST-verified episodes", "937 turns" | Trap-25 sample size (PDF p3–p4) | 100 = 4 configs × 25 traps; 25 × (11.04 + 10.72 + 8.76 + 6.96) = 937.0. So each config is one run per trap (single seed), and the 937 turns are Trap-25 turns. PDF p1 instead says "937 turns of live trajectory telemetry across the 129 development tasks" | arithmetic | OVERSTATED (the 937-turn figure is attributed to two different datasets; "100 episodes" reads as n = 100 per config but is n = 25) |
| 58-task leaderboard: SE 5.25%, "Wilson CI ±9.8 pts", swings of 5–7 pts are luck | PDF p1 | SE = 5.25% reproduced. Wald half-width 10.29 pts; Wilson half-width at p = 0.20 is 10.14 pts (asymmetric [−8.44, +12.08] at 12/58). Two-run MDL at N = 58: 20.8 pts | noise floor; Wilson | HOLDS for SE; "±9.8" does not match any interval computed here. The "5–7 point swings are noise" conclusion HOLDS |
| Compaction 68.2% → 4.7% (−93%); −24.2 pts M0→M1 | PDF p1, p4 | −93.1%; 24.2 pts | arithmetic | HOLDS arithmetically; n of episodes behind the rates not stated, so no CI (CANNOT CHECK) |
| Table 3 relative columns (+13.0, −20.7, −45.1; +19.1, −46.7, −70.8) | Table 3 | all reproduced exactly | arithmetic | HOLDS |
| Softmax dilution 0.72 → 0.06, "+4.51 bits" | PDF p2 §3.1 | log2(0.72/0.06) = 3.585; the definition behind 4.51 bits is not given | arithmetic | CANNOT CHECK (metric undefined) |
| −66.3% VRAM (18.4 vs 54.6 GB); 87.5% budget cut | PDF p4; §3.1 | 66.3%; 87.5% | arithmetic | HOLDS arithmetically |
| Multi-LoRA pass rate 0.33 → 1.00; held-out 0.121 → 0.241; Recall@3 0.448 → 0.931 | PDF p1–p4 | no n stated | — | CANNOT CHECK (sample sizes missing) |

## 3. Main findings

1. **Trap-25 p-value.** The headline 4.2e-9 does not match two-sided Fisher on 24/25 vs 4/25 (7.18e-9) or one-sided (3.59e-9). The comparison is paired (same 25 traps), and the exact paired test cannot go below 1.91e-6. The effect is large (+80 pts) and significant; the reported p-value is 454 to 2,619 times smaller than any paired exact p-value consistent with the totals.
2. **Ablation table.** None of the six module steps in Table 2 is distinguishable from noise: each adds 2–4 of 129 tasks, and even a perfectly paired test gives p ≥ 0.125. Only the cumulative M0 → M6 change (+16 tasks) is significant. Per-module attributions ("what worked best") are not supported by the data.
3. **Version mismatch.** PAPER.md presents 39.5% as swegemma resolution; the PDF says it is a file-isolated protocol and that the same calibrated checkpoint gets 17.1% end-to-end. The end-to-end effect of calibration (M1 → M2) is +4 tasks, p = 0.606.
4. **Single seed, n = 25.** "100 AST-verified episodes" is 25 traps per configuration, run once. The ccr_only → ccr_adaptive increment (+6 traps) is borderline (Fisher p = 0.0488) and below the minimum detectable lift (25.2 pts).
5. **Unreproducible p-values.** McNemar 4.6e-5 (M6 vs M0) falls between attainable exact values (3.05e-5, 1.45e-4) and matches no common variant. McNemar 1.8e-6 (Stage-1) matches a continuity-corrected chi-square at b = 30, c = 2, not the exact test.

## 4. Publication-ready rows

Markdown:

| System | Solved | Rate [95% Wilson CI] |
|---|---|---|
| Stage-1 baseline | 23/129 | 17.8% [12.2, 25.3] |
| Stage-1 hidden thinking | 35/129 | 27.1% [20.2, 35.4] |
| Stage-1 calibrated | 51/129 | 39.5% [31.5, 48.2] |
| E2E M0 | 15/129 | 11.6% [7.2, 18.3] |
| E2E M2 | 22/129 | 17.1% [11.5, 24.5] |
| E2E M6 | 31/129 | 24.0% [17.5, 32.1] |
| Trap-25 baseline_static | 4/25 | 16.0% [6.4, 34.7] |
| Trap-25 ccr_only | 18/25 | 72.0% [52.4, 85.7] |
| Trap-25 ccr_adaptive | 24/25 | 96.0% [80.5, 99.3] |
| sci-trap G-CCR | 5/5 | 100.0% [56.6, 100.0] |

LaTeX:

```latex
Stage-1 baseline        & 23/129 & 17.8\% \,[12.2, 25.3] \\
Stage-1 hidden thinking & 35/129 & 27.1\% \,[20.2, 35.4] \\
Stage-1 calibrated      & 51/129 & 39.5\% \,[31.5, 48.2] \\
E2E M0                  & 15/129 & 11.6\% \,[7.2, 18.3]  \\
E2E M2                  & 22/129 & 17.1\% \,[11.5, 24.5] \\
E2E M6                  & 31/129 & 24.0\% \,[17.5, 32.1] \\
Trap-25 baseline\_static & 4/25  & 16.0\% \,[6.4, 34.7]  \\
Trap-25 ccr\_only        & 18/25 & 72.0\% \,[52.4, 85.7] \\
Trap-25 ccr\_adaptive    & 24/25 & 96.0\% \,[80.5, 99.3] \\
sci-trap G-CCR          & 5/5    & 100.0\% \,[56.6, 100.0] \\
```

Suggested replacement wording for the Trap-25 claim: "24/25 vs 4/25 traps (96.0% [80.5, 99.3] vs 16.0% [6.4, 34.7]); paired exact McNemar p ≤ 1.1e-5 for any pairing consistent with these totals (single run per trap)."
