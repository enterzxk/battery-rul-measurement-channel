# -*- coding: utf-8 -*-
"""ISU sensitivity scan on COMMON evaluated-cell support (fixes the audit's FAIL-B).

isu_budget.py filtered evaluated cells per arm with `len(donors) < m`, so the
one-donor arm evaluated 233 cells and the two-donor arm 223. This script uses the
same convention as the main ISU table (isu_corrected.py:67-69): the eligible cell
set is fixed once, using the maximum donor count, and both arms use it.

Adds a null control (baseline rerun with a different seed) so the scan's noise is
visible. Each config gets a fresh RNG at the same seed, so all configs start from
the same stream.
"""
import numpy as np, json, os, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
z = np.load(os.path.join(HERE, "isu_table.npz"), allow_pickle=True)
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
print("rows %d conditions %d" % (len(y), len(np.unique(grp))), flush=True)

NDRAW = 100; K = 8; MS = (1, 2)
def aff(ps, ys, p):
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

ug = np.unique(grp)

def run(agg="cell", draw="mean", pop="all", seed=0, count_cells=False):
    rng = np.random.default_rng(seed)
    out = {1: {}, 2: {}}
    ncells = {1: 0, 2: 0}
    for g in ug:
        idx = np.where(grp == g)[0]
        c_g, p_g, y_g = cells[idx], pred[idx], y[idx]
        if not np.isfinite(p_g).all(): continue
        gc = np.unique(c_g)
        pool = [c for c in gc if (c_g == c).sum() >= K]
        # COMMON support: eligible for the largest donor count, fixed once
        eval_cells = [c for c in gc if len([d for d in pool if d != c]) >= max(MS)]
        if not eval_cells: continue
        q25 = np.quantile(y_g, 0.25)
        for m in MS:
            cv, qv = [], []
            for c in eval_cells:
                ev = np.where(c_g == c)[0]
                if pop == "late":
                    ev = ev[y_g[ev] <= q25]
                    if ev.size == 0: continue
                donors = [d for d in pool if d != c]
                if len(donors) < m: continue
                per_j = {j: [] for j in ev}
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
                    for j in ev:
                        per_j[j].append(float(np.abs(y_g[j] - aff(p_g[sel], y_g[sel], np.array([p_g[j]]))[0])))
                jm = [float(np.mean(v)) if draw == "mean" else float(np.median(v)) for v in per_j.values() if v]
                if jm:
                    cv.append(float(np.mean(jm))); qv.extend(jm)
            ncells[m] += len(cv)
            out[m][g] = float(np.mean(cv)) if agg == "cell" and cv else (
                float(np.mean(qv)) if qv else np.nan)
    gs = [g for g in ug if np.isfinite(out[1].get(g, np.nan)) and np.isfinite(out[2].get(g, np.nan))]
    a = np.array([out[1][g] for g in gs]); b = np.array([out[2][g] for g in gs])
    t, p = stats.ttest_rel(a, b)
    r = dict(n=len(gs), delta=float((a - b).mean()), p=float(p), better=int(((a - b) > 0).sum()))
    if count_cells: r["cells"] = ncells
    return r

cfgs = [
    ("aggregation -> query-pooled", dict(agg="query")),
    ("draw aggregation -> median", dict(draw="median")),
    ("population -> late-life quartile", dict(pop="late")),
    ("row allocation -> floor(k/m) [NULL = baseline re-run, seed 1]", dict(seed=1)),
    ("baseline re-run, seed 2 [NULL]", dict(seed=2)),
]
print("\n=== ISU sensitivity scan on COMMON support (233 -> fixed set) ===", flush=True)
base_r = run(count_cells=True)
print("common evaluated cells: m=1 %d, m=2 %d" % (base_r["cells"][1], base_r["cells"][2]), flush=True)
print("%-42s %10s %8s %8s" % ("config", "delta", "p", "better"))
rows = [("baseline", base_r)]
print("%-42s %+10.3f %8.4f %2d/%-2d" % ("baseline", base_r["delta"], base_r["p"], base_r["better"], base_r["n"]), flush=True)
for name, kw in cfgs:
    r = run(**kw)
    rows.append((name, r))
    print("%-42s %+10.3f %8.4f %2d/%-2d" % (name, r["delta"], r["p"], r["better"], r["n"]), flush=True)

base = rows[0][1]["delta"]
print("\n=== change from baseline ===")
for name, r in rows:
    ch = r["delta"] - base
    print("%-42s %+9.3f (%+.0f%%)" % (name, ch, 100 * ch / abs(base) if base else float("nan")))
json.dump({name: r for name, r in rows}, open(os.path.join(HERE, "isu_budget_common.json"), "w"), indent=1)
