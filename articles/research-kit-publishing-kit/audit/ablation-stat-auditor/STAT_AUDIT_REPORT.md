# Statistical Audit Report: the research-kit walk-through

Paper of record: `articles/research-kit-publishing-kit/devto-research-kit-publishing-kit.md` (414 lines). Sources: the article's `evidence/` folder, `examples/publishing-kit-article/` and its `paper/` copy of the publishing kit's walk-through. Every value below comes from `audit_stats.py`; tests and the Wilson interval come from the `research-audit` MCP server over stdio, and the Wilson bounds are also recomputed at full precision.

#### Result

39 claim records: 37 VERIFIED, 0 MISMATCH, 2 NOT CHECKABLE. Every count, rate, interval, test and before/after figure the article prints reproduces from its files.

NOT CHECKABLE:

- Line 167, "The claim describes fixed editor behaviour, so one archived paste would support it". This is a premise that Medium's paste handling is deterministic. No statistical method tests it, and no archived paste exists to try it.
- Line 403, "Each skill ran once, as a separate agent, as the example's README records." The README (`examples/publishing-kit-article/README.md:5`) records one separate agent per skill; it states no run count, and the word "once" does not appear in it.

#### Which numbers are samples

Only two figures in the article are inferential, and the methods of this skill apply to those two only.

- **47 of 62** (lines 165, 398) is every paragraph-level block of one dev.to article (58 `<p>` + 4 `<li>`, `devto-hardwrap.txt`). As a description of that article it is a full count and needs no interval. The Wilson interval, 75.806% [63.847%, 84.754%], describes dev.to's behaviour only if those 62 blocks are read as a sample of the paragraphs it renders; the article prints it without saying which reading it means.
- **0 of 4 against 4 of 4** on Medium (line 167). Paired (same four images in both pastes): exact McNemar p = 0.125 at b = 4, c = 0; with all-or-none results p is 0.0625 at five images and 0.03125 at six, so six is the first size below 0.05. Unpaired: two-sided Fisher p = 0.028571. The article states both readings, says no file records which images were pasted (no file in `paper/evidence` covers it), and dates the row 2026-08-30 (`paper/CLAIMS.md:96`). All four statements reproduce. The design choice decides the verdict: paired, the comparison is WITHIN NOISE; unpaired, it is significant.

Everything else is a full count of files or records: audit verdicts (26 = 15/6/5, 16 = 7/6/3, 20 disputed records), links (10 of 11), studio values (130, 0 mismatches), pre-flight status lines (4 traced and 3 disputed before; 5 traced, 0 disputed and 3 noted after; exits 1 and 0), evidence files (15 = 13 + 2), flags (34 to 12 over five outputs), and the `paper-number-check` tallies. Intervals and significance tests describe nothing for these, so none were run; each was recounted from its file.

#### Before/after comparisons

- **3 disputed to 0** (lines 252, 296, 401). Both runs are kit 0.36.1. Before is a copy of the article as published, after is the corrected article with three `## DISPUTED` rows; the 3 disputed numbers before are the same 3 noted after (0 of 4, 320px, 4 of 4).
- **34 flags to 12** (line 364), from `check-facts-0.36.0-vs-0.36.1.txt`: same five outputs, empty ledger, only the kit version changes. The 12 left split into 8 Medium counts (0 and 4) and 4 card-width numbers (320, 320px), which is what the article says.
- **11 to 4 and 9 to 2 noted** (lines 352, 353). The article prints only the 0.36.2 figures (4 and 2), and they match `paper-number-check-0.36.2.txt`. The 0.36.0 run in `paper-number-check.txt` noted 11 and 9, equal to the 0.36.0 flag counts for the same two outputs. Each noted number has a `## DISPUTED` row in the `CLAIMS.md` beside its output; the studio's bare `320` relies on the `320 px` row.

#### Generalisations

- The Compare and Contrast ranking (lines 376 to 383) and "Start with `math-sandbox` and `ablation-stat-auditor`" (line 389) rest on one article and one run per skill. No test can rank skills on n = 1. The Scope paragraph (line 403) states the one-article limit.
- Line 56, "A number that appears in the evidence normally passes", is a description of `check-facts.py` behaviour, outside these methods.

#### Observations outside the verdicts

- Step 1 shows 0.36.2 installed and `$KIT` resolving to 0.36.2, while the Step 9 and Step 10 pre-flight outputs were recorded on kit 0.36.1 (headers of `staged-preflight-before.txt` and `staged-preflight-after.txt`). The Step 11 refusal and the Step 12 run are 0.36.2.
- `examples/publishing-kit-article/README.md` line 20 still gives graphic-story "9 noted", the 0.36.0 figure; the article gives the 0.36.2 figure, 2.

#### All records

