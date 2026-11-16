# RUN_NOTES: math-sandbox on publishing-kit-article

Skill: `plugin/skills/math-sandbox/SKILL.md`. Paper: `examples/publishing-kit-article/paper/devto-publishing-kit.md` (dev.to article, no equations), with `evidence/*.txt` and `CLAIMS.md` as its archived evidence. The kit constants for the 320px card were read from the local publishing-kit checkout (`~/publishing-kit`, HEAD dec86c0 2026-11-16), read-only.
Environment: python3 3.14.7 (pyenv), numpy 2.5.3, scipy 1.18.1, matplotlib 3.11.1, Pillow 12.3.0, Chrome for rendering. No packages installed.

Deliverables in this folder: `PublishingKit_Equation_Guide_v1.pdf` (7 pages), `eq_verified_numbers.json` (26 records), `verify_math.py`, `build_guide.py`, `MathGuide.html`, `figures/` (3 sensitivity plots at 300 DPI, 6 equation SVGs), `PublishingKit_Equation_Guide_v1_preview/` (page PNGs and montage), `mcp_wilson_request.jsonl` / `mcp_wilson_response.jsonl`.

## 1. Commands run and key output

| Command | Key output |
|---|---|
| `python3 -c "from PIL import Image; ..."` over the paper's cover files | `cover.77acc7c4.jpg` and `cover.ae4d639e.jpg` 1376x578; `cover-builder.*` 1200x675; LinkedIn cover 1200x627 |
| `grep -n CARD_W ... ~/publishing-kit/.../make-cover.py` | `CARD_W = 320`, `LEGIBLE_PX = 10`; type sizes are final pixels (`S = 2` supersample then downsample) |
| `python3 -I plugin/mcp/research_audit_mcp.py < mcp_wilson_request.jsonl` | `verify_wilson_ci` 47/62: rate 75.81%, Wilson 63.85-84.75% |
| `python3 verify_math.py` (final, 1.9 s) | `{"VERIFIED": 15, "MISMATCH": 6, "NOT CHECKABLE": 5}` |
| `ruff check` / `ruff format --check` with the repo's `ruff.toml` | all checks pass; `build_guide.py` carries a file-level E501 exemption for its HTML/SVG template text |
| `python3 build_guide.py` | writes `MathGuide.html` and `figures/eq/*.svg` |
| `python3 plugin/skills/math-sandbox/scripts/pdf_tools.py render --html MathGuide.html --pdf PublishingKit_Equation_Guide_v1.pdf` (4 renders) | final: 7 pages, 553,853 bytes |

Page PNGs were opened with Read after each render. Fixes between renders: an orphaned table row on its own page, a table header stranded at a page foot (now `<thead>` repeated on continuation pages, section 5 as one table), long claim ids breaking mid-word (break points after `_`), equation images scaled to one fixed height so the first formula rendered smaller than the rest, and a plot label that rounded an already-rounded bound (63.85 -> 63.9; now 63.8 from the unrounded 63.846).

## 2. Headline findings (from eq_verified_numbers.json)

- **Cover crop: VERIFIED.** 1000/420 = 2.380952 (prints as 2.381). A 1376-wide cover keeps 577.92 rows; 768 - 577.92 = 190.08 rows lost, 95.04 a side. A real Pillow fit=cover crop of a row-encoded 1376x768 image keeps rows 95 to 672. The proxy URL asks for `gravity=auto`, so the 95/95 split assumes a centred crop; the 190-row total does not depend on it. Both shipped covers are 1376x578 and lose 0 rows.
- **320px card:** the kit's own constant is 320 (VERIFIED). With `LEGIBLE_PX = 10`, type under 43.0 px on a 1376-wide cover is lost in the card. That dev.to's card is 320px has no archived measurement (NOT CHECKABLE).
- **47 of 62: VERIFIED** against the evidence (58 `<p>` + 4 `<li>` = 62; 88 total `<br>`). 75.81%, Wilson 95% 63.85-84.75%; bootstrap (100,000 draws, seed 42) SE 5.441 points. The article's wording "a stray break in every paragraph" is a **MISMATCH** with that same measurement: 15 of 62 blocks carry no break.
- **Medium "0 of 4 / 4 of 4": NOT CHECKABLE.** No archived artifact (CLAIMS.md files it as LOG 2026-08-30). This article's own Medium builds hold 2 images each, so the 4 come from another article.
- **CLAIMS.md disagrees with its own evidence in four rows (MISMATCH):** Builder payload 22,542 chars / 521 / 408 lines and 23,214 chars against 23234 chars / 531 / 411 in `builder-payload.txt`; a 105 KB cover that is 106890 bytes (104.38 KiB, 106.89 kB, neither rounds to 105); and pinned commit f7eaac2 where the evidence shows 920fe6c (pinned == HEAD and the inode difference both hold).
- **Archived Medium HTML: MISMATCH.** It has 3 `<pre>` blocks where `substack-paste.txt` counted 4; its third block is the evidence's blocks 3 and 4 joined (65 + 1 + 225 = 291 chars, 1 + 4 = 5 lines). Images, `<h4>` and links match.
- **Cover pixel diffs:** the Builder hero figures fit the triangle-inequality bound (local new-vs-old RGB 14.671, within 0.56 of 14.66; VERIFIED). The Substack figure needs new-vs-old = 18.71; the local files give 18.775 (RGB) and 18.546 (greyscale), so the evidence's unstated method differs (NOT CHECKABLE).
- **Counts inside the article: VERIFIED.** TL;DR is 5 source lines, five faults are listed, the description is 241 chars. Org split 24 + 13 + 3 = 40, fences 23 of 23, KB = chars/1024 for three files, footprint 649 + 809 + 24 + 3098 = 4,580, LinkedIn hook 80 chars.
- The ledger's 0.2.0 footprint row (parts sum to 2,361, 9 short of the stated 2,370) and its token costs have no artifact: `skill-footprint.txt` was overwritten at 0.18.0 (NOT CHECKABLE).

