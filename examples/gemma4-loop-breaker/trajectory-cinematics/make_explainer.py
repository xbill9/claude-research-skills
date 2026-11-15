# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "matplotlib", "imageio", "imageio-ffmpeg"]
# ///
"""Trajectory cinematics for Mirbahar (2026), "Breaking the 15-Minute Cliff in Quantized
Gemma 4 Coding Agents" (paper/PAPER.md and the 5-page PDF).

Three acts on one global timeline, 30 fps:
  Act 1  sweep agent turn t = 1..12   -> panels A (active KV) and B (attention share, Prop. 1)
  Act 2  sweep ablation module M0..M6 -> panel C (Table 2, measured)
  Act 3  sweep Trap-25 configuration  -> panel D (Table 3, measured)

Data provenance (also printed on screen):
  * Per-turn KV curves in panel A are ILLUSTRATIVE: approximate values read off the plotted
    markers of Fig. 2b; the paper publishes no per-turn table. The turn-12 peaks are pinned to
    the measured Peak KV column of Table 3 (24,821 / 31,067 / 10,563).
  * Panel B is computed here from Proposition 1 (Sec. 3.1) under an explicit simplification:
    equal per-token logits, |A| = turn-1 context, |B_t| = everything added since. It is a model
    applied to illustrative inputs, not a measurement.
  * Panels C and D are the paper's measured table values (Table 2, Table 3).

Usage:
  python3 make_explainer.py --preview   # milestone PNGs only
  python3 make_explainer.py             # full .mp4 + narration .md
"""
import argparse
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
OUT_MP4 = os.path.join(HERE, "Gemma4_LoopBreaker_Explainer.mp4")
OUT_NARR = os.path.join(HERE, "Gemma4_LoopBreaker_Narration.md")

# ---------------------------------------------------------------- data from the paper
CLIFF = 14_336            # Sec. 1 item 1: EventsCompactionConfig threshold
MAX_LEN = 32_768          # Sec. 1: max_model_len
TURNS = np.arange(1, 13)  # Fig. 2b x-axis

# ILLUSTRATIVE per-turn active KV (tokens): approximate read-off of Fig. 2b markers;
# turn-12 / peak values pinned to Table 3 "Peak KV Cache".
KV = {
    "naive_subagent": np.array([4.2, 8.1, 12.6, 16.9, 20.4, 23.8, 26.5, 28.4, 29.8, 30.6, 31.0, 31.067]) * 1e3,
    "baseline_static": np.array([3.9, 7.2, 10.9, 14.8, 17.6, 19.9, 21.8, 23.1, 24.0, 24.5, 24.7, 24.821]) * 1e3,
    "ccr_adaptive": np.array([3.4, 5.8, 8.3, 10.563, 4.4, 6.6, 8.9, 10.5, 4.7, 6.8, 8.4, 9.4]) * 1e3,
}
RESET_TURNS = [5, 9]      # sawtooth drops visible in Fig. 2b
KV_STYLE = {
    "naive_subagent": dict(color="#8a94a6", ls="--", marker="s", label="Naive sub-agent"),
    "baseline_static": dict(color="#c0392b", ls="-.", marker="^", label="Baseline static"),
    "ccr_adaptive": dict(color="#1f5fd6", ls="-", marker="o", label="G-CCR + Adaptive"),
}
PEAK_T3 = {"naive_subagent": 31_067, "baseline_static": 24_821, "ccr_adaptive": 10_563}  # Table 3

# Table 2 (measured): cumulative ablation over 129 swegemma tasks
T2_MOD = ["M0", "+M1", "+M2", "+M3", "+M4", "+M5", "+M6"]
T2_DESC = ["Default 9-tool template (T=0.2)", "Lean-6 workspace toolset", "Calibrated thinking (T=1.0)",
           "Turn-1 6-relation parser + 120-line reads", "Call-12 source-edit deadline",
           "Co-change coupling", "Graph backtrack + red-test submit"]
T2_SOLVED = np.array([15, 18, 22, 25, 27, 29, 31])
T2_RATE = np.array([11.6, 14.0, 17.1, 19.4, 20.9, 22.5, 24.0])
T2_COMPACT = np.array([68.2, 44.0, 31.0, 8.5, 6.2, 5.4, 4.7])
T2_PEAKKV = np.array([28_400, 22_100, 18_600, 11_200, 10_400, 9_850, 9_420])
T1_CEILING = 39.5   # Table 1, 51/129
T1_BASE = 17.8      # Table 1, 23/129

