# -*- coding: utf-8 -*-
"""Fill the gap: UConn cycle-unit MEDIAN aggregation arm values (main table rows)."""
import numpy as np, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.isotonic import IsotonicRegression
from scipy import stats
warnings.filterwarnings("ignore")

def holm(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); a = np.empty(n); r = 0.0
    for i, idx in enumerate(o):
        r = max(r, p[idx] * (n - i)); a[idx] = min(1.0, r)
    return a

src = open(r"C:\Users\Administrator\AppData\Local\Temp\v2_main.py", encoding="utf-8").read().split("def main():")[0]
exec(src)
NDRAW = 200; K = 8; MS = [1, 2]
CALS = ["affine", "isotonic", "1nn"]
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_cum"][c] - v for c, v in zip(cells, d["cum"])], float)
pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(A[tr], y[tr]); pred[te] = mm.predict(A[te])
print("preds ready", flush=True)

def calib(kind, ps, ys, p):
    if kind == "1nn": return ys[np.abs(ps[:, None] - p[None, :]).argmin(axis=0)]
    if kind == "isotonic":
        if len(np.unique(ps)) < 2: return p + (ys.mean() - ps.mean())
        try:
            iso = IsotonicRegression(increasing=True, out_of_bounds="clip"); iso.fit(ps, ys); return iso.predict(p)
        except Exception: return p + (ys.mean() - ps.mean())
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

rng = np.random.default_rng(0)
draws = {}
ug = np.unique(grp)
for g in ug:
    mm = grp == g
    idx = np.where(mm)[0]
    c_g, p_g, y_g = cells[idx], pred[idx], y[idx]
    gc = np.unique(c_g)
    pool = [c for c in gc if (c_g == c).sum() >= K]
    ev = [c for c in gc if len([x for x in pool if x != c]) >= max(MS)]
    if not ev: continue
    arr = {(cal, m): np.full(NDRAW, np.nan) for cal in CALS for m in MS}
    for t in range(NDRAW):
        for m in MS:
            per = {cal: [] for cal in CALS}
            for c in ev:
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
                sel = np.array(sel); e = c_g == c
                for cal in CALS:
                    per[cal].append(float(np.abs(y_g[e] - calib(cal, p_g[sel], y_g[sel], p_g[e])).mean()))
            for cal in CALS:
                arr[(cal, m)][t] = float(np.mean(per[cal])) if per[cal] else np.nan
    for k2 in arr: draws.setdefault(k2, {})[g] = arr[k2]
print("conditions: %d" % len(ug), flush=True)

print("\n=== UConn cycle-unit, MEDIAN across draws ===")
print("%-10s %9s %9s | delta     p        better  Holm" % ("calibrator", "m=1", "m=2"))
fam = []
for cal in CALS:
    a = np.array([np.nanmedian(draws[(cal, 1)][g]) for g in ug])
    b = np.array([np.nanmedian(draws[(cal, 2)][g]) for g in ug])
    dlt = a - b; ok = np.isfinite(dlt)
    t, p = stats.ttest_rel(a[ok], b[ok])
    fam.append((cal, p, float(dlt[ok].mean()), float(np.nanmean(a)), int((dlt[ok] > 0).sum()), int(ok.sum())))
adj = holm([f[1] for f in fam])
for i, f in enumerate(fam):
    print("%-10s %9.2f %9.2f | %+8.2f  %.4f  %2d/%-2d  %.4f" % (f[0], f[3], f[3]-f[2], f[2], f[1], f[4], f[5], adj[i]))
