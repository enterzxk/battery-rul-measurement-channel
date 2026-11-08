# -*- coding: utf-8 -*-
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
NDRAW = 100; K = 8; MS = [1, 2]
CALS = ["intercept", "affine", "isotonic", "1nn"]
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_cum"][c] - v for c, v in zip(cells, d["cum"])], float)
cum = d["cum"]; eol = d["eol_cum"]
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
    if kind == "intercept": return p + (ys.mean() - ps.mean())
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

rng = np.random.default_rng(0)
res = {(cal, m): {} for cal in CALS for m in MS}
units = 0
for g in np.unique(grp):
    mm = grp == g
    idx = np.where(mm)[0]
    c_g, p_g, y_g, cum_g = cells[idx], pred[idx], y[idx], cum[idx]
    gc = np.unique(c_g)
    per = {(cal, m): [] for cal in CALS for m in MS}
    for c in gc:
        for j in np.where(c_g == c)[0]:
            T = cum_g[j]
            elig = [x for x in gc if x != c and eol.get(x, np.inf) <= T and (c_g == x).sum() >= K]
            if len(elig) < max(MS): continue
            units += 1
            for m in MS:
                acc = {cal: [] for cal in CALS}
                for _ in range(NDRAW):
                    ds = rng.choice(elig, m, replace=False)
                    base = K // m; rem = K % m
                    takes = [base + (1 if i < rem else 0) for i in range(m)]
                    sel, okk = [], True
                    for dd, tk in zip(ds, takes):
                        q = np.where(c_g == dd)[0]
                        if len(q) < tk: okk = False; break
                        sel.extend(rng.choice(q, tk, replace=False))
                    if not okk: continue
                    sel = np.array(sel)
                    for cal in CALS:
                        pr = calib(cal, p_g[sel], y_g[sel], np.array([p_g[j]]))[0]
                        acc[cal].append(abs(y_g[j] - pr))
                for cal in CALS:
                    if acc[cal]: per[(cal, m)].append(float(np.mean(acc[cal])))
    for key in per:
        if per[key]: res[key][g] = float(np.mean(per[key]))

valid = [g for g in np.unique(grp) if all(g in res[(c, 1)] and g in res[(c, 2)] for c in CALS)]
print("evaluable (cell,rpt) units: %d | conditions with both arms: %d" % (units, len(valid)), flush=True)

print("\n=== as-of constraint: only donors already finished by time T ===")
print("%-11s %9s %9s | delta     p        better  Holm" % ("calibrator", "m=1", "m=2"))
fam = []
for cal in CALS:
    a = np.array([res[(cal, 1)][g] for g in valid])
    b = np.array([res[(cal, 2)][g] for g in valid])
    dlt = a - b
    t, p = stats.ttest_rel(a, b)
    fam.append((cal, p, float(dlt.mean()), float(a.mean()), int((dlt > 0).sum()), len(dlt)))
adj = holm([f[1] for f in fam])
for i, f in enumerate(fam):
    print("%-11s %9.2f %9.2f | %+8.2f  %.4f  %2d/%-2d   %.4f%s" % (
        f[0], f[3], f[3] - f[2], f[2], f[1], f[4], f[5], adj[i], "" if adj[i] < 0.05 else " ns"))
