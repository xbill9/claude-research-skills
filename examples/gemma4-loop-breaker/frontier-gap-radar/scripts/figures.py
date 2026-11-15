"""Figures at 300 DPI: (1) papers x capabilities heatmap with column counts and pairwise co-coverage;
(2) impact-vs-compute for blueprints (placements are judgements)."""
import json, csv, pathlib
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
ROOT = pathlib.Path(__file__).resolve().parent.parent
cod = json.loads((ROOT / "data/coding.json").read_text()); A = json.loads((ROOT / "data/analysis.json").read_text())
rows = list(csv.DictReader(open(ROOT / "matrix.csv")))
D = list(cod["dimensions"]); S = cod["short"]
INK, INK2, GRID, BLUE, EMPTY = "#0b0b0b", "#52514e", "#d9d8d3", "#2a78d6", "#f0efec"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "axes.edgecolor": GRID, "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK})
# order rows by facet group then year
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.4, 5.6), gridspec_kw={"width_ratios": [1.05, 1], "wspace": 0.55})
mat = [[int(r[[k for k in r if k.startswith(dm + "_") and not k.endswith("evidence")][0]]) for dm in D] for r in rows]
labels = [f"{r['short']}{' *' if r['status']=='preprint' else ''}" for r in rows]
ax.imshow(mat, cmap=ListedColormap([EMPTY, BLUE]), aspect="auto", vmin=0, vmax=1)
ax.set_xticks(range(len(D))); ax.set_xticklabels([f"{dm}\n{S[dm]}" for dm in D], rotation=60, ha="right", fontsize=5.6)
ax.set_yticks(range(len(rows))); ax.set_yticklabels(labels, fontsize=5.8)
for i in range(len(rows) + 1): ax.axhline(i - 0.5, color="white", lw=1.2)
for j in range(len(D) + 1): ax.axvline(j - 0.5, color="white", lw=1.2)
for j, dm in enumerate(D):
    ax.text(j, -0.9, str(A["counts"][dm]), ha="center", va="bottom", fontsize=6.5, fontweight="bold")
ax.set_title("Coverage (filled = abstract evidence)\nnumbers = papers per dimension; * = preprint", fontsize=7, pad=14, loc="left")
ax.tick_params(length=0); [s.set_visible(False) for s in ax.spines.values()]
# pairwise
import numpy as np
n = len(D); C = np.zeros((n, n), int)
for x in A["pairs"]:
    i, j = D.index(x["a"]), D.index(x["b"]); C[i, j] = C[j, i] = x["observed"]
for i, dm in enumerate(D): C[i, i] = A["counts"][dm]
seq = ListedColormap(["#f0efec", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])
ax2.imshow(np.minimum(C, 7), cmap=seq, vmin=0, vmax=7)
gapdims = {tuple(sorted(g["dims"])): g["id"] for g in A["gaps"] if g["kind"] == "pair"}
for i in range(n):
    for j in range(n):
        lab = str(C[i, j]); key = tuple(sorted((D[i], D[j])))
        if i != j and key in gapdims and i > j: lab += f"\n{gapdims[key]}"
        ax2.text(j, i, lab, ha="center", va="center", fontsize=5.8 if "\n" in lab else 6.5, color="white" if C[i, j] >= 4 else INK, fontweight="bold" if i == j else "normal")
ax2.set_xticks(range(n)); ax2.set_xticklabels(D, fontsize=6.5); ax2.set_yticks(range(n)); ax2.set_yticklabels([f"{dm} {S[dm]}" for dm in D], fontsize=6)
for k in range(n + 1): ax2.axhline(k - 0.5, color="white", lw=1.2); ax2.axvline(k - 0.5, color="white", lw=1.2)
ax2.tick_params(length=0); [s.set_visible(False) for s in ax2.spines.values()]
ax2.set_title("Co-coverage: papers filling both dimensions\n(diagonal = single-dimension count; Gk = blind spot)", fontsize=7, loc="left", pad=6)
fig.savefig(ROOT / "figures/fig1_capability_heatmap.png", dpi=300, bbox_inches="tight", facecolor="white"); plt.close(fig)
# blueprint chart
bp = json.loads((ROOT / "data/blueprints.json").read_text())
fig, ax = plt.subplots(figsize=(6.2, 3.3))
for b in bp:
    alive = b["status"] != "dropped"
    ax.scatter(b["compute"], b["impact"], s=70, color=BLUE if alive else "#ffffff", edgecolor=BLUE if alive else "#8c8b86", linewidth=1.4, zorder=3)
    ax.annotate(f"{b['id']} ({b['status']})", (b["compute"], b["impact"]), xytext=(7, 4 if b["id"] != "B4" else -10), textcoords="offset points", fontsize=7, color=INK if alive else INK2)
ax.set_xlim(0.5, 5.2); ax.set_ylim(0.8, 5.2); ax.set_xticks(range(1, 6)); ax.set_yticks(range(1, 6))
ax.set_xlabel("Compute required (judgement, 1 = a few GPU-days, 5 = large training runs)"); ax.set_ylabel("Expected impact (judgement, 1-5)")
ax.grid(color=GRID, lw=0.6); ax.set_axisbelow(True); [ax.spines[s].set_visible(False) for s in ("top", "right")]
ax.set_title("Blueprints: impact vs compute — placements are the surveyor's judgement, not measurements\nfilled = survives the prior-art check; hollow = dropped", fontsize=7.5, loc="left")
fig.savefig(ROOT / "figures/fig2_blueprint_impact_compute.png", dpi=300, bbox_inches="tight", facecolor="white"); plt.close(fig)
print("ok")
