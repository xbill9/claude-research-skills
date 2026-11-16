"""SVG engine for the publishing-kit graphic story.

Six recurring characters, each a function returning a Figure (SVG group, face box, tail anchor):
  robot      KIT        the publishing skill and its scripts (the system)
  monster    MANGLER    the destinations' undocumented rewrites (the failure)
  scientist  AUTHOR     the writer narrating (researcher narrator)
  sergeant   MANUAL     the by-hand checklist across four files (rigid baseline)
  explorer   SCOUT      fetch what the destination serves, compare to disk (adaptive method)
  gatekeeper PREFLIGHT  preflight.py --live, exits non-zero (threshold detector)

Text is measured with PIL using the same Lato TTF the page declares, so bubble sizes are computed.
Every Page records the boxes of faces, boards, charts, tables, captions and bubbles; Page.check()
reports any bubble or caption overlapping a face or another box, any tail crossing a face or box,
and anything outside its panel or the page.
"""

from __future__ import annotations

import html
import math
from dataclasses import dataclass, field
from functools import lru_cache

from PIL import ImageFont

FONTS = {
    "regular": "/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
    "bold": "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
    "black": "/usr/share/fonts/truetype/lato/Lato-Black.ttf",
    "italic": "/usr/share/fonts/truetype/lato/Lato-Italic.ttf",
    "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
}
FAMILY = {"regular": "Lato", "bold": "Lato", "black": "Lato", "italic": "Lato", "mono": "DejaVu Sans Mono"}
WEIGHT = {"regular": 400, "bold": 700, "black": 900, "italic": 400, "mono": 400}
FSTYLE = {"italic": "italic"}

PAGE_W, PAGE_H = 794, 1123  # A4 at 96 px per inch
INK = "#22252e"
C = {
    "paper": "#fbf8f1", "panel": "#ffffff", "caption": "#ffe9a8", "board": "#1f3b33", "chalk": "#eef6ee",
    "kit": "#3d7ea6", "kit_dark": "#24536f", "screen": "#0f2230", "led": "#7ff0c5",
    "mangler": "#8e3fa3", "mangler_dark": "#5a2268", "tooth": "#fffaf0",
    "skin": "#f0c7a2", "skin2": "#c98f62", "hair": "#3b2b22", "hoodie": "#e07b39",
    "sergeant": "#6a7440", "sergeant_dark": "#454d27",
    "scout": "#c99b4f", "scout_dark": "#8b6a2e",
    "gate": "#c23b3b", "gate_dark": "#7e2222",
    "good": "#2f9e6b", "bad": "#c6403a", "warn": "#e2a321", "muted": "#8b93a5",
    "devto": "#0a0a0a", "builder": "#ff9900", "medium": "#2b2b2b", "linkedin": "#0a66c2",
}


def esc(s) -> str:
    return html.escape(str(s), quote=False)


@lru_cache(maxsize=None)
def _font(style: str, size: float):
    return ImageFont.truetype(FONTS[style], int(round(size * 4)))


def text_width(s: str, size: float, style: str = "regular") -> float:
    return _font(style, size).getlength(s) / 4.0


def wrap(s: str, width: float, size: float, style: str = "regular") -> list[str]:
    out: list[str] = []
    for para in s.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = f"{cur} {word}".strip()
            if not cur or text_width(trial, size, style) <= width:
                cur = trial
            else:
                out.append(cur)
                cur = word
        out.append(cur)
    return out


def text(lines, x, y, size, style="regular", fill=INK, anchor="start", lh=1.25) -> str:
    if isinstance(lines, str):
        lines = [lines]
    fs = f' font-style="{FSTYLE[style]}"' if style in FSTYLE else ""
    parts = [
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FAMILY[style]}" font-weight="{WEIGHT[style]}"{fs} '
        f'font-size="{size}" fill="{fill}" text-anchor="{anchor}">'
    ]
    for i, ln in enumerate(lines):
        dy = "0" if i == 0 else f"{size * lh:.2f}"
        parts.append(f'<tspan x="{x:.1f}" dy="{dy}">{esc(ln)}</tspan>')
    parts.append("</text>")
    return "".join(parts)


Box = tuple[float, float, float, float]  # x0, y0, x1, y1


def _inter(a: Box, b: Box, pad: float = 0) -> bool:
    return a[0] < b[2] + pad and b[0] < a[2] + pad and a[1] < b[3] + pad and b[1] < a[3] + pad


def _seg_hits_box(p, q, b: Box) -> bool:
    for i in range(1, 40):
        t = i / 40
        x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        if b[0] < x < b[2] and b[1] < y < b[3]:
            return True
    return False