# Table 3 (measured): Trap-25
T3_CFG = ["baseline_static", "naive_subagent", "ccr_only", "ccr_adaptive"]
T3_SOLVED = np.array([4, 5, 18, 24])
T3_ESC = np.array([16.0, 20.0, 72.0, 96.0])
T3_POSTKV = np.array([159_816, 190_410, 85_148, 46_689])
T3_TURNS = np.array([11.04, 10.72, 8.76, 6.96])

# Derived numbers, computed (not typed):
CUT_POSTKV = 1 - T3_POSTKV[3] / T3_POSTKV[0]          # paper: -70.8%
CUT_COMPACT = 1 - T2_COMPACT[-1] / T2_COMPACT[0]      # paper: -93%
for _cfg in KV:
    assert abs(KV[_cfg].max() - PEAK_T3[_cfg]) < 1, _cfg


def cliff_crossing(kv):
    """First fractional turn where a piecewise-linear curve crosses CLIFF (None if never)."""
    for i in range(len(kv) - 1):
        if kv[i] < CLIFF <= kv[i + 1]:
            return TURNS[i] + (CLIFF - kv[i]) / (kv[i + 1] - kv[i])
    return None


CROSS = {k: cliff_crossing(v) for k, v in KV.items()}


def attn_share_A(kv):
    """Prop. 1 with equal per-token logits: weight on A = |A| / (|A| + |B_t|).
    |A| = turn-1 context; after a G-CCR reset B_t is pruned, so |B_t| = max(N_t - |A|, 0)."""
    a = kv[0]
    return a / np.maximum(kv, a)


SHARE = {k: attn_share_A(v) for k, v in KV.items()}

# ---------------------------------------------------------------- timeline
SEG = [("intro", 3.0), ("act1", 18.0), ("hold1", 2.5), ("act2", 9.0), ("hold2", 2.0),
       ("act3", 8.0), ("outro", 5.5)]
SEG_START = {}
_t = 0.0
for _n, _d in SEG:
    SEG_START[_n] = _t
    _t += _d
TOTAL_S = _t
N_FRAMES = int(round(TOTAL_S * FPS))


def state_at(frame):
    """Return (turn_float 1..12, module_float 0..6, config_float 0..3, segment name)."""
    s = frame / FPS
    seg = SEG[-1][0]
    for n, d in SEG:
        if SEG_START[n] <= s < SEG_START[n] + d:
            seg = n
            break

    def frac(n):
        return float(np.clip((s - SEG_START[n]) / dict(SEG)[n], 0, 1))

    turn = 1 + 11 * frac("act1")
    module = 6 * frac("act2") if s >= SEG_START["act2"] else -1
    config = 3 * frac("act3") if s >= SEG_START["act3"] else -1
    return turn, module, config, seg


def frame_for_turn(t):
    return int(np.ceil((SEG_START["act1"] + (t - 1) / 11 * dict(SEG)["act1"]) * FPS))


def frame_for_module(m):
    return int(round((SEG_START["act2"] + m / 6 * dict(SEG)["act2"]) * FPS))


def frame_for_config(c):
    return int(round((SEG_START["act3"] + c / 3 * dict(SEG)["act3"]) * FPS))


