"""Digitize the three KV-cache curves in Figure 2(b) from the 300-DPI raster.

Axis calibration comes from tick marks detected in the image (see RUN_NOTES.md):
x: turn 1 -> px 1876, turn 12 -> px 3085; y: 0 k -> px 953, 30 k -> px 232.
Values are READ FROM PLOT (digitized), not data from the paper.
"""
import json, sys
import numpy as np
from PIL import Image

src = sys.argv[1]
a = np.array(Image.open(src).convert("RGB")).astype(int)
X0, X1, Y0, Y30 = 1876, 3085, 953, 232
def tx(t): return X0 + (t - 1) * (X1 - X0) / 11
def val(py): return (Y0 - py) * 30 / (Y0 - Y30)

colors = {"naive_subagent (gray)": (156, 163, 175),
          "baseline_static (red)": (185, 28, 28),
          "ccr_adaptive (blue)": (29, 78, 216)}
# report the actual dominant colours near markers first
out = {}
for name, rgb in colors.items():
    d = np.sqrt(((a - np.array(rgb)) ** 2).sum(2))
    mask = d < 60
    ys = []
    for t in range(1, 13):
        cx = int(round(tx(t)))
        top = 335 if cx < 2400 else 150   # skip the legend box (rows 150-330, x < 2400)
        win = mask[top:960, cx - 6:cx + 7]
        rr = np.nonzero(win.any(1))[0]
        if len(rr) == 0:
            ys.append(None); continue
        # group contiguous runs, take the longest (marker body)
        runs, start = [], rr[0]
        for i in range(1, len(rr)):
            if rr[i] != rr[i - 1] + 1:
                runs.append((start, rr[i - 1])); start = rr[i]
        runs.append((start, rr[-1]))
        r = max(runs, key=lambda s: s[1] - s[0])
        ys.append(round(float(val(top + (r[0] + r[1]) / 2)), 2))
    out[name] = ys
for k, v in out.items():
    print(f"{k:24s}", v)
b, n, g = out["baseline_static (red)"], out["naive_subagent (gray)"], out["ccr_adaptive (blue)"]
if None not in b + g + n:
    print("sum over 12 turns  baseline %.1f  naive %.1f  ccr_adaptive %.1f" % (sum(b), sum(n), sum(g)))
    print("ccr_adaptive vs baseline, area over 12 turns: %+.1f%%" % (100 * (sum(g) / sum(b) - 1)))
    print("naive vs baseline, area over 12 turns: %+.1f%%" % (100 * (sum(n) / sum(b) - 1)))
    print("peaks  baseline %.1f  naive %.1f  ccr_adaptive %.1f" % (max(b), max(n), max(g)))
    drops = [(t + 1, g[t - 1], g[t]) for t in range(1, 12) if g[t] < g[t - 1]]
    print("ccr_adaptive drops (turn, before, after, pct):", [(t, x, y, round(100 * (y / x - 1), 1)) for t, x, y in drops])
    first = next(t + 1 for t, v in enumerate(b) if v > 14.336)
    print("baseline first turn above 14.336k:", first)
    json.dump(out, open(sys.argv[2], "w"), indent=1)
