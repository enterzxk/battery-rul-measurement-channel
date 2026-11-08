# -*- coding: utf-8 -*-
"""External replication on ISU-ILCC (248 cells / 63 groups): does the donor effect
replicate, and does it stay confined to affine calibrators?"""
import numpy as np, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.isotonic import IsotonicRegression
from scipy import stats
warnings.filterwarnings("ignore")
OUT = r"C:\Users\Administrator\AppData\Local\Temp\isu_replication.json"
NDRAW = 100
K = 8
MS = [1, 2]
CALS = ["affine", "isotonic", "1nn"]

z = np.load(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "isu_table.npz"), allow_pickle=True)
X = z["X"]; cells = z["cells"]
grp = X[:, 0].astype(int); rpt = X[:, 1]
feat = X[:, 2:6]
soh = X[:, 6]
print("rows %d cells %d groups %d" % (len(X), len(np.unique(cells)), len(np.unique(grp))), flush=True)

# EOL per cell
eol = {}
for c in np.unique(cells):
    m = cells == c
    rr, ss = rpt[m], soh[m]
    o = np.argsort(rr); rr, ss = rr[o], ss[o]
    hit = np.where(ss <= 0.80)[0]
    if len(hit): eol[c] = int(rr[hit[0]])
print("cells with EOL: %d / %d" % (len(eol), len(np.unique(cells))), flush=True)

ok = np.array([c in eol and r <= eol[c] for c, r in zip(cells, rpt)])
cells, grp, rpt, feat, soh = cells[ok], grp[ok], rpt[ok], feat[ok], soh[ok]
y = np.array([eol[c] - r for c, r in zip(cells, rpt)], float)
print("usable rows %d  y range %.0f..%.0f" % (len(y), y.min(), y.max()), flush=True)

# LOGO predictions
pred = np.full(len(y), np.nan)
ug = np.unique(grp)
for g in ug:
    te = grp == g; tr = ~te
    if tr.sum() < 50 or te.sum() == 0: continue
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(feat[tr], y[tr]); pred[te] = mm.predict(feat[te])
print("LOGO preds done", flush=True)

def calibrate(kind, ps, ys, p):
    if kind == "1nn":
        idx = np.abs(ps[:, None] - p[None, :]).argmin(axis=0); return ys[idx]
    if kind == "isotonic":
        if len(np.unique(ps)) < 2: return p + (ys.mean() - ps.mean())
        try:
            iso = IsotonicRegression(increasing=True, out_of_bounds="clip"); iso.fit(ps, ys); return iso.predict(p)
        except Exception: return p + (ys.mean() - ps.mean())
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

rng = np.random.default_rng(0)
draws = {(c, m, g): np.full(NDRAW, np.nan) for c in CALS for m in MS for g in ug}
used = 0
for g in ug:
    mm = grp == g
    p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
    gc = np.unique(c_g)
    if len(gc) < 2: continue
    used += 1
    for t in range(NDRAW):
        for m in MS:
            for cal in CALS:
                vals = []
                for c in gc:
                    ev = c_g == c
                    donors = [x for x in gc if x != c]
                    if m > len(donors): continue
                    ds = rng.choice(donors, m, replace=False)
                    base = K // m; rem = K % m
                    takes = [base + (1 if i < rem else 0) for i in range(m)]
                    sel = []
                    okk = True
                    for dd, tk in zip(ds, takes):
                        pool = np.where(c_g == dd)[0]
                        if len(pool) < tk: okk = False; break
                        sel.extend(rng.choice(pool, tk, replace=False))
                    if not okk or len(sel) != K: continue
                    sel = np.array(sel)
                    pr = calibrate(cal, p_g[sel], y_g[sel], p_g[ev])
                    vals.append(float(np.abs(y_g[ev] - pr).mean()))
                draws[(cal, m, g)][t] = float(np.mean(vals)) if vals else np.nan
print("groups used: %d" % used, flush=True)

def cond(cal, m, agg="mean"):
    return np.array([np.nanmean(draws[(cal, m, g)]) if agg == "mean" else np.nanmedian(draws[(cal, m, g)])
                     for g in ug], float)

print("\n=== ISU-ILCC replication, k=8, m=1 vs m=2 ===")
print("%-10s %8s %8s | delta     p      better" % ("calibrator", "m=1", "m=2"))
for cal in CALS:
    a = cond(cal, 1); b = cond(cal, 2)
    dlt = a - b; okk = np.isfinite(dlt)
    if okk.sum() < 5: print("  %-10s insufficient (%d)" % (cal, okk.sum())); continue
    t, p = stats.ttest_rel(a[okk], b[okk])
    bs = np.array([np.mean(rng.choice(dlt[okk], okk.sum(), replace=True)) for _ in range(3000)])
    print("%-10s %8.3f %8.3f | %+.3f  %.4f  %d/%d   CI [%+.3f,%+.3f]" % (
        cal, np.nanmean(a), np.nanmean(b), dlt[okk].mean(), p,
        int((dlt[okk] > 0).sum()), okk.sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)), flush=True)