# Milestones: (frame, banner text, narration text). Banner numbers carry a source.
MILESTONES = [
    (0, "Setup (Sec. 1): gemma-4-31b-it-qat-w4a16-ct on 4x NVIDIA L4, max_model_len 32,768; "
        "ADK compaction fires above 14,336 tokens.",
     "A 4-bit quantized Gemma 4 31B coding agent runs on four L4 GPUs with a 32,768-token context. "
     "Once the dialogue passes 14,336 tokens, the runner compacts it and exact file paths and line numbers are lost (Section 1)."),
    (frame_for_turn(1), "Act 1 - per-turn active KV context. Curve shapes are illustrative (read off Fig. 2b); "
                        "turn-12 peaks are Table 3 values.",
     "Each curve is the active context at each agent turn. The shapes are illustrative, read off Figure 2b; "
     "only the peaks are tabulated in the paper."),
    (frame_for_turn(CROSS["baseline_static"]),
     f"Baseline static crosses the 14,336-token compaction cliff at turn {CROSS['baseline_static']:.1f} "
     f"(on the illustrative curve; naive sub-agent at {CROSS['naive_subagent']:.1f}).",
     f"Without pruning, failed test logs pile up. On these curves the baseline crosses the compaction cliff "
     f"at about turn {CROSS['baseline_static']:.1f}, the naive sub-agent at about turn {CROSS['naive_subagent']:.1f}."),
    (frame_for_turn(5), "Loop detector fires -> G-CCR prunes B_t, inserts a 150-token NEGATIVE_CONSTRAINT_LEDGER, "
                        "6144-token thinking burst at tau=0.75 (Sec. 3.4).",
     "When a loop detector fires (a repeated error signature, diff similarity at least 0.82, or action entropy below "
     "0.55 bits), Counterfactual Context Reset prunes the failed turns, writes a 150-token ledger of what failed, and "
     "starts a 6,144-token thinking burst (Section 3.4)."),
    (frame_for_turn(12), "Peak KV (Table 3): naive 31,067 | baseline 24,821 | G-CCR + adaptive 10,563 - "
                         "below the 14,336 cliff.",
     "By turn 12 the peaks match Table 3: 31,067 tokens for the naive sub-agent, 24,821 for the baseline, "
     "and 10,563 for G-CCR with adaptive thinking, which stays under the cliff."),
    (frame_for_module(0), "Act 2 - Table 2 cumulative ablation, 129 swegemma tasks: M0 solves 15/129 (11.6%), "
                          "compaction on 68.2% of episodes.",
     "Act two is the cumulative ablation on 129 repository tasks. The default template solves 15 of 129, 11.6 percent, "
     "and hits compaction on 68.2 percent of episodes (Table 2)."),
    (frame_for_module(6), f"M6 solves 31/129 (24.0%); compaction 4.7% ({-CUT_COMPACT:.0%} vs M0). "
                          f"Stage-1 isolated ceiling 39.5% (Table 1).",
     f"With all six modules the agent solves 31 of 129, 24.0 percent, and compaction falls to 4.7 percent, "
     f"a {CUT_COMPACT:.0%} cut. File-isolated synthesis reaches 39.5 percent, so a gap remains (Tables 1 and 2)."),
    (frame_for_config(0), "Act 3 - Trap-25 loop recovery (Table 3): baseline static escapes 4/25 traps (16.0%).",
     "Act three is the 25-trap fault-injection suite. The unpruned baseline escapes 4 of 25 traps, 16 percent (Table 3)."),
    (frame_for_config(2.7), f"G-CCR + adaptive: 24/25 (96.0%), Fisher p = 4.2e-9; post-reset KV 159,816 -> 46,689 "
                          f"({-CUT_POSTKV:.1%}) (Table 3).",
     f"Counterfactual Context Reset with adaptive thinking escapes 24 of 25, 96 percent, Fisher's exact p of 4.2 times "
     f"ten to the minus nine, and cuts active post-reset KV tokens from 159,816 to 46,689, {CUT_POSTKV:.1%} (Table 3)."),
    (int(round((SEG_START["outro"] + 2.5) * FPS)), "Takeaway: under a 14,336-token limit, pruning failed turns keeps the agent "
                                           "below the cliff. Panels A-B illustrative; C-D measured.",
     "Under a hard compaction limit, context hygiene decides whether a quantized agent escapes a loop. "
     "Panels A and B are illustrations; panels C and D are the paper's measured tables."),
]


def banner_at(frame):
    txt = MILESTONES[0][1]
    for f, b, _ in MILESTONES:
        if frame >= f:
            txt = b
    return txt


# ---------------------------------------------------------------- figure
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "axes.titlesize": 15,
                     "axes.labelsize": 13, "axes.spines.top": False, "axes.spines.right": False})


def build_figure():
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor="white")
    gs = gridspec.GridSpec(2, 3, figure=fig, width_ratios=[0.95, 1, 1], left=0.035, right=0.955,
                           top=0.885, bottom=0.165, wspace=0.26, hspace=0.42)
    ax_m = fig.add_subplot(gs[:, 0])
    axA = fig.add_subplot(gs[0, 1])
    axB = fig.add_subplot(gs[0, 2])
    axC = fig.add_subplot(gs[1, 1])
    axD = fig.add_subplot(gs[1, 2])
    fig.text(0.035, 0.955, "Breaking the 15-Minute Cliff in Quantized Gemma 4 Coding Agents",
             fontsize=24, weight="bold", va="center")
    fig.text(0.035, 0.918, "Mirbahar (2026) - LoopBreakerEngine / Counterfactual Context Reset (G-CCR), "
             "trajectory explainer", fontsize=14, color="#444", va="center")
    return fig, ax_m, axA, axB, axC, axD


