# -*- coding: utf-8 -*-
"""Verify the linchpin: with ONE fixed donor, does adding rows beyond k=16 buy anything?"""
import numpy as np, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")
src = open(r"C:\Users\Administrator\AppData\Local\Temp\v2_main.py", encoding="utf-8").read().split("def main():")[0]
exec(src)
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, d["rpts"])], float)

# rows per cell
from collections import Counter
cnt = Counter(cells.tolist())
print("rows per cell: min %d  median %d  max %d" % (min(cnt.values()), int(np.median(list(cnt.values()))), max(cnt.values())))
print("cells with >=64 rows:", sum(1 for v in cnt.values() if v >= 64), "/", len(cnt))

pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(A[tr], y[tr]); pred[te] = mm.predict(A[te])

def affine(ps, ys, p):
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

rng = np.random.default_rng(0)
KS = [8, 16, 32, 64]
res = {k: [] for k in KS}
for g in np.unique(grp):
    mm = grp == g
    p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
    gc = np.unique(c_g)
    for c in gc:
        ev = c_g == c
        donors = [x for x in gc if x != c and (c_g == x).sum() >= 64]
        if not donors: continue
        dd = rng.choice(donors)
        pool = np.where(c_g == dd)[0]
        for k in KS:
            if len(pool) < k: res[k].append(np.nan); continue
            per = []
            for _ in range(200):
                sel = rng.choice(pool, k, replace=False)
                pr = affine(p_g[sel], y_g[sel], p_g[ev])
                per.append(float(np.abs(y_g[ev] - pr).mean()))
            res[k].append(float(np.median(per)))

print("\nSINGLE FIXED DONOR, scan k within that donor's own rows:")
for k in KS:
    v = np.array(res[k]); print("  k=%2d  MAE %.3f  (n=%d)" % (k, np.nanmean(v), (~np.isnan(v)).sum()))
a = np.array(res[16]); b = np.array(res[64])
ok = ~np.isnan(a) & ~np.isnan(b)
t, p = stats.ttest_rel(b[ok], a[ok])
print("\nk=16 -> 64: delta %+.3f  t=%.3f  p=%.4f  (n=%d paired units)" % ((b-a)[ok].mean(), t, p, ok.sum()))
