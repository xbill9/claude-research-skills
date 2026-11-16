#!/usr/bin/env python3
"""Python reference model for the publishing-kit explorer.

Three models, each from a number the paper (devto-publishing-kit.md) or its evidence states:

  1. dev.to cover crop   -- fit=cover into a 1000x420 box (evidence/devto-cover-crop.txt).
  2. feed-card type size -- apparent px = type size x card width / cover width, card 320 px
                            (article line 36; CLAIMS.md LOG row). The 10 px legibility threshold is
                            NOT in the paper; it is LEGIBLE_PX in the kit's make-cover.py.
  3. hard-wrap breaks    -- dev.to renders each newline inside a paragraph-level block as <br>
                            (article line 52; evidence/devto-hardwrap.txt). Applied to THIS article's
                            own source, as stored and re-wrapped at a chosen column.

Writes preset_values.json (presets, grounding rows, the article's blocks for the page's wrap model).
"""

import json
import math
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
PAPER = HERE.parent / "paper"
SRC = PAPER / "devto-publishing-kit.md"

DISPLAY = (1000, 420)  # MEASURED, evidence/devto-cover-crop.txt
CARD_W = 320  # article line 36
LEGIBLE_PX = 10  # kit source make-cover.py, not the paper


# ---------------------------------------------------------------- model 1: crop
def crop(w, h, dw=DISPLAY[0], dh=DISPLAY[1]):
    """fit=cover with a centred crop. Returns kept source rows/cols and loss per side."""
    box = dw / dh
    scale = max(dw / w, dh / h)  # source px -> displayed px
    kept_w = dw / scale
    kept_h = dh / scale
    return {
        "box_ratio": box,
        "src_ratio": w / h,
        "scale": scale,
        "kept_w": kept_w,
        "kept_h": kept_h,
        "lost_tb": (h - kept_h) / 2,  # each of top and bottom
        "lost_lr": (w - kept_w) / 2,  # each of left and right
        "lost_frac": 1 - (kept_w * kept_h) / (w * h),
    }


# ---------------------------------------------------------------- model 2: card
def card(w, h, type_px, card_w=CARD_W, legible=LEGIBLE_PX, dw=DISPLAY[0], dh=DISPLAY[1]):
    """Apparent size of a type size drawn on a W-wide cover, at a card_w-wide card (make-cover.py's
    rule: scale = CARD_W / W), and at the 1000 px article header after the crop."""
    c = crop(w, h, dw, dh)
    card_px = type_px * card_w / w
    return {
        "card_scale": card_w / w,
        "card_px": card_px,
        "header_px": type_px * c["scale"],
        "min_legible_type": legible * w / card_w,
        "legible": 1.0 if card_px >= legible else 0.0,
    }


# ---------------------------------------------------------------- model 3: wrap
def parse_blocks(text):
    """Paragraph-level blocks of a markdown body: paragraphs, list items, quoted paragraphs.
    Skips front matter, fenced code, headings and table rows. Mirrors dev.to's <p> + <li> count."""
    lines = text.splitlines()
    i = 0
    if lines and lines[0].strip() == "---":
        i = lines.index("---", 1) + 1
    blocks, cur, fence = [], None, False

    def close():
        nonlocal cur
        if cur:
            blocks.append(cur)
        cur = None

    for n in range(i, len(lines)):
        line = lines[n]
        s = line.strip()
        if s.startswith("```"):
            close()
            fence = not fence
            continue
        if fence:
            continue
        if not s or s.startswith("#") or s.startswith("|"):
            close()
            continue
        if line.startswith(">"):
            body = line[1:].strip()
            if cur and cur["kind"] == "quote":
                cur["lines"].append(line)
                cur["words"] += body.split()
            else:
                close()
                cur = {"kind": "quote", "line": n + 1, "prefix": 2, "lines": [line], "words": body.split()}
            continue
        if line.startswith("- ") or line.startswith("* "):
            close()
            cur = {"kind": "li", "line": n + 1, "prefix": 2, "lines": [line], "words": line[2:].split()}
            continue
        if cur and cur["kind"] == "li" and line.startswith("  "):
            cur["lines"].append(line)
            cur["words"] += s.split()
            continue
        if cur and cur["kind"] == "p":
            cur["lines"].append(line)
            cur["words"] += s.split()
            continue
        close()
        cur = {"kind": "p", "line": n + 1, "prefix": 0, "lines": [line], "words": s.split()}
    close()
    for b in blocks:
        b["stored_lines"] = len(b["lines"])
        b["max_len"] = max(len(x) for x in b["lines"])
    return blocks


def wrap_count(words, width):
    """Greedy word wrap; a word longer than width sits alone on its line. Returns line count."""
    width = max(1, width)
    n, cur = 0, -1
    for w in words:
        L = len(w)
        if cur < 0:
            cur, n = L, 1
        elif cur + 1 + L <= width:
            cur += 1 + L
        else:
            cur, n = L, n + 1
    return n