def draw_monitor(ax, turn, module, config, seg):
    ax.clear()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.005, 0.005), 0.99, 0.99, boxstyle="round,pad=0,rounding_size=0.02",
                                fc="#f6f8fb", ec="#c9d1dc", lw=1.5))
    ax.text(0.04, 0.955, "SYSTEM STATE", fontsize=16, weight="bold", color="#1b2a41", va="top")
    if seg in ("intro", "act1", "hold1"):
        ax.text(0.04, 0.905, f"Act 1  |  agent turn t = {turn:4.1f} / 12", fontsize=14, va="top", family="monospace")
        ax.text(0.04, 0.865, "Context window (bars illustrative, Fig. 2b)", fontsize=11.5, color="#555", va="top")
        t_idx = turn
        y0 = 0.80
        for k in ["naive_subagent", "baseline_static", "ccr_adaptive"]:
            n = float(np.interp(t_idx, TURNS, KV[k]))
            a = KV[k][0]
            st = KV_STYLE[k]
            ax.text(0.04, y0, st["label"], fontsize=12.5, color=st["color"], weight="bold", va="bottom")
            ax.text(0.96, y0, f"{n:,.0f} tok", fontsize=12.5, ha="right", va="bottom", family="monospace")
            bx, bw, bh = 0.04, 0.92, 0.045
            yb = y0 - 0.055
            ax.add_patch(Rectangle((bx, yb), bw, bh, fc="white", ec="#999", lw=1))
            wa = bw * min(n, a) / MAX_LEN
            wb = bw * max(n - a, 0) / MAX_LEN
            ax.add_patch(Rectangle((bx, yb), wa, bh, fc="#2e8b57", ec="none"))
            ax.add_patch(Rectangle((bx + wa, yb), wb, bh, fc="#e67e22" if n > CLIFF else "#f0b27a", ec="none"))
            xc = bx + bw * CLIFF / MAX_LEN
            ax.plot([xc, xc], [yb - 0.008, yb + bh + 0.008], color="#b03a2e", lw=2, ls=":")
            y0 -= 0.135
        ax.text(0.04, 0.395, "green = A (issue + 1-hop slice)   orange = B_t (failed logs/diffs)",
                fontsize=10.5, color="#444", va="top")
        ax.text(0.04, 0.365, f"dotted = 14,336-token cliff; bar width = {MAX_LEN:,} tokens", fontsize=10.5,
                color="#444", va="top")
        # Loop detectors (thresholds from Sec. 3.4); firing timing illustrative
        ax.text(0.04, 0.31, "G-CCR loop detectors (Sec. 3.4)", fontsize=13, weight="bold", va="top")
        firing = any(abs(turn - (r - 0.5)) <= 0.5 for r in RESET_TURNS)
        dets = ["Repeated error  C_err(t) >= 2", "Diff LCS  S_diff(t) >= 0.82", "Action entropy  H_W(t) < 0.55 bits"]
        for i, d in enumerate(dets):
            yy = 0.255 - i * 0.05
            on = firing and i == 0
            ax.add_patch(Circle((0.06, yy), 0.014, fc="#e74c3c" if on else "#cfd6df", ec="#555"))
            ax.text(0.09, yy, d, fontsize=11.5, va="center", family="monospace")
        msg = ("RESET: prune B_t, 150-tok ledger, 6144-tok burst" if firing else "monitoring...")
        ax.text(0.04, 0.085, msg, fontsize=12, va="center", color="#c0392b" if firing else "#666",
                weight="bold" if firing else "normal")
        ax.text(0.04, 0.035, "(firing time illustrative; which detector fired is not reported)",
                fontsize=9.5, color="#777", va="center")
    elif seg in ("act2", "hold2"):
        mi = int(np.floor(module + 1e-9))
        ax.text(0.04, 0.905, "Act 2  |  cumulative ablation (Table 2)", fontsize=14, va="top")
        for i, (m, d) in enumerate(zip(T2_MOD, T2_DESC)):
            yy = 0.82 - i * 0.075
            on = i <= mi
            cur = i == mi
            ax.add_patch(FancyBboxPatch((0.03, yy - 0.028), 0.94, 0.056, boxstyle="round,pad=0,rounding_size=0.01",
                                        fc="#dbe8ff" if cur else ("#eef2f7" if on else "white"),
                                        ec="#1f5fd6" if cur else "#cdd5df", lw=2 if cur else 1))
            ax.text(0.05, yy, f"{m:<4}", fontsize=12.5, weight="bold", va="center", family="monospace",
                    color="#1b2a41" if on else "#aaa")
            ax.text(0.15, yy, d, fontsize=11.5, va="center", color="#1b2a41" if on else "#aaa")
        ax.text(0.04, 0.26, f"Avg calls   {['24.6','21.2','18.9','15.4','13.8','13.1','12.4'][mi]}",
                fontsize=13, family="monospace", va="center")
        ax.text(0.04, 0.21, f"Peak KV     {T2_PEAKKV[mi]:,} tok", fontsize=13, family="monospace", va="center")
        ax.text(0.04, 0.16, f"Compaction  {T2_COMPACT[mi]:.1f}% of episodes", fontsize=13, family="monospace",
                va="center")
        ax.text(0.04, 0.11, f"Solved      {T2_SOLVED[mi]}/129 ({T2_RATE[mi]:.1f}%)", fontsize=13,
                family="monospace", va="center", weight="bold")
        ax.text(0.04, 0.045, "all values measured, Table 2", fontsize=10, color="#777", va="center")
    else:
        ci = int(np.floor(max(config, 0) + 1e-9))
        ax.text(0.04, 0.905, "Act 3  |  Trap-25 loop recovery (Table 3)", fontsize=14, va="top")
        for i, c in enumerate(T3_CFG):
            yy = 0.80 - i * 0.12
            on = i <= ci
            cur = i == ci and seg == "act3"
            ax.add_patch(FancyBboxPatch((0.03, yy - 0.045), 0.94, 0.09, boxstyle="round,pad=0,rounding_size=0.01",
                                        fc="#dbe8ff" if cur else ("#eef2f7" if on else "white"),
                                        ec="#1f5fd6" if cur else "#cdd5df", lw=2 if cur else 1))
            col = "#1b2a41" if on else "#aaa"
            ax.text(0.05, yy + 0.018, c, fontsize=13, weight="bold", va="center", family="monospace", color=col)
            ax.text(0.05, yy - 0.022, f"solved {T3_SOLVED[i]}/25  turns {T3_TURNS[i]:.2f}  "
                    f"post-reset KV {T3_POSTKV[i]:,}", fontsize=10.5, va="center", family="monospace", color=col)
        ax.text(0.04, 0.24, "Fisher's exact p = 4.2e-9 (24/25 vs 4/25)", fontsize=12.5, va="center")
        ax.text(0.04, 0.19, f"Post-reset KV cut: {-CUT_POSTKV:.1%} (Wilcoxon p < 1e-6)", fontsize=12.5, va="center")
        ax.text(0.04, 0.14, "Sole timeout: requests-trap-10 (Sec. 5)", fontsize=12.5, va="center")
        ax.text(0.04, 0.045, "all values measured, Table 3 / Sec. 5", fontsize=10, color="#777", va="center")


