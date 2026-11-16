# Worked example: the research skills on an engineering article

**Paper:** *Streamline Publishing with a Claude Code Skill*, the dogfood article of [publishing-kit](https://github.com/xbill9/publishing-kit), copied unchanged into [`paper/`](paper/) from `articles/publishing-kit-skill/` at `dec86c0`. The paper of record is `paper/devto-publishing-kit.md`; `paper/evidence/` and `paper/CLAIMS.md` are the evidence it cites.

**Method:** each skill was run on 2026-11-16 by a separate agent given only that skill's `SKILL.md`, the paper and an output folder. The runs were independent of one another. Each folder holds the deliverables, the scripts that produced them, and a `RUN_NOTES.md` with the commands run and a numbered list of places where the skill's instructions fell short. The five notes list 66 such items between them. `paper-number-check` was then run on the interactive page against the math and statistics audits.

This article has no equations, no bibliography and no benchmark table. The example shows what each skill finds on that kind of input, and where its instructions stop fitting.

---

#### What each skill produced

| Skill | Deliverables |
| :--- | :--- |
| [`math-sandbox`](math-sandbox/) | 7-page `PublishingKit_Equation_Guide_v1.pdf`, `eq_verified_numbers.json` (26 claims: 15 VERIFIED, 6 MISMATCH, 5 NOT CHECKABLE) |
| [`ablation-stat-auditor`](ablation-stat-auditor/) | `STAT_AUDIT_REPORT.md`, `stat_audit.json` (16 claim records) |
| [`citation-doi-verifier`](citation-doi-verifier/) | `REPORT.md`, `verified_references.bib`, every response in `raw/` |
| [`figure-forensics`](figure-forensics/) | 6-page `PublishingKit_Figure_Anatomy_v1.pdf`, five annotated figures |
| [`interactive-paper-studio`](interactive-paper-studio/) | Offline `index.html`: cover crop, feed-card legibility and hard-wrap explorer; 130 values agree exactly with the Python reference model; `CLAIMS.md` from `paper-number-check` |

`trajectory-cinematics` was not run: the article has no system state that changes across turns or time. `frontier-gap-radar` was not run: it surveys a research literature, and a publishing toolkit has none to survey. `graphic-story` was started and stopped before its page review, so it is not included.

---

#### What the runs found in the article

- **The cover-crop arithmetic holds.** 1000 / 420 = 2.380952, and a 1376×768 cover keeps 577.92 rows, losing 95.04 px top and bottom, assuming a centre crop (the proxy URL says `gravity=auto`).
- **No cover is 1376×768.** Both dev.to covers and the Advocu cover are 1376×578, which the crop leaves whole. The 95 px loss is correct for a size the kit does not ship.
- **"The two numbers on the cover"**: neither number is on any cover. The current cover has no text and five destination markers; the article says four destinations. The numbers appear in the table image.
- **47 of 62 matches its evidence** (58 paragraphs + 4 list items), 75.8%, 95% interval 63.8–84.8%. The article's "a stray break in every paragraph" overstates it: 15 of the 62 blocks had none.
- **"0 of 4 ... 4 of 4" on Medium has no archived evidence.** `CLAIMS.md` carries it from the kit's log of 2026-08-30. Four images cannot reach significance in a paired test; six is the minimum.
- **The footer date covers neither cover number.** It says 2026-08-31; the 47/62 count is dated 2026-09-16 and the Medium count 2026-08-30.
- **The source is wider than its stated 95 columns.** 20 of 106 prose lines are longer, the longest 126 characters.
- **The kit's own legibility rule disagrees with its comment.** With `LEGIBLE_PX = 10` and a 320 px card, a 1376-wide cover needs 43 pt type; the comment in `make-cover.py` says about 40 pt.
- **`CLAIMS.md` disagrees with re-captured evidence in four rows:** two Builder payload sizes, a "105 KB" cover that is 104.38 KiB or 106.89 kB, and a pinned commit (`f7eaac2` in the ledger, `920fe6c` in the evidence). None of these numbers appears in the article.
- **Links:** 10 of 11 resolve and match the article; the Medium copy returns HTTP 403 to scripts. `links.txt` labels the dev.to copies as drafts; the dev.to API reports both published on 2026-09-01.

---

#### Fixed in the kit as a result of this run

- `pdf_tools.py render` deletes old `page_*.png` files before writing a preview. A PDF that went from 8 pages to 7 had left `page_08.png` behind beside the new pages. Version 1.3.1.

#### Found, not yet fixed

- `paper-number-check` flagged 11 numbers on the interactive page; 3 are real disputes and 8 are number collisions. `check-facts.py` matches every number inside a record's `paper_value`, including small integers in a table of counts, and it reads CSS, so `1px`, `4px`, `6px` and `15px` matched. Each is recorded with its reason in [`interactive-paper-studio/CLAIMS.md`](interactive-paper-studio/CLAIMS.md).