@dataclass
class Figure:
    svg: str
    face: Box
    anchor: tuple[float, float]  # where a speech tail ends: just outside the head
    body: Box
    name: str


@dataclass
class Item:
    kind: str  # face, body, board, chart, table, caption, bubble, art
    box: Box
    label: str
    panel: int
    tail: tuple | None = None


@dataclass
class Page:
    title: str
    subtitle: str
    sources: str
    svg: list[str] = field(default_factory=list)
    html: list[str] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)
    panels: list[Box] = field(default_factory=list)

    TOP = 92
    BOTTOM = PAGE_H - 46
    MARGIN = 26

    # ---- panels --------------------------------------------------------------------------------
    def panel(self, x, y, w, h, bg=None) -> int:
        self.panels.append((x, y, x + w, y + h))
        idx = len(self.panels) - 1
        self.svg.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{bg or C["panel"]}" '
            f'stroke="{INK}" stroke-width="2.6"/>'
        )
        return idx

    def add(self, kind, box, label, panel, svg="", tail=None):
        if svg:
            self.svg.append(svg)
        self.items.append(Item(kind, box, label, panel, tail))

    def put(self, fig: Figure, panel: int):
        self.svg.append(fig.svg)
        self.items.append(Item("face", fig.face, fig.name + " face", panel))
        self.items.append(Item("body", fig.body, fig.name + " body", panel))

    # ---- text furniture ------------------------------------------------------------------------
    def bubble(self, panel, txt, x, y, w, to: Figure | None = None, size=12.0, kind="speech", style="regular"):
        pad = 9
        lines = wrap(txt, w - 2 * pad, size, style)
        bw = max(text_width(ln, size, style) for ln in lines) + 2 * pad
        bh = len(lines) * size * 1.25 + 2 * pad - size * 0.25
        box = (x, y, x + bw, y + bh)
        out = []
        tail = None
        if to is not None:
            f = to.face
            if y + bh <= f[1]:
                ax, ay = to.anchor
            elif x >= f[2]:
                ax, ay = f[2] + 6, f[1] + (f[3] - f[1]) * 0.55
            elif x + bw <= f[0]:
                ax, ay = f[0] - 6, f[1] + (f[3] - f[1]) * 0.55
            else:
                ax, ay = to.anchor
            # base of the tail: nearest point on the bubble edge toward the anchor
            cx, cy = x + bw / 2, y + bh / 2
            if ay > y + bh:
                bx, by = min(max(ax, x + 18), x + bw - 18), y + bh
                base = [(bx - 8, by - 1), (bx + 8, by - 1)]
            elif ay < y:
                bx, by = min(max(ax, x + 18), x + bw - 18), y
                base = [(bx - 8, by + 1), (bx + 8, by + 1)]
            elif ax > x + bw:
                bx, by = x + bw, min(max(ay, y + 12), y + bh - 12)
                base = [(bx - 1, by - 7), (bx - 1, by + 7)]
            else:
                bx, by = x, min(max(ay, y + 12), y + bh - 12)
                base = [(bx + 1, by - 7), (bx + 1, by + 7)]
            tail = ((bx, by), (ax, ay))
            if kind == "thought":
                for i, t in enumerate((0.45, 0.75)):
                    px, py = bx + (ax - bx) * t, by + (ay - by) * t
                    out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{4 - i * 1.4:.1f}" fill="#fff" '
                               f'stroke="{INK}" stroke-width="1.6"/>')
            else:
                pts = f"{base[0][0]:.1f},{base[0][1]:.1f} {ax:.1f},{ay:.1f} {base[1][0]:.1f},{base[1][1]:.1f}"
                out.append(f'<polygon points="{pts}" fill="#fff" stroke="{INK}" stroke-width="1.8" '
                           f'stroke-linejoin="round"/>')
        rx = bh / 2 if kind == "thought" else 12
        dash = ' stroke-dasharray="5 3"' if kind == "whisper" else ""
        out.insert(0, f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="{min(rx, 18):.1f}" '
                      f'fill="#fff" stroke="{INK}" stroke-width="1.8"{dash}/>')
        if tail and kind != "thought":  # hide the seam where tail meets bubble
            (b0, b1) = base
            out.append(f'<line x1="{b0[0]:.1f}" y1="{b0[1]:.1f}" x2="{b1[0]:.1f}" y2="{b1[1]:.1f}" '
                       f'stroke="#fff" stroke-width="3"/>')
        out.append(text(lines, x + pad, y + pad + size * 0.82, size, style))
        self.add("bubble", box, txt[:40], panel, "".join(out), tail)
        return box

    def caption(self, panel, txt, x, y, w, size=11.0, style="bold", fill=None, max_w=None):
        pad = 7
        lines = wrap(txt, w - 2 * pad, size, style)
        bw = max(text_width(ln, size, style) for ln in lines) + 2 * pad if max_w is None else w
        bh = len(lines) * size * 1.25 + 2 * pad - size * 0.25
        svg = (f'<rect x="{x}" y="{y}" width="{bw:.1f}" height="{bh:.1f}" fill="{fill or C["caption"]}" '
               f'stroke="{INK}" stroke-width="1.6"/>' + text(lines, x + pad, y + pad + size * 0.82, size, style))
        box = (x, y, x + bw, y + bh)
        self.add("caption", box, txt[:40], panel, svg)
        return box

    def note(self, panel, txt, x, y, w, size=9.0, fill="#555b6b", style="italic"):
        """Small caveat line (no box). Registered so bubbles cannot cover it."""
        lines = wrap(txt, w, size, style)
        bw = max(text_width(ln, size, style) for ln in lines)
        bh = len(lines) * size * 1.25
        box = (x, y, x + bw, y + bh)
        self.add("caption", box, txt[:40], panel, text(lines, x, y + size * 0.85, size, style, fill=fill))
        return box

    def html_box(self, panel, x, y, w, h, inner, label, kind="table"):
        self.html.append(f'<div class="hbox" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">{inner}</div>')
        self.items.append(Item(kind, (x, y, x + w, y + h), label, panel))

    # ---- QA ------------------------------------------------------------------------------------
    def check(self) -> list[str]:
        errs = []
        page_box = (0, 0, PAGE_W, PAGE_H)
        for pb in self.panels:
            if pb[0] < self.MARGIN - 1 or pb[2] > PAGE_W - self.MARGIN + 1 or pb[1] < self.TOP - 1 or \
                    pb[3] > self.BOTTOM + 1:
                errs.append(f"panel {pb} leaves the page body")
        for i, a in enumerate(self.panels):
            for b in self.panels[i + 1:]:
                if _inter(a, b):
                    errs.append(f"panels {a} and {b} overlap")
        for it in self.items:
            pb = self.panels[it.panel] if it.panel is not None and it.panel >= 0 else page_box
            if it.kind in ("bubble", "caption", "table", "board", "chart", "face"):
                if it.box[0] < pb[0] + 2 or it.box[1] < pb[1] + 2 or it.box[2] > pb[2] - 2 or it.box[3] > pb[3] - 2:
                    errs.append(f"{it.kind} '{it.label}' sticks out of panel {it.panel}: {tuple(round(v) for v in it.box)}")
        movable = [it for it in self.items if it.kind in ("bubble", "caption")]
        for m in movable:
            for o in self.items:
                if o is m or o.kind == "art":
                    continue
                if _inter(m.box, o.box, pad=1):
                    errs.append(f"{m.kind} '{m.label}' overlaps {o.kind} '{o.label}'")
            if m.tail:
                for o in self.items:
                    if o is m or o.kind in ("body", "art"):
                        continue
                    if _seg_hits_box(m.tail[0], m.tail[1], o.box):
                        errs.append(f"tail of '{m.label}' crosses {o.kind} '{o.label}'")
        # deduplicate symmetric reports
        return sorted(set(errs))

    # ---- output --------------------------------------------------------------------------------
    def render(self) -> str:
        head = (
            text(self.title, self.MARGIN, 44, 27, "black", fill=INK)
            + text(self.subtitle, self.MARGIN, 70, 13, "italic", fill="#4a5163")
            + f'<line x1="{self.MARGIN}" y1="80" x2="{PAGE_W - self.MARGIN}" y2="80" stroke="{INK}" stroke-width="2"/>'
        )
        foot_lines = wrap("Sources: " + self.sources, PAGE_W - 2 * self.MARGIN, 8.6, "regular")
        foot = text(foot_lines, self.MARGIN, self.BOTTOM + 15, 8.6, "regular", fill="#5d6475", lh=1.3)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="pg" viewBox="0 0 {PAGE_W} {PAGE_H}" '
               f'width="{PAGE_W}" height="{PAGE_H}">'
               f'<rect width="{PAGE_W}" height="{PAGE_H}" fill="{C["paper"]}"/>' + head + "".join(self.svg) + foot
               + "</svg>")
        return f'<section class="page">{svg}{"".join(self.html)}</section>'