def setup_panels(axA, axB, axC, axD):
    axA.set_title("A  Active KV per turn  (illustrative)", loc="left", weight="bold")
    axA.set_xlim(0.7, 12.3)
    axA.set_ylim(0, 34)
    axA.set_xlabel("Agent turn t")
    axA.set_ylabel("Active KV (k tokens)")
    axA.axhline(CLIFF / 1e3, color="#b03a2e", ls=":", lw=2)
    axA.text(12.2, CLIFF / 1e3 + 0.6, "compaction cliff 14,336", color="#b03a2e", fontsize=11, ha="right")
    axA.grid(alpha=0.3)
    linesA = {}
    for k in KV:
        st = KV_STYLE[k]
        (ln,) = axA.plot([], [], color=st["color"], ls=st["ls"], lw=2.6, label=st["label"])
        (mk,) = axA.plot([], [], color=st["color"], ls="none", marker=st["marker"], ms=7)
        linesA[k] = (ln, mk)
    axA.legend(loc="upper left", fontsize=11, frameon=True, ncol=1)
    axA.text(12.2, 1.0, "shape read off Fig. 2b; peaks = Table 3", fontsize=10, ha="right",
             va="bottom", color="#555")
    curA = axA.axvline(1, color="#888", lw=1)

    axB.set_title("B  Attention share on A  (Prop. 1 model)", loc="left", weight="bold")
    axB.set_xlim(0.7, 12.3)
    axB.set_ylim(0, 1.05)
    axB.set_xlabel("Agent turn t")
    axB.set_ylabel("|A| / (|A| + |B_t|)")
    axB.grid(alpha=0.3)
    linesB = {}
    for k in KV:
        st = KV_STYLE[k]
        (ln,) = axB.plot([], [], color=st["color"], ls=st["ls"], lw=2.6, label=st["label"])
        linesB[k] = ln
    axB.text(12.2, 1.0, "equal per-token logits; computed from panel A\n"
             "paper (90-run expt, Sec. 3.1): dilution 0.72 -> 0.06",
             fontsize=10, ha="right", va="top", color="#555")
    curB = axB.axvline(1, color="#888", lw=1)

    axC.set_title("C  Ablation, 129 tasks  (Table 2, measured)", loc="left", weight="bold")
    axC.set_xlim(-0.4, 6.4)
    axC.set_ylim(0, 75)
    axC.set_xticks(range(7))
    axC.set_xticklabels(T2_MOD)
    axC.set_ylabel("% of 129 tasks / episodes")
    axC.grid(alpha=0.3, axis="y")
    axC.axhline(T1_CEILING, color="#0b7a55", ls="--", lw=1.6)
    axC.text(6.35, T1_CEILING + 1.2, "Stage-1 isolated ceiling 39.5% (Table 1)", color="#0b7a55",
             fontsize=10.5, ha="right")
    barsC = axC.bar(range(7), np.zeros(7), color="#1f5fd6", width=0.55, label="Solved (%)")
    (lnC,) = axC.plot([], [], color="#e67e22", marker="D", lw=2.4, label="Compaction (>14.3k, %)")
    axC.legend(loc="upper right", bbox_to_anchor=(1.0, 0.88), fontsize=11)
    txtC = [axC.text(i, 0, "", ha="center", va="bottom", fontsize=11, weight="bold", color="#1f3c88")
            for i in range(7)]

    axD.set_title("D  Trap-25 recovery  (Table 3, measured)", loc="left", weight="bold")
    x = np.arange(4)
    axD.set_xlim(-0.6, 3.6)
    axD.set_ylim(0, 112)
    axD.set_xticks(x)
    axD.set_xticklabels(["baseline\nstatic", "naive\nsub-agent", "ccr_only", "ccr_adaptive"], fontsize=11.5)
    axD.set_ylabel("Escape rate (%)", color="#1f5fd6")
    axD.grid(alpha=0.3, axis="y")
    axD2 = axD.twinx()
    axD2.set_ylim(0, 224)
    axD2.set_ylabel("Active post-reset KV (k tokens)", color="#b9661c")
    axD2.spines["right"].set_visible(True)
    barsD = axD.bar(x - 0.19, np.zeros(4), width=0.36, color="#1f5fd6")
    barsD2 = axD2.bar(x + 0.19, np.zeros(4), width=0.36, color="#e59a3c")
    txtD = [axD.text(i - 0.19, 0, "", ha="center", va="bottom", fontsize=11, weight="bold", color="#1f3c88")
            for i in range(4)]
    return dict(linesA=linesA, curA=curA, linesB=linesB, curB=curB, barsC=barsC, lnC=lnC, txtC=txtC,
                barsD=barsD, barsD2=barsD2, txtD=txtD)


