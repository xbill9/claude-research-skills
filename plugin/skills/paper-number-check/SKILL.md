---
name: paper-number-check
description: Check every story, video narration, interactive studio page or article built from a paper against that paper's audit, and fail on any number the audit marked MISMATCH or NOT CHECKABLE that appears without its caveat. Use when outputs made from a paper are about to be shared or published, or after any of graphic-story, trajectory-cinematics, interactive-paper-studio or an article write-up.
---

# Paper Number Check

An audit records the paper's number beside the recomputed one, so a plain "is this number in the evidence?"
check passes the paper's wrong number. This skill runs the publishing kit's `check-facts.py`, which reads
the audit's verdicts and fails a claim that repeats a disputed paper value.

## Ground rules

- The counts come from `scripts/check_outputs.py`; quote its output, never a count of your own.
- A check against no verdicts proves nothing. The script refuses to run without at least one disputed audit
  record, and refuses any `check-facts.py` that does not flag a known disputed number (copies older than
  publishing-kit 0.36.0 report it as traced).
- Use the active `python3`. PDF outputs need `pymupdf` in it.

## Workflow

1. **Audit first.** Find `eq_verified_numbers.json` (math-sandbox) and `stat_audit.json`
   (ablation-stat-auditor) for this paper. If neither exists, run those skills first. An audit record is a
   JSON object with `paper_value`, `computed` and `verdict` (`VERIFIED` / `MISMATCH` / `NOT CHECKABLE`).
2. **List the outputs.** Pass the text a reader sees: the story's `Story.html` or PDF, the video's narration
   `.md` (the `.mp4` itself cannot be read), the studio's `index.html`, any article `.md`.
3. **Run the check:**

   ```bash
   python3 scripts/check_outputs.py --audit <audit dir or files> -- <output> [<output> ...]
   ```

   It finds `check-facts.py` in `$PUBLISHING_KIT_CHECK_FACTS`, the installed publishing plugin, or a
   `~/*publishing-kit*` checkout, and prints which copy passed its control. `--check-facts <path>` names one
   copy and disables the search. Exit 0: nothing disputed; 1: something disputed; 2: no working
   `check-facts.py`, no audit record, or a missing output.
4. **Fix each `DISPUTED` line at its source**, in the generator, not the rendered file: replace the paper's
   value with the recomputed one, or keep it with its caveat ("the paper reports 4.2 × 10⁻⁹; it recomputes
   to 7.18 × 10⁻⁹") and add a row containing the claim exactly as printed under `## DISPUTED` in a `CLAIMS.md`
   beside that output. Then rebuild the output and run the check again.
5. **Look at the record behind a disputed constant.** When the flagged number is a setting the claim only
   uses (a context limit, a sample size), the audit record put it in `paper_value` wrongly; fix the record
   and say so, instead of adding a caveat to a correct number.
6. **Report** the script's final lines verbatim per output: disputed, noted, traced, untraced. Untraced
   claims do not fail this check; pass the paper or data files with `--evidence` to trace them.