# ---- faces ---------------------------------------------------------------------------------------
def _eyes(cx, cy, dx, r, expr, color=INK):
    out = []
    for sx in (-1, 1):
        ex = cx + sx * dx
        if expr == "happy":
            out.append(f'<path d="M{ex - r:.1f},{cy + 1:.1f} Q{ex:.1f},{cy - r * 1.4:.1f} {ex + r:.1f},{cy + 1:.1f}" '
                       f'fill="none" stroke="{color}" stroke-width="{r * 0.55:.1f}" stroke-linecap="round"/>')
        elif expr == "shut":
            out.append(f'<line x1="{ex - r:.1f}" y1="{cy:.1f}" x2="{ex + r:.1f}" y2="{cy:.1f}" stroke="{color}" '
                       f'stroke-width="{r * 0.5:.1f}" stroke-linecap="round"/>')
        else:
            rr = r * (1.25 if expr == "surprised" else 1)
            out.append(f'<circle cx="{ex:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="{color}"/>')
            out.append(f'<circle cx="{ex + rr * 0.3:.1f}" cy="{cy - rr * 0.35:.1f}" r="{rr * 0.3:.1f}" fill="#fff"/>')
        # brows
        tilt = {"angry": 1, "stern": 1, "worried": -1, "surprised": 0}.get(expr)
        if tilt is not None:
            inner, outer = cy - r * 2.0 + tilt * r * 0.8, cy - r * 2.0 - tilt * r * 0.4
            if expr == "surprised":
                inner = outer = cy - r * 2.6
            x_in, x_out = ex - sx * r * 0.2, ex + sx * r * 1.3
            out.append(f'<line x1="{x_in:.1f}" y1="{inner:.1f}" x2="{x_out:.1f}" y2="{outer:.1f}" stroke="{color}" '
                       f'stroke-width="{r * 0.55:.1f}" stroke-linecap="round"/>')
    return "".join(out)