def partial_curve(y, turn):
    """Piecewise-linear curve revealed up to fractional turn."""
    xs = [t for t in TURNS if t <= turn]
    ys = list(y[: len(xs)])
    if turn > xs[-1] and turn < 12:
        xs = xs + [turn]
        ys = ys + [float(np.interp(turn, TURNS, y))]
    return np.array(xs, float), np.array(ys, float), len([t for t in TURNS if t <= turn])


def update(fig, ax_m, art, banner, frame):
    turn, module, config, seg = state_at(frame)
    draw_monitor(ax_m, turn, module, config, seg)
    for k in KV:
        xs, ys, n = partial_curve(KV[k] / 1e3, turn)
        art["linesA"][k][0].set_data(xs, ys)
        art["linesA"][k][1].set_data(TURNS[:n], KV[k][:n] / 1e3)
        xs, ys, _ = partial_curve(SHARE[k], turn)
        art["linesB"][k].set_data(xs, ys)
    art["curA"].set_xdata([turn, turn])
    art["curB"].set_xdata([turn, turn])

    # Act 2: bars grow module by module (each bar eases in over its slot)
    for i in range(7):
        g = float(np.clip(module - i + 1, 0, 1)) if module >= 0 else 0.0
        art["barsC"][i].set_height(T2_RATE[i] * g)
        art["txtC"][i].set_text(f"{T2_RATE[i]:.1f}%" if g >= 1 else "")
        art["txtC"][i].set_y(T2_RATE[i] * g + 0.8)
    nC = int(np.floor(module + 1e-9)) + 1 if module >= 0 else 0
    art["lnC"].set_data(np.arange(nC), T2_COMPACT[:nC])

    for i in range(4):
        g = float(np.clip(config - i + 1, 0, 1)) if config >= 0 else 0.0
        art["barsD"][i].set_height(T3_ESC[i] * g)
        art["barsD2"][i].set_height(T3_POSTKV[i] / 1e3 * g)
        art["txtD"][i].set_text(f"{T3_ESC[i]:.0f}%" if g >= 1 else "")
        art["txtD"][i].set_y(T3_ESC[i] * g + 1)
    banner.set_text(banner_at(frame))
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()


