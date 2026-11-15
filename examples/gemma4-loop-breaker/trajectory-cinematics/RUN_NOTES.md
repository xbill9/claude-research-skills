# RUN_NOTES: trajectory-cinematics on gemma4-loop-breaker

Skill: `plugin/skills/trajectory-cinematics/SKILL.md`
Paper: `examples/gemma4-loop-breaker/paper/` (PAPER.md, 5-page PDF, 3 figures)
Python: pyenv 3.14.7. No packages installed (numpy, matplotlib, imageio, imageio-ffmpeg, pymupdf were already there).

## Deliverables

| File | What |
| --- | --- |
| `Gemma4_LoopBreaker_Explainer.mp4` | 1920x1080 H.264, 1440 frames, 30 fps, 48.0 s, 2.57 MB |
| `make_explainer.py` | Generator (PEP 723 header). `--preview` renders milestone PNGs; no flag renders the .mp4 and narration |
| `Gemma4_LoopBreaker_Narration.md` | 10 timestamped `mm:ss` lines; timestamps computed from frame indices in the script |
| `preview/` | Milestone PNGs from the preview passes, plus `mid_frame_0720.png` taken from the encoded file |

## 1. Commands and key output

```
# read the skill and the paper
cat plugin/skills/trajectory-cinematics/SKILL.md; cat paper/PAPER.md
python3 -c "import pymupdf ... get_text()"      # 5 pages, 2479 words; checked Table 2/3 and Fig. 2 captions in the PDF
Read figures/fig2_ablation_sawtooth.png, figures/fig3_trap25_domains.png

# milestone previews (3 rounds, fixing layout between rounds)
python3 make_explainer.py --preview
  -> preview/milestone_0231/0286/0975/1257/1439.png (1080, 1920, 3)    round 2
  -> preview/milestone_0232/0287/0975/1281/1439.png (1080, 1920, 3)    round 3 (final)
python3 -c "import make_explainer as m; ..."
  CROSS = {'naive_subagent': 3.40, 'baseline_static': 3.88, 'ccr_adaptive': None}
  CUT_POSTKV = 0.70786  (paper: -70.8%)     CUT_COMPACT = 0.93109  (paper: -93%)
  N_FRAMES = 1440

# full encode
time python3 make_explainer.py      -> real 5m12s

# verification from the file itself
imageio_ffmpeg.count_frames_and_secs(mp4)          -> (1440, 48.0)
ffmpeg -i mp4 -c copy -f null -                    -> h264 (High), yuv420p, 1920x1080, 30 fps; frame=1440
os.path.getsize                                    -> 2.565795 MB
imageio.v2 get_reader().get_meta_data()            -> size (1920, 1080), fps 30.0, duration 48.0, nframes inf
imageio.v3.improps(mp4)                            -> shape=(inf, 1080, 1920, 3), n_images=inf
frame 720 grabbed to preview/mid_frame_0720.png and opened with Read (Act 2 start, layout intact)
```

Video structure (one global timeline in three acts):
- Act 1 (00:03–00:21): agent turn t = 1..12. Panel A: active KV per turn for naive sub-agent, baseline static and G-CCR + adaptive, against the 14,336-token cliff. Panel B: attention share on the issue contract A from Proposition 1. Left monitor: context-window bars (A vs B_t) and the three loop detectors (thresholds from §3.4).
- Act 2 (00:23–00:32): modules M0..M6. Panel C: Table 2 solve rate and compaction rate, Table 1 ceiling of 39.5%.
- Act 3 (00:34–00:42): Trap-25 configurations. Panel D: Table 3 escape rate and active post-reset KV.

Provenance of every number on screen:
- **Measured (paper):** Table 1 (17.8%, 39.5%), Table 2 (all columns), Table 3 (solved, escape rate, avg turns, post-reset KV, peak KV), §1 (32,768, 14,336, 4x L4), §3.4 (detector thresholds 2 / 0.82 / 0.55, 150-token ledger, 6144-token burst, tau 0.75), §3.1 (0.72 -> 0.06), §5 (requests-trap-10), Fisher p = 4.2e-9, Wilcoxon p < 1e-6.
- **Computed in the script:** -70.8% (1 - 46,689/159,816), -93% (1 - 4.7/68.2), cliff-crossing turns 3.4 and 3.9, panel B curves.
- **Illustrative:** the per-turn KV curves in panel A and the monitor bars. The paper gives no per-turn table; I read the values approximately off the plotted markers of Fig. 2b and pinned the turn-12 peaks to Table 3 (`assert` in the script). The reset turns (5 and 9) are the drops visible in Fig. 2b. Which detector fires, and when, is not reported; the monitor lights the first detector at turns 4.5–5.5 and 8.5–9.5 and says on screen that this is illustrative. The cliff-crossing turns are properties of these illustrative curves and are labelled that way in the banner and narration.
- **Panel B** is a model applied to illustrative inputs: Proposition 1 with equal per-token logits, so the weight on A = |A| / (|A| + |B_t|), with |A| = the turn-1 context. It does not reproduce the paper's 0.72 -> 0.06 dilution figure (a separate 90-run experiment), which is quoted as a text note in the panel.

