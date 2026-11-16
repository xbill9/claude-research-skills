# RUN_NOTES: interactive-paper-studio on the publishing-kit article

Skill: `plugin/skills/interactive-paper-studio/SKILL.md`. Paper of record: `../paper/devto-publishing-kit.md`; evidence `../paper/evidence/*.txt` and `../paper/CLAIMS.md`.
Environment: python3 3.14.7 (pyenv), Pillow 12.3.0, node v24.21.0, Google Chrome 157.0.8103.78. No packages installed.
One input from outside the paper folder, labelled as such everywhere it appears: the 10 px legibility threshold, `LEGIBLE_PX = 10` in `~/publishing-kit/skills/publishing/scripts/make-cover.py` (repo at `dec86c0`). The article says the kit "reports which type sizes survive a 320px feed card" but never says what survival means.

## Deliverables

| File | What |
| --- | --- |
| `index.html` | Single-file offline explorer, 47,092 bytes, no `src=`/`href=` to any external resource (the only URLs in it are words of the article inside the embedded JSON) |
| `index.src.html`, `build_page.py` | Page source and the step that embeds `preset_values.json` |
| `verify_model.py` | Python reference model (crop, feed card, hard wrap); writes `preset_values.json` |
| `preset_values.json` | Presets, wrap sweep, the article's 39 paragraph-level blocks, cover-file geometry, grounding rows |
| `check_js.mjs` | Runs the page's own `<script id="model">` in node and compares every preset value with Python |
| `phone_check.mjs` | 390 px mobile emulation over the Chrome DevTools Protocol: scrollWidth per tab, console capture, full-height shots |
| `desk.png`, `phone.png` | Bundled `shot` at 1440x900 and 390x844 |
| `tall_{sim,arch,abl,repro}.png` | 1440x2000 headless-Chrome shots of each tab via `#hash` |
| `phone390_{sim,repro}.png` | Full-height shots at an emulated 390 px viewport |
| `verify_output.txt`, `check_js_output.txt`, `phone_check_output.txt` | Captured output |

## What is modelled

1. **dev.to cover crop.** `fit=cover` into the measured 1000x420 box, centred: scale s = max(1000/W, 420/H), kept = 1000/s x 420/s, lost per side = (H - 420/s)/2 or (W - 1000/s)/2.
2. **Feed card.** Apparent size = type x card / W, the kit's own rule (it scales by cover width and ignores the crop). Legible at 10 px or more.
3. **Hard wrap.** Each paragraph-level block (paragraph, list item, quoted paragraph) with n source lines shows n-1 `<br>` on dev.to. Applied to this article's own source as stored, and re-wrapped (greedy word wrap) at any column 40-200.

Sliders: cover W, cover H, type size, card width, wrap column. Presets: dev.to cover as first shipped (1376x768), `make-cover --mode devto` (1376x578), Builder Center hero (1200x675) on dev.to, LinkedIn cover file (1200x627) on dev.to. The last two are labelled as what-ifs: nobody measured dev.to's proxy on those files, and nothing in the evidence describes how Builder Center or LinkedIn crop their own covers.

**Not modelled:** Medium's 0 of 4 / 4 of 4 data-URI result (two counts, no parameter); the 47 of 62 and 88 `<br>` figures (measured on article 4531800, whose source is not in the evidence); the Builder payload's 531 -> 411 lines (the evidence describes a 534-line, 23,644-char file; `paper/builder-publishing-kit.md` has 180 lines and 10,110 chars); Builder Center, Medium and LinkedIn display crops (no measurement); dev.to's `gravity=auto` behaviour (the evidence and kit treat it as a centre crop; untested).

## Commands and key output

| Command | Key output |
| --- | --- |
| `python3 verify_model.py > verify_output.txt` | 39 blocks (26 p, 10 li, 3 quote); as stored 29 of 39 broken, 67 `<br>`; longest prose line 126, 20 of 106 prose lines over 95, 4 over 100 |
| (same) shipped preset 1376x768 | kept 1376.00 x 577.92, lost 95.0400 per side, 24.75% of area; 40 pt -> 9.3023 px at 320, min legible 43.00 pt |
| (same) devto preset 1376x578 | lost 0.0400 px per side, 0.01% of area |
| (same) builder 1200x675 / linkedin 1200x627 | lost 85.5000 / 61.5000 px per side; min legible 37.50 pt |
| (same) sweep | col 40: 39/39, 208 `<br>`; col 95: 31/39, 70; col 200: 22/39, 27 |
| `python3 build_page.py` | wrote index.html 47092 bytes |
| `node check_js.mjs > check_js_output.txt` | embedded JSON identical to preset_values.json: true; 130 values (64 preset + 66 sweep), 0 mismatches, worst abs error 0.00e+0 |
| `python3 <skill>/scripts/pdf_tools.py shot --html index.html --png desk.png --width 1440 --height 900` | OK |
| `python3 <skill>/scripts/pdf_tools.py shot --html index.html --png phone.png --width 390 --height 844` | OK |
| `google-chrome --headless=new --window-size=1440,2000 --screenshot=tall_<tab>.png file://.../index.html#<tab>` | four tabs rendered |
| `node phone_check.mjs` | sim/arch/abl/repro: innerWidth=390 scrollWidth=390, no horizontal scroll; console: `[self-check] 130 preset values compared, 0 mismatches, worst abs error 0.00e+0` |
| `ruff check` / `ruff format --check` on the two .py files | All checks passed / already formatted |

