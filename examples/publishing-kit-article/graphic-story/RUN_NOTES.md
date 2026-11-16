# RUN_NOTES: graphic-story skill on the publishing-kit article

Paper of record: `../paper/devto-publishing-kit.md` (dev.to article, "Streamline Publishing with a Claude Code Skill").
Evidence: `../paper/evidence/*.txt`; `../paper/CLAIMS.md` read for the source category of each claim.
System `python3` 3.14.7 (pyenv), PyMuPDF and Pillow already installed, Chrome at `/usr/bin/google-chrome`. Nothing installed.

## 1. Commands run and key output

| Command (from this directory) | Key output |
| --- | --- |
| `python3 story_numbers_build.py` | `61 numbers, 12 checks, 0 failed, 6 of 6 CLAIMS.md rows differ from evidence`. Exits 1 if a quoted fragment is not found verbatim in its source file, or a check fails. |
| `python3 build_story.py` | `Story.html: 5 pages, 42 numbers used from story_numbers.json`. Exits 1 on a typed digit or spelled number, an unsourced number in the rendered HTML, or a layout overlap. |
| `python3 ../../../plugin/skills/graphic-story/scripts/pdf_tools.py render --html Story.html --pdf PublishingKit_Comic_v1.pdf --cols 2` | `OK PDF: .../PublishingKit_Comic_v1.pdf (344,761 bytes, 5 pages)`; page PNGs and montage in `PublishingKit_Comic_v1_preview/` |
| `python3 verify_pdf.py PublishingKit_Comic_v1.pdf` | `5 pages, 42 sourced numbers allowed, 0 problems` (checks the PDF's own text and that every page is A4) |
| Negative test: `T('it took 7 days')`, `T('it took seven days')`, `audit_rendered('<p>47 of 99% fine</p>')` | both `T` calls refused; audit returned `number '99%' ... not in story_numbers.json displays` |
| Negative test: `42 ms` injected into a scratch copy of Story.html, rendered, `verify_pdf.py` | `ERROR page 2: number '42' not in story_numbers.json displays`, exit 1 |

Pipeline: `story_numbers_build.py` → `build_story.py` → `pdf_tools.py render` → `verify_pdf.py`; each step fails the build on its own errors.

Six render-and-inspect rounds. All five page PNGs and the montage were opened with Read after each round. Three areas were also checked in 3x zoomed PyMuPDF crops (page 1 sergeant, page 3 gatekeeper, page 5 closing panel). The automated layout check caught these, and they were fixed:
- a bubble over a caption (p1);
- a caption over the robot's face (p2);
- a caveat note running out of its panel (p3);
- tails crossing faces (p1, p2, p3, p5);
- bubbles and notes over character bodies (p3, p5).

Visual inspection caught these, and they were fixed:
- mirrored character labels on flipped figures;
- clipboard covering the sergeant's label;
- right arms swinging across the body, so the gatekeeper's lamp and the scout's magnifier sat on their faces;
- terminal output clipped at the right;
- the last LinkedIn table row clipped;
- an oversized blackboard;
- empty panel space on p5.

Deliverables:
- `PublishingKit_Comic_v1.pdf` (5 A4 pages)
- `Story.html`
- `story_svg_engine.py` (six characters, panels, bubbles, boards, layout QA)
- `build_story.py`
- `story_numbers_build.py`, which writes `story_numbers.json` (61 sourced entries, checks, CLAIMS-vs-evidence comparison)
- `story_numbers_used.json` (the 42 entries shown, with sources and caveats)
- `verify_pdf.py`
- `PublishingKit_Comic_v1_preview/` (page PNGs, montage)

## 2. Headline findings

- **Story (5 pages).** Each page cites its sources in a footer.
  1. *One Article, Four Destinations*: the ceremony, the by-hand baseline, the source-to-four-artifacts pipeline.
  2. *The Mangler*: dev.to hard breaks, 47 of 62 blocks; cover crop at 2.381:1, so a 1376x768 cover loses 95px top and bottom; Medium data: URIs, 0 of 4; LinkedIn accepts only `PUBLISHED`.
  3. *The Gate*: pre-flight decision diamond, check-facts' three kinds of untraced claim, LinkedIn self-checks, the browser route with the 23,234-character Builder payload.
  4. *Fetch What They Serve*: check-links output quoted verbatim, plus a table of symptoms and tools.
  5. *Dogfooding*: the article's cover scoreboard, the five faults the kit found in itself, install-is-a-snapshot, measured on 2026-08-31.
- **Every number checks out against its source.** All 12 consistency checks pass in code:
  - 58 + 4 = 62;
  - 1000/420 = 2.381;
  - round(1376/2.381) = 578 and (768 − 578)/2 = 95;
  - the 1376x578 fixed cover has ratio 2.381;
  - 24 + 13 + 3 = 40 org-routed articles;
  - the article's list of faults has five items;
  - the article's 47 of 62 equals the evidence file.
- **Five numbers shown have no archived measurement** and carry a caveat on the page:
  - the Medium 0 of 4 / 4 of 4 figures (CLAIMS.md LOG, 2026-08-30);
  - the LinkedIn 3,000 limit and 140 fold (third-party per CLAIMS.md);
  - the LinkedIn `PUBLISHED` rule (DOCUMENTED).
  The article's 47 of 62 was measured on 2026-09-16, after its stated 2026-08-31 date; the comic says so.
- **CLAIMS.md is stale against the evidence files.** All 6 rows compared differ (computed in `story_numbers_build.py`, listed under `_ledger_vs_evidence`):
  - Builder payload 22,542 / 521 / 408 and 23,214 / 531 / 411, against evidence 23,234 / 531 / 411;
  - footprint ~187 / ~8k at 0.2.0, against ~190 / ~11.8k at 0.18.0;
  - SKILL.md 446 against 649 lines;
  - 2,370 against 4,580 total lines;
  - pinned commit f7eaac2 against 920fe6c.
  None of these figures are used in the article itself, and the comic quotes the evidence values only.

## 3. Where the skill's instructions fell short for this input

1. **The skill assumes a research paper.** The input is a tool write-up with no tables of results, no method and no baseline. "problem → failure → mechanism → result" had to be mapped by hand (destination quirks as the failure, pre-flight as the mechanism, dogfooding as the result).
2. **The fixed six-role cast is a forced fit.** There is no researcher, rigid baseline or adaptive method in the article. I invented MANUAL (copying by hand across four files) and SCOUT (fetching what the destination serves). The skill does not say whether every role is required.
3. **There is no rule for sources ranked below the paper.** The article mixes measured numbers, numbers from the kit's log, vendor documentation and third-party figures, and CLAIMS.md ranks them. The ground rule covers only `MISMATCH` / `NOT CHECKABLE` from audit files. I attached caveats from CLAIMS.md categories by my own rule.
4. **The audit-file lookup is underspecified, and it conflicted with this task.** The skill says to look up `eq_verified_numbers.json` / `stat_audit.json` "if an audit exists", but not where. No audit was in `paper/` when the run started. Sibling `math-sandbox/` and `ablation-stat-auditor/` folders appeared during the run. The task forbade reading them, so this comic was not checked against them. Unverified: whether they dispute any number shown.
5. **`story_numbers.json` has no schema and no check.** I wrote the format myself: value, display, source, verbatim quote, caveat, derived formula. I also wrote both enforcement steps (an HTML audit and a PDF audit). "Make the build fail on any number not in it" is not something the skill provides.
6. **Spelled-out numbers are not covered.** The article's key counts are words ("four places", "five faults", "three things", "two numbers"). A digit-only rule misses them. I added a word list (two to twenty), which then flagged markdown syntax ("two spaces") and needed its own sourced entry.
7. **Identifiers that contain digits are not addressed.** Filenames such as `cover.77acc7c4.jpg` and `table-1.png` in quoted tool output, and `127.0.0.1`, are numeric tokens. I sourced each as a quoted entry. The skill does not say whether identifiers count as numbers.
8. **Derived numbers are not covered.** 76%, 120 joined lines and 1731 were computed in code with their formulas. The skill does not say whether derived values are allowed.
9. **The comic itself is not asked to show sources or caveats.** Sources are required only in the JSON. I added page footers and on-page caveat notes.
10. **A4 page setup, fonts and text measurement are missing.** The skill does not mention `@page { size: A4; margin: 0 }`, fixed page boxes or `break-after`. It does not mention a local TTF that matches the measured text either. Without these, "no panel cut by a page break" cannot be guaranteed.
11. **Overlap QA is visual only.** The 110 dpi PNGs did not show tails crossing faces or arms crossing labels clearly; zoomed crops did. A face box, body box and tail anchor returned by each character function, checked in code, caught most defects before rendering. The skill's character contract ("returns an SVG `<g>`") is too thin for that.
12. **Paths and outputs are left unstated.** `<Paper>` in the PDF name is undefined; I used `PublishingKit`. `scripts/pdf_tools.py` is relative to the skill directory, not the working directory. The `<pdf stem>_preview/` output folder is not mentioned. "Deliver the PDF" does not say whether the HTML, scripts and JSON are deliverables.
13. **"Verbatim HTML benchmark tables" does not fit this article.** It has one two-row table, which I reproduced verbatim. The LinkedIn and symptom tables are built from evidence and article prose, and are labelled as such. The skill gives no guidance when the source has few tables.
14. **There is no guidance for a ledger that disagrees with its evidence.** CLAIMS.md differs from the evidence files in 6 of 6 rows compared. The skill does not say which one wins. I used the evidence files and recorded the disagreement.

## 4. Not done or not verified

- check-links, check-facts, preflight and the dev.to and LinkedIn measurements were not re-run. All of them are quoted from the article or its evidence.
- Dialogue paraphrases the article; the paraphrases were checked only by reading them. Numbers inside them come from `story_numbers.json`.
- `scripts/pdf_tools.py` in the repo had uncommitted changes from outside this run. The render used the copy on disk at the time.
- The PDF was viewed only as PyMuPDF raster images, not in a PDF viewer.
