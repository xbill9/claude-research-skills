# RUN_NOTES: graphic-story skill test on gemma4-loop-breaker

## 1. Commands run and key output

All commands were run from this directory with the system `python3` (3.14.7). No packages were installed.

```
python3 -I -c "import pymupdf ..."   # extracted the text of the 5-page PDF, page by page
fc-list : family                       # chose Lato (local TTF) so PIL measures text with the same font Chrome draws

python3 story_numbers_build.py
  ... 26 lines "OK  <check>" (each quoted % against its own fraction, plus quoted deltas against computed ones)
  176 numbers, 26 checks, 0 failed

python3 build_story.py
  Story.html: 6 pages, 165 numbers used from story_numbers.json
  (exits non-zero if: a digit is typed into story text, a number shown in the rendered HTML is not in
   story_numbers.json, a bubble/caption covers a face, bar, board or other bubble, a bubble tail crosses
   a face or box, or a panel leaves the page)

python3 /home/xbill/claude-research-skills/plugin/skills/graphic-story/scripts/pdf_tools.py \
    render --html Story.html --pdf LoopBreaker_Comic_v1.pdf --cols 2
  OK PDF: .../LoopBreaker_Comic_v1.pdf (387,604 bytes, 6 pages)
  montage: .../LoopBreaker_Comic_v1_preview/LoopBreaker_Comic_v1_montage.png
```

Five render/inspect rounds. Every page PNG and the montage were opened with Read after each round; two zoomed crops at 216 dpi (PyMuPDF clip) were used to check faces and chest labels. The automated checks caught these problems, which were then fixed:
- caption overlapping a bubble (1a)
- bubble tail crossing another bubble (4d)
- bubble tail crossing the blackboard (6c)
- two bubbles overlapping (6c)
- digits typed in by hand ("Table 1 row 3", "Turns 1 to 4", "Turn 1", bar labels)

These were fixed after visual inspection:
- page 3 title wrapping into the header rule
- equation wrapping on the board
- tails crossing the speaker's own face (fixed by adding side tails)
- swapped worried/stern eyebrows
- robot chest label struck through by its plate border

Deliverables: `LoopBreaker_Comic_v1.pdf`, plus `Story.html`, `story_svg_engine.py`, `story_numbers.json` (`story_numbers_build.py` writes it), `build_story.py`, `story_numbers_used.json` (the subset shown, with sources) and `LoopBreaker_Comic_v1_preview/` (page PNGs and the montage).

## 2. Where SKILL.md was ambiguous, wrong or missing a step

1. **Which source is the paper is not stated.** The task supplied PAPER.md and the PDF, and they disagree. PAPER.md's abstract says M6 = `24.1%`, while its own Table 2 and the PDF say `24.0%`; 31/129 = 24.03, computed in code. PAPER.md lists the checkpoints as `12b`, while the PDF lists `26b-a4b`. PAPER.md presents Table 1 as end-to-end resolution; the PDF presents it as Stage-1 file-isolated synthesis and adds the 22.4-point "Localization-Trajectory Tax". Some numbers appear in only one source: `18.4 GB vs 54.6 GB` and "three or four failed test runs" are only in PAPER.md, the Wilson CIs and McNemar p-values only in the PDF. I used the PDF and cited PDF pages. A line was needed such as "Use the PDF; when sources disagree, record it and quote the PDF."
2. **`story_numbers.json` has no schema, and the rule has no way to be enforced.** The skill says "Every number in a speech bubble, chart or scoreboard is quoted from the paper ... in `story_numbers.json`", but it gives no format and no check. I built my own:
   - each entry holds value, display string, source and verbatim fragment;
   - `{key}` placeholders in the text;
   - a lint on typed digits;
   - an audit of every number in the rendered HTML.
   A schema and a check script bundled with the skill would make the rule testable.
3. **Derived numbers are not covered.** The story needs differences and ratios (+21.7 pts, 2.07x, -93%). The skill says nothing on whether these may be computed or how to cite them. I added `derived` entries with formula and inputs, plus checks against the paper's quoted versions. The paper's "2.1x" (PAPER.md) is 31/15 = 2.07 in code.
4. **`<Paper>` in the output file name is undefined.** In `--pdf <Paper>_Comic_v1.pdf`, it is unclear whether `<Paper>` means the title, the author or the directory. I used `LoopBreaker`.
5. **Working directory and paths are mixed.** The skill says to run "`python3 scripts/pdf_tools.py render --html Story.html`", which assumes the skill directory and the story directory are the same directory. I used the absolute script path. The skill does not say where to write outputs or where the PNGs land: the script writes them to `<pdf stem>_preview/`, which is not mentioned in the skill.
6. **The A4 page setup is missing.** The script is described as producing A4, but it only prints whatever the HTML declares. The skill never says the HTML must set `@page { size: A4; margin: 0 }` and use fixed 210x297 mm page boxes with `break-after: page`. That setup is the only way to guarantee "no panel is cut by a page break". Untested: what Chrome produces without `@page`.
7. **Nothing on fonts or measuring text.** Bubble size depends on text width. The skill gives no font advice, and a web font may not load in headless Chrome. I used a locally installed TTF (Lato) and measured text with PIL using the same file.
8. **Overlap QA is visual only.** "Fix and re-render until no speech bubble covers a face, bar or table row" relies on reading 110 dpi PNGs. At that size, small defects are hard to see: tails crossing faces, brows, a struck-through label. I needed zoomed crops, and the skill does not mention `--dpi` or cropping. Having each character function return its face box, so overlaps can be checked in code, caught most problems before rendering. The skill could require it.
9. **The character contract is underspecified.** It says "one function per character returning an SVG `<g>`", but bubble tails need an anchor point and a face box too. The contract should return (svg, face_box, head_anchor).
10. **The fixed six-member cast is a forced fit.** The skill lists robot, monster, scientist, sergeant, explorer and gatekeeper with no guidance for papers that lack one of the roles. I mapped them as follows:
    - sergeant: greedy τ = 0.2;
    - explorer: T = 1.0;
    - gatekeeper: the three loop detectors.
    This paper fits well, but the skill should say whether every role is mandatory.
11. **"Verbatim HTML benchmark tables" conflicts with the A4 width.** Table 2's row labels are too long for a half-page panel. I kept the values verbatim, shortened the labels, and said so in the table caption. The skill should allow that and require the disclosure.
12. **No instruction to show sources inside the comic.** The ground rule puts sources only in the JSON. I added a footer per page with PDF page/section references. The skill should say whether readers of the PDF should see the citations.
13. **The deliverable list is vague.** "Then deliver the PDF" does not say whether `Story.html`, the engine, the numbers file and the previews are deliverables or scratch files.
14. **No guidance on paper errors.** The skill says nothing about numbers in the paper that are inconsistent (point 1) or that the reader cannot check. I treated the PDF as authoritative and did not add judgement about it to the story.

## 3. Not done or not verified

- The paper's own figures (`figures/*.png`) were not used or inspected; the skill asks for everything to be drawn in code.
- The paper's claims were not checked against the paper's datasets or tests; numbers are quoted as the paper states them. Only internal consistency (fractions against percentages, quoted deltas) was checked, all 26 checks passing.
- The `wilcoxon` entry is quoted from the abstract (`p < 10⁻⁶`); the exact `8.91e-07` appears only in PAPER.md and was not used.
- Bubble wording is invented dialogue that paraphrases the paper. All numbers in it come from `story_numbers.json`, but the paraphrases themselves were checked only by reading them.
- Not tested: render on another browser or OS; the PDF was viewed only as PyMuPDF raster PNGs.