def _mouth(cx, cy, w, expr, color=INK):
    if expr in ("happy", "neutral"):
        depth = w * (0.45 if expr == "happy" else 0.12)
        return (f'<path d="M{cx - w / 2:.1f},{cy:.1f} Q{cx:.1f},{cy + depth:.1f} {cx + w / 2:.1f},{cy:.1f}" '
                f'fill="none" stroke="{color}" stroke-width="2.4" stroke-linecap="round"/>')
    if expr in ("worried", "angry", "stern"):
        depth = -w * (0.3 if expr != "stern" else 0.05)
        return (f'<path d="M{cx - w / 2:.1f},{cy + 3:.1f} Q{cx:.1f},{cy + depth:.1f} {cx + w / 2:.1f},{cy + 3:.1f}" '
                f'fill="none" stroke="{color}" stroke-width="2.4" stroke-linecap="round"/>')
    if expr == "surprised":
        return f'<ellipse cx="{cx:.1f}" cy="{cy + 2:.1f}" rx="{w * 0.18:.1f}" ry="{w * 0.24:.1f}" fill="{color}"/>'
    return ""


def _arm(x0, y0, angle, length, width, color, hand=None, side=1):
    """angle in degrees from straight down; positive swings outward (away from the body) on either side."""
    a = math.radians(angle)
    x1, y1 = x0 + side * length * math.sin(a), y0 + length * math.cos(a)
    h = hand or color
    return (f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{color}" stroke-width="{width:.1f}" '
            f'stroke-linecap="round"/><circle cx="{x1:.1f}" cy="{y1:.1f}" r="{width * 0.62:.1f}" fill="{h}" '
            f'stroke="{INK}" stroke-width="1.4"/>'), (x1, y1)


ARM_POSES = {  # (left angle, right angle) in degrees from straight down; positive swings outward
    "stand": (14, 14), "wave": (14, 145), "point": (14, 95), "cheer": (145, 145), "shrug": (60, 60),
    "think": (14, 125), "stop": (14, 120), "hold": (40, 14),
}


def _flip(svg: str, x: float, w: float, flip: bool) -> str:
    if not flip:
        return svg
    return f'<g transform="translate({2 * x + w:.1f},0) scale(-1,1)">{svg}</g>'


def _label_tag(cx, y, label, size):
    if not label:
        return ""
    w = text_width(label, size, "black") + 10
    return (f'<rect x="{cx - w / 2:.1f}" y="{y:.1f}" width="{w:.1f}" height="{size + 7:.1f}" rx="3" fill="#fff" '
            f'stroke="{INK}" stroke-width="1.2"/>' + text(label, cx, y + size + 1.5, size, "black", anchor="middle"))


