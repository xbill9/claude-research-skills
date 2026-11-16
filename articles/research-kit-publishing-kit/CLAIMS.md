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

**Correction (2026-11-16), second audit round.** math-sandbox (101 records: 87 VERIFIED, 11 MISMATCH,
3 NOT CHECKABLE) and ablation-stat-auditor (39 records: 37 VERIFIED, 0 MISMATCH, 2 NOT CHECKABLE) found no
wrong number. Fixed before publishing:

| Was | Now |
| --- | --- |
| five quoted output blocks cut or reordered with no marker | quoted in evidence order, cuts marked `...` |
| `preflight.py` runs every check | runs its checks, the link check only with `--live` |
| `check-facts.py` pulls each number out of the article | pulls the numbers that look like claims out of the prose |
| paper-number-check fails any output that repeats a disputed number | unless the ledger explains it |
| The same sentence in the article said "every paragraph" | Elsewhere the article said |
| every other step reads the audit records | the pre-flight and paper-number-check read them |
| Live pages were fetched only by the link check | by the link check, `preflight.py --live` and the dev.to API calls |
| Each skill ran once | each skill ran as a separate agent |
| No file records which images were pasted | the evidence does not record it |
| the current cover has no text at all and five destination shapes | figure-forensics counts five shapes and no text |

Steps 9 and 10 were re-captured on publishing kit 0.36.2.

## DISPUTED

Numbers the article states that `check-facts.py` matches to a disputed audit record, kept with the reason.
All four are number collisions: the record stores a small integer that equals one in the claim.

| Claim | Audit record | Why it stays |
| --- | --- | --- |
| 0 of 4 | C18b_covers_no_numbers, NOT CHECKABLE | collision: the record's value is 0 numbers on the covers; the claim is the Medium paste count, labelled as an unarchived log entry |
| 10 of 11 | C20_each_of_11_matched, MISMATCH | collision: 10 of 11 is the record's recomputed value, which the article now states |
| 1px | C27a_exit_code, NOT CHECKABLE | collision: the record's value is exit status 1; 1px is a stylesheet length, counted in `evidence/studio-css-lengths.txt` |
| 2.381:1 | C27a_exit_code, NOT CHECKABLE | collision: same record; 1000/420 = 2.380952 is in `evidence/run-counts.txt` |
