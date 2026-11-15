---
name: ablation-stat-auditor
description: >-
  Audit ML and systems research benchmark tables for statistical rigor: recompute Wilson 95% score
  intervals, Fisher's exact and exact McNemar p-values, Wilcoxon signed-rank tests on resource metrics,
  and leaderboard noise floors / minimum detectable lift. Use when auditing a paper's results table,
  checking whether an ablation gain is significant, comparing two agents or models on a benchmark,
  or writing the evaluation section of a paper.
---

# Ablation & Statistical Auditor

Forensic statistical check of benchmark and ablation tables. Stops small single-seed leaderboards from
being over-read and gives every claim an exact interval or paired test.

## Ground rules

- **Every number is computed, never estimated.** Use the `research-audit` MCP tools (below) or a script;
  quote their output. Do not do interval or p-value arithmetic in your head, including "roughly".
- **Every `k`, `n` and percentage traces to the paper text, a table, or a repo file.** Cite where each came
  from (page / table / file:line). If a paper gives only a percentage, recover `k = round(p * n)` in code and
  say it was recovered.
- Check the inputs you pass, not only the number that comes back: `>=` vs `>`, paired vs unpaired, which
  row is the baseline.

## What gets audited

1. **Wilson score intervals for `k / n`** — `verify_wilson_ci`. Replaces `p ± 1.96·sqrt(p(1-p)/n)`, which
   breaks near 0%, 100% and for small `n` (under ~150).
2. **The right hypothesis test for the design**
   - Same `N` tasks, two systems → **exact McNemar** (`verify_mcnemar_exact`, with `b` = only-method-solves,
     `c` = only-baseline-solves). Needs per-task outcomes; if the paper only gives totals, say the paired
     test cannot be run and fall back to Fisher with that caveat.
   - Independent task sets (e.g. separate fault-injection suites) → **two-sided Fisher's exact**
     (`verify_fisher_exact`).
   - Skewed resource metrics (tokens, latency, VRAM, wall-clock) on paired runs → **Wilcoxon signed-rank**
     in a script (`scipy.stats.wilcoxon`).
3. **Noise floor and winner's curse** — `leaderboard_noise_floor` gives the standard error, the 95% CI
   half-width and the minimum detectable lift at the chosen power, both against a fixed baseline rate and
   between two independently measured runs. Use it to say whether a reported 3–5 point gain on
   `N = 50..60` tasks is distinguishable from noise.

## Workflow

1. Extract every claim into rows: `claim | k | n | source location`.
2. Call the MCP tools per row. If the MCP server is not loaded, write `audit_stats.py` (never `statistics.py`
   or `numbers.py` — they shadow the stdlib and break numpy) and run it with the active `python3`; install
   missing packages into that interpreter (`python3 -m pip install scipy`, or `apt install python3-scipy`).
3. Deliver a **Statistical Audit Report**:

   | Claim | Paper value | Recomputed CI / p-value | Test used | Verdict |
   |---|---|---|---|---|

   Verdicts: `HOLDS`, `WITHIN NOISE` (gain below the minimum detectable lift / CI overlap / p ≥ 0.05),
   `OVERSTATED` (paper wording stronger than the test supports), `CANNOT CHECK` (inputs missing — say which).
4. Add publication-ready Markdown and LaTeX rows, e.g. `39.5\% \,[31.5, 48.2]`, and save the raw tool output
   as `stat_audit.json` next to the report.