def make():
    fig, ax_m, axA, axB, axC, axD = build_figure()
    art = setup_panels(axA, axB, axC, axD)
    banner = fig.text(0.5, 0.055, "", ha="center", va="center", fontsize=16.5, color="white", weight="bold",
                      wrap=True,
                      bbox=dict(boxstyle="round,pad=0.7", fc="#1b2a41", ec="none"))
    return fig, ax_m, art, banner


def fmt(frame):
    s = frame / FPS
    return f"{int(s // 60):02d}:{int(s % 60):02d}"


def write_narration():
    lines = ["# Gemma 4 Loop-Breaker - Narration",
             "",
             f"Video: `{os.path.basename(OUT_MP4)}` ({N_FRAMES} frames at {FPS} fps = {N_FRAMES / FPS:.1f} s). "
             "Timestamps are computed from milestone frame indices in `make_explainer.py`.",
             "",
             "Data note: panel A (per-turn KV) uses illustrative curves read off Fig. 2b with the turn-12 peaks "
             "pinned to Table 3; panel B applies Proposition 1 to those curves under equal per-token logits. "
             "Panels C and D are the paper's measured Table 2 and Table 3 values.",
             ""]
    for f, b, n in MILESTONES:
        lines.append(f"**{fmt(f)}** (frame {f}) - {n}")
        lines.append("")
        lines.append(f"> On-screen banner: {b}")
        lines.append("")
    with open(OUT_NARR, "w") as fh:
        fh.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    fig, ax_m, art, banner = make()
    if args.preview:
        pv = os.path.join(HERE, "preview")
        os.makedirs(pv, exist_ok=True)
        picks = [MILESTONES[2][0], MILESTONES[3][0], MILESTONES[6][0], MILESTONES[8][0] + 30, N_FRAMES - 1]
        for f in picks:
            img = update(fig, ax_m, art, banner, f)
            p = os.path.join(pv, f"milestone_{f:04d}.png")
            plt.imsave(p, img)
            print(p, img.shape)
        return
    import imageio

    w = imageio.get_writer(OUT_MP4, fps=FPS, codec="libx264", pixelformat="yuv420p", quality=8,
                           macro_block_size=1)
    for f in range(N_FRAMES):
        w.append_data(update(fig, ax_m, art, banner, f))
        if f % 150 == 0:
            print(f"frame {f}/{N_FRAMES}", flush=True)
    w.close()
    write_narration()
    print("wrote", OUT_MP4, OUT_NARR)
    print("crossings", CROSS, "cut_postkv", CUT_POSTKV, "cut_compact", CUT_COMPACT)


if __name__ == "__main__":
    main()
