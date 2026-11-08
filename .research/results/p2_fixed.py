# -*- coding: utf-8 -*-
"""P2 corrected — preregistration-faithful.

Per (condition, MC draw): sample ONE nested donor permutation, compute cell-macro MAE
for each m. Then aggregate ACROSS DRAWS with mean or median. Then paired across the
11 conditions. 1000 draws.
"""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")
src = open(r"C:\Users\Administrator\AppData\Local\Temp\v2_main.py", encoding="utf-8").read().split("def main():")[0]
exec(src)
OUT = r"C:\Users\Administrator\AppData\Local\Temp\p2_fixed.json"
NDRAW = 1000
MS = [1, 2, 3, 4, 5]

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

GROUPS = list(np.unique(grp))
rng = np.random.default_rng(0)
# per condition, per m: array of NDRAW cell-macro MAE values
draws = {}
for g in GROUPS:
    mm = grp == g
    p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
    gc = np.unique(c_g)
    arr = {m: np.full(NDRAW, np.nan) for m in MS}
    for t in range(NDRAW):
        for c in gc:
            ev = c_g == c
            donors = [x for x in gc if x != c]
            if not donors: continue
            order = list(rng.permutation(donors))
            for m in MS:
                if m > len(donors): continue
                sel = np.concatenate([np.where(c_g == dd)[0] for dd in order[:m]])
                if len(sel) < 2: continue
                arr[m][t] = np.nan if np.isnan(arr[m][t]) else arr[m][t]
        # cell-macro within this draw
        for m in MS:
            vals = []
            for c in gc:
                ev = c_g == c
                donors = [x for x in gc if x != c]
                if m > len(donors): continue
                order = list(rng.permutation(donors))
                sel = np.concatenate([np.where(c_g == dd)[0] for dd in order[:m]])
                if len(sel) < 2: continue
                vals.append(float(np.abs(y_g[ev] - affine(p_g[sel], y_g[sel], p_g[ev])).mean()))
            arr[m][t] = float(np.mean(vals)) if vals else np.nan
    draws[g] = arr
    print("  condition %s done" % g, flush=True)

res = {}
for agg in ("mean", "median"):
    per_cond = {m: np.array([np.nanmean(draws[g][m]) if agg == "mean" else np.nanmedian(draws[g][m])
                             for g in GROUPS]) for m in MS}
    res[agg] = {m: float(np.nanmean(per_cond[m])) for m in MS}
    print("\n=== %s across draws ===" % agg)
    for m in MS:
        print("  m=%d  %.3f" % (m, res[agg][m]))
    for a, b in [(1, 2), (2, 3), (3, 4), (4, 5)]:
        dlt = (per_cond[a] - per_cond[b])
        ok = np.isfinite(dlt)
        bs = np.array([np.mean(rng.choice(dlt[ok], ok.sum(), replace=True)) for _ in range(5000)])
        t, p = stats.ttest_rel(per_cond[a][ok], per_cond[b][ok])
        print("  %d->%d  delta %+.3f  CI [%+.3f, %+.3f]  t=%.2f p=%.3f  better %d/%d" % (
            a, b, dlt[ok].mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5),
            t, p, int((dlt[ok] > 0).sum()), ok.sum()), flush=True)

print("\n=== joint gate: delta>=0.15 AND both aggregations >=10/11 ===")
for agg in ("mean", "median"):
    pc = {m: np.array([np.nanmean(draws[g][m]) if agg == "mean" else np.nanmedian(draws[g][m])
                       for g in GROUPS]) for m in MS}
    dlt = pc[1] - pc[2]; ok = np.isfinite(dlt)
    print("  %-7s delta %+.3f  better %d/%d  -> %s" % (
        agg, dlt[ok].mean(), int((dlt[ok] > 0).sum()), ok.sum(),
        "PASS" if (dlt[ok].mean() >= 0.15 and (dlt[ok] > 0).sum() >= 10) else "FAIL"))
json.dump(res, open(OUT, "w"), indent=1)
