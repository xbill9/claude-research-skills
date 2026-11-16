"""Overlay numbered badges and shaded regions on the article's figures.

Coordinates are source pixels (Read shows these images at native size). Output keeps native pixel
scale: figsize = pixels / DPI at DPI = 100, bbox_inches=None, so annotated coordinates equal source
coordinates plus any padding. Numbers in labels come from work/measurements.json.

usage: python3 annotate_figures.py <paper_dir> <measurements.json> <out_dir>
"""
import json, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image

P, M, OUT = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)
DPI = 100
K = 1.0  # text scale; raised for composites that are shown smaller on the page
ROSE, GREEN, INK, BLUE, ORANGE, GREY = "#e11d48", "#16a34a", "#111827", "#3b82f6", "#ea580c", "#6b7280"

def badge(ax, x, y, n, fc=INK, ec="white"):
    ax.text(x, y, str(n), ha="center", va="center", fontsize=13 * K, fontweight="bold", color="white",
            bbox=dict(boxstyle="circle,pad=0.3", fc=fc, ec=ec, lw=2 * K), zorder=10)

def note(ax, x, y, s, color="#e5e7eb", ha="left", size=10.5):
    ax.text(x, y, s, ha=ha, va="center", fontsize=size * K, color=color, zorder=9)

def shade(ax, x0, y0, x1, y1, color, label=None, lc=None, ly=None):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=color, alpha=0.16, ec=color, lw=1.2, ls="--", zorder=5))
    if label:
        ax.text(x0 + 10, ly if ly is not None else y0 + 14, label, color=lc or color, fontsize=10 * K, fontweight="bold",
                va="center", zorder=6)

def canvas(img, pad=(0, 0, 0, 0), bg="#1c1c1c"):
    """pad = (left, top, right, bottom) in pixels."""
    w, h = img.size; l, t, r, b = pad
    W, H = w + l + r, h + t + b
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=bg)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(bg)
    ax.imshow(img, extent=(0, w, h, 0)); ax.set_xlim(-l, w + r); ax.set_ylim(h + b, -t); ax.axis("off")
    return fig, ax

def save(fig, name):
    fig.savefig(OUT / name, dpi=DPI, facecolor=fig.get_facecolor()); plt.close(fig); print("wrote", OUT / name)

def load(f):
    return Image.open(P / f).convert("RGB")

# Fig 1: current dev.to cover
def fig1():
    f = "cover.ae4d639e.jpg"; fig, ax = canvas(load(f))
    ep = M["endpoints"][f]
    badge(ax, 185, 168, 1); note(ax, 212, 168, "source file")
    b, o, g = ep[0], ep[1:4], ep[4]
    badge(ax, b["cx"] + 70, b["cy"], 2, BLUE)
    ax.plot([o[0]["cx"] + 50] * 2, [o[0]["cy"] - 20, o[-1]["cy"] + 20], color=ORANGE, lw=2, zorder=8)
    for e in o:
        ax.plot([o[0]["cx"] + 42, o[0]["cx"] + 50], [e["cy"]] * 2, color=ORANGE, lw=2, zorder=8)
    badge(ax, o[0]["cx"] + 80, o[1]["cy"], 3, ORANGE)
    badge(ax, g["cx"] + 70, g["cy"], 4, GREY)
    badge(ax, 1290, 545, 5, ROSE); note(ax, 1262, 545, f"{len(ep)} endpoints", ha="right")
    badge(ax, 40, 40, 6); note(ax, 66, 40, "no text in frame (1376x578)")
    save(fig, "fig1_cover_current_annotated.png")

# Fig 2: previous dev.to cover (text version)
def fig2():
    f = "cover.77acc7c4.jpg"; ink = M["ink_320"]; fig, ax = canvas(load(f))
    k = lambda s: next(v for n, v in ink.items() if n.startswith(s))
    badge(ax, 475, 43, 1); note(ax, 500, 43, f"{k('kicker')['at_320_px']} px at 320", color="#fda4af")
    badge(ax, 790, 88, 2, ROSE); note(ax, 815, 88, "four", color="#fda4af")
    badge(ax, 830, 228, 3)
    badge(ax, 100, 318, 4, BLUE)
    badge(ax, 230, 433, 5); note(ax, 255, 433, f"{k('card label')['at_320_px']} px at 320", color="#fda4af")
    badge(ax, 1335, 557, 6); note(ax, 1310, 557, f"{k('footer')['at_320_px']} px at 320", color="#fda4af", ha="right")
    save(fig, "fig2_cover_previous_annotated.png")

