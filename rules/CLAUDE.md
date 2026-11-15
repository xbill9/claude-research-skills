# Research engineering rules (research-kit)

Copy into a project's CLAUDE.md to make these always-on for research work.

Whenever working on scientific papers, ML ablation benchmarks, mathematical derivations or visual research explainers:

1. **Metric provenance.** Every sample size (N), confidence interval, p-value and benchmark percentage traces to repository data or source text. Compute intervals and p-values with the `research-audit` MCP tools (`verify_wilson_ci`, `verify_fisher_exact`, `verify_mcnemar_exact`, `leaderboard_noise_floor`) or a script; never estimate them.
2. **Scripts run in the active python3.** Install missing packages into that interpreter. Never name a script `numbers.py`, `math.py` or `statistics.py`; they shadow the stdlib and break numpy/scipy.
3. **Visual QA before delivery.** Render every PDF to page PNGs (`scripts/pdf_tools.py render`) and open them with the Read tool to confirm no overlapping callouts, split cards or clipped tables. Screenshot interactive pages at desktop and phone width.
