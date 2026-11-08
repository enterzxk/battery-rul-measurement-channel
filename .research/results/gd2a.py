# -*- coding: utf-8 -*-
"""G-D2a: is the label-budget gain real, or within-cell leakage?

Strict version: calibration labels come ONLY from cells other than the one being
evaluated (cell-disjoint). Compare against the leaky version where labels may come
from the evaluated cell itself.
"""
import numpy as np, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")
src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, d["rpts"])], float)

def affine(psel, ysel, p):
    if np.std(psel) < 1e-9:
        return p + (ysel.mean() - psel.mean())
    a, b = np.polyfit(psel, ysel, 1)
    return a * p + b

KS = [0, 4, 8, 16, 32]
leaky = {k: [] for k in KS}; strict = {k: [] for k in KS}
rng = np.random.default_rng(0)

for g in np.unique(grp):
    te = grp == g; tr = ~te
    m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    m.fit(A[tr], y[tr])
    p_g = m.predict(A[te]); y_g = y[te]; c_g = cells[te]
    gc = np.unique(c_g)
    # ---- leaky: labels may come from any row of the condition
    idx = np.arange(len(y_g))
    for k in KS:
        if k == 0: leaky[k].append(float(np.mean([np.abs(y_g[c_g==c]-p_g[c_g==c]).mean() for c in gc]))); continue
        if k >= len(idx): leaky[k].append(np.nan); continue
        sel = rng.choice(idx, k, replace=False); rest = np.setdiff1d(idx, sel)
        pred = affine(p_g[sel], y_g[sel], p_g[rest])
        leaky[k].append(float(np.mean([np.abs(y_g[rest][c_g[rest]==c]-pred[c_g[rest]==c]).mean()
                                       for c in np.unique(c_g[rest])])))
    # ---- strict: leave one cell out; calibration labels from the OTHER cells only
    for k in KS:
        per_cell = []
        for c in gc:
            ev = c_g == c; cal_pool = ~ev
            if k == 0:
                per_cell.append(float(np.abs(y_g[ev]-p_g[ev]).mean())); continue
            pool = np.where(cal_pool)[0]
            if len(pool) < k:
                per_cell.append(np.nan); continue
            sel = rng.choice(pool, k, replace=False)
            pred = affine(p_g[sel], y_g[sel], p_g[ev])
            per_cell.append(float(np.abs(y_g[ev]-pred).mean()))
        strict[k].append(float(np.nanmean(per_cell)))

print("  k   leaky MAE   strict MAE   strict delta vs k=0")
b_s = np.array(strict[0])
for k in KS:
    print("%3d   %9.3f   %9.3f    %+.3f" % (k, np.nanmean(leaky[k]), np.nanmean(strict[k]),
                                            np.nanmean(np.array(strict[k]) - b_s)))
print()
for k in [8, 16, 32]:
    v = np.array(strict[k]); mm = ~np.isnan(v)
    t, p = stats.ttest_rel(v[mm], b_s[mm])
    try: w = stats.wilcoxon(v[mm], b_s[mm]).pvalue
    except Exception: w = float("nan")
    print("STRICT k=%d: delta %+.3f  t=%.3f p=%.4f  wilcoxon p=%.4f  improved %d/%d" % (
        k, (v-b_s)[mm].mean(), t, p, w, int(((v-b_s)[mm] < 0).sum()), mm.sum()))
