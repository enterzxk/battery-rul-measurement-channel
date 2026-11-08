# -*- coding: utf-8 -*-
"""R0 re-analysis: expectation over draws, not a single sample.

Arms: random (>=1000 draws) | quantile | endpoint (D-optimal) | y-oracle
Plus a clipped affine variant to separate OLS pathology from real effect.
"""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")
src = open(r"C:\Users\Administrator\AppData\Local\Temp\v2_main.py", encoding="utf-8").read().split("def main():")[0]
exec(src)
OUT = r"C:\Users\Administrator\AppData\Local\Temp\r0.json"
NDRAW = 1000
CLIP = (0.5, 2.0)

d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, d["rpts"])], float)
print("rows", len(y), flush=True)

def fit_affine(ps, ys, clip=None):
    if ps.size < 2 or np.std(ps) < 1e-12:
        return 1.0, float(ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    if clip is not None:
        a = float(np.clip(a, clip[0], clip[1]))
    b = float(ys.mean() - a * ps.mean())
    return float(a), b

KS = [2, 3, 4, 6, 8, 16]
rng = np.random.default_rng(0)
res = {}

# precompute LOGO predictions
pred_all = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    m.fit(A[tr], y[tr]); pred_all[te] = m.predict(A[te])
print("preds done", flush=True)

rows_by_cond = {}
for g in np.unique(grp):
    m = grp == g
    rows_by_cond[g] = (pred_all[m], y[m], cells[m])

arms = ["rand", "rand_clip", "quant", "endpoint", "yoracle"]
acc = {a: {k: [] for k in KS} for a in arms}
base_by_cond = {}

for g, (p_g, y_g, c_g) in rows_by_cond.items():
    gc = np.unique(c_g)
    base_by_cond[g] = float(np.mean([np.abs(y_g[c_g == c] - p_g[c_g == c]).mean() for c in gc]))
    for k in KS:
        per = {a: [] for a in arms}
        for c in gc:
            ev = c_g == c
            pool = np.where(~ev)[0]
            if len(pool) < k:
                for a in arms: per[a].append(np.nan)
                continue
            p_pool, y_pool = p_g[pool], y_g[pool]
            # random: expectation over NDRAW draws
            draws = np.array([rng.choice(len(pool), k, replace=False) for _ in range(NDRAW)])
            vals = np.empty(NDRAW); vals_c = np.empty(NDRAW)
            for i in range(NDRAW):
                s = draws[i]
                a1, b1 = fit_affine(p_pool[s], y_pool[s])
                vals[i] = np.abs(y_g[ev] - (a1 * p_g[ev] + b1)).mean()
                a2, b2 = fit_affine(p_pool[s], y_pool[s], CLIP)
                vals_c[i] = np.abs(y_g[ev] - (a2 * p_g[ev] + b2)).mean()
            per["rand"].append(float(np.median(vals)))
            per["rand_clip"].append(float(np.median(vals_c)))
            # quantile design
            order = pool[np.argsort(p_pool)]
            qs = np.linspace(0, 1, k)
            sel = np.unique([order[min(int(round(q * (len(order) - 1))), len(order) - 1)] for q in qs])
            a3, b3 = fit_affine(p_g[sel], y_g[sel])
            per["quant"].append(float(np.abs(y_g[ev] - (a3 * p_g[ev] + b3)).mean()))
            # endpoint / D-optimal: half at each end of the prediction range
            lo = order[: max(1, k // 2)]; hi = order[-(k - max(1, k // 2)):]
            sel2 = np.unique(np.concatenate([lo, hi]))
            a4, b4 = fit_affine(p_g[sel2], y_g[sel2])
            per["endpoint"].append(float(np.abs(y_g[ev] - (a4 * p_g[ev] + b4)).mean()))
            # y-oracle: select by TRUE y quantiles (cheating upper bound)
            order_y = pool[np.argsort(y_pool)]
            sel3 = np.unique([order_y[min(int(round(q * (len(order_y) - 1))), len(order_y) - 1)] for q in qs])
            a5, b5 = fit_affine(p_g[sel3], y_g[sel3])
            per["yoracle"].append(float(np.abs(y_g[ev] - (a5 * p_g[ev] + b5)).mean()))
        for a in arms:
            acc[a][k].append(float(np.nanmean(per[a])))

base = np.array([base_by_cond[g] for g in np.unique(grp)])
print("\nbaseline k=0: %.3f" % base.mean(), flush=True)
print("\n  k   rand(med)  rand_clip   quant   endpoint   yoracle    p(quant vs rand)")
for k in KS:
    r = np.array(acc["rand"][k]); rc = np.array(acc["rand_clip"][k])
    q = np.array(acc["quant"][k]); e = np.array(acc["endpoint"][k]); yo = np.array(acc["yoracle"][k])
    pw = stats.wilcoxon(q, r).pvalue
    print("%3d   %8.3f   %8.3f  %7.3f   %8.3f   %7.3f      %.4f" % (
        k, r.mean(), rc.mean(), q.mean(), e.mean(), yo.mean(), pw), flush=True)
print("\nvs k=0 baseline:")
for k in KS:
    r = np.array(acc["rand"][k]); rc = np.array(acc["rand_clip"][k]); q = np.array(acc["quant"][k])
    print("k=%2d  rand %+.3f (p=%.4f, %d/11) | rand_clip %+.3f (p=%.4f, %d/11) | quant %+.3f (p=%.4f, %d/11)" % (
        k, (r-base).mean(), stats.wilcoxon(r, base).pvalue, int(((r-base) < 0).sum()),
        (rc-base).mean(), stats.wilcoxon(rc, base).pvalue, int(((rc-base) < 0).sum()),
        (q-base).mean(), stats.wilcoxon(q, base).pvalue, int(((q-base) < 0).sum())), flush=True)
json.dump({a: {str(k): acc[a][k] for k in KS} for a in arms} | {"base": base.tolist()}, open(OUT, "w"))
print("\nsaved", OUT)
