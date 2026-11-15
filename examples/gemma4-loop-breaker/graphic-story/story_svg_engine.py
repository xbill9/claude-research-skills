"""SVG drawing engine for the Loop-Breaker graphic story.

One function per recurring character (pose and expression are parameters), plus panels, speech
bubbles, captions, blackboards, bar charts and decision diamonds. Text is measured with PIL using
the same TTF that Chrome renders (Lato), so bubble sizes are exact rather than guessed.

Every Panel records the boxes of faces, bars, tables and bubbles; Panel.check() reports any bubble
that overlaps a face, a bar, another bubble or the panel edge.
"""
from __future__ import annotations

import html
from functools import lru_cache

from PIL import ImageFont

FONT_FILES = {
    "regular": "/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
    "bold": "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
    "black": "/usr/share/fonts/truetype/lato/Lato-Black.ttf",
    "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
}
FAMILY = {"regular": "Lato", "bold": "Lato", "black": "Lato", "mono": "DejaVu Sans Mono"}
WEIGHT = {"regular": 400, "bold": 700, "black": 900, "mono": 400}

INK = "#1f2430"
PAPER = "#fffdf6"
PALETTE = {
    "robot": "#4f7bd9", "robot_dark": "#2f4f9a", "screen": "#16233f",
    "monster": "#c2413b", "monster_dark": "#7d211d",
    "coat": "#f4f4f4", "skin": "#f2c9a0", "hair": "#5b3a29",
    "sergeant": "#5d6b3a", "sergeant_dark": "#3c4626",
    "explorer": "#c9a25a", "explorer_dark": "#8a6a2c",
    "gate": "#6c4fb3", "gate_dark": "#43307a",
    "good": "#2e9e6a", "bad": "#c2413b", "warn": "#e0a224", "muted": "#8a93a6",
    "caption": "#fff1b8", "board": "#23463a",
}


def esc(s) -> str:
    return html.escape(str(s), quote=True)


@lru_cache(maxsize=None)
def _font(style: str, size: float):
    return ImageFont.truetype(FONT_FILES[style], int(round(size * 4)))  # 4x for sub-pixel accuracy


def text_width(s: str, size: float, style: str = "regular") -> float:
    return _font(style, size).getlength(s) / 4.0


def wrap(s: str, width: float, size: float, style: str = "regular") -> list[str]:
    lines: list[str] = []
    for para in s.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = (cur + " " + word).strip()
            if text_width(trial, size, style) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def text_block(lines, x, y, size, style="regular", fill=INK, anchor="start", lh=1.25) -> str:
    out = []
    for i, ln in enumerate(lines):
        out.append(
            f'<text x="{x:.1f}" y="{y + size + i * size * lh:.1f}" font-family="{FAMILY[style]}" '
            f'font-weight="{WEIGHT[style]}" font-size="{size}" fill="{fill}" text-anchor="{anchor}">{esc(ln)}</text>'
        )
    return "".join(out)


def rich_line(parts, x, y, size, anchor="start") -> str:
    """One line of mixed styles: parts = [(text, style, fill), ...]."""
    total = sum(text_width(t, size, st) for t, st, _ in parts)
    cx = x - total / 2 if anchor == "middle" else x
    out = []
    for t, st, fill in parts:
        out.append(f'<text x="{cx:.1f}" y="{y + size:.1f}" font-family="{FAMILY[st]}" font-weight="{WEIGHT[st]}" '
                   f'font-size="{size}" fill="{fill}" xml:space="preserve">{esc(t)}</text>')
        cx += text_width(t, size, st)
    return "".join(out)


