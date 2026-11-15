# RUN_NOTES: interactive-paper-studio on the Gemma 4 loop-breaker paper

Skill: `plugin/skills/interactive-paper-studio/SKILL.md`. Paper: `../paper/` (PDF used as the authoritative text; PAPER.md as a cross-check).
Environment: python3 3.14.7 (pyenv), scipy 1.18.1, pymupdf, pillow; node v24.21.0; Google Chrome 157.0.8103.78. No packages installed.

## Deliverables

| File | What |
| --- | --- |
| `index.html` | The single-file, offline explorer (196 KB, Figure 1 inlined as base64 JPEG, no external URLs: `grep -c "https\?://" index.html` = 0) |
| `verify_model.py` | Python reference model + grounding checks; writes `preset_values.json` |
| `preset_values.json` | Preset readouts, grounding rows, tables, constants |
| `index.src.html`, `build_page.py` | Page source; build step that embeds the JSON and the figure |
| `check_js.mjs` | Runs the page's own `<script id="model">` in node and compares every preset value with Python |
| `phone_check.mjs` | True 390 px mobile emulation over the Chrome DevTools Protocol (see problem 5) |
| `desk.png`, `phone.png` | Bundled `shot` output at 1440x900 and 390x844 |
| `tall_{sim,arch,abl,repro}.png` | 1440-wide tall screenshots of each tab (via `#tab` hash, plain headless Chrome) |
| `phone390_{sim,abl}.png` | Full-height screenshots at an emulated 390 px viewport |
| `verify_output.txt`, `check_js_output.txt`, `phone_check_output.txt` | Captured output |

## What the simulator models

The paper is empirical: apart from Proposition 1 (two-block softmax) and the noise expression in §3.2, its results are table rows with no parameter-to-outcome function. The page therefore has three kinds of number, each labelled in the page:

1. **Recomputed from the paper's raw counts** (Tables 1-3): rates, 95% Wilson intervals, percentage deltas, Fisher exact p vs baseline. Presets select table rows.
2. **Derived directly from a formula the paper states**: log-odds noise sd = sqrt(2)*sigma_q/tau from exp((z+eps)/tau), eps ~ N(0, sigma_q^2) (§3.2), in units of sigma_q because the paper gives no sigma_q; action-window entropy for W = 4 (§3.4), which shows H_W < 0.55 fires only when all four actions are identical (values 0, 0.811, 1.0, 1.5, 2.0 bits).
3. **Illustrative toy** (flagged "illustrative"/"toy" in the page): attention share on B under Proposition 1 with uniform per-token logits, w_B = |B|e^gap / (|A| + |B|e^gap), and a worst-case loop where every turn appends a fixed token count to B and G-CCR prunes B when C_err >= 2 (adding the 150-token ledger, §3.4). The paper gives no closed form for L_{h,B_t}(|B_t|), no |A|, and no per-turn growth, so the page says so and does not back-fit them to 0.72 -> 0.06.

Sliders: tau, |A|, tokens per failed turn, logit gap, turns (5). Toggle: G-CCR. Presets: Unpruned greedy baseline / Low-temp hidden thinking / CCR pruning only / Calibrated optimum (G-CCR), each citing its Table 1/2/3 rows.

## Commands and key output

```
python3 verify_model.py > verify_output.txt
  fisher two-sided ours=7.178606e-09 scipy=7.178606e-09; one-sided ours=3.589303e-09 scipy=3.589303e-09
  grounding: 67 match, 10 mismatch of 77
python3 build_page.py            -> wrote index.html 196244 bytes
node check_js.mjs > check_js_output.txt   (exit 0)
  embedded JSON identical to preset_values.json: true
  80 values, 0 mismatches, worst error 1.80e-14, max abs diff 1.80e-14
python3 <skill>/scripts/pdf_tools.py shot --html index.html --png desk.png  --width 1440 --height 900
python3 <skill>/scripts/pdf_tools.py shot --html index.html --png phone.png --width 390  --height 844
google-chrome --headless=new --window-size=1440,2400 --virtual-time-budget=2000 --screenshot=tall_<tab>.png "file://.../index.html#<tab>"
google-chrome --headless=new --virtual-time-budget=2000 --dump-dom "file://.../index.html#repro"
  SELFCHECK IN CHROME: 80 preset values compared, 0 mismatches, worst error 1.80e-14
node phone_check.mjs
  sim/arch/abl/repro: innerWidth=390 scrollWidth=390 -> no horizontal scroll
  console: log: [self-check] 80 preset values compared, 0 mismatches, worst error 1.80e-14
```

JS vs Python: 80 preset values (4 presets x 20 keys), maximum absolute difference 1.8e-14; Fisher p compared by relative error (see problem 3).

### Published numbers that the paper's own counts do not reproduce (from verify_model.py)

- Fisher's exact p for 24/25 vs 4/25: paper 4.2e-9 (abstract, §3.4, §5); two-sided 7.18e-9, one-sided 3.59e-9 (matches scipy). Boschloo 1.54e-9, Barnard 1.47e-9, chi-square 6.19e-8 / 1.21e-8 (checked once from the command line); none gives 4.2e-9.
- Wilson upper bound for 51/129: 48.157% (rounds to 48.2); Table 1 prints 48.1.
- §1: "95% Wilson CI width ±9.8 pts" for p = 0.20, n = 58: Wilson half-width 10.14 (normal approximation 10.29; 11/58 gives 9.96).
- §3.3 "recovers half that 29-task gap": M2->M6 gains 9 tasks (0.31 of 29); M0->M6 gains 16 (0.55).
- §3.1 dilution 0.72 -> 0.06 "+4.51 bits": log2(0.72/0.06) = 3.585, -log2(0.06) = 4.059, log2 odds ratio = 5.332; no reading tried gives 4.51.
- PAPER.md abstract says M6 is 24.1%; the PDF and Table 2 say 24.0% (31/129 = 24.03%). PAPER.md lists the family as 31b/12b/e4b/e2b; the PDF says 31B/26B-A4B/E4B/E2B.
- Within rounding: all Table 1-3 rates, all other Wilson intervals, all Table 3 % deltas, -93% compaction (-93.1), 2.1x (2.067), +21.7, 22.4-point tax (22.48; the paper subtracts rounded rates), -87.5%, -66.3%, SE 5.25%, per-repo counts (7+6+2+0 = 15, 15+12+3+1 = 31).

