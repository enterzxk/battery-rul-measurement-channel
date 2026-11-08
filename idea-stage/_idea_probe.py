
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd, itertools, json
pd.set_option("display.width", 200)

P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df = pd.read_csv(P)
y  = df.y_true.values.astype(float)
p  = df.pred_A_curve_logo.values.astype(float)
g  = df.group_id.values
c  = df.cell_id.values

print("rows", len(df), "cells", len(np.unique(c)), "groups", len(np.unique(g)))
print("cells per group:", pd.Series(c).groupby(g).nunique().to_dict())
print("rows per group:", pd.Series(c).groupby(g).size().to_dict())

# ---- baseline aggregations ----
err = np.abs(p - y)
print("query-macro MAE  = %.4f" % err.mean())
cm = df.assign(e=err).groupby(["group_id","cell_id"]).e.mean()
print("cell-macro MAE   = %.4f" % cm.groupby(level=0).mean().mean())

def agg_cell_macro(e, g, c):
    t = pd.DataFrame({"e":e,"g":g,"c":c}).groupby(["g","c"]).e.mean()
    return float(t.groupby(level=0).mean().mean())

def per_cond(e, g, c):
    t = pd.DataFrame({"e":e,"g":g,"c":c}).groupby(["g","c"]).e.mean()
    return t.groupby(level=0).mean()

# ---- affine calibration with strict cell-disjoint labels ----
def fit_affine(yy, pp):
    A = np.c_[pp, np.ones(len(pp))]
    coef, *_ = np.linalg.lstsq(A, yy, rcond=None)
    return coef[0], coef[1]

rng = np.random.default_rng(20261108)

def curve(k, reps=100, mode="full"):
    """mode: full affine | intercept only | slope only"""
    rows = []
    for rep in range(reps):
        e = np.empty(len(y))
        for gid in np.unique(g):
            m = g == gid
            cells = np.unique(c[m])
            yg, pg, cg = y[m], p[m], c[m]
            e_g = np.empty(m.sum())
            for tc in cells:
                te = cg == tc
                po = ~te
                if po.sum() < max(k,2):
                    e_g[te] = np.abs(pg[te]-yg[te]); continue
                idx = rng.choice(np.where(po)[0], size=k, replace=False)
                if mode == "full":
                    a,b = fit_affine(yg[idx], pg[idx])
                elif mode == "intercept":
                    a = 1.0; b = float(np.mean(yg[idx]-pg[idx]))
                else:
                    b = 0.0
                    a = float(np.sum(pg[idx]*yg[idx])/max(np.sum(pg[idx]**2),1e-9))
                e_g[te] = np.abs(a*pg[te]+b - yg[te])
            e[m] = e_g
        rows.append(e)
    E = np.array(rows)                      # reps x n
    maes = np.array([agg_cell_macro(E[i], g, c) for i in range(len(E))])
    pc = np.array([per_cond(E[i], g, c).values for i in range(len(E))])   # reps x 11
    return maes, pc, E.mean(0)

print("\n=== strict affine k-curve (100 label-draw reps) ===")
res = {}
for k in [0,2,4,8,12,16,24,32,48,64]:
    if k == 0:
        e0 = err.copy()
        m0 = agg_cell_macro(e0,g,c); pc0 = per_cond(e0,g,c).values
        res[0] = (np.array([m0]), pc0[None,:], e0)
        print("k=%3d  MAE %.4f  (fixed)" % (0, m0)); continue
    maes, pc, em = curve(k, reps=100)
    res[k] = (maes, pc, em)
    print("k=%3d  MAE %.4f  sd(draw) %.4f  [%.4f, %.4f]  min %.4f max %.4f"
          % (k, maes.mean(), maes.std(), np.percentile(maes,2.5), np.percentile(maes,97.5), maes.min(), maes.max()))

print("\n=== per-condition delta at k=16 (mean over draws) ===")
pc0 = res[0][1][0]
for k in [8,16,32]:
    d = res[k][1].mean(0) - pc0
    print("k=%2d  " % k, " ".join("%+.2f" % x for x in d), " | improved %d/11" % (d<0).sum())
    print("      mean %+.3f  sd %.3f  t %.2f" % (d.mean(), d.std(ddof=1), d.mean()/(d.std(ddof=1)/np.sqrt(len(d)))))

np.save(r"E:\桌面\rul\rul_v4_20261107\idea-stage\_probe_curve.npy",
        np.array([res[k][0].mean() for k in [0,2,4,8,12,16,24,32,48,64]]))