# ------------------------------------------------------------------------------------------------
# Panel: an SVG canvas that keeps a registry of boxes for overlap checks
# ------------------------------------------------------------------------------------------------
class Panel:
    def __init__(self, name: str, w: float, h: float, bg: str = PAPER):
        self.name, self.w, self.h = name, w, h
        self.parts: list[str] = [f'<rect x="0" y="0" width="{w}" height="{h}" fill="{bg}"/>']
        self.boxes: list[tuple[str, str, tuple[float, float, float, float]]] = []
        self.tails: list = []

    def add(self, svg: str, kind: str | None = None, box=None, label: str = ""):
        self.parts.append(svg)
        if kind:
            self.boxes.append((kind, label, box))
        return self

    def svg(self) -> str:
        border = f'<rect x="1.5" y="1.5" width="{self.w - 3}" height="{self.h - 3}" fill="none" stroke="{INK}" stroke-width="3"/>'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
                f'height="{self.h}">{"".join(self.parts)}{border}</svg>')

    def check(self) -> list[str]:
        probs = []

        def inter(a, b):
            return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])

        bubbles = [b for b in self.boxes if b[0] in ("bubble", "caption")]
        for i, (k, lab, bb) in enumerate(bubbles):
            if bb[0] < 2 or bb[1] < 2 or bb[2] > self.w - 2 or bb[3] > self.h - 2:
                probs.append(f"{self.name}: {k} '{lab}' leaves the panel {tuple(round(v) for v in bb)} in {self.w}x{self.h}")
            for k2, lab2, bb2 in self.boxes:
                if (k2, lab2, bb2) == (k, lab, bb):
                    continue
                if k2 in ("face", "bar", "table", "board", "chart") and inter(bb, bb2):
                    probs.append(f"{self.name}: {k} '{lab}' covers {k2} '{lab2}'")
            for k2, lab2, bb2 in bubbles[i + 1:]:
                if inter(bb, bb2):
                    probs.append(f"{self.name}: {k} '{lab}' overlaps {k2} '{lab2}'")
        for lab, (bx, by), (tx, ty), target in self.tails:
            for k2, lab2, bb2 in self.boxes:
                if (k2 == "bubble" and lab2 == lab) or (k2 == "face" and lab2 == target):
                    continue
                if k2 not in ("face", "bubble", "caption", "board", "chart", "bar"):
                    continue
                for i in range(1, 19):
                    f = i / 20
                    px, py = bx + (tx - bx) * f, by + (ty - by) * f
                    if bb2[0] < px < bb2[2] and bb2[1] < py < bb2[3]:
                        probs.append(f"{self.name}: tail of '{lab}' crosses {k2} '{lab2}'")
                        break
        return probs


# ------------------------------------------------------------------------------------------------
# Faces and characters. Each returns (svg_g, face_box, head_top_point). Feet at (x, y).
# ------------------------------------------------------------------------------------------------
def _eyes(cx, cy, dx, r, expr, color=INK):
    out = []
    for sx in (-1, 1):
        ex = cx + sx * dx
        if expr in ("happy", "proud"):
            out.append(f'<path d="M{ex - r * 1.3},{cy + r * .4} Q{ex},{cy - r * 1.6} {ex + r * 1.3},{cy + r * .4}" '
                       f'fill="none" stroke="{color}" stroke-width="{r * .7:.1f}" stroke-linecap="round"/>')
        elif expr in ("dizzy", "stuck"):
            out.append(f'<path d="M{ex - r},{cy - r} L{ex + r},{cy + r} M{ex + r},{cy - r} L{ex - r},{cy + r}" '
                       f'stroke="{color}" stroke-width="{r * .6:.1f}" stroke-linecap="round"/>')
        elif expr == "surprised":
            out.append(f'<circle cx="{ex}" cy="{cy}" r="{r * 1.25}" fill="#fff" stroke="{color}" stroke-width="{r * .4:.1f}"/>'
                       f'<circle cx="{ex}" cy="{cy}" r="{r * .55}" fill="{color}"/>')
        else:
            out.append(f'<circle cx="{ex}" cy="{cy}" r="{r}" fill="{color}"/>')
        if expr in ("worried", "stuck"):
            out.append(f'<path d="M{ex - r * 1.4},{cy - r * 2.2 - sx * r * .6} L{ex + r * 1.4},{cy - r * 2.2 + sx * r * .6}" '
                       f'stroke="{color}" stroke-width="{r * .5:.1f}" stroke-linecap="round"/>')
        if expr == "stern":
            out.append(f'<path d="M{ex - r * 1.5},{cy - r * 2.2 + sx * r * .5} L{ex + r * 1.5},{cy - r * 2.2 - sx * r * .5}" '
                       f'stroke="{color}" stroke-width="{r * .6:.1f}" stroke-linecap="round"/>')
    return "".join(out)


