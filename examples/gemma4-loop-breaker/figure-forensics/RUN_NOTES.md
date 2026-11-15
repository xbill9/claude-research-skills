# figure-forensics test run: gemma4-loop-breaker paper

Skill: `plugin/skills/figure-forensics/SKILL.md`. Paper: `examples/gemma4-loop-breaker/paper/`.
Environment: python3 3.14.7, pillow 12.3.0, matplotlib 3.11.1, pymupdf 2.1, scipy 1.18.1, `/usr/bin/google-chrome`. No packages installed.

Deliverables:

- `Gemma4_LoopBreaker_Figure_Anatomy_v1.pdf`: 4-page A4 dossier (summary page, then one page per figure)
- `Anatomy.html`: the dossier source
- `annotated/fig{1,2,3}_*_annotated.png`: the figures with badges and shading, at 300 DPI
- `scripts/annotate_figures.py`, `scripts/check_figure_numbers.py`, `scripts/digitize_fig2b.py`
- `work/`: PDF text dump, check output, digitized Fig. 2(b) values
- `Gemma4_LoopBreaker_Figure_Anatomy_v1_preview/`: the page PNGs and montage that the render step writes

## 1. Commands and key output

1. Inspected the PDF with PyMuPDF. It has 5 pages (612×792 pt, Letter), produced by ReportLab, with one raster image on each of pages 2, 3 and 4 (xrefs 4, 7, 10, each 3180 px wide).
2. Compared the embedded images with `paper/figures/*.png`. They have the same size and a maximum pixel difference of 0, so the figures are 300-DPI rasters and the PNGs are the originals.
3. Dumped the PDF text with `page.get_text()` into `work/paper_text.txt`. **The PDF text differs from PAPER.md** (see section 3), so the PDF is treated as the source of record.
4. Located the Fig. 2(b) axes by detecting spines and tick marks. Turn 1 is at x = 1876 px and turn 12 at x = 3085 px. On the y axis, 0 is at 953 px and 30k at 232 px.
5. Ran `python3 scripts/digitize_fig2b.py paper/figures/fig2_ablation_sawtooth.png work/fig2b_digitized.json`. The first run picked up the legend box as a data point (gray turn 3 = 32.45), so I masked out the legend region. Second run:
   ```
   naive_subagent (gray)    [4.37, 8.13, 12.65, 16.91, 20.41, 23.82, 26.53, 28.4, 29.81, 30.6, 31.02, 31.1]
   baseline_static (red)    [3.99, 7.24, 10.94, 14.79, 17.64, 19.93, 21.84, 23.13, 24.05, 24.55, 24.76, 24.84]
   ccr_adaptive (blue)      [3.41, 5.83, 8.32, 10.42, 4.49, 6.62, 8.9, 10.53, 4.79, 6.82, 8.4, 9.4]
   ccr_adaptive vs baseline, area over 12 turns: -59.6%
   ccr_adaptive drops: (5, 10.42 -> 4.49, -56.9%), (9, 10.53 -> 4.79, -54.5%)
   baseline first turn above 14.336k: 4
   ```
6. Ran `python3 scripts/check_figure_numbers.py`. The full output is in `work/check_figure_numbers.out`. Key lines:
   ```
   Fisher exact 24/25 vs 4/25 (two-sided): p = 7.179e-09
   Fisher exact 24/25 vs 4/25 (greater): p = 3.589e-09
   sum of avg turns x 25 episodes x 4 configs = 937.0
   Tax: Table1 calibrated - M2 = 22.5 pts; 29 tasks
   M2->M6 tasks recovered: 9 of 29 = 31.0%;  M0->M6: 16 tasks
   Remaining gap M6 vs Stage-1 ceiling: 15.5 pts, 20 tasks
   Compaction M0->M6: -93.1%  M2->M3: -72.6%
   softmax dilution 0.72->0.06: log2 ratio = 3.58 bits (paper says +4.51 bits)
   column totals M0/M6/Stage-1: [15, 31, 51] (paper: 15, 31, 51)
   httpx 1/1 Wilson 95% CI: [20.7, 100.0]
   T1 calibrated 51/129 Wilson [31.5, 48.2]   (paper: [31.5%, 48.1%])
   ```
   All other Wilson CIs in Tables 1–3 and all Table 3 percentage changes match the paper exactly.
7. Ran `python3 scripts/annotate_figures.py paper/figures annotated`, then inspected the three annotated PNGs with Read. The first pass had overlaps: Fig. 1 badges covered bullet text, Fig. 2 badges covered the ")" in two value labels and badge 6 touched the x axis, and Fig. 3 badge 3 covered the "16%" label. I moved and shrank the badges, re-rendered and re-inspected. The second pass is clean.
8. Ran `python3 <skill>/scripts/pdf_tools.py render --html Anatomy.html --pdf Gemma4_LoopBreaker_Figure_Anatomy_v1.pdf` → `OK PDF ... (931,443 bytes, 4 pages)`. I opened all 4 page PNGs with Read. No badge overlaps, no card is split across a page break and no table is clipped, so no re-render was needed.

## 2. Problems in SKILL.md

