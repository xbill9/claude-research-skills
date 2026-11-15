---
name: interactive-paper-studio
description: >-
  Build a single-file, zero-backend interactive HTML5 Canvas/SVG explorer (index.html) for a research
  paper, with live sliders over its equations, thresholds and operating regimes and preset scenarios that
  reproduce the published numbers. Use when asked for an interactive paper demo, a web simulator of a
  paper's model, or a GitHub Pages companion site.
---

# Interactive Paper Studio

Turn a technical paper into one self-contained `index.html` that works offline and on GitHub Pages.
Readers drag sliders over the paper's real parameters (sampling temperature τ, context length, SNR,
threshold cut-offs, …) and watch the curves, phase boundaries and KPIs respond in real time.

## Ground rules

- The JavaScript formulas are the paper's formulas. Verify them in Python first and check the JS output
  against the Python output at the preset points — a script compares them, to at least 4 decimal places.
- Every preset and every number in the grounding table cites the paper's table/equation.
- Use the active `python3`; install missing packages into it.

## Layout

1. **Header** — paper title, authors, the one-sentence core finding, quick-jump tabs
   (*Live Simulator*, *Architecture*, *Ablation Matrix*, *Reproducibility*).
2. **Control deck (≈32% width)** — 3–5 range sliders bound to the governing parameters, initialised at the
   paper's nominal baseline; preset buttons for the paper's named operating points
   (e.g. *Unpruned greedy baseline* vs *Calibrated optimum*).
3. **Telemetry viewport (≈68% width)** — `<canvas>` or responsive `<svg>` curves recomputed from the closed
   forms in vanilla ES6, `requestAnimationFrame`-driven; KPI cards with the delta vs baseline (green gain,
   rose cliff).
4. **Grounding table** — simulated readout at each preset beside the exact published value.

Stack sliders above the viewport below ~760px; no horizontal scroll on a phone. No CDN dependencies, so
it works offline (inline any font or math rendering you need).

## Workflow

1. Extract the core equations, threshold detectors and headline benchmark rows (with sources).
2. Implement them in `verify_model.py`; save preset outputs to `preset_values.json`.
3. Write `index.html`; embed the same presets; add a tiny in-page self-check that recomputes the presets and
   logs any mismatch to the console.
4. Verify in a real browser: run `node` on the extracted JS, or screenshot with this skill's bundled script
   (in this skill's base directory) at desktop and phone width and open both PNGs with **Read**:

   ```bash
   python3 scripts/pdf_tools.py shot --html index.html --png desk.png --width 1440 --height 900
   python3 scripts/pdf_tools.py shot --html index.html --png phone.png --width 390 --height 844
   ```

5. Deliver the absolute path to `index.html` and the comparison of JS vs Python preset values.