## 2. Problems in SKILL.md

1. **"four synchronised live data plots evolving across turns, time or a swept parameter"** (description) and **"Encode the full sweep"** (step 3). The skill assumes one sweep axis drives all four panels. This paper has one per-turn figure (Fig. 2b) and three tables of endpoints over configurations (Table 1, 2, 3); no single axis feeds four plots. I improvised a three-act timeline (turns, then ablation modules, then Trap-25 configs), so only two panels are live in each act. It would help to say what to do when the paper's data does not share one axis: allow acts or segments, or say which panels may hold still.
2. **"Curves are computed from the paper's equations or data in the script."** It says nothing about papers that publish only endpoints or only a plotted figure. I had to decide on my own to read values off Fig. 2b, pin them to Table 3, and label them illustrative in the panel title, the banner, the narration and here. The skill should require a provenance label (measured / computed / illustrative) on every panel and say whether reading values off a figure is allowed.
3. **Proposition 1 has unknown logits.** "computed from the paper's equations" assumes an equation can be evaluated with what the paper gives. Prop. 1 needs L_{h,A}, L_{h,B_t}, which the paper never gives; I had to assume equal per-token logits. Guidance on stating assumptions on-screen when evaluating a paper equation would help.
4. **No guidance on what goes in the "system-state monitor"** ("system-state monitor (left or top)"). Nothing says what the monitor should show (a diagram, live counters, a state machine). I built context-window bars, detector lights and a config list. One sentence with an example would help.
5. **No timeline or duration guidance.** The skill never says how long the video should be, how to pace milestones, or how long a banner must stay up. My first timeline put the Act 3 result banner and the outro banner on the same frame (1275), so the result banner never showed; I only caught it by printing milestone frames. A rule like "keep each banner up at least N seconds; assert milestone frames are distinct and increasing" would catch this.
6. **"Render 3–4 milestone frames to PNG"** does not say how the script exposes this (flag, function) or where the PNGs go. I added `--preview` and a `preview/` folder. Also the skill asks for a preview but gives no way to generate a frame at an arbitrary frame index; you need a `render(frame)` structure from the start, which the skill should state.
7. **"confirm resolution, frame count and duration from the file itself (`imageio.v3.improps` / `ffprobe` via `imageio_ffmpeg.get_ffmpeg_exe()`)".** On this machine `imageio.v3.improps` returns `n_images=inf` for the .mp4 (and `get_meta_data()` gives `nframes: inf`), so it does not give a frame count. Also `imageio_ffmpeg.get_ffmpeg_exe()` returns an `ffmpeg` binary, not `ffprobe`; no ffprobe is bundled. What worked: `imageio_ffmpeg.count_frames_and_secs(path)` -> (1440, 48.0), and `ffmpeg -i f -c copy -f null -` for codec/resolution. The skill should name these.
8. **No size or length target.** The skill says nothing about file size or bitrate. `quality=8` gave 2.57 MB for 48 s here, comfortably under the 20 MB limit I was given, but a reader has no target to check against.
9. **Render time is not mentioned.** 1440 full redraws of a 1920x1080 matplotlib figure took 5 min 12 s, which exceeded my tool's 2-minute foreground timeout and had to run in the background. A note to run the encode in the background (or to blit / reuse artists) would help.
10. **"`fig.canvas.buffer_rgba()`"** returns RGBA; the writer wants RGB. The slice `[:, :, :3]` and a `.copy()` are needed; worth stating.
11. **Narration format is underspecified.** "Timestamped `mm:ss` lines aligned to the milestones" does not say whether to include the on-screen banner text, sources, or a data-provenance note. I included all three. The file name `<Paper>_Narration.md` does not say what `<Paper>` is (title, slug, first author); I used `Gemma4_LoopBreaker`.
12. **No guidance on paper inconsistencies.** The abstract says M6 multi-module repair reaches 24.1%; Table 2, Fig. 2a, Fig. 3a and the PDF all say 24.0% (31/129). I used 24.0% from Table 2. The skill should say: prefer table values, and log conflicts.
13. **Output location is not stated.** The skill never says where to write the .mp4, script and narration, or whether preview PNGs are deliverables.
14. **The ground rule "install missing packages into it: imageio, imageio-ffmpeg, matplotlib, numpy, pillow"** lists `pillow`, which the workflow never uses directly (matplotlib pulls it in). Minor.

## 3. Not done or not verified

- The per-turn KV curves are approximate readings of Fig. 2b markers, by eye from the PNG; no source data (the paper's `turn-level telemetry` dataset) was available in the repo, so they could not be checked.
- I did not watch the video end to end; I checked five milestone frames from the preview passes and one frame (720) decoded from the encoded file.
- No audio track: the narration is a script only, as the skill asks.
- The paper's p-values, CIs and table values are quoted, not recomputed (no raw data). Only the two percentage cuts (-70.8%, -93%) were recomputed from table values.
- An earlier preview round's PNGs (milestone_0231, 0286, 1257) remain in `preview/`; my attempt to clear the folder before re-rendering was blocked by a safety check, so stale previews sit next to the final ones. (Removed before commit; the final milestone frames are 0232, 0287, 0975, 1275, 1281 and 1439.)