# Fig 3: Builder Center covers, previous and current, side by side
def fig3():
    global K; K = 2.0
    a, b = load("cover-builder.80aa6ca5.jpg"), load("cover-builder.cabd79f3.jpg")
    gap = 40; w, h = a.size
    combo = Image.new("RGB", (2 * w + gap, h), (255, 255, 255)); combo.paste(a, (0, 0)); combo.paste(b, (w + gap, 0))
    fig, ax = canvas(combo, pad=(0, 70, 0, 0), bg="white")
    crop = M["devto_crop"]["1200x675 (builder covers)"]["lost_each_edge_rows"]
    for x0 in (0, w + gap):
        shade(ax, x0, 0, x0 + w, crop, ROSE)
        shade(ax, x0, h - crop, x0 + w, h, ROSE)
    note(ax, 10, h - crop / 2, f"dev.to 1000x420 crop drops {crop} rows top and bottom (computed)",
         color="#fecdd3", size=10)
    note(ax, 0, -35, "cover-builder.80aa6ca5.jpg  (previous)", color=INK, size=12)
    note(ax, w + gap, -35, "cover-builder.cabd79f3.jpg  (current since 2026-10-05)", color=INK, size=12)
    badge(ax, 690, 162, 1, ROSE)
    badge(ax, 1150, 42, 2, ROSE)
    badge(ax, w + gap + 140, 215, 3)
    ep = M["endpoints"]["cover-builder.cabd79f3.jpg"]
    badge(ax, w + gap + ep[0]["cx"] + 95, ep[0]["cy"], 4, BLUE)
    save(fig, "fig3_builder_covers_annotated.png")

# Fig 4: LinkedIn and Advocu variants
def fig4():
    global K; K = 1.5
    li, ad = load("linkedin-devto-publishing-kit-cover.jpg"), load("advocu-devto-publishing-kit-cover.webp")
    gap = 40; W = max(li.size[0], ad.size[0]); H = li.size[1] + gap + ad.size[1]
    combo = Image.new("RGB", (W, H), (255, 255, 255)); combo.paste(li, (0, 0)); combo.paste(ad, (0, li.size[1] + gap))
    fig, ax = canvas(combo, pad=(0, 50, 0, 0), bg="white")
    note(ax, 0, -25, "linkedin-devto-publishing-kit-cover.jpg  (1200x627)", color=INK, size=12)
    note(ax, 0, li.size[1] + gap / 2, "advocu-devto-publishing-kit-cover.webp  (1376x578)", color=INK, size=12)
    badge(ax, 1110, 60, 1, ROSE); note(ax, 1075, 60, "1.914:1", ha="right")
    e = M["endpoints"]["linkedin-devto-publishing-kit-cover.jpg"]
    badge(ax, e[0]["cx"] + 80, e[0]["cy"], 2)
    y0 = li.size[1] + gap
    badge(ax, 1300, y0 + 50, 3, GREEN); note(ax, 1262, y0 + 50, "WebP of cover.ae4d639e.jpg", ha="right")
    save(fig, "fig4_variants_annotated.png")

# Fig 5: the rendered table
def fig5():
    global K; K = 1.0
    f = "medium/img/devto-publishing-kit-table-1.png"; img = load(f); w, h = img.size
    fig, ax = canvas(img, pad=(70, 0, 20, 0), bg="white")
    shade(ax, 0, 63, w, 116, GREEN); shade(ax, 0, 118, w, h - 1, ROSE)
    badge(ax, -35, 32, 1, "#1e3a8a")
    badge(ax, 765, 35, 2, ROSE)
    badge(ax, -35, 90, 3, GREEN)
    badge(ax, -35, 143, 4, ROSE)
    save(fig, "fig5_table_annotated.png")

for fn in (fig1, fig2, fig3, fig4, fig5):
    fn()
