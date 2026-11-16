# RUN_NOTES: ablation-stat-auditor on publishing-kit-article

Interpreter: system `python3` (pyenv), scipy 1.18.1 present; scipy was not needed. No packages installed, no
virtualenv. Nothing outside this folder was modified.

## 1. Commands run

| Command | Key output |
|---|---|
| `cat plugin/skills/ablation-stat-auditor/SKILL.md` | Skill folder holds SKILL.md only; no scripts or references. |
| `cat paper/devto-publishing-kit.md paper/CLAIMS.md paper/evidence/*` | Article 184 lines; CLAIMS.md 134 lines; 13 evidence files, 641 lines in total (`wc -l`). |
| `grep -n` on the article for counts | Count claims at lines 12, 31, 36, 53, 54, 161, 162, 164, 167, 184. |
| `sed -n 40,256p plugin/mcp/research_audit_mcp.py` | Tool argument names: `successes`/`total`; `k_method`/`n_method`/`k_baseline`/`n_baseline`; `b`/`c`; `num_tasks`/`baseline_rate`. |
| `python3 -I audit_stats.py > audit_stats_output.txt` | Writes `stat_audit.json`: 18 MCP calls recorded, 16 claim records. |
| (same) Wilson | 47/62 → 75.8% [63.8, 84.8]; 0/4 → [0.0, 49.0]; 4/4 → [51.0, 100.0]; 23/23 → [85.7, 100.0]; Substack links 2/4 → [15.0, 85.0], 4/4 → [51.0, 100.0]; Substack images 2/2 → [34.2, 100.0]. |
| (same) tests | Medium 4/4 vs 0/4: Fisher p = 0.02857; exact McNemar b=4, c=0: p = 0.125. Substack links: McNemar b=2, c=0 p = 0.5; Fisher p = 0.4286. Smallest all-or-none paired count reaching p < 0.05: 6. |
| (same) noise floor | n=62, rate 75.81%: SE 5.44, half-width 10.66, MDL 15.24 (fixed) / 21.55 (two runs) pts. |
| (same) arithmetic | 58+4 = 62; 15 blocks without a break; 88 `<br>` / 47 blocks = 1.872; 47 − 43 (bodytext) = 4; fence labels sum to 23; orgs 24+13+3 = 40; 1000/420 = 2.380952; 1376/ratio = 577.92 rows; 95.04 px per side; covers 104.38 / 104.23 / 15.11 KiB; payload 23,234 chars = 22.689 KiB, 531 → 411 lines; footprint files 3,931 + SKILL.md 649 = 4,580 (stated 4,580); LinkedIn 1,269 of 3,000, hook 80 of 140; five faults listed = 5. |
| (same) dates | Article footer 2026-08-31; 47/62 measured 2026-09-16 (16 days later); 0/4 is a LOG entry dated 2026-08-30. |
| (same) verdicts | VERIFIED 7, MISMATCH 6, NOT CHECKABLE 3; conclusions HOLDS 8, OVERSTATED 2, CANNOT CHECK 6. |
| `ruff format` + `ruff check` on `audit_stats.py` | All checks passed. |

## 2. Headline findings

1. **47 of 62 reproduces exactly** from `evidence/devto-hardwrap.txt` (58 `<p>` + 4 `<li>`, 47 with `<br>`):
   75.8%, Wilson [63.8, 84.8]. It is one article, so the interval covers that article's blocks only.
2. **"A stray break in every paragraph" (article line 53) is contradicted by the article's own count**: 15 of the
   62 blocks carry no break, and the Wilson upper bound is 84.8%. The evidence's mechanism claim ("a break at
   every wrap") could be true, but checking it needs the number of source blocks that were wrapped, which is
   not archived.
3. **"0 of 4 / 4 of 4" has no archived artifact.** CLAIMS.md lists it as LOG (2026-08-30), not re-measured.
   As a paired comparison it gives exact McNemar p = 0.125; Fisher, which ignores the pairing, gives 0.0286.
   Four items can never reach p < 0.05 under the paired test (six are needed). The claim is a deterministic
   editor rule, so the right support is one archived, reproducible paste, not a p-value.
4. **The footer date is wrong for both cover numbers**: the article says behaviours were measured on
   2026-08-31; the 47/62 figure was measured 2026-09-16 and the 0/4 figure comes from a 2026-08-30 log.
