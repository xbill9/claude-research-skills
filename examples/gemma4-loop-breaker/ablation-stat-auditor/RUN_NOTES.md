# RUN_NOTES: ablation-stat-auditor on gemma4-loop-breaker

## 1. Commands run and key output

1. `cat plugin/skills/ablation-stat-auditor/SKILL.md`. The skill directory holds only SKILL.md; it has no `scripts/` folder.
2. `cat -n paper/PAPER.md`; PDF text extracted with `python3 -I -c 'import fitz ...'` (5 pages). Figures 2 and 3 viewed as images. **The PDF and PAPER.md are different versions.** The PDF adds Wilson CIs, McNemar p-values (1.8e-6, 4.6e-5), per-repo splits, and reframes 39.5% as "Stage-1 file-isolated". PAPER.md has none of these and says "24.1%" in the abstract.
3. `tools/list` over stdio to `plugin/mcp/research_audit_mcp.py`: 6 tools, schemas as described in the task.
4. Probe calls: `verify_wilson_ci(51,129)` → `39.5% (95% Wilson CI [31.5%, 48.2%])`; `verify_fisher_exact(24,25,4,25)` → p = 7.178606491749202e-09; `verify_mcnemar_exact(28,0)` → 7.45e-09; `leaderboard_noise_floor(129, 0.178)` → MDL 9.44 pts (fixed baseline), 13.34 pts (two runs).
5. `python3 -I audit_stats.py` (run from /tmp). It sends every MCP call through one stdio server process per batch and uses scipy for the rest. It writes `stat_audit.json`, and its console output is saved as `audit_stats_output.txt`. Key output:
   - 14 Wilson CIs from Tables 1–3 all match the PDF to 1 dp except 51/129 upper bound (tool 48.157 → 48.2; PDF prints 48.1).
   - Per-repo counts recovered from percentages: fastapi 7/15/25, rich 6/12/20, requests 2/3/5, httpx 0/1/1; these sum to 15/31/51, matching the tables.
   - Fisher two-sided: T1 51 vs 23 p = 1.79e-4; M6 vs M0 p = 0.0141; single module steps p = 0.606–0.883; Trap-25 24 vs 4 p = 7.18e-9 (paper says 4.2e-9; one-sided 3.59e-9); ccr_adaptive vs ccr_only p = 0.0488; sci-trap 5/5 vs 1/5 p = 0.0476.
   - Exact McNemar feasible ranges from the marginals: T1 [7.45e-9, 1.52e-3]; M6 vs M0 [3.05e-5, 2.59e-2]; Trap-25 [1.91e-6, 1.10e-5].
   - McNemar best case (c = 0) for each module step: 0.125–0.5.
   - Paper's 1.8e-6 = continuity-corrected chi-square at b = 30, c = 2 (1.82e-6). Paper's 4.6e-5 matches no exact, mid-p, chi-square or chi-square-cc value for c = 0..3.
   - Wilcoxon signed-rank at n = 25 pairs: exact minimum p 5.96e-8, normal-approximation minimum 1.23e-5.
   - Arithmetic: 25 × Σ(avg turns) = 937.0; (31−22)/29 = 0.31; log2(0.72/0.06) = 3.585; −93.1% compaction; Table 3 relative columns all reproduce.
6. Ratio check: `python3 -c 'print(1.9073486328125e-06/4.2e-9, 1.1e-5/4.2e-9)'` → 454.1, 2619.0.

No packages were installed. No virtualenv was used. Nothing outside the output directory was modified.

## 2. Problems with SKILL.md

