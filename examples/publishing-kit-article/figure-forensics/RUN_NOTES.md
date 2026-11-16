# figure-forensics run: publishing-kit article

Skill: `plugin/skills/figure-forensics/SKILL.md`. Paper of record: `examples/publishing-kit-article/paper/devto-publishing-kit.md`. Figures: the six cover files, their two Medium copies, and `medium/img/devto-publishing-kit-table-1.png`. Evidence: `paper/evidence/*.txt` and `paper/CLAIMS.md`.
Environment: python3 3.14.7 (pyenv), Pillow 12.3.0, matplotlib 3.11.1, PyMuPDF 2.1, scipy (imported by `measure_figures.py`). No packages installed.

Deliverables:

- `PublishingKit_Figure_Anatomy_v1.pdf`: a 6-page A4 dossier with an inventory and flags page, then one page per figure
- `Anatomy.html`: the dossier source
- `annotated/fig1_cover_current_annotated.png` … `fig5_table_annotated.png`: badges and shading at native pixel scale
- `scripts/measure_figures.py`: geometry, hashes, pixel diffs, endpoint count, ink heights at 320 px, dev.to crop arithmetic
- `scripts/annotate_figures.py`: badge and shading overlays
- `work/measure_figures.out`, `work/measurements.json`: measurement output
- `PublishingKit_Figure_Anatomy_v1_preview/`: the page PNGs and montage that the render step writes

## 1. Commands and key output

| # | Command | Key output |
|---|---|---|
| 1 | `python3 -c "from PIL import Image ..."` over all image files | 1376x578 (ae4d639e, 77acc7c4, advocu webp), 1200x675 (both builder), 1200x627 (linkedin), 1281x166 (table) |
| 2 | Read on each of the 7 distinct images | `ae4d639e`, `cabd79f3`, linkedin and advocu: text-free flow art. `77acc7c4` and `80aa6ca5`: "One source. Four destinations." cards. Table: two rows under "measured" |
| 3 | `grep` over `paper/` for image names, "0 of 4", "Substack", "four", plus cited line numbers | cover_image = ae4d639e (line 6); check-links output names 77acc7c4 (lines 116-117); "0 of 4" only in the two article versions and CLAIMS.md; the article never mentions Substack; "two numbers on the cover" at line 157; "1376x768" at line 54 |
| 4 | `python3 scripts/measure_figures.py ../paper work/measurements.json` | all 6 hash-named files match sha256[:8]; medium/img copies byte-identical; advocu vs ae4d639e mean abs diff 0.441; ae4d639e vs 77acc7c4 18.775; builder pair 14.671; 5 endpoint markers on every flow cover (blue, orange x3, grey); 77acc7c4 ink at 320 px: kicker 2.8, title 8.1, subtitle 5.1, card title 7.0, "REST API" 3.3, footer 3.7; dev.to crop: 1376x768 loses 95.0 rows per edge, 1376x578 0.0, 1200x675 85.5, 1200x627 61.5; 47/62 = 0.7581 |
| 5 | `python3 scripts/annotate_figures.py ../paper work/measurements.json annotated` | 5 annotated PNGs. Read on each at full size. The composites (Figs. 3-4) were unreadable at page width, so text and badges were scaled 2.0x and 1.5x and the figures re-rendered |
| 6 | `python3 <skill>/scripts/pdf_tools.py render --html Anatomy.html --pdf PublishingKit_Figure_Anatomy_v1.pdf` (from this folder) | `OK PDF ... (1,519,177 bytes, 6 pages)`. Read on all 6 page PNGs: no badge overlaps a label or datum, no card is split across a page break, no clipped table |

## 2. Headline findings

