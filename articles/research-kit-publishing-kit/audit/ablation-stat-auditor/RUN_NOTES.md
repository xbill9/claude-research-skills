# RUN_NOTES: ablation-stat-auditor on the research-kit walk-through

Paper of record: `articles/research-kit-publishing-kit/devto-research-kit-publishing-kit.md`. Sources read: the article's `evidence/` folder and `examples/publishing-kit-article/` (math-sandbox, ablation-stat-auditor, citation-doi-verifier, figure-forensics, interactive-paper-studio, graphic-story, paper/).

## Commands

```bash
cd articles/research-kit-publishing-kit/audit/ablation-stat-auditor
python3 audit_stats.py > audit_stats_output.txt   # system python3 3.x with pillow and pymupdf; no virtualenv
ruff format audit_stats.py
```

`audit_stats.py` starts `plugin/mcp/research_audit_mcp.py` as a subprocess and calls `verify_wilson_ci`, `verify_fisher_exact`, `verify_mcnemar_exact` and `leaderboard_noise_floor` over stdio JSON-RPC. Every call and its result is in `stat_audit.json` under `raw_mcp_calls`. Each claim record cites the article line it found by exact-text match, and the script stops if a quoted text is not on exactly one line.

## Findings

43 records: 36 VERIFIED, 3 MISMATCH, 4 NOT CHECKABLE.

- Every count, rate, interval and test printed in the article reproduces: 47 of 62 = 75.806% [63.847, 84.754]; McNemar p = 0.125 at b = 4, c = 0; Fisher p = 0.028571; first p below 0.05 at six images (0.0625 at five, 0.03125 at six); 26 records 15/6/5; 16 records 7/6/3; 10 of 11 links; 130 values, 0 mismatches; 5 disputed to 0 with 5 noted.
- MISMATCH, line 111: "what supports it is one archived paste". No evidence file covers Medium data-URI pastes; the only source is the log row at `paper/CLAIMS.md:96`.
- MISMATCH, line 141: "Each of the 11 links was fetched instead and matched to a second source". 10 were matched; L9 (Medium) got HTTP 403.
- MISMATCH, line 260: "an overstatement and an unsupported comparison". The earlier stat audit's report has 2 OVERSTATED rows.
- NOT CHECKABLE, line 111: "is a paired comparison of the same four images". No per-image record exists. Unpaired, Fisher gives p = 0.0286 and four images already clear 0.05.
- NOT CHECKABLE, lines 184 and 217: "It exits 1." and "It exits 0." The check-facts evidence files do not record exit status.
- NOT CHECKABLE, line 284: "Each skill ran once, as a separate agent." No run log records it.

## Where the skill fell short

1. The skill assumes a benchmark table with tasks, a baseline and a method. This article has one sampled rate and one comparison; the rest are census counts of files, where Wilson intervals describe nothing. The skill gives no rule for telling a census from a sample.
2. The `research-audit` MCP server returns intervals rounded to two decimals. Rounding those again to the article's one decimal is a double rounding: 63.85 can become 63.9 while the true bound 63.847 rounds to 63.8. The script recomputes Wilson at full precision and asserts agreement with the server at two decimals. The skill does not warn about this.
3. Most of what needed checking was wording about numbers ("each of the 11", "an overstatement", "one archived paste", "every dev.to cover"). The skill's verdicts cover printed numbers; the record format has no field for a word like "each" or "every" that implies a count.
4. The skill's verdict set has no place for a design assumption. Whether the Medium comparison is paired decides whether p is 0.125 or 0.0286, and it went into a NOT CHECKABLE record with the consequence in `reason`.
5. The skill says to pick McNemar for paired designs but gives no step for checking that the pairing exists in the data before choosing it.
6. Exit codes, run counts and other process claims are outside any statistical method. They are recorded as NOT CHECKABLE because the evidence files do not capture them.
7. The noise-floor tool has no comparison to judge here. Its n = 62 and n = 4 outputs are kept as context only.
8. Wilcoxon has nothing to run on; the article reports no paired resource metric.
9. The MCP server ships no client. Calling it from a script meant writing a stdio JSON-RPC client inside `audit_stats.py`.
10. `audit_stats.py` sits under the repo's `ruff check .`. After `ruff format` it still had 23 findings (E501, E741, UP031), so it carries a file-level `# ruff: noqa` for those three codes and now passes `ruff check` and `ruff format --check`.
