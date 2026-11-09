# -*- coding: utf-8 -*-
"""PROBE: is the reported "+274% fit-scope" effect a scope effect or a row-budget effect?

Section 5 of the manuscript reports that changing "the scope of the affine fit"
(per-cell -> per-condition) inflates the UConn contrast by +274% (+50.32 cycles,
+18.34 -> +68.65).

Reading budget.py:60-65 shows that the scope=="condition" branch does NOT
implement one shared per-condition fit. It keeps the fit inside the per-evaluated-
cell loop, and instead:
  (a) uses ALL rows of the sampled donor trajectories instead of exactly K=8,
  (b) bypasses the Monte-Carlo draw loop entirely (1 draw instead of 200).

This probe separates the two. Arms:
  A  baseline              per-cell, exactly 8 rows, 200 draws   (expect +18.34)
  B  scope=condition       verbatim original branch              (expect +68.65)
  C  per-cell, ALL donor rows, 1 draw   <-- same row budget as B, same scope as A
  D  per-cell, exactly 8 rows, 1 draw   <-- MC noise floor at 1 draw

If C ~= B, the reported "fit scope" effect is a row-budget effect and the
sensitivity-budget label is wrong.
"""
import numpy as np, warnings, sys
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")

src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
K = 8
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

ug = np.unique(grp)

def run(mode, ndraw, seed=0):
    """mode in {'k8','allrows'} ; returns per-condition cell-macro MAE for m=1,2"""
    rng = np.random.default_rng(seed)
    out = {1: {}, 2: {}}
    for g in ug:
        idx = np.where(grp == g)[0]
        c_g, p_g, y_g = cells[idx], pred[idx], y[idx]
        gc = np.unique(c_g)
        pool_all = [c for c in gc if (c_g == c).sum() >= K]
        for m in (1, 2):
            cell_vals = []
            for c in gc:
                ev = np.where(c_g == c)[0]
                donors = [x for x in pool_all if x != c]
                if len(donors) < m: continue
                per_j = {j: [] for j in ev}
                for _ in range(ndraw):
                    ds = rng.choice(donors, m, replace=False)
                    if mode == "allrows":
                        # exactly what budget.py:60-65 does, but per evaluated cell
                        sel = np.concatenate([np.where(c_g == dd)[0] for dd in ds])
                    else:
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
                jm = [float(np.mean(v)) for v in per_j.values() if v]
                if jm: cell_vals.append(float(np.mean(jm)))
            out[m][g] = float(np.mean(cell_vals)) if cell_vals else np.nan
    gs = [g for g in ug if np.isfinite(out[1].get(g, np.nan)) and np.isfinite(out[2].get(g, np.nan))]
    a = np.array([out[1][g] for g in gs]); b = np.array([out[2][g] for g in gs])
    t, p = stats.ttest_rel(a, b)
    return dict(n=len(gs), m1=float(a.mean()), m2=float(b.mean()),
                delta=float((a - b).mean()), p=float(p), better=int(((a - b) > 0).sum()))

arms = [
    ("A baseline  per-cell / 8 rows / 200 draws", "k8", 200),
    ("C         per-cell / ALL rows / 1 draw",     "allrows", 1),
    ("D         per-cell / 8 rows / 1 draw",       "k8", 1),
]
res = {}
for name, mode, nd in arms:
    r = run(mode, nd)
    res[name] = r
    print("%-45s m1=%8.2f m2=%8.2f delta=%+8.2f p=%.4f better %2d/%-2d" % (
        name, r["m1"], r["m2"], r["delta"], r["p"], r["better"], r["n"]), flush=True)

base = res[arms[0][0]]["delta"]
print("\n=== change relative to baseline (A) ===")
for name, _, _ in arms:
    ch = res[name]["delta"] - base
    print("%-45s %+9.2f (%+.0f%%)" % (name, ch, 100 * ch / abs(base)))

print("\n=== exact vs floor row allocation, K=8 ===")
for m in (1, 2):
    base_ = K // m; rem = K % m
    exact = [base_ + (1 if i < rem else 0) for i in range(m)]
    floor = [K // m] * m
    print("  m=%d  exact=%s (sum %d)   floor=%s (sum %d)   identical=%s" % (
        m, exact, sum(exact), floor, sum(floor), exact == floor))