## Headline findings

- **The crop arithmetic holds.** 1000/420 = 2.380952 (2.381:1). A 1376x768 cover keeps 577.92 rows and loses 95.04 px top and bottom; the evidence rounds kept rows to 578 first and gets 95; both round to 95. A 1376x578 cover loses 0.04 px per side, so "nothing cropped" is right to under a pixel. Every cover file in the paper folder at 1376x578 (three of them) behaves the same.
- **The other destinations' covers would lose more on dev.to than the article's example does by area.** The 1200x675 Builder hero would lose 85.5 px top and bottom (25.33% of its area, against 24.75% for the 1376x768 case); the 1200x627 LinkedIn file 61.5 px (19.62%). These are what-ifs from the measured box, not measurements.
- **The legibility line falls at 43 pt on a 1376-wide cover.** At a 320 px card the scale is 0.2326, so the kit's 10 px threshold needs 43.0 pt. The kit's own comment says type "below about 40pt disappears"; 40 pt renders at 9.30 px, under its threshold. The article states neither number.
- **The article's own source is wider than 95 columns.** It says the repo copy stays "readable at 95 columns"; 20 of its 106 prose lines exceed 95 characters, 4 exceed 100, the longest is 126 (a link-list item).
- **Posted as is, this article would carry 67 stray `<br>` in 29 of its 39 blocks.** Re-wrapped at exactly 95 it would be 70 in 31. The TL;DR block is 5 source lines, matching "posted as five separate lines". The headline 47 of 62 (75.8%) comes from a different article and cannot be reproduced from the evidence.

## Where the skill's instructions fell short for this input

1. **Assumes a paper with equations and operating regimes.** "live sliders over its equations, thresholds and operating regimes", "curves recomputed from the closed forms". A dev.to article has no equations; the only closed forms are one line of crop arithmetic in an evidence file and a scale rule in the kit's source. The skill gives no guidance on deriving a model from prose plus evidence, or on how little is enough to justify a simulator.
2. **No rule for a model input the paper does not state.** The feed-card model is meaningless without a legibility threshold, which exists only in the kit's source. The skill says "every number cites the paper's table/equation" and has no category for an outside value; I labelled it "NOT IN PAPER" with its source.
3. **"Presets reproduce the published numbers" does not fit counts measured on inputs not in the evidence.** The 47 of 62 figure is the article's headline number and cannot be a preset. The skill has no verdict for "not reproducible from the evidence"; I added NOT REPRODUCIBLE and NOT MODELLED rows.
4. **No guidance for what-if presets.** The Builder and LinkedIn presets apply a measured dev.to rule to geometries it was never measured on. The skill says presets are "the paper's named operating points"; it does not say whether extrapolated scenarios are allowed or how to label them.
5. **Audit lookup conflicts with independent runs.** The skill says to look up `eq_verified_numbers.json` / `stat_audit.json` first. During this run `math-sandbox/` and `ablation-stat-auditor/` folders appeared beside this one, but the task forbade reading other skills' output, so no audit was consulted. The skill does not say where an audit lives or what to do when one cannot be used.
6. **"to at least 4 decimal places" is underspecified** for integer outputs (block counts) and gives no relative tolerance. Here every value agreed exactly (worst error 0), so it did not bite.
7. **No comparator script or extraction convention is bundled.** "a script compares them" — I put the model in `<script id="model">` with a `module.exports` guard and wrote `check_js.mjs`.
8. **Step 4 offers node *or* screenshots;** they test different things (numbers vs layout). Both were run.
9. **The bundled `shot` cannot verify the phone layout or other tabs.** It takes a file path (no `#tab`), captures one viewport, and does not report scrollWidth or console output, while the skill requires four tabs, no horizontal scroll, and a console self-check. I used headless Chrome with `#hash` routing for tabs and a CDP script (`phone_check.mjs`) for 390 px emulation, scrollWidth and console.
10. **Tab contents are unspecified.** "Architecture", "Ablation Matrix" and "Reproducibility" are named but not described; "Ablation Matrix" has no meaning for an article with no ablations. I used it for a cover-file x crop table and a wrap-column sweep.
11. **"KPI cards with the delta vs baseline" leaves the baseline undefined.** I used the first-shipped 1376x768 cover; deltas are against it.
12. **No word on dark mode, which input text to model, or source-version mismatches** (the Builder file in `paper/` is not the one the evidence measured). I added prefers-color-scheme tokens and reported the mismatch in the grounding table.
13. **"requestAnimationFrame-driven" has nothing to animate** when values recompute instantly; the crop bands ease toward their target.