1. **"Vector PDF: extract with PyMuPDF … Raster source: work at 300 DPI."** The skill gives no test for which case applies. It also does not say to pull embedded raster images losslessly with `fitz.Pixmap(doc, xref)` rather than re-rasterising a clip rect, and it does not cover a paper that ships both a PDF and a `figures/` folder. *Would help:* "Run `page.get_image_info(xrefs=True)`. If the figure is an embedded image, extract it by xref and compare it with any supplied PNGs. Use clip rendering only for vector figures."
2. **"collect every number the text quotes about it"** The skill assumes one paper text. Here PAPER.md and the PDF are different revisions: PAPER.md says 24.1% where the PDF says 24.0%, lists a `12b` model where the PDF has `26b-a4b`, and has no Stage-1/Protocol A framing. *Would help:* "If there are several versions of the text, pick one as the source of record (normally the PDF, since it holds the figures), say so in the dossier, and list the differences."
3. **The skill never asks for the forensics itself.** Step 1 says to collect numbers but never to check them against tables, recompute derived values (ratios, CIs, p-values, deltas), or check whether a figure's label belongs to the experiment it is drawn in. That checking produced every substantive finding here. *Would help:* add a step such as "Recompute every derived number on the figure in a script and flag mismatches in a red 'Forensic flags' card."
4. **"Do not read values off a plot by eye … label them 'read from plot'."** The skill does not say whether pixel digitizing is allowed, how to calibrate it, or how to label its output. I calibrated from detected tick marks and labelled the values "digitized, read from plot". *Would help:* a short digitizing recipe (find spines and ticks, mask out the legend, colour-match the markers) or a bundled helper script.
5. **"Overlay badges with matplotlib … keeping badges in clear margins."** The skill gives no method for choosing coordinates. Read shows the image downscaled (3180 → 2576 px wide, factor 1.234), so every coordinate has to be rescaled. `bbox_inches="tight"` also changes the output size (3180 → 3192 px), so the annotated image no longer shares coordinates with the source. *Would help:* say to work in source-pixel coordinates and apply the display scale factor, or use `bbox_inches=None` to keep the size; consider a helper that takes badge positions in fractions of the image.
6. **"Shade failure regimes (rose) and gain regimes (green)"** This is undefined for architecture diagrams and for categorical bar charts. I shaded nothing on Fig. 1. On Fig. 3 I used rose for a small-sample warning (the n = 1 repository), which stretches "failure regime". *Would help:* "Shade only where the axis has a meaningful threshold or region; skip shading on diagrams."
7. **"Fix and re-render until no badge overlaps a label or datum"** sits in step 5, where it applies to the 110-DPI dossier page PNGs. At that resolution a full-width figure is too small to judge overlaps. I found all the real overlaps by inspecting the full-size annotated PNGs after step 3. *Would help:* add "Read each annotated PNG at full size before embedding it" to step 3.
8. **"Write the HTML dossier"** comes with no template, no A4 print CSS (`@page`, `break-inside: avoid`), no say on whether images should be relative paths or embedded, and no mention of a summary/cover page or where outputs go. "Engineering Takeaway" has no definition of what it should contain. I improvised all of these.
9. **`python3 scripts/pdf_tools.py render --html Anatomy.html …`** The script path is relative to the skill directory, but `--html` and `--pdf` are relative to the working directory, so no single cwd makes the command work as written. I used the absolute script path from the output directory. The step also does not say that the page PNGs land in `<pdf-stem>_preview/` next to the PDF. *Would help:* write the command as `python3 <skill-dir>/scripts/pdf_tools.py …` run from the output directory.
10. **Multi-panel figures:** the skill does not say whether badge numbers restart per panel. I numbered continuously across panels (a) and (b).
11. **`<Paper>_Figure_Anatomy_v1.pdf`:** the skill does not say what `<Paper>` should be (author, title or short name). I used `Gemma4_LoopBreaker`.

## 3. Not done or not verifiable, and disagreements between the figures and the text

- **Fisher's exact p:** Fig. 1, Fig. 3(b), §3.4 and §5 print p = 4.2e-9 for 24/25 vs 4/25. scipy gives 7.18e-9 two-sided and 3.59e-9 one-sided. Neither matches, and I could not find which test produced 4.2e-9.
- **McNemar p:** 1.8e-6 (Table 1) and 4.6e-5 (Table 2) need paired per-task outcomes, which the paper does not include. Not verified.
- **Fig. 2(b):** the arrow label "−70.8% active KV" sits on one reset, but the digitized dips are −57% and −55% and the 12-turn area ratio is −59.6% (digitized). −70.8% is Table 3's post-reset KV ratio across episodes. The panel's legend peaks and its "937 turns" are Trap-25 data (Table 3), but it sits in the `swegemma` figure. It draws a single trajectory for 12 turns, while Table 3 averages 6.96 to 11.04 turns.
- **Fig. 2(b) and compaction:** the baseline curve passes the 14.3k cliff at turn 4 (digitized) and keeps rising to 24.8k with no compaction. That conflicts with §1, which says compaction fires above 14,336 tokens, unless the Trap-25 sandbox does not use ADK compaction. The paper does not say.
- **"Recovers half that 29-task gap" (§3.3):** M2→M6 adds 9 of 29 tasks, which is 31% (computed).
- **Rounding:** the 22.4-point tax is 22.5 from the counts; the Table 1 Wilson upper bound is 48.1 in the paper and 48.2 computed. Both are minor.
- **§3.1:** "+4.51 bits" for a dilution change from 0.72 to 0.06. log2(0.72/0.06) = 3.58, and the paper does not define the measure, so I could not reproduce it. This is not a figure claim.
- **Fig. 1 attributions:** −93% is credited to 120-line reads, but it is the full M0→M6 stack; the M2→M3 step gave −72.6%. −70.8% is credited to the LDW burst, but `ccr_only` already gives −46.7%. Co-change twins and the Call-12 deadline appear in boxes that do not match their Table 2 modules. Of the four models listed, only the 31B has any reported result.
- **Fig. 3(a):** the per-repository Stage-1 rates (37.3 / 41.7 / 38.5 / 100%) appear only in the figure, not in the text. They are consistent with 51/129 in total (computed).
- **Not done:** the paper's datasets and pytest suite are not in the repo, so none of the underlying data was checked. The digitized values are approximate. No PAPER.md-only content was analysed.
