# -*- coding: utf-8 -*-
"""ISU corrected replication — common support, shared draws, identical populations.

Fixes vs isu_repl.py:
  1. common donor pool: every donor must have >= 8 rows, so m=1 and m=2 draw from
     the SAME pool and the same evaluated cells.
  2. exactly 8 labels in both arms.
  3. the SAME (donor draw, row draw) is used for all three calibrators -> paired.
  4. MAE and paired deltas computed on the identical condition set (conditions where
     both arms produced a value). Draw-level results saved.
"""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.isotonic import IsotonicRegression
from scipy import stats
warnings.filterwarnings("ignore")
OUT = r"C:\Users\Administrator\AppData\Local\Temp\isu_corrected.json"
NDRAW = 200
K = 8
MS = [1, 2]
CALS = ["affine", "isotonic", "1nn"]

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
print("rows %d  groups %d  preds ready" % (len(y), len(np.unique(grp))), flush=True)

def calib(kind, ps, ys, p):
    if kind == "1nn":
        return ys[np.abs(ps[:, None] - p[None, :]).argmin(axis=0)]
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
draws = {}
valid_cond = []
for g in ug:
    mm = grp == g
    p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
    if not np.isfinite(p_g).all(): continue
    gc = np.unique(c_g)
    lengths = {c: int((c_g == c).sum()) for c in gc}
    pool = [c for c in gc if lengths[c] >= K]          # COMMON donor pool
    eval_cells = [c for c in gc if len([d for d in pool if d != c]) >= max(MS)]
    if len(eval_cells) < 1 or len(pool) < 1: continue
    arr = {(cal, m): np.full(NDRAW, np.nan) for cal in CALS for m in MS}
    for t in range(NDRAW):
        for m in MS:
            per_cell = {cal: [] for cal in CALS}
            for c in eval_cells:
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
                sel = np.array(sel)
                ev = c_g == c
                for cal in CALS:
                    pr = calib(cal, p_g[sel], y_g[sel], p_g[ev])
                    per_cell[cal].append(float(np.abs(y_g[ev] - pr).mean()))
            for cal in CALS:
                arr[(cal, m)][t] = float(np.mean(per_cell[cal])) if per_cell[cal] else np.nan
    if all(np.isfinite(arr[(cal, 1)]).any() and np.isfinite(arr[(cal, 2)]).any() for cal in CALS):
        for key in arr: draws.setdefault(key, {})[g] = arr[key]
        valid_cond.append(g)
print("conditions with both arms on common support: %d" % len(valid_cond), flush=True)

def cond(cal, m, agg="mean"):
    return np.array([np.nanmean(draws[(cal, m)][g]) if agg == "mean" else np.nanmedian(draws[(cal, m)][g])
                     for g in valid_cond], float)

print("\n=== ISU corrected, common support, shared draws, k=8 ===")
print("%-10s %8s %8s | delta     p        better     CI" % ("calibrator", "m=1", "m=2"))
fam = []
for cal in CALS:
    for agg in ("mean", "median"):
        a, b = cond(cal, 1, agg), cond(cal, 2, agg)
        dlt = a - b; okk = np.isfinite(dlt)
        t, p = stats.ttest_rel(a[okk], b[okk])
        bs = np.array([np.mean(rng.choice(dlt[okk], okk.sum(), replace=True)) for _ in range(5000)])
        print("%-10s %-6s %8.3f %8.3f | %+.3f  %.4f  %3d/%-3d  [%+.3f,%+.3f]" % (
            cal, agg, np.nanmean(a), np.nanmean(b), dlt[okk].mean(), p,
            int((dlt[okk] > 0).sum()), okk.sum(),
            np.percentile(bs, 2.5), np.percentile(bs, 97.5)), flush=True)
        fam.append((cal, agg, p, float(dlt[okk].mean())))

print("\n=== Holm over 6 tests (3 calibrators x 2 aggregations) ===")
ps = [f[2] for f in fam]; order = np.argsort(ps); adj = np.ones(len(ps))
for rank, idx in enumerate(order): adj[idx] = min(1.0, ps[idx] * (len(ps) - rank))
for i, f in enumerate(fam):
    print("  %-10s %-6s p=%.4f Holm=%.4f %s" % (f[0], f[1], f[2], adj[i], "PASS" if adj[i] < 0.05 else "fail"))
json.dump({"n_cond": len(valid_cond), "family": [{"cal": f[0], "agg": f[1], "p": f[2], "delta": f[3], "holm": float(adj[i])}
                                                 for i, f in enumerate(fam)]}, open(OUT, "w"), indent=1)