def _mouth(cx, cy, w, expr, color=INK):
    sw = max(1.6, w * .12)
    if expr in ("happy", "proud"):
        return f'<path d="M{cx - w / 2},{cy} Q{cx},{cy + w * .55} {cx + w / 2},{cy}" fill="none" stroke="{color}" stroke-width="{sw:.1f}" stroke-linecap="round"/>'
    if expr in ("worried", "sad"):
        return f'<path d="M{cx - w / 2},{cy + w * .25} Q{cx},{cy - w * .25} {cx + w / 2},{cy + w * .25}" fill="none" stroke="{color}" stroke-width="{sw:.1f}" stroke-linecap="round"/>'
    if expr in ("stuck", "dizzy"):
        pts = " ".join(f"{cx - w / 2 + i * w / 6:.1f},{cy + (w * .12 if i % 2 else -w * .12):.1f}" for i in range(7))
        return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{sw:.1f}" stroke-linejoin="round"/>'
    if expr == "surprised":
        return f'<ellipse cx="{cx}" cy="{cy + w * .1}" rx="{w * .2}" ry="{w * .28}" fill="{color}"/>'
    if expr == "stern":
        return f'<path d="M{cx - w / 2},{cy + w * .08} L{cx + w / 2},{cy + w * .08}" stroke="{color}" stroke-width="{sw * 1.3:.1f}" stroke-linecap="round"/>'
    return f'<path d="M{cx - w / 2.4},{cy + w * .05} Q{cx},{cy + w * .25} {cx + w / 2.4},{cy + w * .05}" fill="none" stroke="{color}" stroke-width="{sw:.1f}" stroke-linecap="round"/>'


