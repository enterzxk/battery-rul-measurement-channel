# -*- coding: utf-8 -*-
"""Round 2 — the decisive separation experiment.

At a FIXED row budget k, does spreading those rows over more donor cells help?
If yes -> donor identity has an effect independent of row count.
If no  -> P2's effect is entirely "more rows", and the result is purely descriptive.

MC aggregation per CD-006: cell-macro MAE within (condition, draw, m), then
mean/median across draws, then paired across the 11 conditions.
"""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")
src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
OUT = r"C:\Users\Administrator\AppData\Local\Temp\matched_budget.json"
NDRAW = 200
KS = [8, 16, 32]
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

GROUPS = list(np.unique(grp))
rng = np.random.default_rng(0)
draws = {(k, m): {} for k in KS for m in MS}

for g in GROUPS:
    mm = grp == g
    p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
    gc = np.unique(c_g)
    for k in KS:
        for m in MS:
            arr = np.full(NDRAW, np.nan)
            for t in range(NDRAW):
                vals = []
                for c in gc:
                    ev = c_g == c
                    donors = [x for x in gc if x != c]
                    if m > len(donors): continue
                    ds = rng.choice(donors, m, replace=False)
                    per_donor = max(1, k // m)
                    sel = []
                    ok = True
                    for dd in ds:
                        pool = np.where(c_g == dd)[0]
                        if len(pool) < per_donor: ok = False; break
                        sel.extend(rng.choice(pool, per_donor, replace=False))
                    if not ok or len(sel) < 2: continue
                    sel = np.array(sel)
                    vals.append(float(np.abs(y_g[ev] - affine(p_g[sel], y_g[sel], p_g[ev])).mean()))
                arr[t] = float(np.mean(vals)) if vals else np.nan
            draws[(k, m)][g] = arr
    print("  %s done" % g, flush=True)

print("\n=== MAE at matched row budget k, by donor count m ===")
print("   k |" + "".join("    m=%d " % m for m in MS) + " |  m1->m4 (mean agg)")
res = {}
for k in KS:
    row = []
    for m in MS:
        v = np.array([np.nanmean(draws[(k, m)][g]) for g in GROUPS])
        row.append(float(np.nanmean(v)))
        res["k%d_m%d" % (k, m)] = row[-1]
    print("%4d |" % k + "".join("  %6.3f " % v for v in row) + " |   %+.3f" % (row[0] - row[-1]))

print("\n=== paired across 11 conditions, MC-aggregated ===")
for k in KS:
    for a, b in [(1, 2), (2, 3), (1, 4)]:
        for agg in ("mean", "median"):
            va = np.array([np.nanmean(draws[(k, a)][g]) if agg == "mean" else np.nanmedian(draws[(k, a)][g]) for g in GROUPS])
            vb = np.array([np.nanmean(draws[(k, b)][g]) if agg == "mean" else np.nanmedian(draws[(k, b)][g]) for g in GROUPS])
            dlt = va - vb; ok = np.isfinite(dlt)
            if ok.sum() < 6: continue
            t, p = stats.ttest_rel(va[ok], vb[ok])
            bs = np.array([np.mean(rng.choice(dlt[ok], ok.sum(), replace=True)) for _ in range(3000)])
            print("  k=%2d m%d->m%d %-6s delta %+.3f CI [%+.3f,%+.3f] p=%.3f better %d/%d" % (
                k, a, b, agg, dlt[ok].mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5),
                p, int((dlt[ok] > 0).sum()), ok.sum()), flush=True)
json.dump(res, open(OUT, "w"), indent=1)
print("\nsaved", OUT)