def wrap_stats(blocks, col):
    lines = [wrap_count(b["words"], col - b["prefix"]) for b in blocks]
    breaks = [x - 1 for x in lines]
    return {
        "blocks": len(blocks),
        "blocks_broken": sum(1 for x in breaks if x > 0),
        "br_total": sum(breaks),
    }


def stored_stats(blocks):
    breaks = [b["stored_lines"] - 1 for b in blocks]
    return {
        "blocks": len(blocks),
        "blocks_broken": sum(1 for x in breaks if x > 0),
        "br_total": sum(breaks),
        "max_prose_line": max(b["max_len"] for b in blocks),
        "prose_lines_over_95": sum(1 for b in blocks for x in b["lines"] if len(x) > 95),
        "prose_lines_over_100": sum(1 for b in blocks for x in b["lines"] if len(x) > 100),
        "prose_lines": sum(b["stored_lines"] for b in blocks),
    }


# ---------------------------------------------------------------- presets
PRESETS = [
    {
        "id": "shipped",
        "name": "dev.to cover as first shipped",
        "w": 1376,
        "h": 768,
        "type": 40,
        "card": 320,
        "col": 95,
        "cite": "article l.53-54; evidence/devto-cover-crop.txt; make-cover.py 'below about 40pt'",
    },
    {
        "id": "devto",
        "name": "make-cover --mode devto (1376x578)",
        "w": 1376,
        "h": 578,
        "type": 40,
        "card": 320,
        "col": 95,
        "cite": "evidence/devto-cover-crop.txt last line; cover.ae4d639e.jpg measured 1376x578",
    },
    {
        "id": "builder",
        "name": "Builder Center hero (1200x675) on dev.to",
        "w": 1200,
        "h": 675,
        "type": 40,
        "card": 320,
        "col": 95,
        "cite": "evidence/cover-refresh.txt 1200x675; dev.to crop is a what-if, not measured",
    },
    {
        "id": "linkedin",
        "name": "LinkedIn cover file (1200x627) on dev.to",
        "w": 1200,
        "h": 627,
        "type": 40,
        "card": 320,
        "col": 95,
        "cite": "linkedin-devto-publishing-kit-cover.jpg measured 1200x627; dev.to crop is a what-if",
    },
]


def evaluate(p, blocks):
    out = {}
    out.update(crop(p["w"], p["h"]))
    out.update(card(p["w"], p["h"], p["type"], p["card"]))
    out.update({"wrap_" + k: float(v) for k, v in wrap_stats(blocks, p["col"]).items()})
    return out


