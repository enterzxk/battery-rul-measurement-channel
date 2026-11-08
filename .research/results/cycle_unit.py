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
        running = max(running, p[idx] * (n - i)); adj[idx] = min(1.0, running)
    return adj

src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
NDRAW = 200; K = 8; MS = [1, 2]
CALS = ["affine", "isotonic", "1nn", "1nn_resid"]
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y_cycle = np.array([d["eol_cum"][c] - v for c, v in zip(cells, d["cum"])], float)
y_rpt = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, d["rpts"])], float)
print("cycle-unit RUL: min %.0f median %.0f max %.0f" % (y_cycle.min(), np.median(y_cycle), y_cycle.max()), flush=True)

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

def run(y, label):
    pred = np.full(len(y), np.nan)
    for g in np.unique(grp):
        te = grp == g; tr = ~te
        mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
        mm.fit(A[tr], y[tr]); pred[te] = mm.predict(A[te])
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
    print("\n=== %s (conditions %d) ===" % (label, len(valid)))
    print("%-11s %9s %9s | delta      p        better" % ("calibrator", "m=1", "m=2"))
    fam = []
    for cal in CALS:
        a = np.array([np.nanmean(draws[(cal, 1)][g]) for g in valid])
        b = np.array([np.nanmean(draws[(cal, 2)][g]) for g in valid])
        dlt = a - b; okk = np.isfinite(dlt)
        t, p = stats.ttest_rel(a[okk], b[okk])
        print("%-11s %9.2f %9.2f | %+9.2f  %.4f  %3d/%-3d" % (
            cal, np.nanmean(a), np.nanmean(b), dlt[okk].mean(), p,
            int((dlt[okk] > 0).sum()), okk.sum()), flush=True)
        fam.append((cal, p, float(dlt[okk].mean()), float(np.nanmean(a))))
    adj = holm([f[1] for f in fam])
    print("Holm:", "  ".join("%s=%.4f%s" % (f[0], adj[i], "OK" if adj[i] < 0.05 else "ns") for i, f in enumerate(fam)))
    for f, ai in zip(fam, adj):
        print("   %-11s delta %+8.2f = %5.2f%% of baseline %.2f" % (f[0], f[2], 100 * f[2] / f[3], f[3]))

run(y_cycle, "UConn, RUL in REAL CYCLES")
run(y_rpt, "UConn, RUL in RPT counts")