def robot(x, y, s=1.0, expr="neutral", pose="stand", flip=False, label="KIT", screen=None) -> Figure:
    """The publishing skill. (x, y) is the top-left of a 100 x 160 box at scale s."""
    W = 100 * s
    cx = x + W / 2
    hx, hy, hw, hh = cx - 34 * s, y + 18 * s, 68 * s, 52 * s
    parts = [
        f'<line x1="{cx:.1f}" y1="{y + 4 * s:.1f}" x2="{cx:.1f}" y2="{hy:.1f}" stroke="{INK}" stroke-width="{2.4 * s:.1f}"/>',
        f'<circle cx="{cx:.1f}" cy="{y + 5 * s:.1f}" r="{5 * s:.1f}" fill="{C["led"]}" stroke="{INK}" stroke-width="1.5"/>',
        f'<rect x="{hx:.1f}" y="{hy:.1f}" width="{hw:.1f}" height="{hh:.1f}" rx="{10 * s:.1f}" fill="{C["kit"]}" '
        f'stroke="{INK}" stroke-width="2.4"/>',
        f'<rect x="{hx + 7 * s:.1f}" y="{hy + 7 * s:.1f}" width="{hw - 14 * s:.1f}" height="{hh - 14 * s:.1f}" '
        f'rx="{6 * s:.1f}" fill="{C["screen"]}"/>',
        _eyes(cx, hy + 22 * s, 13 * s, 4.6 * s, expr, color=C["led"]),
        _mouth(cx, hy + 34 * s, 16 * s, expr, color=C["led"]),
    ]
    by, bw, bh = hy + hh + 4 * s, 76 * s, 62 * s
    bx = cx - bw / 2
    la, ra = ARM_POSES.get(pose, ARM_POSES["stand"])
    arm_l, _ = _arm(bx + 4 * s, by + 12 * s, la, 40 * s, 10 * s, C["kit_dark"], side=-1)
    arm_r, _ = _arm(bx + bw - 4 * s, by + 12 * s, ra, 40 * s, 10 * s, C["kit_dark"], side=1)
    parts.insert(0, arm_l + arm_r)
    parts += [
        f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="{9 * s:.1f}" fill="{C["kit"]}" '
        f'stroke="{INK}" stroke-width="2.4"/>',
        f'<rect x="{cx - 24 * s:.1f}" y="{by + 32 * s:.1f}" width="{48 * s:.1f}" height="{20 * s:.1f}" rx="3" '
        f'fill="{C["screen"]}"/>',
    ]
    top = _label_tag(cx, by + 9 * s, label, 11 * s)
    if screen:
        top += text(screen, cx, by + 46 * s, 9.5 * s, "mono", fill=C["led"], anchor="middle")
    parts += [
        f'<rect x="{cx - 26 * s:.1f}" y="{by + bh:.1f}" width="{14 * s:.1f}" height="{18 * s:.1f}" fill="{C["kit_dark"]}" stroke="{INK}" stroke-width="1.6"/>',
        f'<rect x="{cx + 12 * s:.1f}" y="{by + bh:.1f}" width="{14 * s:.1f}" height="{18 * s:.1f}" fill="{C["kit_dark"]}" stroke="{INK}" stroke-width="1.6"/>',
    ]
    svg = _flip("".join(parts), x, W, flip) + top
    return Figure(svg, (hx, y, hx + hw, hy + hh), (cx, y - 6 * s), (bx - 30 * s, by, bx + bw + 30 * s, by + bh + 18 * s), "KIT")