1. **"bundled scripts, if any, are under its scripts/"** (task brief) versus SKILL.md: "write `audit_stats.py`". The skill ships no script, so every user writes the Wilson/Fisher/McNemar/Wilcoxon code from scratch. A reference `scripts/audit_stats.py` that accepts a CSV of `claim,k,n,source` rows (or a stdio client for the MCP server) would make runs reproducible and identical between users.
2. **"If the MCP server is not loaded, write `audit_stats.py`"**: this misses the middle case. The server file exists in `plugin/mcp/` and can be driven over stdio. The skill should say where the server lives and show the one-line JSON-RPC call, so the fallback still uses the same tested implementation.
3. **"Needs per-task outcomes; if the paper only gives totals, say the paired test cannot be run and fall back to Fisher with that caveat."** This is too weak. With marginals alone you can compute the full range of exact McNemar p-values over every feasible (b, c) (c from 0 to min(k_base, n − k_method)). That bound decided two findings here: the Trap-25 p = 4.2e-9 is impossible for any paired outcome (min 1.91e-6), and no single ablation step can reach p < 0.05 (best case 0.125). The skill should ask for the feasibility range alongside the Fisher fallback, and say that Fisher on a paired design understates p.
4. **No step for checking the paper's own reported p-values.** The workflow says to recompute and give a verdict, but not to *trace* a reported p that does not match (one-sided vs two-sided, chi-square vs exact, continuity correction, mid-p). That trace showed 1.8e-6 is a chi-square-cc value and 4.6e-5 is unattainable. I had to improvise the variant table.
5. **"Skewed resource metrics ... on paired runs → Wilcoxon signed-rank in a script"** assumes per-run data. It gives no guidance when only means are published, which is the usual case. A feasibility check helps here: the minimum attainable p for n pairs, exact vs normal approximation. Also, the MCP server has no Wilcoxon tool, unlike the other three tests.
6. **"Verdicts: HOLDS, WITHIN NOISE ..., OVERSTATED ..., CANNOT CHECK"** — the four verdicts do not cover "significant, but the reported p-value is wrong" (Trap-25) or "CI correct except a rounding slip" (48.1 vs 48.2). I used HOLDS plus a qualifier. A verdict such as `MISREPORTED` (the conclusion survives, the number does not) would help.
7. **"Extract every claim into rows: `claim | k | n | source location`"** — no instruction for handling two versions of the same paper (Markdown vs PDF) that disagree. Here they disagree on what 39.5% measures, which is the paper's biggest framing issue. The skill should say to diff versions and audit the union.
8. **No instruction to check what `n` is.** "Across 100 AST-verified episodes" reads as n = 100. Arithmetic shows 100 = 4 configs × 25 traps and 937 turns = 25 × Σ avg turns, i.e. single seed, n = 25 per arm. A step like "reconcile every stated sample size (episodes, turns, tasks, seeds) against the table rows" would catch this routinely. The ground rule "Check the inputs you pass ... paired vs unpaired" hints at it but does not say how.
9. **"`leaderboard_noise_floor` ... Use it to say whether a reported 3–5 point gain on N = 50..60 tasks is distinguishable from noise"** — the tool's `min_detectable_lift_two_runs` assumes two *independent* runs. Most ablations here are paired on the same 129 tasks, where the relevant floor depends on the discordance rate, which is unknown. The skill should say which of the two MDL figures applies to a paired ablation, or warn that both are approximations there.
10. **Ablation-specific checks are missing despite the skill's name.** Nothing says to (a) test each cumulative step separately, not only first-vs-last, or (b) flag rows that change several factors at once (Table 1 row 2→3 changes temperature, top-k and include_thoughts). Both were needed here.
11. **"recover `k = round(p * n)` in code and say it was recovered"** — the skill should also say to check the recovered k round-trips to the printed percentage and that recovered subgroup counts sum to the reported total. I did both, and they confirmed the per-repo splits.
12. **Arithmetic claims (relative %, "2.1x", "half the gap", "−93%") are out of scope as written** ("Wilson ... Fisher ... McNemar ... Wilcoxon ... noise floor"). Several of the overstatements found were plain arithmetic ("recovers half" = 31%). One line adding "recompute every derived ratio/delta" would cover it.
13. **MCP tool output precision.** `verify_wilson_ci` returns bounds at 2 dp (`wilson_high_pct: 48.16`). Rounding those again to 1 dp to compare with a paper double-rounds: 13.49 → 13.5 is fine, but my first comparison flagged 25/129 and 4/25 as mismatches until I recomputed at full precision (27.045, 34.654). The skill should say to compare against the tool's `formatted` string or full-precision values, not re-round the 2-dp fields.
14. **Deliverable naming is loose.** "Deliver a Statistical Audit Report" gives no file name; only `stat_audit.json` is named. I used `STAT_AUDIT_REPORT.md`.

## 3. Not done or not verifiable

- No per-task or per-episode outcomes were available. The paper's datasets (`trap_tasks_25.jsonl`, telemetry CSVs) and its 20-test `pytest` suite are referenced but not in the repo. So no McNemar or Wilcoxon test could actually be run; only feasibility bounds.
- Wilcoxon p = 8.91e-07 / p < 1e-6: CANNOT CHECK (n and per-episode KV values not stated).
- Multi-LoRA pass rate 0.33 → 1.00, held-out score, Recall@3, compaction rates, and "+4.51 bits": no sample sizes or metric definitions, so no CIs or tests.
- The paper's "±9.8 pts Wilson CI" for 58 tasks did not match any interval computed here (Wald 10.29, Wilson at p = 0.2 10.14); I could not identify how it was produced.
- References were not checked (out of scope for this skill; `verify_doi_metadata` exists but belongs to a different audit).