1. **"The two numbers on the cover are real"** (article line 157). Neither cover carries them. The current dev.to cover `cover.ae4d639e.jpg` has no text at all, and the previous `cover.77acc7c4.jpg` has a title, card labels and a footer with no figures. The Builder, LinkedIn and Advocu variants have no figures either. The two numbers appear only in the table image.
2. **The current cover draws five destinations.** 5 endpoint markers (1 blue, 3 orange, 1 grey; computed) on every flow-cover variant. The article says "four places" (line 15) and "all four of its artifacts" (line 12), and the cover it replaced reads "One source. Four destinations." No file maps the markers to destinations. Reading them with the old cover's colour key would make the third orange one Substack, but that is an inference, and the article never mentions Substack.
3. **The 1376x768 example in the article describes no cover in the folder.** "a 1376x768 cover loses 95px off the top and bottom" (line 54): the arithmetic reproduces 95.0, but both dev.to covers are 1376x578 (ratio 2.3806 against 2.3810) and lose 0.0 rows. `CLAIMS.md` line 30 traces "1376x768" to `toolchain-run.txt`, which gives byte counts for those covers and no dimensions.
4. **Table row 2 is labelled "measured" but recorded as LOG.** "0 of 4 survived; from real URLs, 4 of 4" is a LOG entry in `CLAIMS.md` (2026-08-30, "NOT re-measured here") and appears in no evidence file. Row 1 (47 of 62) traces to `devto-hardwrap.txt` (58 `<p>` + 4 `<li>`, 47 with `<br>`, 0 lines ending in two spaces).
5. **The Medium cover has drifted.** The hosted Medium HTML opens with `cover.ae4d639e.jpg`, while `cover-refresh.txt` says the live Medium story "still shows cover.77acc7c4.jpg".
6. **What checks out.** All 6 hash-named files match their sha256 prefix. The Advocu WebP is the current cover: 0.441 mean abs diff, as `advocu-devto-publishing-kit.md` states. The local builder-pair diff of 14.671 and dev.to-pair diff of 18.775 sit within 0.07 of the live-copy diffs in `cover-refresh.txt` (14.66, 18.71).
7. **Legibility at the 320 px feed card** that the article names (line 36). The replaced text cover has three lines with 2.8 to 3.7 px of ink at that width (computed). The current cover avoids the problem by having no text. No file states a legibility threshold.
8. **Untraced:** the LinkedIn cover's 1200x627 geometry. No file in `paper/` references the image or states LinkedIn's image size.

## 3. Where SKILL.md fell short for this input

1. **The skill assumes a research paper with plots and architecture diagrams.** This input is a blog article whose figures are covers (illustrations with no data) and a table rendered to an image. The ARCHITECTURE → MECHANISM → EMPIRICAL GAIN arc fits only loosely. "Shade failure regimes (rose) and gain regimes (green)" has no axis to apply to. I used rose for computed crop bands and for an untraced row, which stretches the meaning.
2. **"Raster source: work at 300 DPI"** does not apply to screen images that have pixel dimensions and no physical size. Upsampling adds nothing. I worked at native pixels (figsize = px/100 at 100 DPI, `bbox_inches=None` so coordinates are preserved), which the skill does not mention.
3. **No guidance when one figure exists as several files.** Here there are 6 cover files and 2 copies covering 2 artworks across destinations. The skill does not say how to pick the figure of record, or whether to check that variants match (hashes, byte identity, pixel difference). That check produced finding 6 and the Medium-drift finding.
4. **"collect every number the text quotes about it"** assumes the figure carries numbers. The covers carry none, and the substantive findings come from what the prose says about the figure ("two numbers on the cover", "four destinations", "1376x768"). The skill has no step for "check every claim the text makes about the figure against the image".
5. **No forensic or verification step at all**, so there is no instruction to recompute derived values, trace numbers to evidence files, or report flags. All the headline findings came from work the skill does not ask for. I added a "Forensic flags" card and Flag cards on my own initiative.
6. **No notion of display context.** For covers, the questions that matter are the size the figure is seen at (a 320 px card, a 1000x420 crop) and whether text survives it. The skill has no step for rendering or measuring a figure at its destination size.
7. **No method for counting or locating features** such as markers. The rule against eyeballing values implies measuring in code, but the skill gives no recipe. I used connected components plus colour classification in `measure_figures.py`.
8. **Badge sizing for composites and small figures.** A two-panel 2440 px composite shown at page width made badges and labels unreadable. The skill says nothing about scaling badge size to the displayed width. I found this by reading the full-size PNG and fixed it with a text-scale factor.
9. **Dark-background images.** The badge style assumed by the skill (dark fill) disappears on a dark cover. A white outline is needed, and the skill gives no guidance on contrast.
10. **`python3 scripts/pdf_tools.py render --html Anatomy.html ...`** puts the script path relative to the skill directory and the HTML and PDF paths relative to the working directory. I ran the script by its absolute path from the output folder. The skill also does not say that the page PNGs land in `<pdf-stem>_preview/`.
11. **No dossier template, print CSS or definition of "Engineering Takeaway".** For a blog article, the takeaway became a design or provenance lesson rather than an engineering result. Page layout was improvised.
12. **`<Paper>_Figure_Anatomy_v1.pdf`** does not define `<Paper>`. I used `PublishingKit`.
