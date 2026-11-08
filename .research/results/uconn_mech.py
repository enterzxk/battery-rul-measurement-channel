# -*- coding: utf-8 -*-
import numpy as np, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.isotonic import IsotonicRegression
from scipy import stats
warnings.filterwarnings("ignore")

def holm(pvals):
    p = np.asarray(pvals, float); n = len(p)
    order = np.argsort(p); adj = np.empty(n); running = 0.0
    for i, idx in enumerate(order):
        running = max(running, p[idx] * (n - i))
        adj[idx] = min(1.0, running)
    return adj

src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
NDRAW = 200; K = 8; MS = [1, 2]
CALS = ["affine", "isotonic", "1nn", "1nn_resid"]
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, d["rpts"])], float)
pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(A[tr], y[tr]); pred[te] = mm.predict(A[te])

def calib(kind, ps, ys, p):
    if kind == "1nn": return ys[np.abs(ps[:, None] - p[None, :]).argmin(axis=0)]
    if kind == "1nn_resid":
        r = ys - ps; idx = np.abs(ps[:, None] - p[None, :]).argmin(axis=0); return p + r[idx]
    if kind == "isotonic":
        if len(np.unique(ps)) < 2: return p + (ys.mean() - ps.mean())
        try:
            iso = IsotonicRegression(increasing=True, out_of_bounds="clip"); iso.fit(ps, ys); return iso.predict(p)
        except Exception: return p + (ys.mean() - ps.mean())
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

rng = np.random.default_rng(0); ug = np.unique(grp)
draws = {}; valid = []
for g in ug:
    mm = grp == g
    p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
    gc = np.unique(c_g)
    lengths = {c: int((c_g == c).sum()) for c in gc}
    pool = [c for c in gc if lengths[c] >= K]
    ev_cells = [c for c in gc if len([x for x in pool if x != c]) >= max(MS)]
    if not ev_cells or not pool: continue
    arr = {(cal, m): np.full(NDRAW, np.nan) for cal in CALS for m in MS}
    for t in range(NDRAW):
        for m in MS:
            per = {cal: [] for cal in CALS}
            for c in ev_cells:
                donors = [x for x in pool if x != c]
                if m > len(donors): continue
                ds = rng.choice(donors, m, replace=False)
                base = K // m; rem = K % m
                takes = [base + (1 if i < rem else 0) for i in range(m)]
                sel, okk = [], True
                for dd, tk in zip(ds, takes):
                    q = np.where(c_g == dd)[0]
                    if len(q) < tk: okk = False; break
                    sel.extend(rng.choice(q, tk, replace=False))
                if not okk or len(sel) != K: continue
                sel = np.array(sel); ev = c_g == c
                for cal in CALS:
                    per[cal].append(float(np.abs(y_g[ev] - calib(cal, p_g[sel], y_g[sel], p_g[ev])).mean()))
            for cal in CALS:
                arr[(cal, m)][t] = float(np.mean(per[cal])) if per[cal] else np.nan
    if all(np.isfinite(arr[(x, 1)]).any() and np.isfinite(arr[(x, 2)]).any() for x in CALS):
        for k2 in arr: draws.setdefault(k2, {})[g] = arr[k2]
        valid.append(g)

def cond(cal, m):
    return np.array([np.nanmean(draws[(cal, m)][g]) for g in valid], float)

print("UConn locked follow-up — conditions: %d" % len(valid))
print("%-11s %8s %8s | delta     p        better" % ("calibrator", "m=1", "m=2"))
fam = []
for cal in CALS:
    a, b = cond(cal, 1), cond(cal, 2)
    dlt = a - b; okk = np.isfinite(dlt)
    t, p = stats.ttest_rel(a[okk], b[okk])
    print("%-11s %8.3f %8.3f | %+.3f  %.4f  %3d/%-3d" % (
        cal, np.nanmean(a), np.nanmean(b), dlt[okk].mean(), p, int((dlt[okk] > 0).sum()), okk.sum()))
    fam.append((cal, p, float(dlt[okk].mean())))

print("\nHolm (corrected, cumulative max):")
adj = holm([f[1] for f in fam])
for i, f in enumerate(fam):
    print("  %-11s p=%.4f Holm=%.4f %s" % (f[0], f[1], adj[i], "PASS" if adj[i] < 0.05 else "fail"))

a1, b1 = cond("1nn", 1), cond("1nn", 2)
a2, b2 = cond("1nn_resid", 1), cond("1nn_resid", 2)
d_level = a1 - b1; d_resid = a2 - b2
inter = d_resid - d_level; okk = np.isfinite(inter)
t, p = stats.ttest_rel(d_resid[okk], d_level[okk])
print("\ninteraction (delta_resid - delta_level) = %+.3f  t=%.2f p=%.4f  n=%d" % (
    inter[okk].mean(), t, p, okk.sum()))
