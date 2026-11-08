# -*- coding: utf-8 -*-
"""Decisive factorial: donor pool (unrestricted U vs restricted R) x donor count (m=1 vs 2)
on IDENTICAL queries, IDENTICAL weights, IDENTICAL MC budget.

I = Delta_R - Delta_U isolates the eligibility-policy effect from the population effect.
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
# key: (condition, cell, row index) -> per-arm MAE
per_key = {}
for g in np.unique(grp):
    mm = grp == g
    idx = np.where(mm)[0]
    c_g, p_g, y_g, cum_g = cells[idx], pred[idx], y[idx], cum[idx]
    gc = np.unique(c_g)
    for c in gc:
        for j in np.where(c_g == c)[0]:
            T = cum_g[j]
            restr = [x for x in gc if x != c and eol.get(x, np.inf) <= T and (c_g == x).sum() >= K]
            unrestr = [x for x in gc if x != c and (c_g == x).sum() >= K]
            if len(restr) < max(MS) or len(unrestr) < max(MS): continue
            rec = {}
            for pool_name, pool in (("R", restr), ("U", unrestr)):
                for m in MS:
                    acc = {cal: [] for cal in CALS}
                    for _ in range(NDRAW):
                        ds = rng.choice(pool, m, replace=False)
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
                            acc[cal].append(abs(y_g[j] - calib(cal, p_g[sel], y_g[sel], np.array([p_g[j]]))[0]))
                    for cal in CALS:
                        if acc[cal]: rec[(pool_name, m, cal)] = float(np.mean(acc[cal]))
            if len(rec) == 2 * 2 * len(CALS):
                per_key[(g, c, j)] = rec
print("identical-query keys: %d" % len(per_key), flush=True)

def cond_mae(pool, m, cal):
    """query -> cell -> condition, identical weights in every arm."""
    out = {}
    for (g, c, j), rec in per_key.items():
        out.setdefault(g, {}).setdefault(c, []).append(rec[(pool, m, cal)])
    res = {}
    for g, cellmap in out.items():
        res[g] = float(np.mean([np.mean(v) for v in cellmap.values()]))
    return res

conds = sorted({g for (g, c, j) in per_key})
print("conditions: %d" % len(conds), flush=True)

print("\n%-11s %10s %10s | %8s | %10s %10s | %8s | interaction" % (
    "calibrator", "R_m1", "R_m2", "dR", "U_m1", "U_m2", "dU"))
rows = []
for cal in CALS:
    R1 = cond_mae("R", 1, cal); R2 = cond_mae("R", 2, cal)
    U1 = cond_mae("U", 1, cal); U2 = cond_mae("U", 2, cal)
    dR = np.array([R1[g] - R2[g] for g in conds])
    dU = np.array([U1[g] - U2[g] for g in conds])
    I = dR - dU
    t, p = stats.ttest_rel(dR, dU)
    rows.append((cal, dR.mean(), dU.mean(), I.mean(), p, int((I < 0).sum())))
    print("%-11s %10.2f %10.2f | %+8.2f | %10.2f %10.2f | %+8.2f | %+8.2f p=%.4f" % (
        cal, np.mean([R1[g] for g in conds]), np.mean([R2[g] for g in conds]), dR.mean(),
        np.mean([U1[g] for g in conds]), np.mean([U2[g] for g in conds]), dU.mean(),
        I.mean(), p), flush=True)

print("\nHolm over 4 interaction tests (n=11 conditions):")
adj = holm([r[4] for r in rows])
for i, r in enumerate(rows):
    print("  %-11s interaction %+8.2f  p=%.4f  Holm=%.4f %s" % (
        r[0], r[3], r[4], adj[i], "PASS" if adj[i] < 0.05 else "ns"))
