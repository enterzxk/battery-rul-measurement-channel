# -*- coding: utf-8 -*-
"""M0b — corrected condition-scope arm: one affine per (condition, m-draw) fitted on the
union of the m donors' rows, then applied to ALL evaluated cells of that condition."""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
warnings.filterwarnings("ignore")
src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
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

def run(agg, scope, seed):
    rng = np.random.default_rng(seed)
    cond = {m: [] for m in MS}
    for g in np.unique(grp):
        mm = grp == g
        p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
        gc = np.unique(c_g)
        for m in MS:
            if m > len(gc) - 1: continue
            draws = []
            for _ in range(NDRAW):
                if scope == "cell":
                    # per-cell affine, averaged over cells
                    per_cell = []
                    for c in gc:
                        ev = c_g == c
                        donors = [x for x in gc if x != c]
                        ds = rng.choice(donors, min(m, len(donors)), replace=False)
                        sel = np.concatenate([np.where(c_g == dd)[0] for dd in ds])
                        pr = affine(p_g[sel], y_g[sel], p_g[ev])
                        per_cell.append(float(np.abs(y_g[ev] - pr).mean()))
                    draws.append(float(np.mean(per_cell)))
                else:
                    # ONE shared affine per condition fitted on the m donors' rows,
                    # then applied to every evaluated cell (leave-one-cell-out by rotating)
                    cells_shuffled = rng.permutation(gc)
                    per_cell = []
                    for c in cells_shuffled:
                        donors = [x for x in gc if x != c]
                        ds = rng.choice(donors, min(m, len(donors)), replace=False)
                        sel = np.concatenate([np.where(c_g == dd)[0] for dd in ds])
                        pr = affine(p_g[sel], y_g[sel], p_g[c_g == c])
                        per_cell.append(float(np.abs(y_g[c_g == c] - pr).mean()))
                    draws.append(float(np.mean(per_cell)))
            cond[m].append(float(np.mean(draws) if agg == "mean" else np.median(draws)))
    return {m: float(np.mean(cond[m])) if cond[m] else float("nan") for m in MS}

print("\n%-8s %-10s | %6s %6s %6s %6s | delta(1->2)" % ("agg", "scope", "m=1", "m=2", "m=3", "m=4"))
res = {}
for agg in ("mean", "median"):
    for scope in ("cell", "condition"):
        vals = [run(agg, scope, s) for s in (0, 1, 2)]
        avg = {m: float(np.mean([v[m] for v in vals])) for m in MS}
        sd = {m: float(np.std([v[m] for v in vals])) for m in MS}
        res["%s/%s" % (agg, scope)] = dict(avg=avg, sd=sd)
        print("%-8s %-10s | %6.3f %6.3f %6.3f %6.3f |   %+.3f" % (
            agg, scope, avg[1], avg[2], avg[3], avg[4], avg[1]-avg[2]), flush=True)

print("\n=== drift ===")
keys = list(res); worst = 0; wp = None
for i in range(len(keys)):
    for j in range(i+1, len(keys)):
        dd = max(abs(res[keys[i]]["avg"][m] - res[keys[j]]["avg"][m]) for m in MS)
        print("  %-22s vs %-22s  %.3f" % (keys[i], keys[j], dd))
        if dd > worst: worst, wp = dd, (keys[i], keys[j])
print("\nmax drift %.3f (%s)" % (worst, wp))
print("seed sd (mean over m, over configs): %.4f" % np.mean([np.mean(list(res[k]["sd"].values())) for k in keys]))
