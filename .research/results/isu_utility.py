# -*- coding: utf-8 -*-
"""ISU practical-utility: does the LOO-selected allocation rule recover the best fixed
strategy on the second dataset (57 conditions, much better powered than UConn's 11)?"""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.isotonic import IsotonicRegression
from scipy import stats
from collections import Counter
warnings.filterwarnings("ignore")

def holm(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); a = np.empty(n); r = 0.0
    for i, idx in enumerate(o):
        r = max(r, p[idx] * (n - i)); a[idx] = min(1.0, r)
    return a

z = np.load(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "isu_table.npz"), allow_pickle=True)
X = z["X"]; cells = z["cells"]
grp = X[:, 0].astype(int); rpt = X[:, 1]; feat = X[:, 2:6]; soh = X[:, 6]
eol = {}
for c in np.unique(cells):
    m = cells == c
    rr, ss = rpt[m], soh[m]
    o = np.argsort(rr); rr, ss = rr[o], ss[o]
    hit = np.where(ss <= 0.80)[0]
    if len(hit): eol[c] = int(rr[hit[0]])
ok = np.array([c in eol and r <= eol[c] for c, r in zip(cells, rpt)])
cells, grp, rpt, feat = cells[ok], grp[ok], rpt[ok], feat[ok]
y = np.array([eol[c] - r for c, r in zip(cells, rpt)], float)
pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    if tr.sum() < 50 or te.sum() == 0: continue
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(feat[tr], y[tr]); pred[te] = mm.predict(feat[te])
print("rows %d groups %d" % (len(y), len(np.unique(grp))), flush=True)

NDRAW = 50; K = 8; MS = [1, 2]
CALS = ["intercept", "affine", "isotonic", "1nn"]

def calib(kind, ps, ys, p):
    if kind == "1nn": return ys[np.abs(ps[:, None] - p[None, :]).argmin(axis=0)]
    if kind == "isotonic":
        if len(np.unique(ps)) < 2: return p + (ys.mean() - ps.mean())
        try:
            iso = IsotonicRegression(increasing=True, out_of_bounds="clip"); iso.fit(ps, ys); return iso.predict(p)
        except Exception: return p + (ys.mean() - ps.mean())
    if kind == "intercept": return p + (ys.mean() - ps.mean())
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

rng = np.random.default_rng(0)
T = {}
ug = np.unique(grp)
for g in ug:
    mm = grp == g
    idx = np.where(mm)[0]
    p_g, y_g, c_g = pred[idx], y[idx], cells[idx]
    if not np.isfinite(p_g).all(): continue
    gc = np.unique(c_g)
    pool = [c for c in gc if (c_g == c).sum() >= K]
    ev_cells = [c for c in gc if len([x for x in pool if x != c]) >= max(MS)]
    if not ev_cells: continue
    for cal in CALS:
        for m in MS:
            per = []
            for c in ev_cells:
                donors = [x for x in pool if x != c]
                if len(donors) < m: continue
                vals = []
                for j in np.where(c_g == c)[0]:
                    acc = []
                    for _ in range(NDRAW):
                        ds = rng.choice(donors, m, replace=False)
                        base = K // m; rem = K % m
                        takes = [base + (1 if i < rem else 0) for i in range(m)]
                        sel, okk = [], True
                        for dd, tk in zip(ds, takes):
                            q = np.where(c_g == dd)[0]
                            if len(q) < tk: okk = False; break
                            sel.extend(rng.choice(q, tk, replace=False))
                        if not okk: continue
                        sel = np.array(sel)
                        acc.append(abs(y_g[j] - calib(cal, p_g[sel], y_g[sel], np.array([p_g[j]]))[0]))
                    if acc: vals.append(float(np.mean(acc)))
                if vals: per.append(float(np.mean(vals)))
            if per: T[(cal, m, g)] = float(np.mean(per))
print("arm table entries: %d" % len(T), flush=True)

arms = [(c, m) for c in CALS for m in MS]
print("\n=== ISU arm means ===")
for a in arms:
    v = [T[(a[0], a[1], g)] for g in ug if (a[0], a[1], g) in T]
    print("  %-10s m=%d  %7.3f  (n=%d)" % (a[0], a[1], np.mean(v), len(v)))

sel = []
for g in ug:
    best, bv = None, np.inf
    for a in arms:
        v = [T[(a[0], a[1], x)] for x in ug if x != g and (a[0], a[1], x) in T]
        if len(v) < 10: continue
        if np.mean(v) < bv: bv, best = np.mean(v), a
    if best and (best[0], best[1], g) in T:
        sel.append((g, T[(best[0], best[1], g)], best))
fixed = min(arms, key=lambda a: np.mean([T[(a[0], a[1], g)] for g in ug if (a[0], a[1], g) in T]))
gs = [s[0] for s in sel]
a1 = np.array([s[1] for s in sel])
b1 = np.array([T[(fixed[0], fixed[1], g)] for g in gs])
t, pv = stats.ttest_rel(a1, b1)
print("\n=== ISU leave-one-condition-out selection ===")
print("  selected arms:", dict(Counter(str(s[2]) for s in sel)))
print("  best fixed arm: %s (%.3f)" % (str(fixed), np.mean([T[(fixed[0], fixed[1], g)] for g in ug if (fixed[0], fixed[1], g) in T])))
print("  LOO-selected %.3f vs best-fixed %.3f | delta %+.3f p=%.4f  selected better %d/%d" % (
    a1.mean(), b1.mean(), (a1 - b1).mean(), pv, int((a1 < b1).sum()), len(gs)))
best_m2 = min([a for a in arms if a[1] == 2], key=lambda a: np.mean([T[(a[0], a[1], g)] for g in ug if (a[0], a[1], g) in T]))
best_m1 = min([a for a in arms if a[1] == 1], key=lambda a: np.mean([T[(a[0], a[1], g)] for g in ug if (a[0], a[1], g) in T]))
v2 = np.mean([T[(best_m2[0], 2, g)] for g in ug if (best_m2[0], 2, g) in T])
v1 = np.mean([T[(best_m1[0], 1, g)] for g in ug if (best_m1[0], 1, g) in T])
print("  best m=2 arm %s %.3f  vs  best m=1 arm %s %.3f  -> %+.3f" % (str(best_m2), v2, str(best_m1), v1, v1 - v2))
