# -*- coding: utf-8 -*-
"""Sensitivity budget on ISU-ILCC: replicate the five-decision scan on the second dataset."""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")

z = np.load(r"C:\Users\Administrator\AppData\Local\Temp\isu_table.npz", allow_pickle=True)
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
print("rows %d groups %d" % (len(y), len(np.unique(grp))), flush=True)

NDRAW = 100; K = 8
def aff(ps, ys, p):
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

rng = np.random.default_rng(0)
ug = np.unique(grp)

def run(agg="cell", draw="mean", scope="cell", pop="all", alloc="exact"):
    out = {1: {}, 2: {}}
    for g in ug:
        mm = grp == g
        idx = np.where(mm)[0]
        c_g, p_g, y_g = cells[idx], pred[idx], y[idx]
        if not np.isfinite(p_g).all(): continue
        gc = np.unique(c_g)
        pool_all = [c for c in gc if (c_g == c).sum() >= K]
        q25 = np.quantile(y_g, 0.25)
        for m in (1, 2):
            cell_vals, query_vals = [], []
            for c in gc:
                ev = np.where(c_g == c)[0]
                if pop == "late":
                    ev = ev[y_g[ev] <= q25]
                    if ev.size == 0: continue
                donors = [x for x in pool_all if x != c]
                if len(donors) < m: continue
                if scope == "condition":
                    ds = rng.choice(donors, m, replace=False)
                    sel = np.concatenate([np.where(c_g == dd)[0] for dd in ds])
                    pr = [float(np.abs(y_g[j] - aff(p_g[sel], y_g[sel], np.array([p_g[j]]))[0])) for j in ev]
                    cell_vals.append(float(np.mean(pr))); query_vals.extend(pr)
                    continue
                per_j = {j: [] for j in ev}
                for _ in range(NDRAW):
                    ds = rng.choice(donors, m, replace=False)
                    if alloc == "exact":
                        base = K // m; rem = K % m
                        takes = [base + (1 if i < rem else 0) for i in range(m)]
                    else:
                        takes = [K // m] * m
                    sel, okk = [], True
                    for dd, tk in zip(ds, takes):
                        q = np.where(c_g == dd)[0]
                        if len(q) < tk: okk = False; break
                        sel.extend(rng.choice(q, tk, replace=False))
                    if not okk: continue
                    sel = np.array(sel)
                    for j in ev:
                        per_j[j].append(float(np.abs(y_g[j] - aff(p_g[sel], y_g[sel], np.array([p_g[j]]))[0])))
                jm = [float(np.mean(v)) if draw == "mean" else float(np.median(v)) for v in per_j.values() if v]
                if jm: cell_vals.append(float(np.mean(jm))); query_vals.extend(jm)
            out[m][g] = float(np.mean(cell_vals)) if agg == "cell" and cell_vals else (
                float(np.mean(query_vals)) if query_vals else np.nan)
    return out

def summ(name, out):
    gs = [g for g in ug if np.isfinite(out[1].get(g, np.nan)) and np.isfinite(out[2].get(g, np.nan))]
    a = np.array([out[1][g] for g in gs]); b = np.array([out[2][g] for g in gs])
    t, p = stats.ttest_rel(a, b)
    return dict(name=name, n=len(gs), delta=float((a - b).mean()), p=float(p), better=int(((a - b) > 0).sum()))

cfgs = [
    ("baseline", dict()),
    ("aggregation -> query-pooled", dict(agg="query")),
    ("draw aggregation -> median", dict(draw="median")),
    ("affine scope -> per-condition", dict(scope="condition")),
    ("population -> late only", dict(pop="late")),
    ("row allocation -> floor(k/m)", dict(alloc="floor")),
]
rows = []
print("\n=== ISU sensitivity budget ===", flush=True)
for name, kw in cfgs:
    rows.append(summ(name, run(**kw)))
    print("%-40s delta %+8.3f p=%.4f better %2d/%-2d" % (
        name, rows[-1]["delta"], rows[-1]["p"], rows[-1]["better"], rows[-1]["n"]), flush=True)
base = rows[0]["delta"]
print("\n%-40s %10s %10s" % ("decision varied", "delta", "change"))
for r in rows:
    ch = r["delta"] - base
    pct = 100 * ch / abs(base) if base else float("nan")
    print("%-40s %+10.3f %+9.3f (%+.0f%%)" % (r["name"], r["delta"], ch, pct))
json.dump(rows, open(r"C:\Users\Administrator\AppData\Local\Temp\isu_budget.json", "w"), indent=1)
