# -*- coding: utf-8 -*-
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.isotonic import IsotonicRegression
from scipy import stats
warnings.filterwarnings("ignore")

src = open(r"C:\Users\Administrator\AppData\Local\Temp\v2_main.py", encoding="utf-8").read().split("def main():")[0]
exec(src)
NDRAW = 100; K = 8; MS = [1, 2]
CALS = ["intercept", "affine", "isotonic", "1nn"]
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_cum"][c] - v for c, v in zip(cells, d["cum"])], float)
ug = np.unique(grp)

preds = {}
p = np.full(len(y), np.nan)
for g in ug:
    te = grp == g; tr = ~te
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(A[tr], y[tr]); p[te] = mm.predict(A[te])
preds["HGB"] = p
p = np.full(len(y), np.nan)
for g in ug:
    te = grp == g; tr = ~te
    mu, sd = A[tr].mean(0), A[tr].std(0) + 1e-9
    m2 = Ridge(alpha=10.0); m2.fit((A[tr] - mu) / sd, y[tr])
    p[te] = m2.predict((A[te] - mu) / sd)
preds["Ridge"] = p
print("preds ready", flush=True)

def calib(kind, ps, ys, pv):
    if kind == "1nn": return ys[np.abs(ps[:, None] - pv[None, :]).argmin(axis=0)]
    if kind == "isotonic":
        if len(np.unique(ps)) < 2: return pv + (ys.mean() - ps.mean())
        try:
            iso = IsotonicRegression(increasing=True, out_of_bounds="clip"); iso.fit(ps, ys); return iso.predict(pv)
        except Exception: return pv + (ys.mean() - ps.mean())
    if kind == "intercept": return pv + (ys.mean() - ps.mean())
    if ps.size < 2 or np.std(ps) < 1e-12: return pv + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * pv + (ys.mean() - a * ps.mean())

def table(pred):
    rng = np.random.default_rng(0)
    T = {}
    for g in ug:
        mm = grp == g
        idx = np.where(mm)[0]
        c_g, p_g, y_g = cells[idx], pred[idx], y[idx]
        gc = np.unique(c_g)
        for cal in CALS:
            for m in MS:
                per_cell = []
                for c in gc:
                    donors = [x for x in gc if x != c and (c_g == x).sum() >= K]
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
                    if vals: per_cell.append(float(np.mean(vals)))
                if per_cell: T[(cal, m, g)] = float(np.mean(per_cell))
    return T

for name in ("HGB", "Ridge"):
    T = table(preds[name])
    print("\n=== %s ===" % name)
    arms = [(c, m) for c in CALS for m in MS]
    print("  arm                 overall MAE")
    for a in arms:
        v = [T[(a[0], a[1], g)] for g in ug if (a[0], a[1], g) in T]
        print("  %-10s m=%d        %8.2f" % (a[0], a[1], np.mean(v)))
    # LOO selection: pick best arm on the other 10 conditions, evaluate on held-out
    sel, best_fixed_vals = [], {}
    for g in ug:
        best, bv = None, np.inf
        for a in arms:
            v = [T[(a[0], a[1], x)] for x in ug if x != g and (a[0], a[1], x) in T]
            if len(v) < 5: continue
            if np.mean(v) < bv: bv, best = np.mean(v), a
        if best and (best[0], best[1], g) in T:
            sel.append((g, T[(best[0], best[1], g)], best))
    fixed_best = min(arms, key=lambda a: np.mean([T[(a[0], a[1], g)] for g in ug if (a[0], a[1], g) in T]))
    gs = [s[0] for s in sel]
    a1 = np.array([s[1] for s in sel])
    b1 = np.array([T[(fixed_best[0], fixed_best[1], g)] for g in gs])
    t, pv = stats.ttest_rel(a1, b1)
    from collections import Counter
    print("  LOO-selected arms:", dict(Counter(str(s[2]) for s in sel)))
    print("  best fixed arm: %s (%.2f)" % (str(fixed_best), np.mean([T[(fixed_best[0], fixed_best[1], g)] for g in ug if (fixed_best[0], fixed_best[1], g) in T])))
    print("  LOO-selected %.2f vs best-fixed %.2f | delta %+.2f p=%.4f selected better %d/%d" % (
        a1.mean(), b1.mean(), (a1 - b1).mean(), pv, int((a1 < b1).sum()), len(gs)))