5. **The 2.381:1 crop and the 95 px loss reproduce** (2.380952; 95.04 px), from one fetched display size and
   assuming a centre crop that `gravity=auto` does not promise.
6. **Several CLAIMS.md rows cite files that now hold a later capture**: skill footprint (446 vs 649 SKILL.md
   lines; 2,370 vs 4,580 total, file now at 0.18.0), Builder payload (22,542 and 23,214 chars vs 23,234), cover
   size 105 KB (104.38 KiB / 106.89 kB). The archived files are internally consistent; the ledger rows lost
   their artifact. None of these numbers appear in the article itself.
7. Counts that check out: 23/23 labelled fences (labels sum to 23), 40 articles = 24 + 13 + 3, five faults
   listed, LinkedIn 1,269 chars and 80-char hook.

## 3. Where SKILL.md fell short for this input

1. **No path for non-benchmark input.** The skill assumes a results table of systems on tasks. It gives no
   instruction for an article whose counts describe deterministic software behaviour, where a significance
   test is the wrong instrument, and no verdict for "statistical methods do not apply".
2. **No unit-of-analysis check.** Wilson treats the 62 blocks as independent draws, but they come from one
   article; the same holds for 23/23 fences. The skill should require stating what was sampled (items within
   one artifact vs artifacts) before quoting an interval as a rate.
3. **Paired test when one arm is all-or-none.** The skill says McNemar needs per-task outcomes and falls back to
   Fisher on totals. When one arm is 0/n or n/n, the paired table is fully determined from the totals
   (here b=4, c=0), so McNemar can be run exactly. On this input Fisher (0.0286) and McNemar (0.125) fall on
   opposite sides of 0.05, so the fallback would have produced the wrong verdict.
4. **No feasibility check.** Nothing asks whether the sample could ever reach significance. At 4 paired items
   the smallest attainable McNemar p is 0.125; 6 discordant items are the minimum for p < 0.05.
5. **No provenance step.** "Every k, n traces to ... a repo file" does not ask whether the cited file still
   contains the number. Here four ledger rows cite files that were overwritten by later captures.
6. **Quantifier claims are out of scope as written.** "Every paragraph" is the article's strongest statement and
   is contradicted by its own count, but the workflow extracts only `k | n` rows. The skill should say to
   check universal wording ("every", "all", "never") against the counts.
7. **Dates of measurement are not audited.** The article's footer date matches neither headline number's
   measurement date. A "when was each number measured" column would catch this.
8. **Derived arithmetic and units are not covered.** The crop ratio, the 95 px loss and the KB figures are plain
   arithmetic; "KB" is ambiguous (105 matches neither 1,024- nor 1,000-byte conversion). The skill names only
   Wilson, Fisher, McNemar, Wilcoxon and the noise floor.
9. **Noise floor has no stated precondition.** The skill says to use it on a reported gain; it does not say to
   skip it when the paper makes no comparison. Here it is reported as context only.
10. **Wilcoxon has no "not applicable" path** when the paper contains no paired resource series, and the MCP
    server has no Wilcoxon tool.
11. **Claim-record schema omits `conclusion` from its field list.** Step 5 says the table verdict "goes in the
    record as `conclusion`", but the listed fields are `id`, `statement`, `paper_value`, `paper_source`,
    `computed`, `verdict`, `reason`.
12. **`paper_value` must be "only the number(s)"**, which leaves no encoding for a quantifier ("every") or a
    date; this audit used `{"blocks_with_break": "every"}` and `{"date": "2026-08-31"}`.
13. **Audit scope across paper and ledger is undefined.** The paper of record is the article, but its ledger
    (CLAIMS.md) and evidence carry many numbers the article never states. The skill does not say whether
    those are in scope or how to mark them; this audit includes them and labels each source.
14. **MCP argument names and server path are not given.** SKILL.md names the tools but not their arguments
    (`successes`/`total`, `k_method`/`n_baseline`, `num_tasks`/`baseline_rate`) or where the server lives for
    stdio use; both had to be read from `plugin/mcp/research_audit_mcp.py`.
15. **The report file is not named.** Only `stat_audit.json` has a fixed name; this run used
    `STAT_AUDIT_REPORT.md`.
