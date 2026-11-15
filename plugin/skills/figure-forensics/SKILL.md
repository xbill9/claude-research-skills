---
name: figure-forensics
description: >-
  Dissect a research paper's architecture diagrams and empirical plots into an annotated A4 Visual Anatomy
  PDF: numbered callout badges, shaded failure/gain regimes, a "Visual Anatomy" decode card and an
  "Engineering Takeaway" card per figure. Use when asked to break down, annotate, decode or explain a
  paper's figures, plots or diagrams.
---

# Figure Forensics & Visual Anatomy

Turn dense figures, multi-panel ablations and architecture diagrams into an A4 **Visual Anatomy Dossier
PDF**. Each figure gets numbered callout badges (`1`, `2`, `3`…), shaded regimes, a decode card that walks
the reader through it, and an engineering takeaway.

## Ground rules

- Every number on a card is quoted from the paper text or table (with page/figure reference) or computed
  in a script. Do not read values off a plot by eye and present them as exact; label them "read from plot".
- Use the active `python3`; install missing packages into it (`pymupdf`, `pillow`, `matplotlib`).
- Name scripts for what they do (`annotate_figures.py`), never after a stdlib module.

## Workflow

1. **Narrative arc — ARCHITECTURE → MECHANISM → EMPIRICAL GAIN.** For each figure, say which step of the
   paper's argument it carries, and collect every number the text quotes about it.
2. **Get the figure at print quality.**
   - Vector PDF: extract with PyMuPDF (`page.get_pixmap(dpi=300)` on the figure's clip rect, or
     `page.get_drawings()` for paths).
   - Raster source: work at 300 DPI.
3. **Overlay badges** with `matplotlib` (`bbox_inches="tight"`), keeping badges in clear margins away from
   tick labels, legends and data. Shade failure regimes (rose) and gain regimes (green) with low alpha.
4. **Write the HTML dossier** — one figure per page section: annotated image, numbered decode steps that
   match the badges, an Engineering Takeaway card, source reference.
5. **Render and inspect.** Run this skill's bundled script (path relative to this skill's base directory):

   ```bash
   python3 scripts/pdf_tools.py render --html Anatomy.html --pdf <Paper>_Figure_Anatomy_v1.pdf
   ```

   Open every `page_NN.png` it prints with the **Read** tool. Fix and re-render until no badge overlaps a
   label or datum, no card is split across a page break and no table is clipped. Only then deliver the PDF.
