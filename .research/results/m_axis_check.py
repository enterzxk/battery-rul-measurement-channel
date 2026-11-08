# -*- coding: utf-8 -*-
"""Action 2: is the m-knee a group-size artifact? Recompute on condition 11 alone (4 cells),
and redo the m-axis under a LOCKED protocol (per-condition shared affine, pool excludes the
evaluated cell entirely, cell-macro weighted by cell not by row)."""
import numpy as np, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")
src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
NDRAW = 300
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, d["rpts"])], float)

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
MS = [1, 2, 3, 4]

def run(groups, label):
    out = {m: [] for m in MS}; base = []
    for g in groups:
        mm = grp == g
        p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
        gc = np.unique(c_g)
        base.append(float(np.mean([np.abs(y_g[c_g == c] - p_g[c_g == c]).mean() for c in gc])))
        for c in gc:
            ev = c_g == c
            donors = [x for x in gc if x != c]
            for m in MS:
                if m > len(donors): out[m].append(np.nan); continue
                per = []
                for _ in range(NDRAW):
                    ds = rng.choice(donors, m, replace=False)
                    sel = np.concatenate([np.where(c_g == dd)[0] for dd in ds])
                    if len(sel) < 2: continue
                    pr = affine(p_g[sel], y_g[sel], p_g[ev])
                    per.append(float(np.abs(y_g[ev] - pr).mean()))
                out[m].append(float(np.median(per)) if per else np.nan)
    print("\n=== %s (n_cells=%d) baseline=%.3f ===" % (label, len(base), np.mean(base)))
    for m in MS:
        v = np.array(out[m]); ok = ~np.isnan(v)
        print("  m=%d  MAE %.3f  (n=%d)" % (m, np.nanmean(v), ok.sum()), flush=True)
    return out

groups = np.unique(grp)
run(groups, "ALL conditions")
# condition 11 alone
g11 = [g for g in groups if (grp == g).sum() <= 8]
if g11:
    for g in g11:
        n_cells = len(np.unique(cells[grp == g]))
        if n_cells <= 5:
            run([g], "condition %s only (%d cells)" % (g, n_cells))
            break