## Problems with SKILL.md

1. **Assumes a closed-form model.** "curves recomputed from the closed forms" and "3-5 range sliders bound to the governing parameters". This paper is mostly empirical tables; only Proposition 1 and the §3.2 noise term are formulas, and neither has the free parameters filled in. The skill says nothing about what to do when the paper has no closed form, so I split the page into recomputed-from-counts, derived-from-stated-formula, and labelled toy. Helpful: a short section "If the paper is empirical" with that split and the rule "label every illustrative input as such".
2. **Presets vs sliders are conflated.** "preset buttons for the paper's named operating points" + "preset scenarios that reproduce the published numbers". When the published numbers are table rows, a preset cannot reproduce them by setting sliders; it has to select rows. I made presets do both (set tau/reset and choose rows). Helpful: say whether a preset is a slider state, a data-row selector, or both.
3. **"to at least 4 decimal places" is the wrong tolerance for small values.** Fisher p-values are ~1e-9, so any two numbers agree to 4 decimals. I compared with abs < 5e-5 or rel < 1e-9. Helpful: "absolute 1e-4 or relative 1e-6, whichever applies". Also "a script compares them" — no script is bundled and nothing says how to get the JS out of the page; I put the model in `<script id="model">` with a `module.exports` guard and wrote `check_js.mjs`. A bundled comparator with that convention would remove the guesswork.
4. **Step 4 offers node *or* screenshots as alternatives.** "run `node` on the extracted JS, or screenshot with this skill's bundled script". They check different things (numbers vs layout); I did both. Helpful: "and".
5. **The bundled `shot` does not render a 390 px phone viewport.** With `--width 390` headless Chrome lays the page out at innerWidth = 500 (measured with an on-page overlay in a `shot` capture: `iw=500 sw=500`) and crops to 390. So `phone.png` neither tests a 390 px layout nor detects horizontal scroll, which the skill requires ("no horizontal scroll on a phone"). I wrote `phone_check.mjs` (CDP `Emulation.setDeviceMetricsOverride` with mobile: true), which reports innerWidth = 390 and scrollWidth = 390 on all four tabs. Helpful: fix `shot` to use device-metrics emulation, and add a scrollWidth check.
6. **`shot` captures only the first viewport of the first tab.** It takes a file path (`as_uri()`), so no `#hash`/query to reach other tabs, no full-page option, and no console capture. The skill mandates four tabs and a console self-check, neither verifiable with the bundled tool. I added hash routing to the page and used Chrome directly (`--screenshot` with tall windows, `--dump-dom` to read the self-check text) plus the CDP script for console logs. Helpful: `--full-page`, `--url-suffix`, and `--console` options.
7. **Tab contents unspecified.** The header lists *Architecture*, *Ablation Matrix*, *Reproducibility*, but the Layout section describes only the simulator and grounding table. I chose: Figure 1 + formulas + detector table; Table 2 charts + Tables 1-3; grounding table + self-check.
8. **No rule for unreproducible or conflicting published numbers.** "Every preset and every number in the grounding table cites the paper" does not say what to do when recomputation disagrees with the paper, or which source wins when PAPER.md and the PDF disagree (24.1% vs 24.0%). I used the PDF and show mismatches with a match column and note. Helpful: "show the mismatch; never adjust the model to hit it"; "PDF is authoritative".
9. **No step for checking the paper's own arithmetic**, which is where all the useful findings came from (problem list above). Step 1 only says extract.
10. **"KPI cards with the delta vs baseline"** — the baseline is undefined when the presets span three tables; I used the first preset (Table 1 row 1, M0, baseline_static).
11. **Single-file + figures.** "No CDN dependencies" but no mention of how to include the paper's figures or the presets; I added a build step (`build_page.py`) that base64-inlines a downscaled Figure 1 and the JSON. Helpful: say a build step is expected, and give the embed convention.
12. **"requestAnimationFrame-driven"** — unclear what should animate when curves are recomputed instantly; I eased curve values toward the new target over frames.
13. **Not covered:** dark mode (added via prefers-color-scheme), the GitHub Pages deploy promised in the description (not done; no instructions), and the "inline any font or math rendering" note gives no way to do offline math; I used HTML sub/sup.

## Not done or not verified

- No GitHub Pages deployment (skill gives no step; told not to commit).
- McNemar p-values (1.8e-6, 4.6e-5) and Wilcoxon p (< 1e-6, 8.91e-07) need paired per-task / per-episode data that the paper does not include; not reproduced and not shown as checked.
- The 0.72 -> 0.06 dilution pair and 4.51 bits are shown as unreproduced; the toy model is not fitted to them.
- Interaction (slider drags, detector controls, row clicks) checked only by screenshots of preset states (baseline, and optimum via a scratch copy with `applyPreset("optimum")`), not by scripted input events.
- Dark-mode rendering not screenshotted.
