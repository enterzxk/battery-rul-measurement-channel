# -*- coding: utf-8 -*-
"""Add the controls CD-013 demanded: uncalibrated, intercept-only, and a second frozen
base predictor (Ridge instead of HGB). Cycle-unit RUL, k=8, common support."""
import numpy as np, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.isotonic import IsotonicRegression
from scipy import stats
warnings.filterwarnings("ignore")

def holm(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); a = np.empty(n); r = 0.0
    for i, idx in enumerate(o):
        r = max(r, p[idx] * (n - i)); a[idx] = min(1.0, r)
    return a

src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
NDRAW = 200; K = 8; MS = [1, 2]
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_cum"][c] - v for c, v in zip(cells, d["cum"])], float)

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

def run(pred, label):
    rng = np.random.default_rng(0); ug = np.unique(grp)
    CALS = ["none", "intercept", "affine", "isotonic", "1nn"]
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
                        if cal == "none": pr = p_g[ev]
                        elif cal == "intercept": pr = p_g[ev] + (y_g[sel].mean() - p_g[sel].mean())
                        else: pr = calib(cal, p_g[sel], y_g[sel], p_g[ev])
                        per[cal].append(float(np.abs(y_g[ev] - pr).mean()))
                for cal in CALS:
                    arr[(cal, m)][t] = float(np.mean(per[cal])) if per[cal] else np.nan
        if all(np.isfinite(arr[(x, 1)]).any() and np.isfinite(arr[(x, 2)]).any() for x in CALS):
            for k2 in arr: draws.setdefault(k2, {})[g] = arr[k2]
            valid.append(g)
    print("\n=== %s (conditions %d) ===" % (label, len(valid)))
    print("%-11s %9s %9s | delta     p        better  Holm" % ("calibrator", "m=1", "m=2"))
    fam = []
    for cal in CALS:
        a = np.array([np.nanmean(draws[(cal, 1)][g]) for g in valid])
        b = np.array([np.nanmean(draws[(cal, 2)][g]) for g in valid])
        dlt = a - b; okk = np.isfinite(dlt)
        t, p = stats.ttest_rel(a[okk], b[okk])
        fam.append((cal, p, float(dlt[okk].mean()), float(np.nanmean(a)), int((dlt[okk] > 0).sum()), int(okk.sum())))
    adj = holm([f[1] for f in fam])
    for i, f in enumerate(fam):
        print("%-11s %9.2f %9.2f | %+8.2f  %.4f  %2d/%-2d   %.4f%s" % (
            f[0], f[3], f[3] - f[2], f[2], f[1], f[4], f[5], adj[i], "" if adj[i] < 0.05 else " ns"))

# base predictor 1: HGB
pred_hgb = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(A[tr], y[tr]); pred_hgb[te] = mm.predict(A[te])
run(pred_hgb, "base predictor = HGB")

# base predictor 2: Ridge on standardised features
pred_ridge = np.full(len(y), np.nan)
mu, sd = A.mean(0), A.std(0) + 1e-9
Az = (A - mu) / sd
for g in np.unique(grp):
    te = grp == g; tr = ~te
    m2 = Ridge(alpha=10.0); m2.fit(Az[tr], y[tr]); pred_ridge[te] = m2.predict(Az[te])
run(pred_ridge, "base predictor = Ridge")