def main():
    text = SRC.read_text()
    blocks = parse_blocks(text)
    st = stored_stats(blocks)
    tldr = blocks[0]
    imgs = {}
    for f in sorted(list(PAPER.glob("*.jpg")) + list(PAPER.glob("*.webp"))):
        imgs[f.name] = list(Image.open(f).size)

    presets = {p["id"]: {"inputs": p, "out": evaluate(p, blocks)} for p in PRESETS}
    sweep = [{"col": c, **wrap_stats(blocks, c)} for c in range(40, 201, 5)]
    geo = {name: crop(*wh) for name, wh in imgs.items()}

    sh = presets["shipped"]["out"]
    dv = presets["devto"]["out"]
    hw_blocks, hw_broken, hw_br = 62, 47, 88  # evidence/devto-hardwrap.txt (other article)
    bp_lines = len((PAPER / "builder-publishing-kit.md").read_text().splitlines())
    bp_chars = len((PAPER / "builder-publishing-kit.md").read_text())

    def row(claim, published, model, verdict, src, note=""):
        return {"claim": claim, "published": published, "model": model, "verdict": verdict, "src": src, "note": note}

    grounding = [
        row("dev.to proxy ratio", "2.381:1", f"{sh['box_ratio']:.6f}", "MATCH", "article l.53; devto-cover-crop.txt"),
        row(
            "1376x768 cover: rows kept",
            "577.9 -> 578",
            f"{sh['kept_h']:.4f}",
            "MATCH",
            "devto-cover-crop.txt ARITH",
        ),
        row(
            "1376x768 cover: lost top and bottom",
            "95 px each",
            f"{sh['lost_tb']:.4f}",
            "MATCH",
            "article l.54; devto-cover-crop.txt ARITH",
            "evidence rounds kept rows first: (768-578)/2 = 95; unrounded 95.04",
        ),
        row(
            "1376x578 cover: nothing cropped",
            "nothing cropped",
            f"{dv['lost_tb']:.4f} px per side",
            "MATCH",
            "devto-cover-crop.txt MEASURED",
            "under one source pixel",
        ),
        row("feed card width", "320 px", "input", "INPUT", "article l.36; CLAIMS.md LOG 2026-08-31"),
        row(
            "type size that survives the card (1376 wide)",
            "not stated in the paper",
            f"{presets['shipped']['out']['min_legible_type']:.2f} pt at 10 px",
            "NOT IN PAPER",
            "make-cover.py LEGIBLE_PX=10 (kit source)",
            "kit comment says 'below about 40pt disappears'; 40 pt renders "
            f"{sh['card_px']:.2f} px, under the 10 px threshold",
        ),
        row(
            "TL;DR posted as five separate lines",
            "5 lines",
            f"{tldr['stored_lines']} lines (block at l.{tldr['line']})",
            "MATCH" if tldr["stored_lines"] == 5 else "MISMATCH",
            "article l.171-172",
        ),
        row(
            "repo copy readable at 95 columns",
            "95 columns",
            f"longest prose line {st['max_prose_line']}; {st['prose_lines_over_95']} of "
            f"{st['prose_lines']} prose lines over 95",
            "MISMATCH" if st["max_prose_line"] > 95 else "MATCH",
            "article l.52, l.127-128",
            "the article's own source is wrapped wider than 95 in places",
        ),
        row(
            "hard-wrapped blocks on dev.to",
            "47 of 62",
            f"{hw_broken}/{hw_blocks} = {hw_broken / hw_blocks:.4f}; this article as stored: "
            f"{st['blocks_broken']} of {st['blocks']}",
            "NOT REPRODUCIBLE",
            "devto-hardwrap.txt (article 4531800)",
            "the measured article's source is not in the evidence",
        ),
        row(
            "<br> per broken block",
            "88 <br> over 47 blocks",
            f"{hw_br / hw_broken:.4f}; this article as stored: {st['br_total'] / st['blocks_broken']:.4f}",
            "NOT REPRODUCIBLE",
            "devto-hardwrap.txt",
        ),
        row(
            "Builder payload lines",
            "531 before unwrap, 411 after",
            f"builder-publishing-kit.md in paper/ has {bp_lines} lines, {bp_chars} chars",
            "NOT REPRODUCIBLE",
            "builder-payload.txt",
            "evidence describes a 534-line, 23,644-char file; the copy in paper/ is a different version",
        ),
        row("Medium data: URI images", "0 of 4; hosted 4 of 4", "not modelled", "NOT MODELLED", "article table"),
        row(
            "Builder Center hero geometry",
            "1200x675",
            "x".join(map(str, imgs.get("cover-builder.cabd79f3.jpg", []))),
            "MATCH",
            "cover-refresh.txt; image header",
        ),
        row(
            "dev.to cover file geometry",
            "1376x578",
            "x".join(map(str, imgs.get("cover.ae4d639e.jpg", []))),
            "MATCH",
            "devto-cover-crop.txt; image header",
        ),
    ]

    data = {
        "constants": {"display": DISPLAY, "card_w": CARD_W, "legible_px": LEGIBLE_PX},
        "presets": presets,
        "stored": st,
        "blocks": [
            {
                "kind": b["kind"],
                "line": b["line"],
                "prefix": b["prefix"],
                "stored_lines": b["stored_lines"],
                "words": b["words"],
            }
            for b in blocks
        ],
        "sweep": sweep,
        "images": imgs,
        "geometry": geo,
        "grounding": grounding,
    }
    (HERE / "preset_values.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))

    print(
        f"source: {SRC.name}, {len(blocks)} paragraph-level blocks "
        f"({sum(b['kind'] == 'p' for b in blocks)} p, {sum(b['kind'] == 'li' for b in blocks)} li, "
        f"{sum(b['kind'] == 'quote' for b in blocks)} quote)"
    )
    print("as stored:", st)
    for pid, v in presets.items():
        o = v["out"]
        print(
            f"preset {pid:9s} {v['inputs']['w']}x{v['inputs']['h']}: kept {o['kept_w']:.2f}x{o['kept_h']:.2f} "
            f"lost_tb {o['lost_tb']:.4f} lost_lr {o['lost_lr']:.4f} lost {o['lost_frac'] * 100:.2f}% | "
            f"card {o['card_px']:.4f}px legible={int(o['legible'])} min type {o['min_legible_type']:.2f} | "
            f"wrap@{v['inputs']['col']}: {int(o['wrap_blocks_broken'])}/{int(o['wrap_blocks'])}"
            f" br {int(o['wrap_br_total'])}"
        )
    print("images:", imgs)
    for name, g in geo.items():
        print(f"  {name:42s} ratio {g['src_ratio']:.4f} lost_tb {g['lost_tb']:.3f} lost_lr {g['lost_lr']:.3f}")
    print(
        "sweep (col: broken/blocks br):",
        " ".join(
            f"{s['col']}:{s['blocks_broken']}/{s['blocks']}/{s['br_total']}"
            for s in sweep
            if s["col"] % 20 == 0 or s["col"] == 95
        ),
    )
    for g in grounding:
        print(f"  [{g['verdict']}] {g['claim']}: paper {g['published']} | model {g['model']}")
    # sanity: math.isclose against hand-free restatement of the evidence arithmetic
    assert math.isclose(sh["kept_h"], 1376 * 420 / 1000)
    return 0


if __name__ == "__main__":
    sys.exit(main())
