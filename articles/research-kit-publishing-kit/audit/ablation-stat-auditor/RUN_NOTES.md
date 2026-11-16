# RUN_NOTES: ablation-stat-auditor on the research-kit walk-through

Paper of record: `articles/research-kit-publishing-kit/devto-research-kit-publishing-kit.md`, audited 2026-11-16.

## Commands

```bash
cd articles/research-kit-publishing-kit/audit/ablation-stat-auditor
python3 audit_stats.py > audit_stats_output.txt   # system python3 (pyenv 3.14.7) with pillow and pymupdf
ruff check audit_stats.py && ruff format --check audit_stats.py   # repo ruff.toml; file-level noqa for E501, UP031
```

`audit_stats.py` starts `plugin/mcp/research_audit_mcp.py` and calls `verify_wilson_ci`, `verify_mcnemar_exact` (b = 4, c = 0, and b = 1..10, c = 0) and `verify_fisher_exact` over stdio JSON-RPC; every call and result is in `stat_audit.json` under `raw_mcp_calls`. Each record names its article line, and the script stops if the quoted text is not on that line.

## Result

39 records: 37 VERIFIED, 0 MISMATCH, 2 NOT CHECKABLE (line 167, the one-paste premise; line 403, "Each skill ran once"). Details in `STAT_AUDIT_REPORT.md`.

## Where the skill fell short

1. The skill expects a benchmark table. Here two figures are samples (47 of 62, the Medium 4-image comparison) and the rest are full counts of files, which the skill gives no rule for telling apart. Each record carries a `kind` field (`sample`, `census`, `premise`, `process`) for that.
2. The verdict set has no place for a design assumption: whether the Medium pastes were paired moves p from 0.0286 to 0.125. The paired record's `conclusion` is WITHIN NOISE, the unpaired one HOLDS.
3. The MCP Wilson tool rounds to two decimals; the script recomputes at full precision and asserts agreement, to avoid rounding 63.85 again to 63.9.
4. Process claims (exit codes, run counts, which kit version produced an output) are outside the statistics; they were checked by file lookup, and the run count could not be.
5. The noise-floor tool and Wilcoxon have nothing to run on: there is no leaderboard and no paired resource metric.
