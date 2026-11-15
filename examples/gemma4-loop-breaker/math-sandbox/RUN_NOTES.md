# RUN_NOTES: math-sandbox on gemma4-loop-breaker

Skill: `plugin/skills/math-sandbox/SKILL.md`. Paper: `examples/gemma4-loop-breaker/paper/` (5-page PDF used as primary source; PAPER.md checked where it differs).
Environment: python3 3.14.7 (pyenv), numpy 2.5.3, scipy 1.18.1, matplotlib 3.11.1, pymupdf, Chrome at /usr/bin/google-chrome. No packages installed.

## 1. Commands run and key output

| Command | Key output |
|---|---|
| `python3 -I -c "import fitz; ..."` (PDF text dump to scratchpad) | 5 pages; the PDF has Wilson CIs, McNemar p-values and a 58-task noise paragraph that PAPER.md lacks |
| `python3 -I plugin/mcp/research_audit_mcp.py` with `tools/list` | 6 tools: verify_wilson_ci, verify_fisher_exact, verify_mcnemar_exact, leaderboard_noise_floor, verify_doi_metadata, search_crossref_by_title |
| `python3 verify_math.py` (final run, ~3.5 s) | `{"VERIFIED": 37, "NOT CHECKABLE": 7, "MISMATCH": 5}` |
| MCP `verify_fisher_exact` 24/25 vs 4/25 | `p_value 7.178606491749202e-09` (same as scipy; paper says 4.2e-9) |
| MCP `verify_wilson_ci` 51/129 | `[31.52, 48.16]`, formatted `48.2%` (paper Table 1 prints 48.1) |
| MCP `leaderboard_noise_floor` num_tasks=58, baseline_rate=0.2 | SE 5.25%, 95% half-width 10.29 (paper says Wilson ±9.8) |
| scipy search over McNemar variants (inline `python3 -c`) | 1.8e-6 reproduced only by continuity-corrected chi-square at b=30, c=2 (p=1.815e-6); 4.6e-5 reproduced by no variant for b−c=16 |
| `python3 build_guide.py` | writes `MathGuide.html`, equation SVGs in `figures/eq/` |
| `python3 plugin/skills/math-sandbox/scripts/pdf_tools.py render --html MathGuide.html --pdf Gemma4_LoopBreaker_Equation_Guide_v1.pdf` (5 renders in total) | final: `11 pages`, 778,891 bytes; page PNGs and montage in `Gemma4_LoopBreaker_Equation_Guide_v1_preview/` |

I opened every page PNG and the montage with Read after each render. Fixes made between renders: a legend covering a plot annotation, a verdict pill clipped at the cell edge, a table header left alone at the bottom of a page, headings split from their figures, and `np.int64(...)` labels / `-0.000` in the entropy plot.

### Headline findings (from eq_verified_numbers.json)
- Proposition 1 block-softmax identity: VERIFIED to 2.2e-15 over 2000 random draws, once L is read as a log-sum-exp and Z as a within-block average (the paper defines neither). Dilution rises monotonically with |B_t|: VERIFIED. The Ω(r/log N) threshold is not checkable because r is never defined.
- "0.72 → 0.06 = 4.51 bits": NOT CHECKABLE. Six readings give 0.53 to 5.33 bits. None gives 4.51.
- Law 1 (low τ amplifies quantization noise): the direction is VERIFIED (TV ratio 4.4 at τ=0.2 vs 1.0, with σ_q set to 0.05 for illustration). It applies only to sampled decoding.
- Tables 1–3: 13 of 14 rates and Wilson CIs VERIFIED. Table 1 row 3's upper bound is 48.157, which the paper prints as 48.1 (MISMATCH). PAPER.md's abstract says 24.1% where the tables give 24.0% (MISMATCH).
- Fisher p for Trap-25: MISMATCH. The paper says 4.2e-9; recomputed it is 7.18e-9. The test also treats the 25 traps as independent across arms even though both arms run the same traps. The best-case paired test gives 1.9e-6.
- McNemar p-values: 4.6e-5 (Table 2) is unattainable under four standard variants (MISMATCH). 1.8e-6 (Table 1) is reproducible with one variant (NOT CHECKABLE).
- 58-task Wilson ±9.8: MISMATCH (recomputed 10.14).
- The per-repo breakdown, the 937-turn total (25 × the sum of Avg Turns), all percentage deltas and the −93% compaction figure: VERIFIED.
- "Active post-reset KV" values are 4.9–5.8× the 32,768-token context, so they must be cumulative; the paper never defines this. The low-entropy detector with W=4 reduces to "four identical actions in a row".

