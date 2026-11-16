# Statistical Audit Report

Paper: `articles/research-kit-publishing-kit/devto-research-kit-publishing-kit.md` (295 lines), audited 2026-11-16 with the `ablation-stat-auditor` skill from research-kit 1.3.1. Every value below comes from `audit_stats.py` (output in `audit_stats_output.txt`, records in `stat_audit.json`). Intervals and tests were computed by the `research-audit` MCP server over stdio; the 47 of 62 interval was also computed at full precision in the script, because the server rounds to two decimals and the article rounds to one.

## Result

43 claim records: 36 VERIFIED, 3 MISMATCH, 4 NOT CHECKABLE.

Every count, rate, interval and test the article prints reproduces from its files. The three mismatches are sentences that describe those numbers more strongly than the files support. The four NOT CHECKABLE records are one design assumption and three statements no file records.

## Where the skill's methods apply

The skill is built for benchmark tables: k of n tasks, a baseline, a method, and a test between them. This article has one sampled rate and one two-way comparison.

- **47 of 62 paragraphs** is a rate from one measured article. Wilson applies: 75.8% [63.8, 84.8]. It describes paragraphs of that one article. It cannot be read as a rate for dev.to articles in general, and the article does not read it that way.
- **0 of 4 against 4 of 4 on Medium** is the one comparison. Fisher and McNemar both apply, and they disagree at 0.05: McNemar p = 0.125, Fisher p = 0.0286. Which one is right depends on whether the same four images were pasted both ways, and no file says.
- Everything else the article counts is a census of files, not a sample: 26 and 16 audit records, 10 of 11 links, 130 studio values, 5 comic pages, check-facts lines. Wilson intervals on these (10 of 11 gives [62.3, 98.4]) have no population to describe. They are checked as counts only.
- Wilcoxon does not apply: the article reports no paired resource metric.
- The noise floor has no comparison to judge. For context: at n = 62 and 75.8%, the 95% half-width is 10.66 points and the minimum detectable lift between two runs is 21.55 points. At n = 4 the half-width is 49.0 points.

## Audit table

