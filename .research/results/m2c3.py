# -*- coding: utf-8 -*-
"""M2-C3 — estimator control for the surviving claim (k=8, m=1 vs m=2).

Does the +0.19 MAE survive under isotonic, 1-NN and clipped-affine calibrators?
If it only exists for plain OLS affine, it is an estimator artifact, not a donor effect.
"""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.isotonic import IsotonicRegression
from scipy import stats
warnings.filterwarnings("ignore")
src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
OUT = r"C:\Users\Administrator\AppData\Local\Temp\m2c3.json"
NDRAW = 100
K = 8
MS = [1, 2, 3]
CALS = ["affine", "affine_clip", "isotonic", "1nn"]

d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, d["rpts"])], float)
pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(A[tr], y[tr]); pred[te] = mm.predict(A[te])
print("preds ready", flush=True)

def calibrate(kind, ps, ys, p):
    if kind == "1nn":
        idx = np.abs(ps[:, None] - p[None, :]).argmin(axis=0)
        return ys[idx]
    if kind == "isotonic":
        if len(np.unique(ps)) < 2: return p + (ys.mean() - ps.mean())
        iso = IsotonicRegression(increasing=True, out_of_bounds="clip")
        try:
            iso.fit(ps, ys); return iso.predict(p)
        except Exception:
            return p + (ys.mean() - ps.mean())
    if ps.size < 2 or np.std(ps) < 1e-12:
        return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    if kind == "affine_clip": a = float(np.clip(a, 0.5, 2.0))
    return a * p + (ys.mean() - a * ps.mean())

GROUPS = list(np.unique(grp))
rng = np.random.default_rng(0)
draws = {(cal, m, g): np.full(NDRAW, np.nan) for cal in CALS for m in MS for g in GROUPS}

for g in GROUPS:
    mm = grp == g
    p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
    gc = np.unique(c_g)
    for t in range(NDRAW):
        for m in MS:
            for cal in CALS:
                vals = []
                for c in gc:
                    ev = c_g == c
                    donors = [x for x in gc if x != c and (c_g == x).sum() >= K]
                    if m > len(donors): continue
                    ds = rng.choice(donors, m, replace=False)
                    base = K // m; rem = K % m
                    takes = [base + (1 if i < rem else 0) for i in range(m)]
                    sel = []
                    ok = True
                    for dd, tk in zip(ds, takes):
                        pool = np.where(c_g == dd)[0]
                        if len(pool) < tk: ok = False; break
                        sel.extend(rng.choice(pool, tk, replace=False))
                    if not ok or len(sel) != K: continue
                    sel = np.array(sel)
                    pr = calibrate(cal, p_g[sel], y_g[sel], p_g[ev])
                    vals.append(float(np.abs(y_g[ev] - pr).mean()))
                draws[(cal, m, g)][t] = float(np.mean(vals)) if vals else np.nan
    print("  %s done" % g, flush=True)

print("\n=== k=8, MAE by calibrator and donor count ===")
print("%-12s %8s %8s %8s | m1->m2" % ("calibrator", "m=1", "m=2", "m=3"))
res = {}
for cal in CALS:
    row = []
    for m in MS:
        v = np.array([np.nanmean(draws[(cal, m, g)]) for g in GROUPS])
        row.append(float(np.nanmean(v)))
    print("%-12s %8.3f %8.3f %8.3f | %+.3f" % (cal, row[0], row[1], row[2], row[0] - row[1]))
    res[cal] = row

print("\n=== paired m1->m2 over 11 conditions ===")
family = []
for cal in CALS:
    for agg in ("mean", "median"):
        va = np.array([np.nanmean(draws[(cal,1,g)]) if agg=="mean" else np.nanmedian(draws[(cal,1,g)]) for g in GROUPS])
        vb = np.array([np.nanmean(draws[(cal,2,g)]) if agg=="mean" else np.nanmedian(draws[(cal,2,g)]) for g in GROUPS])
        dlt = va - vb; ok = np.isfinite(dlt)
        if ok.sum() < 6: continue
        t, p = stats.ttest_rel(va[ok], vb[ok])
        bs = np.array([np.mean(rng.choice(dlt[ok], ok.sum(), replace=True)) for _ in range(3000)])
        print("  %-12s %-6s n=%2d delta %+.3f CI [%+.3f,%+.3f] p=%.4f better %d/%d" % (
            cal, agg, ok.sum(), dlt[ok].mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5),
            p, int((dlt[ok] > 0).sum()), ok.sum()), flush=True)
        family.append((cal, agg, p, float(dlt[ok].mean())))

print("\n=== Holm over the calibrator family (mean agg only) ===")
mf = [f for f in family if f[1] == "mean"]
ps = [f[2] for f in mf]; order = np.argsort(ps); adj = np.ones(len(ps))
for rank, idx in enumerate(order):
    adj[idx] = min(1.0, ps[idx] * (len(ps) - rank))
for i, f in enumerate(mf):
    print("  %-12s p=%.4f  Holm=%.4f  %s" % (f[0], f[2], adj[i], "PASS" if adj[i] < 0.05 else "fail"))
json.dump({"mae": res, "family": [{"cal": f[0], "agg": f[1], "p": f[2], "delta": f[3]} for f in family]},
          open(OUT, "w"), indent=1)
