# -*- coding: utf-8 -*-
"""Does the donor effect change sign with RUL magnitude?

Unrestricted pool, k=8, m=1 vs m=2, cycle-unit RUL, stratified by RUL quartile.
Query -> cell -> condition aggregation inside each stratum; paired across conditions.
"""
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

src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
NDRAW = 100; K = 8; MS = [1, 2]
CALS = ["intercept", "affine", "isotonic", "1nn"]
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_cum"][c] - v for c, v in zip(cells, d["cum"])], float)
pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(A[tr], y[tr]); pred[te] = mm.predict(A[te])

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

q = np.quantile(y, [0.25, 0.5, 0.75])
strata = np.digitize(y, q)   # 0..3
names = ["Q1 (small RUL)", "Q2", "Q3", "Q4 (large RUL)"]
print("RUL quantiles: %.0f %.0f %.0f | strata sizes %s" % (q[0], q[1], q[2], np.bincount(strata)), flush=True)

rng = np.random.default_rng(0)
recs = []
for g in np.unique(grp):
    mm = grp == g
    idx = np.where(mm)[0]
    c_g, p_g, y_g = cells[idx], pred[idx], y[idx]
    gc = np.unique(c_g)
    for c in gc:
        donors_all = [x for x in gc if x != c]
        for j in np.where(c_g == c)[0]:
            pool = [x for x in donors_all if (c_g == x).sum() >= K]
            if len(pool) < 2: continue
            row = {"g": g, "c": c, "s": int(strata[j]), "y": y_g[j]}
            for m in MS:
                acc = {cal: [] for cal in CALS}
                for _ in range(NDRAW):
                    ds = rng.choice(pool, m, replace=False)
                    base = K // m; rem = K % m
                    takes = [base + (1 if i < rem else 0) for i in range(m)]
                    sel, okk = [], True
                    for dd, tk in zip(ds, takes):
                        p2 = np.where(c_g == dd)[0]
                        if len(p2) < tk: okk = False; break
                        sel.extend(rng.choice(p2, tk, replace=False))
                    if not okk: continue
                    sel = np.array(sel)
                    for cal in CALS:
                        acc[cal].append(abs(y_g[j] - calib(cal, p_g[sel], y_g[sel], np.array([p_g[j]]))[0]))
                for cal in CALS:
                    if acc[cal]: row[(cal, m)] = float(np.mean(acc[cal]))
            if all((cal, m) in row for cal in CALS for m in MS):
                recs.append(row)
print("queries: %d" % len(recs), flush=True)

def strat_cond(s, cal, m):
    out = {}
    for r in recs:
        if r["s"] != s: continue
        out.setdefault(r["g"], {}).setdefault(r["c"], []).append(r[(cal, m)])
    return {g: float(np.mean([np.mean(v) for v in cm.values()])) for g, cm in out.items()}

print("\n=== donor effect (m1 - m2) by RUL stratum; positive = 2 donors better ===")
print("%-11s %-15s %8s %8s | %8s  %8s  %6s" % ("calibrator", "stratum", "m=1", "m=2", "delta", "p", "better"))
rows = []
for cal in CALS:
    for s in range(4):
        A1 = strat_cond(s, cal, 1); A2 = strat_cond(s, cal, 2)
        gs = sorted(set(A1) & set(A2))
        if len(gs) < 6: continue
        a = np.array([A1[g] for g in gs]); b = np.array([A2[g] for g in gs])
        dlt = a - b
        t, p = stats.ttest_rel(a, b)
        rows.append((cal, s, float(dlt.mean()), float(p), int((dlt > 0).sum()), len(gs)))
        print("%-11s %-15s %8.1f %8.1f | %+8.2f  %.4f  %2d/%-2d" % (
            cal, names[s], a.mean(), b.mean(), dlt.mean(), p, int((dlt > 0).sum()), len(gs)), flush=True)

print("\nHolm within each calibrator across the 4 strata:")
for cal in CALS:
    sub = [r for r in rows if r[0] == cal]
    adj = holm([r[3] for r in sub])
    for i, r in enumerate(sub):
        print("  %-11s %-15s delta %+8.2f p=%.4f Holm=%.4f %s" % (
            cal, names[r[1]], r[2], r[3], adj[i], "PASS" if adj[i] < 0.05 else "ns"))
