---
name: trajectory-cinematics
description: >-
  Render a 1920x1080 H.264 .mp4 explainer animation of a research paper's system state and four
  synchronised live data plots evolving across turns, time or a swept parameter, together with the
  reproducible generator script and a timestamped voice-over script. Use when asked for an animated
  video explainer, a telemetry animation, or a parameter-sweep video of a paper.
---

# Trajectory & Telemetry Cinematics

Produce a clean **1920×1080 H.264 `.mp4` dashboard animation**, its reproducible generator script, and a
timestamped narration `.md`, showing the paper's system state and a 2×2 grid of quantitative curves
evolving live.

## Ground rules

- Curves are computed from the paper's equations or data in the script; captions and milestone banners
  quote numbers from the paper with a source. The narration quotes the same numbers.
- If an audit of this paper exists (`eq_verified_numbers.json` from math-sandbox, `stat_audit.json` from
  ablation-stat-auditor), look up every number in it first. A paper value whose verdict is `MISMATCH` or
  `NOT CHECKABLE` never appears alone: show the recomputed value, or the paper's with its caveat
  ("the paper reports 4.2 × 10⁻⁹; it recomputes to 7.18 × 10⁻⁹").
- Use the active `python3`; install missing packages into it: `imageio`, `imageio-ffmpeg` (bundles an
  ffmpeg binary, so no system ffmpeg is needed), `matplotlib`, `numpy`, `pillow`.

## Workflow

1. **Generator script (`make_explainer.py`).** Layout with `matplotlib.gridspec`: system-state monitor
   (left or top) and a 2×2 telemetry grid, figure at `figsize=(19.2, 10.8), dpi=100`. Draw each frame to an
   RGB array (`fig.canvas.buffer_rgba()`) and write it with
   `imageio.get_writer(out, fps=30, codec="libx264", pixelformat="yuv420p", quality=8, macro_block_size=1)`
   so 1080 rows are kept exactly. Put a short PEP 723 header at the top listing the dependencies.
2. **Milestone preview first.** Render 3–4 milestone frames to PNG and open them with **Read**: check
   gridspec margins, non-overlapping legends, readable axis labels and the bottom milestone banner. Fix
   before encoding the full video.
3. **Encode and check.** Encode the full sweep, then confirm resolution, frame count and duration from the
   file itself (`imageio.v3.improps` / `ffprobe` via `imageio_ffmpeg.get_ffmpeg_exe()`), and grab a frame
   from the middle and open it with **Read**.
4. **Narration (`<Paper>_Narration.md`).** Timestamped `mm:ss` lines aligned to the milestones, computed
   from frame indices / fps in the script.
5. Deliver the `.mp4`, `make_explainer.py` and the narration.
