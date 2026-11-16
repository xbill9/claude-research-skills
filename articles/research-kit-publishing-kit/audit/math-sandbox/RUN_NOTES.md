# RUN_NOTES: math-sandbox on devto-research-kit-publishing-kit.md

Paper of record: `../../devto-research-kit-publishing-kit.md`. Evidence: `../../evidence/`, the worked example in
`examples/publishing-kit-article/`, the plugin manifests, and the publishing-kit working tree at `~/publishing-kit`
(corrected article, `CLAIMS.md`, `make-cover.py`). System `python3`, PyMuPDF and Pillow already installed; nothing installed.

## 1. Commands

| Command (from this folder) | Output |
| --- | --- |
| `python3 verify_math.py` | `records: 45 {'VERIFIED': 38, 'MISMATCH': 3, 'NOT CHECKABLE': 4}` |

`verify_math.py` calls `plugin/mcp/research_audit_mcp.py` over stdio for Wilson (47/62), Fisher (4/4 vs 0/4) and
exact McNemar (b=4,c=0 and b=1..10,c=0). The requests and raw replies are in `mcp_calls.jsonl` and `mcp_responses.txt`.
No PDF guide, sensitivity plots or Monte Carlo: the article has no formula with a parameter to sweep and nothing stochastic.

## 2. Findings

Records are one per claim occurrence where the same number appears on several lines (the 26/15/6/5 tally three times,
47 of 62 twice, 10 of 11 twice), so check-facts can match each.

MISMATCH

- C17, line 126: "Every dev.to cover the kit made is 1376x578, which the 2.381:1 crop leaves whole. The article's 1376x768
  example describes a size the kit does not ship." The audited paper's own `evidence/toolchain-run.txt` (2026-08-31) records
  the kit writing `devto-cover-aws.44aee846.jpg` and `devto-cover-gde.0d021e90.jpg`; its `CLAIMS.md` line 30 lists them as
  1376x768, and `~/gemma4-dev/docs/devto-cover-aws.jpg` and `-gde.jpg` measure 1376x768. Only the covers in `paper/` are
  1376x578. The "leaves whole" part holds (0.08 source rows lost).
- C20, line 141: "Each of the 11 links was fetched instead and matched to a second source". REPORT.md: 10 of 11 matched;
  L9 (Medium) is BLOCKED with HTTP 403, as the article's next sentence says.
- C37, line 9: "The research skills recompute every number the article states." 5 of 26 math-sandbox records are
  NOT CHECKABLE, so 21 were recomputed to a value. Same wording at line 23 ("Recomputes each quantitative claim") and
  line 278 ("26 claims recomputed").

NOT CHECKABLE

- C18b, line 128: "Both covers carry no numbers, and the current one has no text at all". Established by figure-forensics
  reading the images; no computed text measure exists. (The "five destination shapes" part is VERIFIED: 5 endpoints in
  `figure-forensics/work/measurements.json`.)
- C27a, line 184: "It exits 1." and C27b, line 217: "It exits 0." The evidence files capture output only, no exit status.
- C36, line 284: "Each skill ran once, as a separate agent." One RUN_NOTES.md per skill folder; nothing records agent
  separation or run count. Line 81 makes the same claim.

Notes that are not verdicts

- Line 207-214: the "after" block shows 3 of the 8 claim lines in `check-facts-after.txt` with no mark that lines were cut;
  every line shown is verbatim and the summary line matches. A reader could take it as 3 claims checked.
- Line 260: the Compare table sums ablation-stat-auditor as "an overstatement and an unsupported comparison"; its file has
  6 MISMATCH and 3 NOT CHECKABLE records (line 105 states this correctly).
- Line 153-156: `make-cover.py` now says 43pt; `evidence/make-cover-constants.txt` still shows the old "about 40pt" line 263
  next to the new line 264, so that evidence file reads as if both are present.

## 3. Where the skill fell short

1. The skill assumes equations, theorems and control laws. A technical article has counts, sizes, versions and tallies, and
   the skill has no step for pulling quantitative claims out of prose with line numbers.
2. Step 2 gives two different record schemas (one with `simulated`, `abs_gap`, `tolerance`; one with `statement`,
   `paper_source`, `reason`). I wrote the second plus `evidence`.
3. `seed=42`, Monte Carlo, sensitivity plots and the PDF are mandatory steps with nothing to apply them to here; the skill
   does not say when to skip them.
4. No rounding rule. The MCP server returns Wilson bounds at 2 dp (63.85); rounding that again to 1 dp gives 63.9 against
   the article's 63.8, while the full-precision bound is 63.847. The skill should say: compare at full precision, round once.
5. No verdict or field for wording that overstates its evidence ("every", "each"). I recorded those as MISMATCH with
   `overstatement: true`.
6. No guidance for a claim made several times: one record per claim or per occurrence. check-facts matches numbers by
   occurrence, so it matters.
7. No guidance for quoted tool output that is accurate but abridged (C26 above).
8. The skill does not mention the plugin's own MCP server for Wilson, Fisher and McNemar, or how to call it outside a session.
9. No route for claims about image content (text, numbers on a cover); those need figure-forensics and stay NOT CHECKABLE here.
10. No rule for evidence outside the paper's folder. Four records read the publishing-kit working tree and `~/gemma4-dev`,
    which can change after this run; the skill does not ask for a commit id or snapshot.
11. The skill does not ask that evidence capture exit status, so every "it exits N" claim is NOT CHECKABLE.
