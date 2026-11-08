# -*- coding: utf-8 -*-
"""Is the cost framing real? Cross k (labeled rows) with m (distinct donor cells).

If at FIXED k, more donors (m) helps -> donor diversity has value beyond row count,
and 'acquisition cost' is a real axis. If not, only row count matters and the
framing collapses to 'more labels is better'.
"""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")
src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
NDRAW = 200
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, d["rpts"])], float)

pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    m_ = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    m_.fit(A[tr], y[tr]); pred[te] = m_.predict(A[te])
print("preds ready", flush=True)

def affine(ps, ys, p):
    if ps.size < 2 or np.std(ps) < 1e-12:
        return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    b = ys.mean() - a * ps.mean()
    return a * p + b

rng = np.random.default_rng(0)
KS = [4, 8, 16, 32]
MS = [1, 2, 3, 4]
grid = {(k, m): [] for k in KS for m in MS}
base = []

for g in np.unique(grp):
    mm = grp == g
    p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
    gc = np.unique(c_g)
    base.append(float(np.mean([np.abs(y_g[c_g == c] - p_g[c_g == c]).mean() for c in gc])))
    for c in gc:
        ev = c_g == c
        donors = [x for x in gc if x != c]
        if len(donors) < 1: continue
        for k in KS:
            for m in MS:
                if m > len(donors): grid[(k, m)].append(np.nan); continue
                per = []
                for _ in range(NDRAW):
                    ds = rng.choice(donors, m, replace=False)
                    per_donor = max(1, k // m)
                    sel = []
                    for dd in ds:
                        pool = np.where(c_g == dd)[0]
                        if len(pool) == 0: continue
                        take = min(per_donor, len(pool))
                        sel.extend(rng.choice(pool, take, replace=False))
                    if len(sel) < 2: continue
                    sel = np.array(sel)
                    pr = affine(p_g[sel], y_g[sel], p_g[ev])
                    per.append(float(np.abs(y_g[ev] - pr).mean()))
                grid[(k, m)].append(float(np.median(per)) if per else np.nan)

base = np.array(base)
print("\nbaseline k=0: %.3f\n" % base.mean(), flush=True)
print("   k |" + "".join("    m=%d " % m for m in MS) + " |  m-effect (m=4 - m=1)")
for k in KS:
    row = [np.nanmean(grid[(k, m)]) for m in MS]
    eff = row[-1] - row[0]
    print("%4d |" % k + "".join("  %6.3f " % v for v in row) + " |   %+.3f" % eff, flush=True)

print("\nmarginal effect of donor count at fixed k (paired over conditions):")
for k in KS:
    a1 = np.array(grid[(k, 1)]); a4 = np.array(grid[(k, 4)])
    ok = ~np.isnan(a1) & ~np.isnan(a4)
    if ok.sum() < 5: continue
    t, p = stats.ttest_rel(a4[ok], a1[ok])
    print("k=%2d: m1 %.3f -> m4 %.3f  delta %+.3f  p=%.4f  improved %d/%d" % (
        k, a1[ok].mean(), a4[ok].mean(), (a4-a1)[ok].mean(), p, int(((a4-a1)[ok] < 0).sum()), ok.sum()))

print("\nrow-count vs donor-count: compare k=32,m=1 against k=8,m=4 (same 32 rows, 1 vs 4 donors)")
a = np.array(grid[(32, 1)]); b = np.array(grid[(8, 4)])
ok = ~np.isnan(a) & ~np.isnan(b)
t, p = stats.ttest_rel(a[ok], b[ok])
print("k=32,m=1 %.3f  vs  k=8,m=4 %.3f  delta %+.3f  p=%.4f" % (a[ok].mean(), b[ok].mean(), (b-a)[ok].mean(), p))