def monster(x, y, s=1.0, expr="angry", label="MANGLER", flip=False, held=None) -> Figure:
    """The destinations' undocumented rewrites. 140 x 150 box at scale s."""
    W = 140 * s
    cx = x + W / 2
    body = (f'<path d="M{x + 12 * s:.1f},{y + 150 * s:.1f} C{x - 6 * s:.1f},{y + 70 * s:.1f} {x + 24 * s:.1f},{y + 8 * s:.1f} '
            f'{cx:.1f},{y + 8 * s:.1f} C{x + 116 * s:.1f},{y + 8 * s:.1f} {x + 146 * s:.1f},{y + 70 * s:.1f} '
            f'{x + 128 * s:.1f},{y + 150 * s:.1f} L{x + 108 * s:.1f},{y + 136 * s:.1f} L{x + 90 * s:.1f},{y + 150 * s:.1f} '
            f'L{cx:.1f},{y + 136 * s:.1f} L{x + 50 * s:.1f},{y + 150 * s:.1f} L{x + 32 * s:.1f},{y + 136 * s:.1f} Z" '
            f'fill="{C["mangler"]}" stroke="{INK}" stroke-width="2.6"/>')
    horns = (f'<path d="M{x + 34 * s:.1f},{y + 22 * s:.1f} L{x + 22 * s:.1f},{y - 6 * s:.1f} L{x + 48 * s:.1f},{y + 14 * s:.1f} Z" '
             f'fill="{C["mangler_dark"]}" stroke="{INK}" stroke-width="2"/>'
             f'<path d="M{x + 106 * s:.1f},{y + 22 * s:.1f} L{x + 118 * s:.1f},{y - 6 * s:.1f} L{x + 92 * s:.1f},{y + 14 * s:.1f} Z" '
             f'fill="{C["mangler_dark"]}" stroke="{INK}" stroke-width="2"/>')
    eye_y = y + 48 * s
    eyes = "".join(
        f'<circle cx="{cx + dx * s:.1f}" cy="{eye_y:.1f}" r="{12 * s:.1f}" fill="#fff" stroke="{INK}" stroke-width="2"/>'
        for dx in (-22, 22)) + _eyes(cx, eye_y + 1 * s, 22 * s, 5.5 * s, expr if expr != "happy" else "neutral")
    my = y + 80 * s
    teeth = "".join(
        f'<path d="M{cx + (i - 3) * 10 * s:.1f},{my:.1f} l{5 * s:.1f},{9 * s:.1f} l{5 * s:.1f},{-9 * s:.1f}" fill="{C["tooth"]}" '
        f'stroke="{INK}" stroke-width="1.2"/>' for i in range(6))
    mouth = (f'<path d="M{cx - 34 * s:.1f},{my:.1f} Q{cx:.1f},{my + 38 * s:.1f} {cx + 34 * s:.1f},{my:.1f} Z" '
             f'fill="{C["mangler_dark"]}" stroke="{INK}" stroke-width="2"/>' + teeth)
    extra = ""
    if held:
        extra = held
    svg = _flip(horns + body + eyes + mouth + extra, x, W, flip) + _label_tag(cx, y + 118 * s, label, 10 * s)
    face = (cx - 40 * s, y + 28 * s, cx + 40 * s, y + 104 * s)
    return Figure(svg, face, (cx, y - 12 * s), (x, y, x + W, y + 150 * s), "MANGLER")


def _human(x, y, s, expr, pose, flip, shirt, shirt_dark, hat, extra, label, name, skin=None, hair=True):
    W = 100 * s
    cx = x + W / 2
    hy = y + 44 * s
    skin = skin or C["skin"]
    torso_y = y + 76 * s
    la, ra = ARM_POSES.get(pose, ARM_POSES["stand"])
    arm_l, hl = _arm(cx - 26 * s, torso_y + 10 * s, la, 46 * s, 11 * s, shirt_dark, skin, side=-1)
    arm_r, hr = _arm(cx + 26 * s, torso_y + 10 * s, ra, 46 * s, 11 * s, shirt_dark, skin, side=1)
    parts = [
        f'<rect x="{cx - 20 * s:.1f}" y="{torso_y + 70 * s:.1f}" width="{15 * s:.1f}" height="{14 * s:.1f}" fill="{INK}"/>',
        f'<rect x="{cx + 5 * s:.1f}" y="{torso_y + 70 * s:.1f}" width="{15 * s:.1f}" height="{14 * s:.1f}" fill="{INK}"/>',
        arm_l, arm_r,
        f'<path d="M{cx - 30 * s:.1f},{torso_y + 72 * s:.1f} L{cx - 28 * s:.1f},{torso_y + 6 * s:.1f} '
        f'Q{cx:.1f},{torso_y - 6 * s:.1f} {cx + 28 * s:.1f},{torso_y + 6 * s:.1f} L{cx + 30 * s:.1f},{torso_y + 72 * s:.1f} Z" '
        f'fill="{shirt}" stroke="{INK}" stroke-width="2.4"/>',
        f'<circle cx="{cx:.1f}" cy="{hy:.1f}" r="{27 * s:.1f}" fill="{skin}" stroke="{INK}" stroke-width="2.4"/>',
    ]
    if hair:
        parts.append(f'<path d="M{cx - 27 * s:.1f},{hy - 2 * s:.1f} Q{cx - 24 * s:.1f},{hy - 34 * s:.1f} {cx:.1f},{hy - 28 * s:.1f} '
                     f'Q{cx + 26 * s:.1f},{hy - 34 * s:.1f} {cx + 27 * s:.1f},{hy - 4 * s:.1f} Q{cx + 8 * s:.1f},{hy - 18 * s:.1f} '
                     f'{cx - 27 * s:.1f},{hy - 2 * s:.1f} Z" fill="{C["hair"]}"/>')
    parts.append(_eyes(cx, hy + 2 * s, 10 * s, 3.3 * s, expr))
    parts.append(_mouth(cx, hy + 14 * s, 13 * s, expr))
    parts.append(hat(cx, hy, s))
    parts.append(extra(cx, hy, s, hl, hr))
    svg = _flip("".join(parts), x, W, flip) + _label_tag(cx, torso_y + 22 * s, label, 9.5 * s)
    face = (cx - 28 * s, hy - 30 * s, cx + 28 * s, hy + 28 * s)
    body = (cx - 60 * s, torso_y - 4 * s, cx + 60 * s, torso_y + 86 * s)
    return Figure(svg, face, (cx, hy - 40 * s), body, name)


