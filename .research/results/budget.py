# -*- coding: utf-8 -*-
"""Sensitivity budget for calibration post-processing.

Fix the headline contrast (UConn, cycle RUL, k=8, affine, m=1 vs m=2) and vary ONE
post-processing decision at a time. Report how much each decision moves the answer.
"""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")

def holm(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); a = np.empty(n); r = 0.0
    for i, idx in enumerate(o):
        r = max(r, p[idx] * (n - i)); a[idx] = min(1.0, r)
    return a

src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
NDRAW = 200; K = 8
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_cum"][c] - v for c, v in zip(cells, d["cum"])], float)
pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(A[tr], y[tr]); pred[te] = mm.predict(A[te])
print("preds ready", flush=True)

def aff(ps, ys, p):
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

rng = np.random.default_rng(0)
ug = np.unique(grp)

def run(agg="cell", draw="mean", scope="cell", pop="all", alloc="exact"):
    """returns per-condition cell-macro (or query-pooled) MAE for m=1 and m=2"""
    out = {1: {}, 2: {}}
    for g in ug:
        mm = grp == g
        idx = np.where(mm)[0]
        c_g, p_g, y_g = cells[idx], pred[idx], y[idx]
        gc = np.unique(c_g)
        pool_all = [c for c in gc if (c_g == c).sum() >= K]
        if pop == "late":
            q25 = np.quantile(y_g, 0.25)
            sel_rows = np.where(y_g <= q25)[0]
        for m in (1, 2):
            cell_vals, query_vals = [], []
            for c in gc:
                ev = np.where(c_g == c)[0]
                if pop == "late":
                    ev = np.intersect1d(ev, sel_rows)
                    if ev.size == 0: continue
                donors = [x for x in pool_all if x != c]
                if len(donors) < m: continue
                if scope == "condition":
                    ds = rng.choice(donors, m, replace=False)
                    sel = np.concatenate([np.where(c_g == dd)[0] for dd in ds])
                    preds = [float(np.abs(y_g[j] - aff(p_g[sel], y_g[sel], np.array([p_g[j]]))[0])) for j in ev]
                    cell_vals.append(float(np.mean(preds))); query_vals.extend(preds)
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
            if agg == "cell":
                out[m][g] = float(np.mean(cell_vals)) if cell_vals else np.nan
            else:
                out[m][g] = float(np.mean(query_vals)) if query_vals else np.nan
    return out

def summarize(name, out):
    gs = [g for g in ug if np.isfinite(out[1].get(g, np.nan)) and np.isfinite(out[2].get(g, np.nan))]
    a = np.array([out[1][g] for g in gs]); b = np.array([out[2][g] for g in gs])
    dlt = (a - b).mean()
    t, p = stats.ttest_rel(a, b)
    return dict(name=name, n=len(gs), m1=float(a.mean()), m2=float(b.mean()),
                delta=float(dlt), p=float(p), better=int(((a - b) > 0).sum()))

configs = [
    ("baseline (cell-macro, mean, per-cell, all, exact-k)", dict()),
    ("aggregation -> query-pooled", dict(agg="query")),
    ("draw aggregation -> median", dict(draw="median")),
    ("affine scope -> per-condition", dict(scope="condition")),
    ("population -> late only (RUL Q1)", dict(pop="late")),
    ("row allocation -> floor(k/m)", dict(alloc="floor")),
]
rows = []
for name, kw in configs:
    rows.append(summarize(name, run(**kw)))
    print("%-52s delta %+8.2f  p=%.4f  better %2d/%-2d" % (
        name, rows[-1]["delta"], rows[-1]["p"], rows[-1]["better"], rows[-1]["n"]), flush=True)

base = rows[0]["delta"]
print("\n=== sensitivity budget (change in the reported contrast) ===")
print("%-52s %10s %10s" % ("decision varied", "delta", "change vs base"))
for r in rows:
    ch = r["delta"] - base
    pct = 100 * ch / abs(base) if base else float("nan")
    print("%-52s %+10.2f %+9.2f (%+.0f%%)" % (r["name"], r["delta"], ch, pct))
json.dump(rows, open(r"C:\Users\Administrator\AppData\Local\Temp\budget.json", "w"), indent=1, ensure_ascii=False)
