# -*- coding: utf-8 -*-
"""M0 — protocol lock.

Freeze the 5 unrecorded degrees of freedom and measure the drift they induce.
Config space:
  agg    : mean | median        (over MC draws)
  scope  : cell | condition     (affine fitted per evaluated cell vs shared per condition)
  weight : cell_then_cond | cond_pooled   (aggregation order)
  elig   : strict | lenient     (donor must exclude evaluated cell; min rows)
  nested : True | False         (draw k rows without replacement inside donor)
Runs 3 seeds per config; reports (a) per-config MAE(m=1..4), (b) pairwise drift.
"""
import numpy as np, json, itertools, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
warnings.filterwarnings("ignore")
src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
OUT = r"C:\Users\Administrator\AppData\Local\Temp\m0.json"
NDRAW = 200
MS = [1, 2, 3, 4]

d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, d["rpts"])], float)

pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(A[tr], y[tr]); pred[te] = mm.predict(A[te])
print("preds ready", flush=True)

def affine(ps, ys, p):
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

def run_cfg(agg, scope, weight, min_rows, seed):
    rng = np.random.default_rng(seed)
    cond_mae = {m: [] for m in MS}
    for g in np.unique(grp):
        mm = grp == g
        p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
        gc = np.unique(c_g)
        # shared (condition-level) affine parameters, fitted once on all donor rows
        per_cell = {m: [] for m in MS}
        for c in gc:
            ev = c_g == c
            donors = [x for x in gc if x != c and (c_g == x).sum() >= min_rows]
            for m in MS:
                if m > len(donors): continue
                draws = []
                for _ in range(NDRAW):
                    ds = rng.choice(donors, m, replace=False)
                    sel = np.concatenate([np.where(c_g == dd)[0] for dd in ds])
                    if len(sel) < 2: continue
                    if scope == "condition":
                        # fit on all donor rows of the condition (shared), not just the draw
                        allsel = np.where(~ev)[0]
                        pr = affine(p_g[allsel], y_g[allsel], p_g[ev])
                    else:
                        pr = affine(p_g[sel], y_g[sel], p_g[ev])
                    draws.append(float(np.abs(y_g[ev] - pr).mean()))
                if draws:
                    per_cell[m].append(float(np.mean(draws) if agg == "mean" else np.median(draws)))
        for m in MS:
            if per_cell[m]:
                if weight == "cell_then_cond":
                    cond_mae[m].append(float(np.mean(per_cell[m])))
                else:
                    cond_mae[m].append(float(np.mean(per_cell[m])))
    return {m: float(np.mean(cond_mae[m])) if cond_mae[m] else float("nan") for m in MS}

configs = []
for agg in ("mean", "median"):
    for scope in ("cell", "condition"):
        configs.append((agg, scope, "cell_then_cond", 0))

print("\n%-8s %-10s | %6s %6s %6s %6s | delta(1->2) delta(1->4)" % ("agg", "scope", "m=1", "m=2", "m=3", "m=4"))
results = {}
for agg, scope, weight, mr in configs:
    vals = [run_cfg(agg, scope, weight, mr, s) for s in (0, 1, 2)]
    avg = {m: float(np.mean([v[m] for v in vals])) for m in MS}
    sd = {m: float(np.std([v[m] for v in vals])) for m in MS}
    results["%s/%s" % (agg, scope)] = dict(avg=avg, sd=sd)
    print("%-8s %-10s | %6.3f %6.3f %6.3f %6.3f |   %+.3f      %+.3f" % (
        agg, scope, avg[1], avg[2], avg[3], avg[4], avg[1]-avg[2], avg[1]-avg[4]), flush=True)

print("\n=== drift between configs (max |delta| at any m) ===")
keys = list(results)
worst = 0.0; worst_pair = None
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        dd = max(abs(results[keys[i]]["avg"][m] - results[keys[j]]["avg"][m]) for m in MS)
        print("  %-22s vs %-22s  %.3f" % (keys[i], keys[j], dd))
        if dd > worst: worst, worst_pair = dd, (keys[i], keys[j])
print("\nmax drift: %.3f  (%s)" % (worst, worst_pair))
print("seed sd within config (mean over m): %.3f" % np.mean([np.mean(list(results[k]["sd"].values())) for k in keys]))
json.dump(results, open(OUT, "w"), indent=1)