def scientist(x, y, s=1.0, expr="neutral", pose="stand", flip=False, label="AUTHOR") -> Figure:
    def hat(cx, hy, s):
        return (f'<circle cx="{cx - 10 * s:.1f}" cy="{hy + 2 * s:.1f}" r="{7 * s:.1f}" fill="none" stroke="{INK}" stroke-width="1.6"/>'
                f'<circle cx="{cx + 10 * s:.1f}" cy="{hy + 2 * s:.1f}" r="{7 * s:.1f}" fill="none" stroke="{INK}" stroke-width="1.6"/>'
                f'<line x1="{cx - 3 * s:.1f}" y1="{hy + 2 * s:.1f}" x2="{cx + 3 * s:.1f}" y2="{hy + 2 * s:.1f}" stroke="{INK}" stroke-width="1.6"/>')

    def extra(cx, hy, s, hl, hr):
        return ""

    return _human(x, y, s, expr, pose, flip, C["hoodie"], "#b25a22", hat, extra, label, "AUTHOR")


def sergeant(x, y, s=1.0, expr="stern", pose="stand", flip=False, label="MANUAL") -> Figure:
    def hat(cx, hy, s):
        return (f'<path d="M{cx - 30 * s:.1f},{hy - 14 * s:.1f} L{cx - 22 * s:.1f},{hy - 34 * s:.1f} L{cx + 22 * s:.1f},{hy - 34 * s:.1f} '
                f'L{cx + 30 * s:.1f},{hy - 14 * s:.1f} Z" fill="{C["sergeant_dark"]}" stroke="{INK}" stroke-width="2"/>'
                f'<rect x="{cx - 34 * s:.1f}" y="{hy - 16 * s:.1f}" width="{68 * s:.1f}" height="{6 * s:.1f}" rx="2" fill="{INK}"/>'
                f'<polygon points="{cx:.1f},{hy - 30 * s:.1f} {cx + 4 * s:.1f},{hy - 22 * s:.1f} {cx - 4 * s:.1f},{hy - 22 * s:.1f}" fill="{C["warn"]}"/>')

    def extra(cx, hy, s, hl, hr):
        # clipboard in the left hand
        x0, y0 = hl[0] - 26 * s, hl[1] - 26 * s
        return (f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{30 * s:.1f}" height="{38 * s:.1f}" rx="2" fill="#f6efe0" stroke="{INK}" stroke-width="1.6"/>'
                + "".join(f'<line x1="{x0 + 5 * s:.1f}" y1="{y0 + (10 + 7 * i) * s:.1f}" x2="{x0 + 25 * s:.1f}" '
                          f'y2="{y0 + (10 + 7 * i) * s:.1f}" stroke="{C["muted"]}" stroke-width="1.4"/>' for i in range(4)))

    return _human(x, y, s, expr, pose, flip, C["sergeant"], C["sergeant_dark"], hat, extra, label, "MANUAL", hair=False)


def explorer(x, y, s=1.0, expr="happy", pose="stand", flip=False, label="SCOUT") -> Figure:
    def hat(cx, hy, s):
        return (f'<ellipse cx="{cx:.1f}" cy="{hy - 18 * s:.1f}" rx="{40 * s:.1f}" ry="{8 * s:.1f}" fill="{C["scout"]}" stroke="{INK}" stroke-width="2"/>'
                f'<path d="M{cx - 26 * s:.1f},{hy - 18 * s:.1f} Q{cx:.1f},{hy - 52 * s:.1f} {cx + 26 * s:.1f},{hy - 18 * s:.1f} Z" '
                f'fill="{C["scout"]}" stroke="{INK}" stroke-width="2"/>'
                f'<rect x="{cx - 25 * s:.1f}" y="{hy - 24 * s:.1f}" width="{50 * s:.1f}" height="{5 * s:.1f}" fill="{C["scout_dark"]}"/>')

    def extra(cx, hy, s, hl, hr):
        # magnifying glass in the right hand
        gx, gy = hr[0] + 12 * s, hr[1] - 12 * s
        return (f'<line x1="{hr[0]:.1f}" y1="{hr[1]:.1f}" x2="{gx:.1f}" y2="{gy:.1f}" stroke="{INK}" stroke-width="{4 * s:.1f}"/>'
                f'<circle cx="{gx + 6 * s:.1f}" cy="{gy - 8 * s:.1f}" r="{11 * s:.1f}" fill="#d9f1ff" fill-opacity="0.8" '
                f'stroke="{INK}" stroke-width="{3 * s:.1f}"/>')

    return _human(x, y, s, expr, pose, flip, "#5f8f6a", "#3e6447", hat, extra, label, "SCOUT")


