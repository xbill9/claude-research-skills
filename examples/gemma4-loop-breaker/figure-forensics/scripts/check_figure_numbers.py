"""Recompute every derived number that Figures 1-3 print, from the counts the paper states (PDF, Tables 1-3, §3.3)."""
import math
from scipy.stats import fisher_exact, binomtest

def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)

print("== Table 1 / Table 2 rates and Wilson 95% CIs (n=129) ==")
for name, k in [("T1 baseline", 23), ("T1 hidden-thoughts", 35), ("T1 calibrated", 51),
                ("M0", 15), ("M1", 18), ("M2", 22), ("M3", 25), ("M4", 27), ("M5", 29), ("M6", 31)]:
    lo, hi = wilson(k, 129); print(f"{name:20s} {k:3d}/129 = {100*k/129:5.2f}%  Wilson [{lo:.1f}, {hi:.1f}]")

print("\n== Trap-25 (Table 3) ==")
for name, k in [("baseline_static", 4), ("naive_subagent", 5), ("ccr_only", 18), ("ccr_adaptive", 24)]:
    lo, hi = wilson(k, 25); print(f"{name:16s} {k}/25 = {100*k/25:.1f}%  Wilson [{lo:.1f}, {hi:.1f}]")
for alt in ("two-sided", "greater"):
    print(f"Fisher exact 24/25 vs 4/25 ({alt}): p = {fisher_exact([[24, 1], [4, 21]], alternative=alt)[1]:.3e}")
turns = [11.04, 10.72, 8.76, 6.96]
print("sum of avg turns x 25 episodes x 4 configs =", round(sum(t * 25 for t in turns), 2))
for lab, base, vals in [("think tokens", 45220, [51118, 35881, 24842]), ("post-reset KV", 159816, [190410, 85148, 46689])]:
    print(lab, "changes vs baseline:", [f"{100*(v/base-1):+.1f}%" for v in vals])

print("\n== Gaps quoted in text / Figure 1 / Figure 2 ==")
print("Stage-1 gain 39.5-17.8 =", round(100*51/129 - 100*23/129, 1), "pts")
print("Tax: Table1 calibrated - M2 =", round(100*51/129 - 100*22/129, 1), "pts;", 51 - 22, "tasks")
print("M2->M6 tasks recovered:", 31 - 22, "of 29 =", f"{100*9/29:.1f}%;  M0->M6:", 31 - 15, "tasks")
print("Remaining gap M6 vs Stage-1 ceiling:", round(100*(51-31)/129, 1), "pts,", 51 - 31, "tasks")
print("M6/M0 ratio:", round(31/15, 2))
print("Compaction M0->M6:", f"{100*(4.7/68.2-1):.1f}%", " M0->M1 pts:", round(68.2-44.0, 1),
      " M2->M3 (120-line reads + parser):", f"{100*(8.5/31.0-1):.1f}%")
print("thinking budget 4096->512:", f"{100*(512/4096-1):.1f}%")
print("softmax dilution 0.72->0.06: log2 ratio =", round(math.log2(0.72/0.06), 2), "bits (paper says +4.51 bits)")
print("58-task SE at p=0.2:", f"{100*math.sqrt(0.2*0.8/58):.2f}%", " pts/task:", round(100/58, 2))

print("\n== Figure 3(a) per-repo labels -> implied integer counts ==")
repos = {"fastapi": (67, [10.4, 22.4, 37.3]), "rich": (48, [12.5, 25.0, 41.7]),
         "requests": (13, [15.4, 23.1, 38.5]), "httpx": (1, [0.0, 100.0, 100.0])}
tot = [0, 0, 0]
for r, (n, pcts) in repos.items():
    ks = []
    for i, p in enumerate(pcts):
        k = round(p * n / 100); assert abs(100 * k / n - p) < 0.05, (r, p); ks.append(k); tot[i] += k
    print(f"{r:9s} n={n:2d} share={100*n/129:.1f}%  M0/M6/Stage-1 = {ks}  ({[f'{100*k/n:.1f}' for k in ks]})")
print("column totals M0/M6/Stage-1:", tot, "(paper: 15, 31, 51)")
print("sum of n:", sum(v[0] for v in repos.values()))
lo, hi = wilson(1, 1); print(f"httpx 1/1 Wilson 95% CI: [{lo:.1f}, {hi:.1f}]")
lo, hi = wilson(0, 1); print(f"httpx 0/1 Wilson 95% CI: [{lo:.1f}, {hi:.1f}]")
print("sci-trap 5/5 vs 1/5 Fisher two-sided p =", f"{fisher_exact([[5,0],[1,4]])[1]:.3f}")
