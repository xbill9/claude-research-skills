# RUN_NOTES: math-sandbox on devto-research-kit-publishing-kit.md

Paper of record: `../../devto-research-kit-publishing-kit.md` (414 lines). Sources read: `../../evidence/`, the
worked example `examples/publishing-kit-article/`, `~/publishing-kit` (the corrected walk-through, its
`CLAIMS.md`, `skills/publishing/scripts/`), the installed plugin cache and `claude plugin list --json`.
System `python3` with PyMuPDF and Pillow; nothing installed. No PDF guide, plots or Monte Carlo: the caller
asked to skip the PDF, and the article has no formula with a parameter to sweep and nothing sampled.

## Commands

| Command (from this folder) | Output |
| --- | --- |
| `python3 verify_math.py` | `records: 101 {'VERIFIED': 87, 'MISMATCH': 11, 'NOT CHECKABLE': 3}` |
| `check-facts.py ../../devto-research-kit-publishing-kit.md --evidence eq_verified_numbers.json ../../evidence/*` (0.36.2 from the cache) | `18 traced, 0 cited from the log, 0 untraced, 0 disputed`, exit 0 |

`verify_math.py` calls `plugin/mcp/research_audit_mcp.py` over stdio for Wilson (47/62), Fisher (4/4 vs 0/4)
and exact McNemar (b = 1..8, c = 0); requests and replies are in `mcp_log.jsonl`. It also re-runs, read-only:
check-facts 0.36.2 on a temp copy of `paper/` with both audits staged (Step 9), check-facts on the corrected
walk-through in `~/publishing-kit` (Step 10), and `check_outputs.py` in the example folder (Step 12). Every
quoted output block is compared with its evidence file line by line; a dropped non-blank line with no `...`
in its place, or a reordered line, is a MISMATCH.

The second command shows this audit's records add no collision: no number the article states matches a
MISMATCH or NOT CHECKABLE record here, because every non-numeric record carries a string `paper_value`.

## Findings

MISMATCH, quoted blocks (lines picked from an evidence file without `...`):

1. Line 146-147: two lines from `run-counts.txt` lines 2 and 16; 13 lines between them dropped.
2. Line 161-162: `run-counts.txt` lines 3 and 5; the `wilson:` line between them dropped.
3. Line 176-179: four of six image lines, reordered (`cover-builder.cabd79f3.jpg` is listed last; it is line 9
   of the evidence, before the others), and `linkedin-devto-publishing-kit-cover.jpg` dropped.
4. Line 193-194: the two citation lines in reverse order (`citation links` is line 6, `citation dois/arxiv` line 7).
5. Line 254-255: `FAIL  facts` then `1 check(s) failed: facts`; the three `PASS` lines between them (prose,
   article, linkedin) are dropped with no `...`. Readers see a pre-flight that ran only one check.

MISMATCH, wording against the source or the evidence:

6. Line 39, "`preflight.py` runs every check": `check-links.py` runs only with `--live` (preflight.py 90-94).
7. Line 39, "pulls each number out of the article": check-facts extracts only numbers that match its claim
   patterns, in prose outside fenced code; the walk-through yields 7 claims.
8. Line 165, "The same sentence in the article said 'a stray break in every paragraph'": in the walk-through
   "every paragraph" is at line 53 and "47 of 62" at line 161 (a table row). Same claim, two places.
9. Line 31, `paper-number-check` "Fails any output that repeats a number the audit disputes": a repeat with a
   `## DISPUTED` ledger row passes as NOTED (Step 12 shows 6), and only pattern-matched prose numbers are seen.
10. Line 389, "every other step reads them": figure-forensics and citation-doi-verifier ran given only their
    SKILL.md, the paper and a folder (README line 5; the article's own line 137).
11. Line 403, "Live pages were fetched only by the link check": the article itself reports citation-doi-verifier
    fetching 11 links, `preflight.py --live` (check-links and make-linkedin), and publish-devto calling dev.to.

NOT CHECKABLE: line 167 "No file records which images were pasted" (an absence); line 184 "no text at all and
five destination shapes" (visual; figure-forensics reports 5 computed markers, not re-measured here); line 403
"Each skill ran once" (the README says separate, independent agents and gives no run count).

Verified with a note: Wilson 63.8% is right (exact lower bound 63.8475%); the MCP's 2-decimal `63.85` re-rounded
gives 63.9, so compare from the `formatted` field. Steps 9-10 outputs were captured under publishing-kit 0.36.1
while the Scope line says 0.36.2; every script `preflight.py` runs is byte-identical in the two, and the claim
rows re-run under 0.36.2 match. The Step 10 ledger block shows 3 of the 5 `## DISPUTED` rows (the other two
explain collisions). "47 of 62 paragraphs" counts 58 `<p>` and 4 `<li>` blocks. `evidence/make-cover-constants.txt`
is headed "publishing-kit ff55eee" but its line 263 ("about 40pt") is from dec86c0; ff55eee has only line 264.

## Where the skill fell short

1. The workflow covers equations only. An article's numbers come with quoted tool output, statements about what
   tools do, and words like "every"; the skill has no step for comparing a quoted block with its evidence file,
   checking behaviour claims against source, or flagging overstated quantifiers. All 11 MISMATCHes came from
   work it does not ask for.
2. Step 2 gives two record schemas: the first adds `simulated`, `abs_gap` and `tolerance`, the second lists
   `id, statement, paper_value, paper_source, computed, verdict, reason`. It does not say which wins.
3. `seed=42`, Monte Carlo and sensitivity plots are mandatory with no clause for a paper that has nothing to
   sample or sweep.
4. It does not say what `paper_value` holds for a non-numeric claim. A number there collides in check-facts
   with an unrelated claim (an exit-status record matching `2.381:1` happened in an earlier audit of this
   article); a string is safe. Nor does it say to run check-facts on the article with the new records before
   handing them off, which is how a collision is caught.
5. No rounding rule. Comparing a one-decimal paper value with an already-rounded tool value can turn a correct
   figure into a MISMATCH (63.85 to 63.9 against an exact 63.8475).
6. No top-level JSON shape is given (a list, or an object with `equations`). check-facts walks any nesting, but
   `evidence/run_counts.py` reads `["equations"]`.
7. No rule for a claim repeated on several lines: one record per occurrence or one per claim.
8. "Deliver the PDF" has no opt-out for a quick audit; the PDF was skipped on the caller's instruction.
9. No guidance on evidence files that are themselves excerpts or mixed captures (`publish-devto-refuses.txt` keeps
   only the facts rows of what publish-devto printed; `make-cover-constants.txt` mixes two commits under one header).