def gatekeeper(x, y, s=1.0, expr="stern", pose="stop", flip=False, label="PREFLIGHT", lamp="red") -> Figure:
    def hat(cx, hy, s):
        return (f'<path d="M{cx - 28 * s:.1f},{hy - 12 * s:.1f} Q{cx:.1f},{hy - 50 * s:.1f} {cx + 28 * s:.1f},{hy - 12 * s:.1f} Z" '
                f'fill="{C["gate_dark"]}" stroke="{INK}" stroke-width="2"/>'
                f'<path d="M{cx - 4 * s:.1f},{hy - 14 * s:.1f} L{cx + 36 * s:.1f},{hy - 10 * s:.1f} L{cx - 4 * s:.1f},{hy - 6 * s:.1f} Z" '
                f'fill="{INK}"/>')

    def extra(cx, hy, s, hl, hr):
        col = {"red": C["bad"], "green": C["good"]}[lamp]
        return (f'<line x1="{hr[0]:.1f}" y1="{hr[1]:.1f}" x2="{hr[0] + 14 * s:.1f}" y2="{hr[1] - 22 * s:.1f}" stroke="{INK}" stroke-width="{3.5 * s:.1f}"/>'
                f'<circle cx="{hr[0] + 18 * s:.1f}" cy="{hr[1] - 32 * s:.1f}" r="{12 * s:.1f}" fill="{col}" stroke="{INK}" stroke-width="2"/>')

    return _human(x, y, s, expr, pose, flip, C["gate"], C["gate_dark"], hat, extra, label, "PREFLIGHT",
                  skin=C["skin2"], hair=False)


# ---- props ---------------------------------------------------------------------------------------
def blackboard(page: Page, panel, x, y, w, h, rows, title=None, size=11.5, label="board"):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{C["board"]}" stroke="#6b4a2b" stroke-width="6"/>']
    ty = y + 22
    if title:
        out.append(text(title, x + 14, ty, size + 2, "bold", fill=C["warn"]))
        ty += size * 1.7
    for row in rows:
        style = "mono" if row.startswith("$ ") or row.startswith("  ") else "regular"
        lines = wrap(row, w - 28, size, style)
        out.append(text(lines, x + 14, ty, size, style, fill=C["chalk"]))
        ty += len(lines) * size * 1.3 + 3
    if ty - size > y + h - 6:
        raise ValueError(f"blackboard '{label}' overflows: needs {ty - size - y:.0f} of {h}")
    page.add("board", (x, y, x + w, y + h), label, panel, "".join(out))


def box(page: Page, panel, x, y, w, h, txt, fill="#eef4fb", size=11, style="bold", stroke=INK, label=None, color=INK):
    lines = wrap(txt, w - 10, size, style)
    th = len(lines) * size * 1.2
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
           + text(lines, x + w / 2, y + h / 2 - th / 2 + size * 0.85, size, style, anchor="middle", fill=color, lh=1.2))
    if th > h - 4:
        raise ValueError(f"box text overflows: {txt}")
    page.add("board", (x, y, x + w, y + h), label or txt[:30], panel, out)


def arrow(page: Page, x1, y1, x2, y2, color=INK, width=2.4):
    a = math.atan2(y2 - y1, x2 - x1)
    hx1, hy1 = x2 - 10 * math.cos(a - 0.4), y2 - 10 * math.sin(a - 0.4)
    hx2, hy2 = x2 - 10 * math.cos(a + 0.4), y2 - 10 * math.sin(a + 0.4)
    page.svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"/>'
                    f'<polygon points="{x2:.1f},{y2:.1f} {hx1:.1f},{hy1:.1f} {hx2:.1f},{hy2:.1f}" fill="{color}"/>')


def diamond(page: Page, panel, cx, cy, w, h, txt, size=11, fill="#fff3d0"):
    lines = wrap(txt, w * 0.62, size, "bold")
    th = len(lines) * size * 1.2
    out = (f'<polygon points="{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} {cx - w / 2},{cy}" fill="{fill}" '
           f'stroke="{INK}" stroke-width="2.2"/>' + text(lines, cx, cy - th / 2 + size * 0.85, size, "bold", anchor="middle", lh=1.2))
    page.add("board", (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), txt[:30], panel, out)


def sfx(page: Page, txt, x, y, size=24, color=None, rotate=-7):
    page.svg.append(f'<g transform="rotate({rotate} {x} {y})">'
                    + text(txt, x, y, size, "black", fill=color or C["bad"]) + "</g>")
