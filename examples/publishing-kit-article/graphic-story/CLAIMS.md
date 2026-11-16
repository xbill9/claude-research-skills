# Claims in Story.html that the audit disputes

Checked with `paper-number-check` against `../math-sandbox/eq_verified_numbers.json` and
`../ablation-stat-auditor/stat_audit.json`.

## DISPUTED

| Claim | Record | Status in the story |
| --- | --- | --- |
| 0 of 4 | E3_medium_data_uri_0_of_4, NOT CHECKABLE | Real dispute. Shown on pages 2 and 5 only beside the caveat "Kit log, 2026-08-30, not re-measured: no artifact is archived (audit: NOT CHECKABLE), and this article's own Medium builds hold different images". `build_story.py` fails if the caveat is missing. |
| 4 of 4 | E3_medium_data_uri_0_of_4, NOT CHECKABLE | Same record and caveat as 0 of 4. |
| 95px | M1_own_source_95_columns | Number collision. The story's 95px is the cover crop, VERIFIED in B2_crop_loss_95px and devto-crop-95px. M1 is about the 95-column source wrap, which the story no longer quotes. |
| 2.381:1 | M5_substack_source_shape | Number collision. 2.381 is VERIFIED (D1_proxy_ratio, devto-crop-ratio: 1000/420 = 2.380952); the match is the "1" against M5's code-block line counts. |
| 1px | M5_substack_source_shape | Number collision with a CSS border width, not a claim. |
| 2px | M5_substack_source_shape | Number collision with a CSS border width, not a claim. |
| 4px | E3_medium_data_uri_0_of_4 | Number collision with a CSS padding value, not a claim. |
| 6px | M5_substack_source_shape | Number collision with a CSS border radius, not a claim. |
| 7px | M5_substack_source_shape | Number collision with a CSS padding value, not a claim. |

## Removed at the source

| Article wording | Record | Change in `build_story.py` |
| --- | --- | --- |
| "a stray break in every paragraph" | E2_break_in_every_paragraph, hardwrap-every-paragraph (MISMATCH) | Replaced by the measured "47 of your 62 blocks". |
| "The two numbers on the cover" | No audit record; `../README.md` finds neither number on any cover | Caption now reads "The article's dogfooding table, quoted as printed". |
| "measured on 2026-08-31" | measured-date (MISMATCH) | Kept as "The article dates these behaviours 2026-08-31", with the audit's dates printed below. |
| "95 columns" | M1_own_source_95_columns (NOT CHECKABLE) | Dropped from page 2 and page 4. |

`build_story.py` fails the build if the story prints "every paragraph" or "numbers on the cover", or shows a
disputed number without its caveat.