def _arm(x0, y0, pose_angle_deg, length, width, color):
    import math
    a = math.radians(pose_angle_deg)
    x1, y1 = x0 + length * math.cos(a), y0 + length * math.sin(a)
    return (f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'
            f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="{width * .55:.1f}" fill="{color}" stroke="{INK}" stroke-width="1.5"/>'), (x1, y1)


ARM_ANGLES = {  # (left arm angle, right arm angle) in degrees, 90 = straight down; right side is +x
    "stand": (110, 70), "wave": (110, -60), "point": (110, -5), "point_left": (185, 70),
    "shrug": (200, -20), "cheer": (-120, -60), "slump": (100, 80), "present": (160, 20),
}


def _label(x, y, text, size, fill="#fff"):
    return text_block([text], x, y - size * .95, size, "black", fill, "middle")


def robot(x, y, s=1.0, expr="neutral", pose="stand", label="G4-31B", flip=False):
    """The agent: quantized Gemma 4 31B coding robot."""
    c, cd = PALETTE["robot"], PALETTE["robot_dark"]
    g = [f'<g transform="translate({x},{y}) scale({-s if flip else s},{s})">']
    g.append(f'<rect x="-20" y="-28" width="12" height="28" rx="3" fill="{cd}" stroke="{INK}" stroke-width="2"/>'
             f'<rect x="8" y="-28" width="12" height="28" rx="3" fill="{cd}" stroke="{INK}" stroke-width="2"/>')
    g.append(f'<rect x="-30" y="-78" width="60" height="52" rx="8" fill="{c}" stroke="{INK}" stroke-width="2.5"/>')
    g.append(f'<rect x="-24" y="-68" width="48" height="16" rx="3" fill="#dfe8ff" stroke="{INK}" stroke-width="1.5"/>')
    g.append(_label(0, -55, label, 9, cd))
    la, ra = ARM_ANGLES[pose]
    a1, _ = _arm(-30, -70, la, 30, 9, c)
    a2, _ = _arm(30, -70, ra, 30, 9, c)
    g.append(a1 + a2)
    g.append(f'<rect x="-6" y="-86" width="12" height="9" fill="{cd}" stroke="{INK}" stroke-width="2"/>')
    g.append(f'<rect x="-28" y="-128" width="56" height="44" rx="10" fill="#c9d4ea" stroke="{INK}" stroke-width="2.5"/>')
    g.append(f'<rect x="-21" y="-121" width="42" height="30" rx="6" fill="{PALETTE["screen"]}"/>')
    glow = "#7df9c1" if expr not in ("stuck", "dizzy", "worried") else "#ff8a7a"
    g.append(_eyes(0, -109, 9, 3.4, expr, glow))
    g.append(_mouth(0, -99, 14, expr, glow))
    bulb = PALETTE["bad"] if expr in ("stuck", "dizzy") else PALETTE["good"]
    g.append(f'<line x1="0" y1="-128" x2="0" y2="-140" stroke="{INK}" stroke-width="2.5"/>'
             f'<circle cx="0" cy="-143" r="5" fill="{bulb}" stroke="{INK}" stroke-width="2"/>')
    if expr in ("stuck", "dizzy"):
        g.append('<path d="M-36,-138 q6,-8 12,0 q6,8 12,0" fill="none" stroke="#c2413b" stroke-width="2"/>')
    g.append("</g>")
    face = (x - 28 * s, y - 128 * s, x + 28 * s, y - 84 * s)
    return "".join(g), face, (x, y - 150 * s)


def monster(x, y, s=1.0, expr="grin", label="LOOP", size_k=1.0):
    """The failure bottleneck: a pile of failed tracebacks that eats attention."""
    k = size_k
    c, cd = PALETTE["monster"], PALETTE["monster_dark"]
    g = [f'<g transform="translate({x},{y}) scale({s * k},{s * k})">']
    g.append(f'<path d="M-60,0 C-70,-40 -62,-95 -30,-118 C-10,-132 12,-132 32,-118 C64,-95 70,-40 60,0 '
             f'L45,-10 L32,0 L18,-10 L4,0 L-10,-10 L-24,0 L-38,-10 Z" fill="{c}" stroke="{INK}" stroke-width="3"/>')
    for i, t in enumerate(["Traceback", "AssertionError"]):
        g.append(f'<text x="{-30 + i * 2}" y="{-36 + i * 9}" font-family="DejaVu Sans Mono" font-size="7" fill="#ffd9d4" opacity=".9">{esc(t)}</text>')
    g.append(_eyes(0, -88, 18, 6, "surprised" if expr == "shrink" else "stern", INK))
    if expr == "grin":
        g.append(f'<path d="M-26,-62 Q0,-44 26,-62 L18,-60 L14,-54 L8,-58 L2,-52 L-4,-58 L-10,-53 L-15,-59 L-20,-55 Z" fill="#fff" stroke="{INK}" stroke-width="2"/>')
    else:
        g.append(_mouth(0, -62, 18, "surprised", INK))
    g.append(f'<path d="M-58,-60 q-22,-6 -26,-28" fill="none" stroke="{cd}" stroke-width="8" stroke-linecap="round"/>'
             f'<path d="M58,-60 q22,-6 26,-28" fill="none" stroke="{cd}" stroke-width="8" stroke-linecap="round"/>')
    g.append(_label(0, -16, label, 11, "#fff"))
    g.append("</g>")
    sk = s * k
    face = (x - 40 * sk, y - 120 * sk, x + 40 * sk, y - 48 * sk)
    return "".join(g), face, (x, y - 134 * sk)


def _human(x, y, s, expr, pose, flip, body_fill, body_dark, hat_svg, extra_svg, label, skin=None, coat_label_fill=None):
    skin = skin or PALETTE["skin"]
    g = [f'<g transform="translate({x},{y}) scale({-s if flip else s},{s})">']
    g.append(f'<rect x="-15" y="-34" width="11" height="34" rx="3" fill="{body_dark}" stroke="{INK}" stroke-width="2"/>'
             f'<rect x="4" y="-34" width="11" height="34" rx="3" fill="{body_dark}" stroke="{INK}" stroke-width="2"/>')
    g.append(f'<path d="M-24,-30 L-20,-82 Q0,-90 20,-82 L24,-30 Z" fill="{body_fill}" stroke="{INK}" stroke-width="2.5"/>')
    la, ra = ARM_ANGLES[pose]
    a1, _ = _arm(-20, -76, la, 30, 8, body_fill)
    a2, _ = _arm(20, -76, ra, 30, 8, body_fill)
    g.append(a1 + a2)
    if label:
        g.append(_label(0, -44, label, 8.5, coat_label_fill or INK))
    g.append(extra_svg)
    g.append(f'<rect x="-5" y="-92" width="10" height="9" fill="{skin}" stroke="{INK}" stroke-width="1.5"/>')
    g.append(f'<circle cx="0" cy="-110" r="20" fill="{skin}" stroke="{INK}" stroke-width="2.5"/>')
    g.append(_eyes(0, -112, 7, 2.6, expr))
    g.append(_mouth(0, -101, 11, expr))
    g.append(hat_svg)
    g.append("</g>")
    face = (x - 20 * s, y - 130 * s, x + 20 * s, y - 90 * s)
    return "".join(g), face


def scientist(x, y, s=1.0, expr="neutral", pose="stand", flip=False):
    """Researcher narrator: lab coat, glasses."""
    hair = (f'<path d="M-21,-112 Q-22,-136 0,-134 Q22,-136 21,-112 Q14,-126 0,-124 Q-12,-126 -21,-112 Z" '
            f'fill="{PALETTE["hair"]}" stroke="{INK}" stroke-width="2"/>'
            f'<circle cx="-7" cy="-112" r="6" fill="none" stroke="{INK}" stroke-width="1.8"/>'
            f'<circle cx="7" cy="-112" r="6" fill="none" stroke="{INK}" stroke-width="1.8"/>'
            f'<line x1="-1" y1="-112" x2="1" y2="-112" stroke="{INK}" stroke-width="1.8"/>')
    extra = (f'<path d="M0,-84 L0,-34" stroke="{INK}" stroke-width="1.5"/>'
             f'<rect x="6" y="-74" width="9" height="11" fill="#9ec3ff" stroke="{INK}" stroke-width="1.2"/>')
    svg, face = _human(x, y, s, expr, pose, flip, PALETTE["coat"], "#56607a", hair, extra, "")
    return svg, face, (x, y - 140 * s)


def sergeant(x, y, s=1.0, expr="stern", pose="stand", flip=False, label="τ=0.2"):
    """Rigid baseline: low-temperature greedy decoding."""
    hat = (f'<path d="M-22,-118 L22,-118 L18,-134 Q0,-142 -18,-134 Z" fill="{PALETTE["sergeant_dark"]}" stroke="{INK}" stroke-width="2"/>'
           f'<rect x="-25" y="-121" width="38" height="5" rx="2" fill="{INK}"/>'
           f'<circle cx="0" cy="-129" r="3" fill="#e8c547"/>'
           f'<path d="M-9,-103 q4.5,-4 9,0 q4.5,-4 9,0" fill="{PALETTE["hair"]}" stroke="{INK}" stroke-width="1.2"/>')
    extra = (f'<rect x="-14" y="-74" width="9" height="4" fill="#e8c547"/><rect x="-14" y="-68" width="9" height="4" fill="#c2413b"/>')
    svg, face = _human(x, y, s, expr, pose, flip, PALETTE["sergeant"], PALETTE["sergeant_dark"], hat, extra, label, coat_label_fill="#fff")
    return svg, face, (x, y - 146 * s)


def explorer(x, y, s=1.0, expr="happy", pose="stand", flip=False, label="T=1.0"):
    """Adaptive method: calibrated sampling that explores."""
    hat = (f'<ellipse cx="0" cy="-124" rx="32" ry="7" fill="{PALETTE["explorer_dark"]}" stroke="{INK}" stroke-width="2"/>'
           f'<path d="M-17,-125 Q-16,-146 0,-146 Q16,-146 17,-125 Z" fill="{PALETTE["explorer"]}" stroke="{INK}" stroke-width="2"/>'
           f'<rect x="-17" y="-131" width="34" height="5" fill="{PALETTE["explorer_dark"]}"/>')
    extra = (f'<rect x="-30" y="-80" width="10" height="38" rx="4" fill="#7a5a2a" stroke="{INK}" stroke-width="1.5"/>'
             f'<circle cx="10" cy="-60" r="7" fill="#fff" stroke="{INK}" stroke-width="1.8"/>'
             f'<path d="M10,-66 L12,-60 L10,-54 L8,-60 Z" fill="#c2413b"/>')
    svg, face = _human(x, y, s, expr, pose, flip, PALETTE["explorer"], PALETTE["explorer_dark"], hat, extra, label)
    return svg, face, (x, y - 152 * s)


def gatekeeper(x, y, s=1.0, expr="stern", lamps=(False, False, False), pose="stand", flip=False, label="DETECT"):
    """Threshold detector: a tall guard whose staff carries the three loop-detector lamps."""
    lamp_cols = [PALETTE["bad"] if on else "#5a5f6e" for on in lamps]
    helmet = (f'<path d="M-22,-110 Q-22,-138 0,-140 Q22,-138 22,-110 L16,-112 Q0,-122 -16,-112 Z" '
              f'fill="{PALETTE["gate_dark"]}" stroke="{INK}" stroke-width="2"/>'
              f'<path d="M0,-140 L0,-152" stroke="{INK}" stroke-width="3"/><circle cx="0" cy="-154" r="4" fill="#e8c547" stroke="{INK}"/>')
    staff = [f'<line x1="38" y1="0" x2="38" y2="-150" stroke="#6b4a2a" stroke-width="5" stroke-linecap="round"/>']
    for i, col in enumerate(lamp_cols):
        cy = -150 + i * 16
        staff.append(f'<circle cx="38" cy="{cy}" r="7" fill="{col}" stroke="{INK}" stroke-width="1.8"/>')
    robe = f'<path d="M-28,0 L-22,-84 Q0,-92 22,-84 L28,0 Z" fill="{PALETTE["gate"]}" stroke="{INK}" stroke-width="2.5"/>'
    g = [f'<g transform="translate({x},{y}) scale({-s if flip else s},{s})">', robe, "".join(staff)]
    a1, _ = _arm(-20, -76, ARM_ANGLES[pose][0], 30, 8, PALETTE["gate"])
    g.append(a1)
    g.append(f'<line x1="20" y1="-76" x2="36" y2="-96" stroke="{PALETTE["gate"]}" stroke-width="8" stroke-linecap="round"/>'
             f'<circle cx="37" cy="-98" r="5" fill="{PALETTE["gate"]}" stroke="{INK}" stroke-width="1.5"/>')
    g.append(_label(0, -40, label, 8.5, "#fff"))
    g.append(f'<rect x="-5" y="-92" width="10" height="9" fill="{PALETTE["skin"]}" stroke="{INK}" stroke-width="1.5"/>'
             f'<circle cx="0" cy="-110" r="20" fill="{PALETTE["skin"]}" stroke="{INK}" stroke-width="2.5"/>')
    g.append(_eyes(0, -110, 7, 2.6, expr))
    g.append(_mouth(0, -100, 11, expr))
    g.append(helmet)
    g.append("</g>")
    sx = -1 if flip else 1
    xs = sorted([x - 22 * s, x + 22 * s, x + sx * 46 * s])
    face = (min(xs), y - 158 * s, max(xs), y - 90 * s)
    return "".join(g), face, (x, y - 162 * s)


CHARACTERS = {"robot": robot, "monster": monster, "scientist": scientist, "sergeant": sergeant,
              "explorer": explorer, "gatekeeper": gatekeeper}


class Anchor:
    """Where a bubble tail may point: the head top and the face box of one character."""
    def __init__(self, top, face, name):
        self.top, self.face, self.name = top, face, name


def put(panel: Panel, who: str, x, y, s=1.0, label_name: str | None = None, **kw):
    """Draw a character in a panel and register its face box. Returns an Anchor for bubble tails."""
    svg, face, top = CHARACTERS[who](x, y, s, **kw)
    panel.add(svg, "face", face, label_name or who)
    return Anchor(top, face, label_name or who)


def _tail_geometry(tail, x, y, w, h):
    """Return (triangle points, base-mid, tip). Tails go to the head top when the bubble is above the
    head, and to the side of the face when the bubble sits beside it, so a tail never crosses a face."""
    if isinstance(tail, Anchor):
        fx0, fy0, fx1, fy1 = tail.face
        mid = (fy0 + fy1) / 2
        if y + h <= fy0 + 4:
            tx, ty = min(max(x + w / 2, fx0 + 4), fx1 - 4), tail.top[1]
            tx = tail.top[0]
        elif x >= fx1:
            tx, ty = fx1 + 6, mid
        elif x + w <= fx0:
            tx, ty = fx0 - 6, mid
        else:
            tx, ty = tail.top
    else:
        tx, ty = tail
    if ty >= y + h or ty <= y:  # base on bottom or top edge
        bx = min(max(tx, x + 18), x + w - 18)
        by = y + h if ty > y + h / 2 else y
        return f"M{bx - 9:.1f},{by:.1f} L{tx:.1f},{ty:.1f} L{bx + 9:.1f},{by:.1f} Z", ((bx - 7.5, by), (bx + 7.5, by)), (bx, by), (tx, ty)
    bx = x if tx < x else x + w
    by = min(max(ty, y + 10), y + h - 10)
    return f"M{bx:.1f},{by - 8:.1f} L{tx:.1f},{ty:.1f} L{bx:.1f},{by + 8:.1f} Z", ((bx, by - 6.5), (bx, by + 6.5)), (bx, by), (tx, ty)


# ------------------------------------------------------------------------------------------------
# Bubbles, captions, boards, charts, diamonds
# ------------------------------------------------------------------------------------------------
def bubble(panel: Panel, text: str, x, y, w, tail=None, size=12.5, kind="speech", style="regular", label=""):
    """Speech bubble with its top-left corner at (x, y) and text width w. tail = (tx, ty) point."""
    pad = 9
    lines = wrap(text, w - 2 * pad, size, style)
    h = len(lines) * size * 1.25 + 2 * pad - size * .2
    tw = max(text_width(ln, size, style) for ln in lines) + 2 * pad
    w = max(min(w, tw), 40)
    fill = "#fff" if kind != "shout" else "#ffe9e6"
    stroke = INK if kind != "shout" else PALETTE["bad"]
    out = []
    geo = None
    if tail and kind != "thought":
        geo = _tail_geometry(tail, x, y, w, h)
        out.append(f'<path d="{geo[0]}" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-linejoin="round"/>')
    if kind == "thought" and tail:
        tx, ty = tail.top if isinstance(tail, Anchor) else tail
        bx, by = x + w / 2, y + h
        for i, r in enumerate((6, 4, 2.6)):
            f = (i + 1) / 4
            out.append(f'<circle cx="{bx + (tx - bx) * f:.1f}" cy="{by + (ty - by) * f:.1f}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
    rx = h / 2 if kind == "thought" else 12
    out.append(f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h:.1f}" rx="{min(rx, 22):.1f}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    if geo:  # hide the seam where the tail meets the box
        (sx0, sy0), (sx1, sy1) = geo[1]
        out.append(f'<line x1="{sx0:.1f}" y1="{sy0:.1f}" x2="{sx1:.1f}" y2="{sy1:.1f}" stroke="{fill}" stroke-width="3"/>')
    out.append(text_block(lines, x + pad, y + pad - size * .15, size, style))
    lab = label or text[:24]
    panel.add("".join(out), "bubble", (x, y, x + w, y + h), lab)
    if geo:
        panel.tails.append((lab, geo[2], geo[3], tail.name if isinstance(tail, Anchor) else None))
    return (x, y, x + w, y + h)


def caption(panel: Panel, text: str, x, y, w, size=11.5, style="bold", fill=None, label=""):
    pad = 7
    lines = wrap(text, w - 2 * pad, size, style)
    h = len(lines) * size * 1.25 + 2 * pad - size * .2
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h:.1f}" fill="{fill or PALETTE["caption"]}" stroke="{INK}" stroke-width="2"/>'
           + text_block(lines, x + pad, y + pad - size * .15, size, style))
    panel.add(out, "caption", (x, y, x + w, y + h), label or text[:24])
    return (x, y, x + w, y + h)


