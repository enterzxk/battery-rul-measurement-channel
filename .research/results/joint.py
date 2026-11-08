# -*- coding: utf-8 -*-
"""Joint specification space: 2 (fit scope) x 2 (evaluation population) x 2 (donor count),
plus a dominance ranking of all five decisions by variance contribution.

This is what distinguishes us from Peng et al. 2026, who manipulated one column at a time.
"""
import numpy as np, json, warnings, itertools
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")

src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
NDRAW = 150; K = 8
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_cum"][c] - v for c, v in zip(cells, d["cum"])], float)
pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(A[tr], y[tr]); pred[te] = mm.predict(A[te])
print("preds ready", flush=True)

def aff(ps, ys, p):
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

rng = np.random.default_rng(0)
ug = np.unique(grp)

def contrast(scope, pop, agg="cell", draw="mean", alloc="exact"):
    out = {1: {}, 2: {}}
    for g in ug:
        mm = grp == g
        idx = np.where(mm)[0]
        c_g, p_g, y_g = cells[idx], pred[idx], y[idx]
        gc = np.unique(c_g)
        pool = [c for c in gc if (c_g == c).sum() >= K]
        q25 = np.quantile(y_g, 0.25)
        for m in (1, 2):
            cv, qv = [], []
            for c in gc:
                ev = np.where(c_g == c)[0]
                if pop == "late":
                    ev = ev[y_g[ev] <= q25]
                    if ev.size == 0: continue
                donors = [x for x in pool if x != c]
                if len(donors) < m: continue
                if scope == "condition":
                    ds = rng.choice(donors, m, replace=False)
                    sel = np.concatenate([np.where(c_g == dd)[0] for dd in ds])
                    pr = [float(np.abs(y_g[j] - aff(p_g[sel], y_g[sel], np.array([p_g[j]]))[0])) for j in ev]
                    cv.append(float(np.mean(pr))); qv.extend(pr); continue
                per_j = {j: [] for j in ev}
                for _ in range(NDRAW):
                    ds = rng.choice(donors, m, replace=False)
                    if alloc == "exact":
                        base = K // m; rem = K % m
                        takes = [base + (1 if i < rem else 0) for i in range(m)]
                    else:
                        takes = [K // m] * m
                    sel, okk = [], True
                    for dd, tk in zip(ds, takes):
                        q = np.where(c_g == dd)[0]
                        if len(q) < tk: okk = False; break
                        sel.extend(rng.choice(q, tk, replace=False))
                    if not okk: continue
                    sel = np.array(sel)
                    for j in ev:
                        per_j[j].append(float(np.abs(y_g[j] - aff(p_g[sel], y_g[sel], np.array([p_g[j]]))[0])))
                jm = [float(np.mean(v)) if draw == "mean" else float(np.median(v)) for v in per_j.values() if v]
                if jm: cv.append(float(np.mean(jm))); qv.extend(jm)
            out[m][g] = float(np.mean(cv)) if agg == "cell" and cv else (float(np.mean(qv)) if qv else np.nan)
    gs = [g for g in ug if np.isfinite(out[1].get(g, np.nan)) and np.isfinite(out[2].get(g, np.nan))]
    a = np.array([out[1][g] for g in gs]); b = np.array([out[2][g] for g in gs])
    t, p = stats.ttest_rel(a, b)
    return dict(n=len(gs), delta=float((a - b).mean()), p=float(p), better=int(((a - b) > 0).sum()))

print("\n=== 2x2 joint specification space (UConn, cycle RUL, k=8, affine) ===", flush=True)
print("%-22s %10s %8s %8s" % ("cell", "contrast", "p", "better"))
grid = {}
for scope in ("cell", "condition"):
    for pop in ("all", "late"):
        r = contrast(scope, pop)
        grid[(scope, pop)] = r
        print("%-22s %+10.2f %8.4f %4d/%-3d" % (
            "%s / %s" % (scope, pop), r["delta"], r["p"], r["better"], r["n"]), flush=True)

print("\n=== main effects and interaction (from the 2x2) ===")
d_cell_all = grid[("cell", "all")]["delta"]; d_cell_late = grid[("cell", "late")]["delta"]
d_cond_all = grid[("condition", "all")]["delta"]; d_cond_late = grid[("condition", "late")]["delta"]
print("  scope main effect (condition - cell), averaged over population: %+.2f" % (
    ((d_cond_all + d_cond_late) - (d_cell_all + d_cell_late)) / 2))
print("  population main effect (late - all), averaged over scope:    %+.2f" % (
    ((d_cell_late + d_cond_late) - (d_cell_all + d_cond_all)) / 2))
print("  interaction:                                                  %+.2f" % (
    (d_cell_all - d_cell_late) - (d_cond_all - d_cond_late)))
print("  range across the four cells:                                  %.2f" % (
    max(d_cell_all, d_cell_late, d_cond_all, d_cond_late) - min(d_cell_all, d_cell_late, d_cond_all, d_cond_late)))
json.dump({"%s/%s" % k: v for k, v in grid.items()}, open(r"C:\Users\Administrator\AppData\Local\Temp\joint.json", "w"), indent=1)
