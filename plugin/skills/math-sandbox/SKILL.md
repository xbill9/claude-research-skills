---
name: math-sandbox
description: >-
  Decompose a research paper's equations, theorems, bounds and control laws into colour-coded operator
  blocks, verify each one numerically with deterministic NumPy/SciPy evaluation and Monte Carlo checks,
  and compile an A4 Mathematical Verification Guide PDF plus eq_verified_numbers.json. Use when asked to
  explain, check, verify or sanity-test a paper's math, derivations or closed-form claims.
---

# Mathematical Operator Sandbox & Verifier

Explain and computationally check every equation, proposition, lemma and control law in a paper:
colour-coded operator pills, plain-English intuition, step-by-step derivations, deterministic numerical
evaluation and sensitivity plots, in one A4 PDF.

## Ground rules

- **The verdict on each claim comes from code.** Closed-form values, simulated values, their gap and
  pass/fail all come from `verify_math.py` and `eq_verified_numbers.json`; the PDF quotes that file.
- Name the script `verify_math.py` — never `numbers.py`, `math.py` or `statistics.py`, which shadow the
  stdlib and break `import numpy` (the plugin's hook blocks creating them).
- Use the active `python3`; install missing packages into it (`numpy`, `scipy`, `matplotlib`).

## Workflow

1. **Operator dependency graph.** Trace how definitions feed bounds, detectors/estimators and empirical
   metrics. Give each operator class a colour (definitions, bounds, estimators, metrics) used consistently
   for pills in the PDF.
2. **Deterministic sandbox.** In `verify_math.py`, with `seed=42` and the paper's nominal parameters:
   - evaluate every formula;
   - check each closed-form claim by simulation (Monte Carlo with a stated sample count and its standard error);
   - write `eq_verified_numbers.json`: per equation — `id`, `paper_value` (with source), `computed`,
     `simulated`, `abs_gap`, `tolerance`, `verdict` (`VERIFIED` / `MISMATCH` / `NOT CHECKABLE`, with reason).
3. **Sensitivity plots** (`matplotlib`, 300 DPI): sweep each key formula across its critical parameter,
   marking the failure regime and the calibrated operating point.
4. **Render and inspect.** Write `MathGuide.html` (KaTeX inlined or pre-rendered for offline use), then run
   this skill's bundled script (in this skill's base directory):

   ```bash
   python3 scripts/pdf_tools.py render --html MathGuide.html --pdf <Paper>_Equation_Guide_v1.pdf
   ```

   Open every page PNG with **Read**; fix colliding pills or split derivations and re-render. Deliver the
   PDF, `eq_verified_numbers.json` and `verify_math.py`.