| Claim | Line | Paper value | Recomputed | Test | Verdict | Conclusion |
|---|---|---|---|---|---|---|
| nine skills | 19 | 9 | 9 skill folders | count | VERIFIED | HOLDS |
| plugin version | 63 | 1.3.1 | 1.3.1 (plugin.json, evidence) | file | VERIFIED | HOLDS |
| math-sandbox records | 90, 259, 278 | 26: 15 / 6 / 5 | 26: 15 / 6 / 5 | count | VERIFIED | HOLDS |
| crop arithmetic | 91, 94 | 2.380952, 577.92, 95.04; 95px | same; 95 | arithmetic | VERIFIED | HOLDS; the even top/bottom split assumes a centre crop (line 96) |
| 1376x578 left whole | 126 | whole | 0.04 px lost per side | arithmetic | VERIFIED | HOLDS |
| stat-auditor records | 105 | 16: 7 / 6 / 3 | 16: 7 / 6 / 3 | count | VERIFIED | HOLDS |
| tests line | 106 | Fisher 0.02857, McNemar 0.125 (b=4, c=0) | 0.028571, 0.125 | Fisher, McNemar | VERIFIED | HOLDS |
| 47 of 62 | 109, 279 | 75.8% [63.8, 84.8] | 75.806% [63.847, 84.754]; k, n from devto-hardwrap.txt:12-13 | Wilson | VERIFIED | HOLDS |
| 15 of 62 had none | 109 | 15 | 15 | count | VERIFIED | HOLDS |
| paired p | 111 | 0.125 | 0.125 | exact McNemar | VERIFIED | above 0.05 if paired |
| "a paired comparison of the same four images" | 111 | paired | unknown; unpaired Fisher p = 0.0286 | design | NOT CHECKABLE | OVERSTATED: an assumption stated as fact |
| "first drops below 0.05 at six images" | 111 | 6 | 6 (p = 0.0625 at 5, 0.03125 at 6); 4 if unpaired | McNemar sweep | VERIFIED | HOLDS if paired |
| "what supports it is one archived paste" | 111 | 1 archived paste | 0 evidence files on it; only CLAIMS.md:96 | provenance | MISMATCH | OVERSTATED |
| log dated 2026-08-30 | 111 | 2026-08-30 | CLAIMS.md:96 | provenance | VERIFIED | HOLDS |
| four image sizes | 120-123 | as printed | same (PIL) | measurement | VERIFIED | HOLDS |
| every dev.to cover is 1376x578 | 126 | all | 3 of 3 in the folder | measurement | VERIFIED | HOLDS for this folder; covers for other articles not measured |
| five destination shapes | 128 | 5 | 5 endpoint markers on each of 4 covers | measurement | VERIFIED | count holds; reading markers as destinations is an inference |
| DOIs / arXiv ids | 137 | 0 | 0 | count | VERIFIED | HOLDS |
| 10 of 11 links | 138, 263 | 10 / 11 | 10 / 11 | count (census) | VERIFIED | HOLDS |
| "Each of the 11 links ... matched to a second source" | 141 | 11 | 10; L9 (Medium) blocked | count | MISMATCH | OVERSTATED; the next sentence corrects it |
| studio check | 150 | 130 values, 0 mismatches | 64 rows + 66 sweep = 130, 0 | count | VERIFIED | HOLDS |
| legibility | 153, 156 | 43.0pt; 9.3 px | 43.0; 9.3 (CARD_W 320, LEGIBLE_PX 10) | arithmetic | VERIFIED | HOLDS |
| 5-page comic | 159 | 5 | 5 | count | VERIFIED | HOLDS |
| check-facts before | 173-181 | 2 traced, 5 disputed | 2 ok, 5 DISPUTED; block equals evidence | count | VERIFIED | HOLDS |
| "It exits 1." | 184 | 1 | not recorded | provenance | NOT CHECKABLE | CANNOT CHECK |
| check-facts after | 214 | 3 / 0 / 5 | 3 ok, 0 DISPUTED, 5 NOTED | count | VERIFIED | HOLDS; article shows 3 of 8 lines unmarked |
| "It exits 0." | 217 | 0 | not recorded | provenance | NOT CHECKABLE | CANNOT CHECK |
| paper-number-check | 231-232 | 0/11/5/30; 0/9/7/20 | same | count | VERIFIED | HOLDS |
| kit 0.36.0 | 47 | 0.36.0 | path in evidence | file | VERIFIED | HOLDS |
| two collisions of five | 243 | 2 of 5 | 2 of 5; D1 (2.381) VERIFIED | count | VERIFIED | HOLDS |
| 1px and 4px match | 245 | both | 6 and 3 occurrences | count | VERIFIED | HOLDS |
| stat-auditor found "an overstatement" | 260 | 1 | 2 OVERSTATED rows | count | MISMATCH | HOLDS in kind; the count is 2 |
| three overstatements fixed | 280 | 3 | 3 in the Step 9 table | count | VERIFIED | HOLDS |
| "Each skill ran once" | 284 | 1 run each | not recorded | provenance | NOT CHECKABLE | CANNOT CHECK |

## Comparison and generalisation

- **Medium, 0 of 4 against 4 of 4 (line 111).** The article picks the paired test and states the pairing as fact. If paired: p = 0.125, and six all-or-none images are the smallest set that clears 0.05. If unpaired: p = 0.0286, and four already clear it. Either way the claim rests on a ledger row with no artifact. The article's own conclusion, that the claim describes fixed editor behaviour and needs one archived paste, is the right reading; the sentence says that paste exists, and the files say it does not.
- **"Every dev.to cover the kit made" (line 126)** generalises from the three covers in this article's folder. All three are 1376x578.
- **"five destination shapes" (line 128)** counts endpoint markers on the art. Five is measured; that each marks a destination is figure-forensics' reading.
- **"recomputes every count" (line 9 and Step 4)**: the article itself says each verdict is a recomputation. That holds for the numbers here; it does not hold for its three NOT CHECKABLE statements about runs and exit codes, which no file records.

## Publication-ready rows

| Measure | Value |
|---|---|
| dev.to hard-wrapped blocks with a break | 47/62, 75.8% [63.8, 84.8] |
| Medium data-URI images surviving | 0/4, 0.0% [0.0, 49.0] |
| Medium hosted images surviving | 4/4, 100.0% [51.0, 100.0] |

```latex
Hard-wrapped blocks with a break & 47/62 & $75.8\% \,[63.8, 84.8]$ \\
Medium data-URI images surviving & 0/4 & $0.0\% \,[0.0, 49.0]$ \\
Medium hosted images surviving & 4/4 & $100.0\% \,[51.0, 100.0]$ \\
```