| Line | Article text | Paper value | Computed | Method | Verdict | Conclusion |
|---|---|---|---|---|---|---|
| 146 | math-sandbox claims: 26 {'VERIFIED': 15, 'NOT CHECKABLE': 5, 'MISMATCH': 6} | `{"total": 26, "VERIFIED": 15, "MISMATCH": 6, "NOT CHECKABLE": 5}` | `{"total": 26, "VERIFIED": 15, "MISMATCH": 6, "NOT CHECKABLE": 5}` | full count | VERIFIED | HOLDS |
| 397 | 26 claims checked: 15 verified, 6 mismatches, 5 not checkable | `{"total": 26, "VERIFIED": 15, "MISMATCH": 6, "NOT CHECKABLE": 5}` | `{"total": 26, "VERIFIED": 15, "MISMATCH": 6, "NOT CHECKABLE": 5}` | full count | VERIFIED | HOLDS |
| 378 | 6 mismatches, 5 not checkable | `{"MISMATCH": 6, "NOT CHECKABLE": 5}` | `{"MISMATCH": 6, "NOT CHECKABLE": 5}` | full count | VERIFIED | HOLDS |
| 161 | ablation-stat-auditor claim records: 16 {'VERIFIED': 7, 'MISMATCH': 6, 'NOT CHECKABLE': 3} | `{"total": 16, "VERIFIED": 7, "MISMATCH": 6, "NOT CHECKABLE": 3}` | `{"total": 16, "VERIFIED": 7, "MISMATCH": 6, "NOT CHECKABLE": 3}` | full count | VERIFIED | HOLDS |
| 379 | 6 mismatches, 3 not checkable | `{"MISMATCH": 6, "NOT CHECKABLE": 3}` | `{"MISMATCH": 6, "NOT CHECKABLE": 3}` | full count | VERIFIED | HOLDS |
| 351 | audit: 2 file(s), 20 disputed record(s) | `{"disputed_records": 20}` | `{"disputed_records": 20}` | full count | VERIFIED | HOLDS |
| 165 | 75.8%, with a 95% interval of 63.8% to 84.8% | `{"k": 47, "n": 62, "rate_pct": 75.8, "ci": [63.8, 84.8]}` | `{"k": 47, "n": 62, "rate_pct": 75.806, "ci": [63.847, 84.754]}` | Wilson 95% score interval | VERIFIED | HOLDS |
| 398 | 47 of 62 matches its evidence: 75.8%, 95% interval 63.8% to 84.8% | `{"k": 47, "n": 62, "rate_pct": 75.8, "ci": [63.8, 84.8]}` | `{"k": 47, "n": 62, "rate_pct": 75.806, "ci": [63.847, 84.754]}` | Wilson 95% score interval | VERIFIED | HOLDS |
| 165 | 15 of the 62 had none | `{"k": 15, "n": 62}` | `{"k": 15, "n": 62}` | full count | VERIFIED | HOLDS |
| 167 | If the same four images went into both, the paired test gives p = 0.125 | `{"p": 0.125, "b": 4, "c": 0}` | `{"p": 0.125, "b": 4, "c": 0}` | exact McNemar (paired) | VERIFIED | WITHIN NOISE |
| 167 | first drops below 0.05 at six images | `{"images": 6}` | `{"images": 6, "p_at_5": 0.0625, "p_at_6": 0.03125}` | exact McNemar (paired) | VERIFIED | HOLDS |
| 167 | Fisher's test gives p = 0.0286 | `{"p": 0.0286}` | `{"p": 0.02857142857142857}` | two-sided Fisher (unpaired) | VERIFIED | HOLDS |
| 167 | No file records which images were pasted. | `{"files_recording_images": 0}` | `{"files_recording_images": 0, "matched": []}` | full count | VERIFIED | HOLDS |
| 167 | the ledger carries it from a log dated 2026-08-30 with no artifact | `{"date": "2026-08-30"}` | `{"date": "2026-08-30", "row": "paper/CLAIMS.md:96"}` | full count | VERIFIED | HOLDS |
| 167 | The claim describes fixed editor behaviour, so one archived paste would support it | `{"pastes_needed": 1}` | `null` | none applies | NOT CHECKABLE | CANNOT CHECK |
| 194 | citation links: 10 of 11 resolving and identified | `{"identified": 10, "links": 11}` | `{"identified": 10, "links": 11}` | full count | VERIFIED | HOLDS |
| 382 | 10 of 11 links confirmed | `{"identified": 10, "links": 11}` | `{"identified": 10, "links": 11}` | full count | VERIFIED | HOLDS |
| 197 | All 11 links were fetched, and 10 were matched to a second source | `{"fetched": 11, "matched": 10}` | `{"fetched": 11, "matched": 10, "http_403": ["L9"]}` | full count | VERIFIED | HOLDS |
| 193 | citation dois/arxiv in paper text: 0 | `{"count": 0}` | `{"count": 0}` | full count | VERIFIED | HOLDS |
| 206 | studio check: 130 values, 0 mismatches | `{"values": 130, "mismatches": 0}` | `{"values": 130, "mismatches": 0}` | full count | VERIFIED | HOLDS |
| 215 | draws a 5-page comic | `{"pages": 5}` | `{"pages": 5}` | full count | VERIFIED | HOLDS |
| 21 | nine skills | `{"skills": 9}` | `{"skills": 9}` | full count | VERIFIED | HOLDS |
| 182 | Every dev.to cover in the article's directory is 1376x578 | `{"size": "1376x578"}` | `{"advocu-devto-publishing-kit-cover.webp": "1376x578", "cover.77acc7c4.jpg": "1376x578", "cover.ae4d639e.jp...` | full count | VERIFIED | HOLDS |
| 252 | 4 traced, 0 cited from the log, 0 untraced, 3 disputed | `{"traced": 4, "disputed": 3}` | `{"traced": 4, "disputed": 3}` | full count | VERIFIED | HOLDS |
| 258 | It exits 1. | `{"exit": 1}` | `{"exit": 1}` | full count | VERIFIED | HOLDS |
| 296 | 5 traced, 0 cited from the log, 0 untraced, 0 disputed, 3 disputed with a caveat | `{"traced": 5, "disputed": 0, "noted": 3}` | `{"traced": 5, "disputed": 0, "noted": 3}` | full count | VERIFIED | HOLDS |
| 306 | It exits 0. | `{"exit": 0}` | `{"exit": 0}` | full count | VERIFIED | HOLDS |
| 401 | pre-flight went from 3 disputed numbers to 0, with all 3 explained in the ledger | `{"before": 3, "after": 0, "noted": 3}` | `{"before": 3, "after": 0, "noted": 3}` | full count | VERIFIED | HOLDS |
| 318 | 4 traced, 0 cited from the log, 0 untraced, 3 disputed | `{"disputed": 3}` | `{"disputed": 3, "exit": 1}` | full count | VERIFIED | HOLDS |
| 258 | The 15 evidence files are the 13 the article already had plus the two audit records | `{"total": 15, "had": 13, "added": 2}` | `{"total_in_preflight": 15, "had_in_paper_copy": 13, "had_recorded": 13, "added": 2}` | full count | VERIFIED | HOLDS |
| 242 | 7 claim(s) against 15 evidence file(s), 15 dated log row(s) | `{"claims": 7, "evidence_files": 15, "log_rows": 15}` | `{"claims_listed": 7, "evidence_files": 15, "log_rows_preflight": 15, "log_rows_with_a_date_in_paper_CLAIMS"...` | full count | VERIFIED | HOLDS |
| 364 | Over the five outputs in this run that took the flags from 34 to 12 | `{"outputs": 5, "before": 34, "after": 12}` | `{"outputs": 5, "before": 34, "after": 12}` | full count | VERIFIED | HOLDS |
| 364 | the 12 are the Medium counts and the 320px card width | `{"other": 0}` | `{"medium count": 8, "card width": 4}` | full count | VERIFIED | HOLDS |
| 352 | 0 disputed, 4 noted, 7 traced, 15 untraced | `{"disputed": 0, "noted": 4, "traced": 7, "untraced": 15}` | `{"disputed": 0, "noted": 4, "traced": 7, "untraced": 15, "noted_with_0.36.0": 11, "flags_0.36.0": 11}` | full count | VERIFIED | HOLDS |
| 353 | 0 disputed, 2 noted, 8 traced, 4 untraced | `{"disputed": 0, "noted": 2, "traced": 8, "untraced": 4}` | `{"disputed": 0, "noted": 2, "traced": 8, "untraced": 4, "noted_with_0.36.0": 9, "flags_0.36.0": 9}` | full count | VERIFIED | HOLDS |
| 358 | Each noted number has a row in a `CLAIMS.md` beside its output. | `{"noted": {"interactive-paper-studio": 4, "graphic-story": 2}}` | `{"disputed_rows": {"interactive-paper-studio": ["0 of 4", "320 px", "320px", "4 of 4"], "graphic-story": ["...` | full count | VERIFIED | HOLDS |
| 137 | each skill ran as a separate agent given only its `SKILL.md`, the paper and that folder | `{"agents_per_skill": 1}` | `{"readme": true}` | file lookup | VERIFIED | HOLDS |
| 403 | Each skill ran once, as a separate agent, as the example's README records. | `{"runs_per_skill": 1}` | `{"readme_mentions_once": false}` | file lookup | NOT CHECKABLE | CANNOT CHECK |
| 403 | The comic run stopped before its final page review. | `{"stopped": true}` | `{"readme": true}` | file lookup | VERIFIED | HOLDS |

#### Publication-ready rows

Markdown: `75.8% [63.8%, 84.8%]` (47 of 62, Wilson 95%); `p = 0.125` (exact McNemar, b = 4, c = 0); `p = 0.0286` (two-sided Fisher, 4/4 vs 0/4).

LaTeX: `75.8\% \,[63.8, 84.8]`; `p = 0.125`; `p = 0.0286`.
