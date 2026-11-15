# Worked example: all eight skills on one paper

**Paper:** Robina Mirbahar, *Breaking the 15-Minute Cliff in Quantized Gemma 4 Coding Agents* (2026), copied unchanged into [`paper/`](paper/) from [My-antigravity-research-skills](https://github.com/RobinaMirbahar/My-antigravity-research-skills) at `da292de` (MIT). The PDF and `PAPER.md` differ in places; where they disagree the runs treat the PDF as the paper of record.

**Method:** each skill was run on 2026-11-15 by a separate agent that was given only that skill's `SKILL.md`, the paper and an output folder. The runs were independent of one another. Each folder holds the deliverables, the scripts that produced them, and a `RUN_NOTES.md` with the commands run and a numbered list of places where the skill's instructions fell short. The 8 notes list 109 such items between them. The key numbers below were then recomputed separately with the plugin's own `research-audit` server functions.

---

#### What each skill produced

| Skill | Deliverables |
| :--- | :--- |
| [`ablation-stat-auditor`](ablation-stat-auditor/) | `STAT_AUDIT_REPORT.md`, `stat_audit.json` |
| [`citation-doi-verifier`](citation-doi-verifier/) | `REPORT.md` (traffic-light table), `verified_references.bib`, every registry response in `raw/` |
| [`math-sandbox`](math-sandbox/) | 11-page `Gemma4_LoopBreaker_Equation_Guide_v1.pdf`, `eq_verified_numbers.json` (49 claims: 37 VERIFIED, 7 NOT CHECKABLE, 5 MISMATCH) |
| [`figure-forensics`](figure-forensics/) | 4-page `Gemma4_LoopBreaker_Figure_Anatomy_v1.pdf`, annotated figures |
| [`interactive-paper-studio`](interactive-paper-studio/) | Offline `index.html`; 80 preset values agree with the Python reference model to within 1.8e-14 |
| [`trajectory-cinematics`](trajectory-cinematics/) | `Gemma4_LoopBreaker_Explainer.mp4` (1920×1080 H.264, 30 fps, 1,440 frames, 48.0 s, 2.57 MB), generator, narration |
| [`graphic-story`](graphic-story/) | 6-page `LoopBreaker_Comic_v1.pdf`; `story_numbers.json` holds 176 sourced numbers and the build fails on any number outside it |
| [`frontier-gap-radar`](frontier-gap-radar/) | 8-page `Agent_Context_Recovery_Gap_Radar_v1.pdf`, `matrix.csv` (25 papers × 7 dimensions), `references.csv` |

---

#### What the runs found in the paper

Each line was recomputed with `plugin/mcp/research_audit_mcp.py` or read from the PDF text.

- **Trap-25 p-value.** Fisher's exact test on 24/25 vs 4/25 gives p = 7.18 × 10⁻⁹; the paper prints 4.2 × 10⁻⁹. All four configurations ran on the same 25 traps, so the paired test applies: exact McNemar gives p between 1.91 × 10⁻⁶ and 1.10 × 10⁻⁵, depending on how the solved traps overlap. The 80-point gain remains significant under every reading.
- **Ablation steps.** Each M0→M6 step adds 2–4 of 129 tasks; Fisher's exact p per step ranges from 0.606 to 0.883. The full M0→M6 change (15 → 31 of 129) gives p = 0.0141.
- **What 39.5% measures.** The PDF calls Table 1 "Stage-1 Isolated Patch Synthesis", which "supplies the exact target file slice", and reports 17.1% (22/129) for the same calibrated model end to end. `PAPER.md` presents 39.5% as the `swegemma` resolution rate.
- **937 turns** equals 25 × the sum of Table 3's average turns (11.04 + 10.72 + 8.76 + 6.96). That makes it Trap-25 telemetry. One sentence in the PDF credits it to the 129 development tasks.
- **"Recovers half that 29-task gap":** M6 recovers 9 of the 29 tasks (0.31).
- **Wilson interval for 51/129:** [31.5%, 48.2%]; the PDF prints 48.1%.
- **"±9.8 pts" on a 58-task leaderboard at p = 0.20:** the Wilson half-width at 12/58 is 10.26 points and the normal-approximation half-width is 10.29.
- **24.1% vs 24.0%:** the abstract of `PAPER.md` says 24.1%; Table 2 and the PDF say 24.0% (31/129).
- **References:** 3 of 12 confirmed as peer-reviewed by Crossref; 4 flagged, including reference 2, which has no record in any registry searched. Reference 5's ICLR 2024 venue is confirmed on OpenReview ("ICLR 2024 poster"). The citation run classed it as preprint-only because the kit had no OpenReview lookup at the time; `search_openreview_by_title` now covers that case.

---

#### Fixed in the kit as a result of this run

- `research-audit` tools reject argument names their schema does not list. A misspelled option previously fell back to its default and returned a number for a different question.
- `verify_doi_metadata` falls back to DataCite, which registers arXiv `10.48550` DOIs; Crossref returns 404 for all of them.
- New `search_openreview_by_title` returns venue labels for ICLR, NeurIPS and TMLR papers.
- `pdf_tools.py shot` renders a true narrow viewport. Headless Chrome lays pages out at 500 CSS pixels minimum, so a 390 px screenshot was a crop of a 500 px layout.
