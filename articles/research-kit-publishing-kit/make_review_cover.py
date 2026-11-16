#!/usr/bin/env python3
"""Textless cover: a document under a magnifying glass, inside a review loop.

Drawn at 2x and downsampled, in make-cover.py's palette. Writes one design at the
dev.to (1376x578) and Builder Center (1200x675) sizes, each named by a hash of
its bytes.

    python3 make_review_cover.py [--out-dir .]
"""

import argparse
import hashlib
import io
import math
import pathlib

from PIL import Image, ImageDraw, ImageFilter

SURFACE = (26, 26, 25)
PAPER = (236, 234, 226)
LINE = (170, 168, 158)
BLUE = (57, 135, 229)
ORANGE = (217, 89, 38)
MUTED = (128, 127, 120)
S = 2  # supersample


def draw(W, H):
    img = Image.new("RGB", (W * S, H * S), SURFACE)
    # One unit, sized off the 578-tall dev.to band so both sizes share a layout.
    u = min(W / 1376, H / 578) * S
    cx, cy = W * S / 2, H * S / 2

    # Soft glow behind the group.
    glow = Image.new("L", img.size, 0)
    ImageDraw.Draw(glow).ellipse([cx - 330 * u, cy - 250 * u, cx + 330 * u, cy + 250 * u], fill=40)
    glow = glow.filter(ImageFilter.GaussianBlur(90 * u))
    img.paste(Image.new("RGB", img.size, (52, 58, 70)), mask=glow)
    d = ImageDraw.Draw(img)

    # Review loop: an arc around the group, orange into blue, with an arrowhead.
    R = 245 * u
    steps = 220
    a0, a1 = 200, 200 + 300  # degrees, leaves a gap for the arrowhead
    for i in range(steps):
        t = i / steps
        col = tuple(int(ORANGE[c] + (BLUE[c] - ORANGE[c]) * t) for c in range(3))
        a = math.radians(a0 + (a1 - a0) * t)
        b = math.radians(a0 + (a1 - a0) * (i + 1.6) / steps)
        d.line([(cx + R * math.cos(a), cy + R * math.sin(a)), (cx + R * math.cos(b), cy + R * math.sin(b))],
               fill=col, width=int(9 * u))
    ae = math.radians(a1)
    tip = (cx + R * math.cos(ae), cy + R * math.sin(ae))
    tang = ae + math.pi / 2
    back = 30 * u
    side = 18 * u
    base = (tip[0] - back * math.cos(tang), tip[1] - back * math.sin(tang))
    d.polygon([(tip[0] + 8 * u * math.cos(tang), tip[1] + 8 * u * math.sin(tang)),
               (base[0] + side * math.cos(ae), base[1] + side * math.sin(ae)),
               (base[0] - side * math.cos(ae), base[1] - side * math.sin(ae))], fill=BLUE)

    # The document, left of centre, with a folded corner.
    pw, ph = 190 * u, 250 * u
    px, py = cx - 125 * u, cy - ph / 2 - 12 * u
    fold = 34 * u
    d.polygon([(px, py), (px + pw - fold, py), (px + pw, py + fold), (px + pw, py + ph), (px, py + ph)], fill=PAPER)
    d.polygon([(px + pw - fold, py), (px + pw - fold, py + fold), (px + pw, py + fold)], fill=(200, 198, 190))
    rows = []
    for i in range(8):
        y = py + 44 * u + i * 25 * u
        w = (0.78, 0.62, 0.84, 0.55, 0.74, 0.66, 0.8, 0.48)[i] * (pw - 50 * u)
        rows.append((px + 26 * u, y, w))
        d.rounded_rectangle([px + 26 * u, y - 4 * u, px + 26 * u + w, y + 4 * u], radius=4 * u, fill=LINE)

    # Margin marks: blue ticks on checked lines, one orange ring on a disputed one.
    for i in (0, 2, 4, 6):
        x, y, _ = rows[i]
        d.ellipse([x - 16 * u, y - 4 * u, x - 8 * u, y + 4 * u], fill=BLUE)
    x, y, w = rows[3]
    d.rounded_rectangle([x - 6 * u, y - 11 * u, x + w + 6 * u, y + 11 * u], radius=11 * u,
                        outline=ORANGE, width=int(4 * u))

    # Magnifying glass over the lower right of the page.
    gx, gy, gr = rows[3][0] + rows[3][2] / 2, rows[3][1], 74 * u  # centred on the disputed line
    lens = Image.new("L", img.size, 0)
    ImageDraw.Draw(lens).ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=255)
    zoom = img.crop((int(gx - gr / 1.5), int(gy - gr / 1.5), int(gx + gr / 1.5), int(gy + gr / 1.5)))
    zoom = zoom.resize((int(2 * gr), int(2 * gr)), Image.LANCZOS)
    tinted = Image.blend(zoom, Image.new("RGB", zoom.size, (210, 225, 245)), 0.12)
    layer = Image.new("RGB", img.size, SURFACE)
    layer.paste(tinted, (int(gx - gr), int(gy - gr)))
    img.paste(layer, mask=lens)
    d = ImageDraw.Draw(img)
    hx, hy = gx + gr * math.cos(math.radians(45)), gy + gr * math.sin(math.radians(45))
    d.line([(hx, hy), (hx + 95 * u, hy + 95 * u)], fill=(90, 90, 86), width=int(26 * u))
    d.line([(hx + 6 * u, hy + 6 * u), (hx + 90 * u, hy + 90 * u)], fill=(120, 120, 114), width=int(12 * u))
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], outline=(225, 225, 218), width=int(12 * u))
    d.ellipse([gx - gr + 6 * u, gy - gr + 6 * u, gx + gr - 6 * u, gy + gr - 6 * u], outline=BLUE, width=int(4 * u))
    # Highlight on the glass.
    d.arc([gx - gr + 22 * u, gy - gr + 22 * u, gx + gr - 22 * u, gy + gr - 22 * u], 200, 250,
          fill=(245, 245, 240), width=int(6 * u))

    return img.resize((W, H), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=".")
    a = ap.parse_args()
    out = pathlib.Path(a.out_dir)
    for stem, size in (("devto-cover", (1376, 578)), ("devto-cover-builder", (1200, 675))):
        buf = io.BytesIO()
        draw(*size).save(buf, "JPEG", quality=92)
        data = buf.getvalue()
        name = f"{stem}.{hashlib.sha256(data).hexdigest()[:8]}.jpg"
        (out / name).write_bytes(data)
        print(f"wrote {name}  {size[0]}x{size[1]}  {len(data) // 1024} KB")


if __name__ == "__main__":
    main()
