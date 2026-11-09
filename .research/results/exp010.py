# -*- coding: utf-8 -*-
"""EXP-010 — matched row budget, EXACT k, common support, frozen family + Holm.

Fixes vs EXP-009:
  1. exact-k allocation: base = k//m, remainder distributed one extra row to the first
     (k % m) donors  -> total rows is exactly k for every m.
  2. common support: eligible donors = cells with >= k rows (same pool for all m),
     same evaluated cells and same conditions across arms.
  3. report n and exclusions; Holm-correct the frozen family {k in 8,16,32} x {m1->m2}.
"""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")
src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
OUT = r"C:\Users\Administrator\AppData\Local\Temp\exp010.json"
NDRAW = 200
KS = [8, 16, 32]
MS = [1, 2, 3, 4]

d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, d["rpts"])], float)
pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(A[tr], y[tr]); pred[te] = mm.predict(A[te])
print("preds ready", flush=True)

def affine(ps, ys, p):
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

GROUPS = list(np.unique(grp))
rng = np.random.default_rng(0)
draws = {}
support = {}

for k in KS:
    for g in GROUPS:
        mm = grp == g
        p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
        gc = np.unique(c_g)
        for m in MS:
            arr = np.full(NDRAW, np.nan); n_used = 0
            for t in range(NDRAW):
                vals = []
                for c in gc:
                    ev = c_g == c
                    # common support: donor must have >= k rows (so exact-k is feasible for any m)
                    donors = [x for x in gc if x != c and (c_g == x).sum() >= k]
                    if m > len(donors): continue
                    ds = rng.choice(donors, m, replace=False)
                    base = k // m; rem = k % m
                    takes = [base + (1 if i < rem else 0) for i in range(m)]
                    sel = []
                    ok = True
                    for dd, tk in zip(ds, takes):
                        pool = np.where(c_g == dd)[0]
                        if len(pool) < tk: ok = False; break
                        sel.extend(rng.choice(pool, tk, replace=False))
                    if not ok or len(sel) != k: continue
                    sel = np.array(sel)
                    vals.append(float(np.abs(y_g[ev] - affine(p_g[sel], y_g[sel], p_g[ev])).mean()))
                arr[t] = float(np.mean(vals)) if vals else np.nan
                n_used = max(n_used, len(vals))
            draws[(k, m, g)] = arr
            support[(k, m, g)] = n_used
    print("  k=%d done" % k, flush=True)

def cond_stat(k, m, agg):
    out = []
    for g in GROUPS:
        a = draws[(k, m, g)]
        out.append(np.nanmean(a) if agg == "mean" else np.nanmedian(a))
    return np.array(out, float)

print("\n=== exact-k matched budget ===")
print("   k |" + "".join("    m=%d " % m for m in MS))
for k in KS:
    row = [float(np.nanmean(cond_stat(k, m, "mean"))) for m in MS]
    print("%4d |" % k + "".join("  %6.3f " % v for v in row))

print("\n=== m1->m2, common support, paired over conditions ===")
family = []
for k in KS:
    for agg in ("mean", "median"):
        va = cond_stat(k, 1, agg); vb = cond_stat(k, 2, agg)
        dlt = va - vb; ok = np.isfinite(dlt)
        if ok.sum() < 6:
            print("  k=%2d %-6s insufficient units (%d)" % (k, agg, ok.sum())); continue
        t, p = stats.ttest_rel(va[ok], vb[ok])
        bs = np.array([np.mean(rng.choice(dlt[ok], ok.sum(), replace=True)) for _ in range(5000)])
        print("  k=%2d %-6s n=%2d delta %+.3f CI [%+.3f,%+.3f] p=%.4f better %d/%d" % (
            k, agg, ok.sum(), dlt[ok].mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5),
            p, int((dlt[ok] > 0).sum()), ok.sum()), flush=True)
        family.append((k, agg, p, dlt[ok].mean()))

print("\n=== Holm over the frozen family ===")
ps = [f[2] for f in family]
order = np.argsort(ps)
mtests = len(ps); adj = np.ones(mtests); run = 0.0
for rank, idx in enumerate(order):
    run = max(run, ps[idx] * (mtests - rank)); adj[idx] = min(1.0, run)
print("  " + "  ".join("k=%d/%s p=%.4f adj=%.4f" % (family[i][0], family[i][1], family[i][2], adj[i])
                       for i in range(mtests)))
json.dump({"family": [{"k": f[0], "agg": f[1], "p": f[2], "delta": f[3], "holm": float(adj[i])}
                      for i, f in enumerate(family)]}, open(OUT, "w"), indent=1)
print("\nsaved", OUT)