## 3. Where the skill's instructions fell short for this input

1. **Scope.** The skill covers "equations, theorems, bounds and control laws". This paper has none; its checkable content is geometry, one proportion and counts and sizes in prose, evidence and a claim ledger. The skill does not say whether such claims are in scope, or which files count as "the paper" (article only, or also its evidence and `CLAIMS.md`, whose rows produced four of the six MISMATCHes).
2. **Two record schemas in one step.** Step 2 lists `id, paper_value (with source), computed, simulated, abs_gap, tolerance, verdict` and then a second, different list (`statement, paper_source, reason`, no `simulated`). I wrote the union.
3. **Mandatory Monte Carlo.** "Check each closed-form claim by simulation" has no meaning for integer counts, file sizes or commit ids. The skill does not say when `simulated` may be null. I simulated only the crop (a real Pillow crop) and the 47/62 proportion (bootstrap).
4. **What VERIFIED means for self-reported evidence.** Most checks here compare the article against its own archived files. The skill has no verdict for "consistent with the paper's evidence, not re-measured", nor for "true of the author's tool, unknown for the destination" (I split the 320px claim into two records for that).
5. **Wording claims.** "A stray break in every paragraph" is false on a literal reading and plausible on a charitable one ("every wrapped paragraph"). The skill gives no rule for literal versus charitable reading, or for when that is MISMATCH rather than NOT CHECKABLE.
6. **Dated and overwritten evidence.** Two evidence files were re-captured at later versions (footprint at 0.18.0, install snapshot at 0.6.0), so ledger rows dated earlier no longer have an artifact. The skill says nothing about evidence that is newer than the claim.
7. **Unstated measurement methods.** The pixel-difference figures name no method. The skill gives no guidance on trying several methods or setting a tolerance when the method is unknown.
8. **Sources outside the paper folder.** The 320px constant can only be checked against the kit's source code, which lives outside the paper directory and is at a later commit than the article. The skill does not say whether reading external source is allowed or how to record the version read.
9. **"Nominal parameters", "failure regime", "calibrated operating point".** These fit control laws. For a crop, the failure regime is clear (taller than 2.381:1), but a proportion has no calibrated point, so I plotted the claim line instead.
10. **Render path and output naming.** `scripts/pdf_tools.py` is relative to the skill directory while the HTML sits in the output folder, so an absolute script path is needed. `<Paper>` and the output directory are undefined.
11. **Stale preview pages.** `pdf_tools.py render` does not clear its preview folder. A render that dropped from 8 pages to 7 left the old `page_08.png` in place, which looks like a real page. The skill's "open every page PNG" step does not warn about this; I deleted the folder before each later render.
12. **KaTeX.** The skill asks for KaTeX "inlined or pre-rendered" but ships none. I pre-rendered formulas to SVG with matplotlib mathtext.
13. **Deliverables and the "PDF quotes that file" step.** No mechanism is given for filling the HTML from the JSON. `build_guide.py`, `MathGuide.html` and the figures are needed to rebuild the PDF but are not on the deliverables list.
14. **Table layout.** There are no CSS hints for page breaks. Chrome printing stranded a header row and orphaned a single row until `thead { display: table-header-group }` and `tr { break-inside: avoid }` were added.
15. **The research-audit MCP tools are not mentioned.** `verify_wilson_ci` was used to confirm the 47/62 interval; the skill does not point to it.
16. **check-facts consumption.** Several records concern `CLAIMS.md` values (23,214, 105 KB, f7eaac2) rather than article sentences. The skill does not say whether `check-facts.py` should treat those as paper values, or how a multi-number record such as `{"data_uri_survived": [0, 4]}` maps onto numbers in later prose.

## 4. Not done

- No live fetch of dev.to, Medium, Substack or Builder Center; every VERIFIED is against archived files or the kit's source.
- The 2026-08-31 version of `make-cover.py` was not checked out; the constants are from HEAD dec86c0.
- No `git commit`; nothing outside `math-sandbox/` was modified.
