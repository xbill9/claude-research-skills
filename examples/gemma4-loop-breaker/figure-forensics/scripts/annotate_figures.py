"""Overlay numbered callout badges and shaded regimes on the paper's three 300-DPI figures.

Coordinates are in original-image pixels. They were picked by eye on the displayed image
(displayed width 2576 -> original 3180, factor 3180/2576) and checked by re-rendering.
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image

SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
S = 3180 / 2576  # displayed -> original pixels
ROSE, GREEN = "#e11d48", "#16a34a"

def badge(ax, x, y, n, color="#111827"):
    ax.text(x * S, y * S, str(n), ha="center", va="center", fontsize=12, fontweight="bold", color="white",
            bbox=dict(boxstyle="circle,pad=0.28", fc=color, ec="white", lw=2.5), zorder=10)

def shade(ax, x0, y0, x1, y1, color, label=None):
    ax.add_patch(Rectangle((x0 * S, y0 * S), (x1 - x0) * S, (y1 - y0) * S, fc=color, alpha=0.12, ec=color,
                           lw=1.2, ls="--", zorder=5))
    if label:
        ax.text(x0 * S + 8, y1 * S - 8, label, color=color, fontsize=9.5, fontweight="bold", va="bottom", zorder=6)

def figure(name, draw):
    im = Image.open(SRC / f"{name}.png").convert("RGB")
    w, h = im.size
    fig = plt.figure(figsize=(w / 300, h / 300), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(im); ax.set_xlim(0, w); ax.set_ylim(h, 0); ax.axis("off")
    draw(ax)
    fig.savefig(OUT / f"{name}_annotated.png", dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("wrote", OUT / f"{name}_annotated.png")

def fig1(ax):
    # boxes span y 190-665 (displayed); badges in empty bottom-right corner of each box
    for n, xl in enumerate([342, 837, 1332, 1827], start=1):
        badge(ax, xl + 40, 635, n)            # empty bottom-left corner inside each box
    badge(ax, 305, 708, 5, "#1e3a8a")         # left of the core-finding footer

def fig2(ax):
    # (b) rose: above the 14.3k ADK compaction cliff (y=492 displayed) within the plot box
    shade(ax, 1522, 112, 2498, 490, ROSE)
    # (b) green: below the cliff, where G-CCR keeps context
    shade(ax, 1522, 494, 2498, 770, GREEN)
    # (a) badges right of value labels
    badge(ax, 975, 163, 1, "#6b7280")          # M0
    badge(ax, 1080, 322, 2, ROSE)              # M2 17.1% vs Stage-1 39.5%
    badge(ax, 1175, 637, 3, "#1e3a8a")         # M6
    badge(ax, 1355, 717, 4, "#047857")         # Stage-1 ceiling
    # (b)
    badge(ax, 2540, 492, 5, "#c2410c")         # compaction cliff
    badge(ax, 1790, 735, 6, "#1d4ed8")         # sawtooth reset
    badge(ax, 2540, 168, 7, "#6b7280")         # naive sub-agent peak

def fig3(ax):
    shade(ax, 985, 110, 1180, 740, ROSE)       # httpx: n = 1
    shade(ax, 2122, 110, 2310, 740, GREEN)     # ccr_adaptive
    badge(ax, 370, 462, 1)                     # fastapi staircase
    badge(ax, 1088, 128, 2, ROSE)              # httpx n=1
    badge(ax, 1462, 555, 3, "#1d4ed8")         # baseline 16%
    badge(ax, 2085, 190, 4, "#047857")         # 96%
    badge(ax, 1885, 205, 5, "#c2410c")         # orange KV bars / right axis

figure("fig1_framework", fig1)
figure("fig2_ablation_sawtooth", fig2)
figure("fig3_trap25_domains", fig3)
