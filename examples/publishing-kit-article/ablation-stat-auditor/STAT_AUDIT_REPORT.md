# Statistical Audit Report: "Streamline Publishing with a Claude Code Skill"

Paper of record: `paper/devto-publishing-kit.md`. Evidence: `paper/evidence/*.txt` and `paper/CLAIMS.md`.
All values below come from `audit_stats.py` (output in `audit_stats_output.txt`, raw tool output and claim
records in `stat_audit.json`). Intervals, Fisher and McNemar p-values come from the research-audit MCP server
called over stdio; sums, ratios, unit conversions and date gaps are computed in the script.

## Scope

This is an engineering article. It reports two counts on its cover table, one cropping calculation, a fault
count, and a measurement date; its evidence files and claim ledger add sizes, counts and sums. There is no
benchmark, no seeds and no paired resource series, so:

- **Wilson intervals** apply to the counts, with one caveat: every `n` comes from a single article or a single
  build, so the interval describes items inside that one artifact and says nothing about other articles.
- **Fisher / McNemar** apply to one comparison (Medium, data-URI build vs hosted build). The behaviour claimed is
  a deterministic editor rule, so a significance test on four images is the wrong instrument; the result is
  reported to show what four items can and cannot support.
- **Wilcoxon** was not run: no paired resource metric exists in the paper or its evidence.
- **Noise floor** was computed for the 62-block count only as context; the paper makes no comparison against it.

## Audit table

| Claim | Paper value (source) | Recomputed | Test used | Verdict |
|---|---|---|---|---|
| dev.to hard-wrapped paragraphs | 47 of 62 (article:161) | 75.8% [63.8, 84.8]; evidence 58 `<p>` + 4 `<li>` = 62, 47 with `<br>` | Wilson | HOLDS (one article) |
| "a stray break in every paragraph" | every (article:53) | 15 of 62 blocks have no break; Wilson upper bound 84.8% | Wilson + count | OVERSTATED |
| Medium data-URI images survived | 0 of 4 (article:162) | 0.0% [0.0, 49.0] | Wilson | CANNOT CHECK (no archived artifact; CLAIMS.md LOG dated 2026-08-30) |
| Medium hosted images survived | 4 of 4 (article:162) | 100.0% [51.0, 100.0] | Wilson | CANNOT CHECK (same) |
| Medium drops data-URI images on paste | 0/4 vs 4/4 (article:54, 162) | exact McNemar b=4, c=0: p = 0.125; Fisher (unpaired, wrong design): p = 0.0286 | McNemar exact | CANNOT CHECK (deterministic claim; inputs not archived; paired p above 0.05) |
| dev.to proxies the cover at 2.381:1 | 2.381 (article:53) | 1000/420 = 2.380952 | arithmetic | HOLDS |
| 1376x768 cover loses 95px top and bottom | 95 (article:54) | kept 577.92 rows; 95.04 px each side (95.0 from rounded rows) | arithmetic | HOLDS (assumes a centre crop; the URL says `gravity=auto`) |
| five faults found in the kit | 5 (article:167) | 5 items listed | count | HOLDS |
| behaviours "measured on 2026-08-31" | 2026-08-31 (article:184) | 47/62 measured 2026-09-16 (16 days later); 0/4 is a log entry dated 2026-08-30 | provenance | OVERSTATED |
| 23 of 23 opening fences labelled | 23/23 (CLAIMS.md:29) | label counts sum to 23; 100.0% [85.7, 100.0] | Wilson + sum | HOLDS (one article) |
| 40 articles: gde 24, aws-builders 13, none 3 | 40 (CLAIMS.md:32) | parts sum to 40 | sum | HOLDS |
| SKILL.md 446 lines; 2,370 total | (CLAIMS.md:21-22) | archived file is publishing 0.18.0: 649 lines, 4,580 total (internally consistent) | provenance | CANNOT CHECK (cited file overwritten) |
| Builder payload 22,542 chars, 521 → 408 lines | (CLAIMS.md:35) | evidence: 23,234 chars, 531 → 411 | provenance | CANNOT CHECK |
| Builder payload 23,214 chars, 531 → 411 lines | (CLAIMS.md:134) | evidence: 23,234 chars, 531 → 411 | provenance | CANNOT CHECK (lines match, chars differ) |
| covers 105 KB / 104 KB / 15 KB | (CLAIMS.md:30) | 104 / 104 / 15 KiB; 107 / 107 / 15 kB | unit conversion | HOLDS in size class; 105 reproduces under neither unit |
| LinkedIn post 1,269 chars, hook 80 | (CLAIMS.md:36) | 1,269 of 3,000; hook 80 within a 140-char fold | read-back | HOLDS |

Additional evidence-only figures (not claims in the article): Substack link targets kept 2 of 4 on the first
paste, 4 of 4 after `ss.prepare()` (paired McNemar b=2, c=0: p = 0.5); Substack images 2 of 2
(100.0% [34.2, 100.0]); Substack code-block line counts 2/2/1/4 preserved exactly.

## What four items can support

With all-or-none paired outcomes, exact McNemar first reaches two-sided p < 0.05 at 6 discordant items
(`mcnemar_min_discordant_for_p_lt_0.05` in `stat_audit.json`). The Medium comparison has 4. Its evidence for
the claim is the mechanism (the editor strips `data:` URIs), which needs no p-value and one reproducible run,
neither of which is archived.

## Noise floor for the 62-block count (context only)

At n = 62 and a 75.81% rate: standard error 5.44 pts, 95% half-width 10.66 pts, minimum detectable lift 15.24
pts against a fixed rate and 21.55 pts between two independent articles of the same size (80% power,
alpha 0.05). A difference smaller than 21.55 points between two such articles is not reliably detected.

## Publication-ready rows

Markdown:

| Measure | Rate [95% Wilson CI] |
|---|---|
| dev.to blocks with a stray break | 75.8% [63.8, 84.8] (47/62, one article) |
| Medium images kept, data-URI build | 0.0% [0.0, 49.0] (0/4) |
| Medium images kept, hosted build | 100.0% [51.0, 100.0] (4/4) |
| Opening fences labelled | 100.0% [85.7, 100.0] (23/23, one article) |

LaTeX:

```latex
dev.to blocks with a stray break & 47/62 & $75.8\% \,[63.8, 84.8]$ \\
Medium images kept, data-URI build & 0/4 & $0.0\% \,[0.0, 49.0]$ \\
Medium images kept, hosted build & 4/4 & $100.0\% \,[51.0, 100.0]$ \\
Medium hosted vs data-URI (exact McNemar) & $b{=}4, c{=}0$ & $p = 0.125$ \\
Opening fences labelled & 23/23 & $100.0\% \,[85.7, 100.0]$ \\
```

## Record counts

`stat_audit.json` holds 16 claim records: 7 VERIFIED, 6 MISMATCH, 3 NOT CHECKABLE. Conclusions: 8 HOLDS,
2 OVERSTATED, 6 CANNOT CHECK.