def blackboard(panel: Panel, x, y, w, h, rows, title=None, label="board"):
    """rows = [(text, size, style, color)] drawn in chalk; returns bottom y used."""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PALETTE["board"]}" stroke="#7a5a2a" stroke-width="6"/>']
    cy = y + 10
    if title:
        out.append(text_block([title], x + 12, cy, 12, "black", "#ffe58a"))
        cy += 20
    for text, size, style, color in rows:
        lines = wrap(text, w - 24, size, style)
        out.append(text_block(lines, x + 12, cy, size, style, color))
        cy += len(lines) * size * 1.25 + 5
    if cy > y + h:
        panel.parts.append("")  # keep going, but record the overflow as a problem
        panel.boxes.append(("caption", f"OVERFLOW board {label}", (x, y, x + w, cy)))
    panel.add("".join(out), "board", (x, y, x + w, y + h), label)
    return cy


def bar_chart(panel: Panel, x, y, w, h, items, vmax, title=None, unit_fmt=None, label="chart", horizontal=False, size=11):
    """items = [(label, value, display, color)]. Bars register as 'bar' boxes so bubbles cannot cover them."""
    out = []
    top = y
    if title:
        out.append(text_block([title], x, y, 12, "black"))
        top += 20
    if horizontal:
        lab_w = max(text_width(it[0], size, "bold") for it in items) + 8
        val_w = max(text_width(it[2], size, "black") for it in items) + 8
        bh = (y + h - top) / len(items)
        for i, (lab, val, disp, col) in enumerate(items):
            by = top + i * bh + bh * .15
            bw = (w - lab_w - val_w) * val / vmax
            out.append(text_block([lab], x + lab_w - 6, by + bh * .35 - size * .65, size, "bold", INK, "end"))
            out.append(f'<rect x="{x + lab_w}" y="{by:.1f}" width="{bw:.1f}" height="{bh * .7:.1f}" fill="{col}" stroke="{INK}" stroke-width="1.5"/>')
            out.append(text_block([disp], x + lab_w + bw + 5, by + bh * .35 - size * .65, size, "black"))
            panel.boxes.append(("bar", f"{label}:{lab}", (x + lab_w, by, x + lab_w + bw + val_w, by + bh * .7)))
    else:
        base = y + h - 30
        n = len(items)
        slot = w / n
        out.append(f'<line x1="{x}" y1="{base}" x2="{x + w}" y2="{base}" stroke="{INK}" stroke-width="2"/>')
        for i, (lab, val, disp, col) in enumerate(items):
            bw = slot * .62
            bx = x + i * slot + (slot - bw) / 2
            bh = (base - top - 22) * val / vmax
            out.append(f'<rect x="{bx:.1f}" y="{base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{col}" stroke="{INK}" stroke-width="1.5"/>')
            out.append(text_block([disp], bx + bw / 2, base - bh - size * 1.45, size, "black", INK, "middle"))
            for j, ln in enumerate(wrap(lab, slot - 4, size - 1.5, "bold")):
                out.append(text_block([ln], bx + bw / 2, base + 3 + j * (size - 1.5) * 1.2, size - 1.5, "bold", INK, "middle"))
            panel.boxes.append(("bar", f"{label}:{lab}", (bx, base - bh - size * 1.5, bx + bw, base)))
    panel.add("".join(out))


