# -*- coding: utf-8 -*-
"""I-1 probe: at the SAME budget k, does WHERE you place the labels change the sign?

random-k  vs  quantile-spread-k  (both cell-disjoint: labels only from other cells)
"""
import numpy as np, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")
src = open(r"C:\Users\Administrator\AppData\Local\Temp\v2_main.py", encoding="utf-8").read().split("def main():")[0]
exec(src)
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, d["rpts"])], float)

def affine(ps, ys, p):
    if np.std(ps) < 1e-9: return p + (ys.mean() - ps.mean())
    a, bb = np.polyfit(ps, ys, 1)
    return a * p + bb

KS = [2, 3, 4, 6, 8, 16]
rng = np.random.default_rng(0)
res = {("rand", k): [] for k in KS}
res.update({("quant", k): [] for k in KS})
res.update({("none", 0): []})

for g in np.unique(grp):
    te = grp == g; tr = ~te
    m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    m.fit(A[tr], y[tr])
    p_g = m.predict(A[te]); y_g = y[te]; c_g = cells[te]
    gc = np.unique(c_g)
    base = []
    for c in gc:
        ev = c_g == c
        base.append(float(np.abs(y_g[ev] - p_g[ev]).mean()))
    res[("none", 0)].append(float(np.mean(base)))

    for k in KS:
        for mode in ("rand", "quant"):
            per_cell = []
            for c in gc:
                ev = c_g == c
                pool = np.where(~ev)[0]
                if len(pool) < k: per_cell.append(np.nan); continue
                if mode == "rand":
                    sel = rng.choice(pool, k, replace=False)
                else:
                    order = pool[np.argsort(p_g[pool])]
                    qs = np.linspace(0, 1, k)
                    sel = np.array([order[min(int(round(q*(len(order)-1))), len(order)-1)] for q in qs])
                    sel = np.unique(sel)
                pred = affine(p_g[sel], y_g[sel], p_g[ev])
                per_cell.append(float(np.abs(y_g[ev] - pred).mean()))
            res[(mode, k)].append(float(np.nanmean(per_cell)))

base = np.array(res[("none", 0)])
print("  k    random    quantile   delta(quant-rand)   p_wilcox")
for k in KS:
    r = np.array(res[("rand", k)]); q = np.array(res[("quant", k)])
    mm = ~np.isnan(r) & ~np.isnan(q)
    try: pw = stats.wilcoxon(q[mm], r[mm]).pvalue
    except Exception: pw = float("nan")
    print("%3d   %7.3f   %7.3f      %+7.3f            %.4f" % (k, np.nanmean(r), np.nanmean(q), (q-r)[mm].mean(), pw))
print()
for k in KS:
    r = np.array(res[("rand", k)]); q = np.array(res[("quant", k)]); mm = ~np.isnan(r)
    print("k=%2d  rand vs k=0: %+.3f (p=%.4f, %d/11) | quant vs k=0: %+.3f (p=%.4f, %d/11)" % (
        k, (r-base)[mm].mean(), stats.wilcoxon(r[mm], base[mm]).pvalue, int(((r-base)[mm] < 0).sum()),
        (q-base)[mm].mean(), stats.wilcoxon(q[mm], base[mm]).pvalue, int(((q-base)[mm] < 0).sum())))
