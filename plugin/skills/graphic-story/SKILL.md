---
name: graphic-story
description: >-
  Turn a technical research paper into an A4 graphic-novel PDF drawn entirely in code (SVG + HTML,
  rendered by headless Chrome): recurring characters, architecture blackboards, decision gates and
  benchmark scoreboards that quote the paper's real numbers. Use when asked for a comic, graphic story,
  or visual storytelling summary of a paper.
---

# Technical Graphic-Novel Studio

Turn a systems, AI or science paper into an A4 **vector graphic-novel PDF**, drawn from Python-generated
SVG/HTML — no image-generation API — and faithful to the paper's exact numbers.

## Ground rules

- Every number in a speech bubble, chart or scoreboard is quoted from the paper, with its page/table
  source, in `story_numbers.json`. Charts and scoreboards are drawn from that file, not retyped.
- Use the active `python3`; install missing packages into it.

## Workflow

1. **Cast technical archetypes.** Map the paper onto a recurring cast: the system/agent (`robot`), the
   failure bottleneck (`monster`), a researcher narrator (`scientist`), the rigid baseline (`sergeant`),
   the adaptive method (`explorer`) and the threshold detector (`gatekeeper`). Write
   `story_svg_engine.py` with one function per character returning an SVG `<g>` (pose and expression as
   parameters) plus helpers for panels, speech bubbles and captions, so every page reuses the same drawings.
2. **Script the pages.** 4–6 A4 pages, 3–6 panels each: problem → failure → mechanism → result. Pair
   dialogue with SVG blackboards (equations, architecture), bar charts, decision diamonds and verbatim HTML
   benchmark tables.
3. **Render and inspect.** Generate `Story.html`, then (script in this skill's base directory):

   ```bash
   python3 scripts/pdf_tools.py render --html Story.html --pdf <Paper>_Comic_v1.pdf --cols 2
   ```

   Open every page PNG and the 2-up montage with **Read**. Fix and re-render until no speech bubble covers
   a face, bar or table row and no panel is cut by a page break. Then deliver the PDF.