def diamond(panel: Panel, cx, cy, w, h, text, size=11, fill="#fff3d6", label="diamond"):
    lines = wrap(text, w * .62, size, "bold")
    out = (f'<path d="M{cx},{cy - h / 2} L{cx + w / 2},{cy} L{cx},{cy + h / 2} L{cx - w / 2},{cy} Z" fill="{fill}" stroke="{INK}" stroke-width="2.5"/>'
           + text_block(lines, cx, cy - len(lines) * size * 1.25 / 2 - size * .1, size, "bold", INK, "middle"))
    panel.add(out, "chart", (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), label)


def box(panel: Panel, x, y, w, h, text, size=11, fill="#eef3ff", style="bold", label="box", stroke=INK):
    lines = wrap(text, w - 12, size, style)
    th = len(lines) * size * 1.25
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
           + text_block(lines, x + w / 2, y + (h - th) / 2 - size * .1, size, style, INK, "middle"))
    panel.add(out, "chart", (x, y, x + w, y + h), label)


def arrow(panel: Panel, x1, y1, x2, y2, color=INK, width=2.5, text=None, size=10):
    import math
    a = math.atan2(y2 - y1, x2 - x1)
    hx1, hy1 = x2 - 10 * math.cos(a - .4), y2 - 10 * math.sin(a - .4)
    hx2, hy2 = x2 - 10 * math.cos(a + .4), y2 - 10 * math.sin(a + .4)
    out = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>'
           f'<path d="M{x2},{y2} L{hx1:.1f},{hy1:.1f} L{hx2:.1f},{hy2:.1f} Z" fill="{color}"/>')
    if text:
        out += text_block([text], (x1 + x2) / 2 + 4, (y1 + y2) / 2 - size - 2, size, "bold", color, "start")
    panel.add(out)


def sfx(panel: Panel, text, x, y, size=26, color="#c2413b", rotate=-8):
    panel.add(f'<g transform="rotate({rotate},{x},{y})"><text x="{x}" y="{y}" font-family="Lato" font-weight="900" '
              f'font-size="{size}" fill="{color}" stroke="{INK}" stroke-width="1.2" text-anchor="middle">{esc(text)}</text></g>')