## 2. Where the SKILL.md was ambiguous, wrong or incomplete

1. **"Write `MathGuide.html` (KaTeX inlined or pre-rendered for offline use)"**. The skill ships no KaTeX and does not say how to get it offline. I improvised by pre-rendering the equations to SVG with matplotlib mathtext. What would help: bundle KaTeX, or name a supported pre-render route.
2. **"with `seed=42` and the paper's nominal parameters"**. This paper gives no σ_q, |A|, logit gaps or r. The skill says nothing about choosing illustrative parameters or labelling them. I marked mine "illustrative" in the JSON. What would help: a rule for parameters the paper leaves out.
3. **"check each closed-form claim by simulation (Monte Carlo …)"**. Most checkable claims here are counts, percentages and p-values, where MC adds nothing, or where p ≈ 1e-9 is far below MC resolution (2M permutations, 0 hits). I improvised a parametric bootstrap and a permutation bound. What would help: say when MC is meaningful and when to set `simulated: null`.
4. **"every equation, proposition, lemma and control law"**. The paper has one displayed equation, and Proposition 2 is a single sentence. Most of the auditable maths is arithmetic and statistics in the prose and tables. The skill does not say whether those are in scope. I included them. It also never mentions the plugin's research-audit MCP tools, which overlap directly.
5. **"`paper_value` (with source)"**. It is unclear whether the source belongs inside the value or in its own field (I added `paper_source`). The skill defines no schema for qualitative claims or dict-valued results, and `abs_gap` is undefined for those.
6. **"`tolerance`"**. The skill gives no policy. I used half a unit of the printed precision (0.05 pts). Some judgment calls depend on that policy: 39.5−17.1 = 22.4 from rounded rates vs 22.48 from counts, and a CI end of 48.157 printed as 48.1.
7. **"`verdict` (`VERIFIED` / `MISMATCH` / `NOT CHECKABLE`)"**. There is no state for "consistent but not uniquely determined", such as a McNemar p that some unreported (b, c) reproduces. NOT CHECKABLE ends up covering both "undefined in the paper" and "data missing but consistent".
8. **"Trace how definitions feed bounds …"**. The skill asks for the dependency graph but says nothing about its form (a figure in the PDF? a JSON field?). I drew an inline SVG on page 1.
9. **"python3 scripts/pdf_tools.py render --html MathGuide.html --pdf <Paper>_Equation_Guide_v1.pdf"**. The path is relative to the skill directory, but the HTML lives in the output directory, so an absolute script path is needed. `<Paper>` is not defined (short name? author?). The output directory is never specified.
10. **"Open every page PNG with Read"**. The skill does not say where the PNGs land. I had to read the script to learn it was `<pdf stem>_preview/page_NN.png` plus a montage.
11. **"the PDF quotes that file"**. No mechanism is given. I wrote `build_guide.py` to fill the HTML from the JSON, but the skill's list of deliverables (PDF, JSON, verify_math.py) leaves out the HTML builder, `MathGuide.html` and the figures.
12. **"fix colliding pills or split derivations and re-render"**. There are no CSS hints. Chrome print needed `break-inside: avoid` on a heading+figure wrapper to keep headings with their figures, and it took 5 renders to get there.
13. **"marking the failure regime and the calibrated operating point"**. Several formulas here (the entropy threshold, the binomial SE) have no calibrated point or failure regime, so I had to make them up.
14. **"Paper"**. The paper directory holds a PDF and a PAPER.md that disagree (24.1% vs 24.0%; the PDF adds CIs, McNemar p-values and a 58-task noise paragraph). The skill does not say which one is authoritative.

## 3. Not done or not verified

- No original data (graph_encoding_ablation_90.csv, per-task outcomes, KV telemetry), so the McNemar p-values, the Wilcoxon p, the 0.72/0.06 dilution and Proposition 2's budget mapping cannot be checked against data.
- The Sanford et al. Lemma 39 and the Ω(r/log N) threshold were not checked against reference [3]. No reference was fetched.
- Law 1's Monte Carlo uses a 256-token toy vocabulary with σ_q = 0.05 (illustrative). It shows the direction of the effect, not its size in the real model.
- Plugin finding, outside the skill: the MCP `leaderboard_noise_floor` silently ignored an unknown argument (`p`) and fell back to `baseline_rate=0.25` without an error.
- No `git commit`; nothing outside `math-sandbox/` was modified.
