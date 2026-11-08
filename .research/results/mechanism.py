# -*- coding: utf-8 -*-
"""Mechanism test for the 1-NN reversal.

Hypothesis: 1-NN borrows the LEVEL y of the nearest calibration point; different
donors sit at different levels for the same prediction, so adding a donor introduces
level jumps -> harm. If instead we borrow the RESIDUAL (y - pred) of the nearest
point and add it to the test prediction, the donor-specific level cancels and the
harm should disappear.

If 1nn_resid stops hurting, the mechanism is donor-specific level offset.
"""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.isotonic import IsotonicRegression
from scipy import stats
warnings.filterwarnings("ignore")
OUT = r"C:\Users\Administrator\AppData\Local\Temp\mechanism.json"
NDRAW = 200
K = 8
MS = [1, 2]
CALS = ["affine", "isotonic", "1nn", "1nn_resid"]

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

def calib(kind, ps, ys, p):
    if kind == "1nn":
        return ys[np.abs(ps[:, None] - p[None, :]).argmin(axis=0)]
    if kind == "1nn_resid":
        r = ys - ps
        idx = np.abs(ps[:, None] - p[None, :]).argmin(axis=0)
        return p + r[idx]
    if kind == "isotonic":
        if len(np.unique(ps)) < 2: return p + (ys.mean() - ps.mean())
        try:
            iso = IsotonicRegression(increasing=True, out_of_bounds="clip"); iso.fit(ps, ys); return iso.predict(p)
        except Exception: return p + (ys.mean() - ps.mean())
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

rng = np.random.default_rng(0)
ug = np.unique(grp)
draws = {}; valid = []
for g in ug:
    mm = grp == g
    p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
    if not np.isfinite(p_g).all(): continue
    gc = np.unique(c_g)
    lengths = {c: int((c_g == c).sum()) for c in gc}
    pool = [c for c in gc if lengths[c] >= K]
    ev_cells = [c for c in gc if len([d for d in pool if d != c]) >= max(MS)]
    if not ev_cells or not pool: continue
    arr = {(cal, m): np.full(NDRAW, np.nan) for cal in CALS for m in MS}
    for t in range(NDRAW):
        for m in MS:
            per = {cal: [] for cal in CALS}
            for c in ev_cells:
                donors = [d for d in pool if d != c]
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
                    pr = calib(cal, p_g[sel], y_g[sel], p_g[ev])
                    per[cal].append(float(np.abs(y_g[ev] - pr).mean()))
            for cal in CALS:
                arr[(cal, m)][t] = float(np.mean(per[cal])) if per[cal] else np.nan
    if all(np.isfinite(arr[(c2, 1)]).any() and np.isfinite(arr[(c2, 2)]).any() for c2 in CALS):
        for k2 in arr: draws.setdefault(k2, {})[g] = arr[k2]
        valid.append(g)
print("conditions:", len(valid), flush=True)

def cond(cal, m, agg="mean"):
    return np.array([np.nanmean(draws[(cal, m)][g]) if agg == "mean" else np.nanmedian(draws[(cal, m)][g])
                     for g in valid], float)

print("\n=== ISU: does borrowing the RESIDUAL remove the 1-NN harm? ===")
print("%-11s %8s %8s | delta     p        better" % ("calibrator", "m=1", "m=2"))
fam = []
for cal in CALS:
    a, b = cond(cal, 1), cond(cal, 2)
    dlt = a - b; okk = np.isfinite(dlt)
    t, p = stats.ttest_rel(a[okk], b[okk])
    print("%-11s %8.3f %8.3f | %+.3f  %.4f  %3d/%-3d" % (
        cal, np.nanmean(a), np.nanmean(b), dlt[okk].mean(), p,
        int((dlt[okk] > 0).sum()), okk.sum()), flush=True)
    fam.append((cal, p, float(dlt[okk].mean())))
print("\nHolm over 4 calibrators:")
ps = [f[1] for f in fam]; order = np.argsort(ps); adj = np.ones(len(ps))
for rank, idx in enumerate(order): adj[idx] = min(1.0, ps[idx] * (len(ps) - rank))
for i, f in enumerate(fam):
    print("  %-11s p=%.4f Holm=%.4f %s" % (f[0], f[1], adj[i], "PASS" if adj[i] < 0.05 else "fail"))
json.dump({"n": len(valid), "fam": [{"cal": f[0], "p": f[1], "delta": f[2], "holm": float(adj[i])} for i, f in enumerate(fam)]},
          open(OUT, "w"), indent=1)
