"""Measure the article's figures: geometry, content hashes, pixel differences between variants,
endpoint markers on the flow covers, text ink heights on the text cover at a 320px feed card,
and the dev.to 1000x420 crop applied to each geometry. Writes JSON and prints a report.

usage: python3 measure_figures.py <paper_dir> <out_json>
"""
import hashlib, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(sys.argv[1]); OUT = Path(sys.argv[2])
FILES = ["cover.ae4d639e.jpg", "cover.77acc7c4.jpg", "cover-builder.cabd79f3.jpg", "cover-builder.80aa6ca5.jpg",
         "linkedin-devto-publishing-kit-cover.jpg", "advocu-devto-publishing-kit-cover.webp",
         "medium/img/cover.ae4d639e.jpg", "medium/img/cover.77acc7c4.jpg", "medium/img/devto-publishing-kit-table-1.png"]
res = {"files": {}, "diffs": {}, "endpoints": {}, "ink_320": {}, "devto_crop": {}, "table": {}}

def arr(f):
    return np.asarray(Image.open(P / f).convert("RGB")).astype(np.int16)

print("== geometry and content hashes")
for f in FILES:
    b = (P / f).read_bytes(); im = Image.open(P / f)
    sha = hashlib.sha256(b).hexdigest()
    stem_hash = f.rsplit(".", 2)[-2] if f.count(".") >= 2 else None
    named = stem_hash is not None and len(stem_hash) == 8 and all(c in "0123456789abcdef" for c in stem_hash)
    r = {"w": im.size[0], "h": im.size[1], "ratio": round(im.size[0] / im.size[1], 4), "bytes": len(b),
         "sha256_8": sha[:8], "name_hash_matches": (sha[:8] == stem_hash) if named else None}
    res["files"][f] = r
    print(f"{f:45s} {r['w']}x{r['h']} ratio {r['ratio']:.4f} {r['bytes']:>7d} B sha256[:8]={r['sha256_8']} "
          f"name-hash-match={r['name_hash_matches']}")

print("== byte identity and mean abs pixel difference (0-255 scale)")
pairs = [("cover.ae4d639e.jpg", "medium/img/cover.ae4d639e.jpg"), ("cover.77acc7c4.jpg", "medium/img/cover.77acc7c4.jpg"),
         ("cover.ae4d639e.jpg", "advocu-devto-publishing-kit-cover.webp"), ("cover.ae4d639e.jpg", "cover.77acc7c4.jpg"),
         ("cover-builder.cabd79f3.jpg", "cover-builder.80aa6ca5.jpg")]
for a, b in pairs:
    same = (P / a).read_bytes() == (P / b).read_bytes()
    d = float(np.abs(arr(a) - arr(b)).mean())
    res["diffs"][f"{a} | {b}"] = {"bytes_identical": same, "mean_abs_diff": round(d, 3)}
    print(f"{a} vs {b}: bytes identical={same}, mean abs diff={d:.3f}")

print("== endpoint markers on the flow covers (right 30% of frame, components taller than 30px)")
def classify(rgb):
    r, g, b = rgb
    if b > r + 40: return "blue"
    if r > b + 60: return "orange"
    return "grey"
for f in ["cover.ae4d639e.jpg", "cover-builder.cabd79f3.jpg", "linkedin-devto-publishing-kit-cover.jpg",
          "advocu-devto-publishing-kit-cover.webp"]:
    a = arr(f); h, w, _ = a.shape; x0 = int(w * 0.70)
    sub = a[:, x0:]
    mask = sub.max(axis=2) > 110
    lab, n = ndimage.label(mask)
    marks = []
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        hh = sl[0].stop - sl[0].start; ww = sl[1].stop - sl[1].start
        if hh > 30 and ww > 30:
            px = sub[lab == i]
            mean = tuple(int(v) for v in px.mean(axis=0))
            marks.append({"cx": x0 + (sl[1].start + sl[1].stop) // 2, "cy": (sl[0].start + sl[0].stop) // 2,
                          "w": ww, "h": hh, "mean_rgb": mean, "colour": classify(mean)})
    marks.sort(key=lambda m: m["cy"])
    res["endpoints"][f] = marks
    print(f"{f}: {len(marks)} markers, colours top->bottom {[m['colour'] for m in marks]}, "
          f"centres {[(m['cx'], m['cy']) for m in marks]}, sizes {[(m['w'], m['h']) for m in marks]}")

print("== ink height of each text line on cover.77acc7c4.jpg, native and at a 320px-wide feed card")
a = arr("cover.77acc7c4.jpg"); lum = a.mean(axis=2)
bg = float(np.median(lum))
scale = 320 / a.shape[1]
regions = {  # name: (x0, x1, y0, y1) boxes around each text line, chosen from the Read view, measured here
    "kicker 'PUBLISHING-KIT - A CLAUDE CODE SKILL'": (70, 460, 28, 60),
    "title 'One source. Four destinations.'": (70, 760, 62, 116),
    "subtitle 'Write once. ...'": (70, 640, 117, 150),
    "card title 'dev.to'": (90, 260, 360, 415),
    "card label 'REST API'": (90, 200, 420, 448),
    "footer 'publishing-kit - one markdown file in ...'": (70, 790, 544, 572),
}
for name, (x0, x1, y0, y1) in regions.items():
    rows = np.where(((lum[y0:y1, x0:x1] - bg) > 40).any(axis=1))[0]
    ink = int(rows.max() - rows.min() + 1) if len(rows) else 0
    res["ink_320"][name] = {"native_px": ink, "at_320_px": round(ink * scale, 1)}
    print(f"{name:48s} ink {ink:3d}px native -> {ink * scale:4.1f}px at 320px wide (scale {scale:.4f})")
res["ink_320"]["background_luma"] = bg

print("== dev.to header crop: displayed 1000x420, fit=cover (devto-cover-crop.txt)")
R = 1000 / 420
for name, (w, h) in {"1376x768 (article's example)": (1376, 768), "1376x578 (cover.ae4d639e)": (1376, 578),
                     "1200x675 (builder covers)": (1200, 675), "1200x627 (linkedin cover)": (1200, 627)}.items():
    kept = w / R
    if kept <= h:
        lost = (h - kept) / 2; res["devto_crop"][name] = {"kept_rows": round(kept, 1), "lost_each_edge_rows": round(lost, 1)}
        print(f"{name:30s} keeps {kept:.1f} of {h} rows; {lost:.1f} rows off top and bottom")
    else:
        kept_c = h * R; lost = (w - kept_c) / 2; res["devto_crop"][name] = {"kept_cols": round(kept_c, 1), "lost_each_side_cols": round(lost, 1)}
        print(f"{name:30s} keeps {kept_c:.1f} of {w} cols; {lost:.1f} cols off each side")
print(f"ratio 1000/420 = {R:.4f}; cover.ae4d639e ratio 1376/578 = {1376/578:.4f}")

print("== table figure numbers")
res["table"] = {"hardwrap_share": round(47 / 62, 4), "p_plus_li": 58 + 4, "br_per_affected_block": round(88 / 47, 3)}
print(f"47/62 = {47/62:.4f}; 58 <p> + 4 <li> = {58+4}; 88 <br> / 47 blocks = {88/47:.3f}")
OUT.write_text(json.dumps(res, indent=1)); print("wrote", OUT)
