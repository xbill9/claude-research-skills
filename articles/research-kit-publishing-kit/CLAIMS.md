# Claim ledger

Evidence for every number in `devto-research-kit-publishing-kit.md` is in `evidence/`. The article was
audited with research-kit's `math-sandbox` and `ablation-stat-auditor`; their records are in `audit/`.

## Corrections

**Correction (2026-11-16).** The audits found six sentences that said more than their evidence. Each was
reworded before publishing:

| Was | Now | Audit record |
| --- | --- | --- |
| The research skills recompute every number the article states | recompute the numbers ... and mark the ones they cannot check | 21 of 26 recomputed; 5 NOT CHECKABLE |
| Every dev.to cover the kit made is 1376x578; the 1376x768 example describes a size the kit does not ship | every dev.to cover in the article's directory; the kit made 1376x768 covers before `--mode devto` changed | `evidence/older-covers.txt` |
| Each of the 11 links was fetched and matched | all 11 fetched, 10 matched | C20_each_of_11_matched |
| a paired comparison of the same four images | if the same four images went into both pastes; no file records which | pairing NOT CHECKABLE |
| what supports it is one archived paste | one archived paste would support it | 0 archived pastes |
| 26 claims recomputed | 26 claims checked | 5 of 26 NOT CHECKABLE |

The Compare and Contrast row for `ablation-stat-auditor` now states its tallies (6 mismatches, 3 not
checkable), and the exit codes the article states are recorded in `evidence/check-facts-exit-codes.txt`.

## DISPUTED

Numbers the article states that `check-facts.py` matches to a disputed audit record, kept with the reason.
All four are number collisions: the record stores a small integer that equals one in the claim.

| Claim | Audit record | Why it stays |
| --- | --- | --- |
| 0 of 4 | C18b_covers_no_numbers, NOT CHECKABLE | collision: the record's value is 0 numbers on the covers; the claim is the Medium paste count, labelled as an unarchived log entry |
| 10 of 11 | C20_each_of_11_matched, MISMATCH | collision: 10 of 11 is the record's recomputed value, which the article now states |
| 1px | C27a_exit_code, NOT CHECKABLE | collision: the record's value is exit status 1; 1px is a stylesheet length, counted in `evidence/studio-css-lengths.txt` |
| 2.381:1 | C27a_exit_code, NOT CHECKABLE | collision: same record; 1000/420 = 2.380952 is in `evidence/run-counts.txt` |
