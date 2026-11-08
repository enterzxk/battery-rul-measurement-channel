
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df = pd.read_csv(P)
y  = df.y_true.values.astype(float); p = df.pred_A_curve_logo.values.astype(float)
g  = df.group_id.values; c = df.cell_id.values
rng = np.random.default_rng(7)

def cell_macro(e):
    t = pd.DataFrame({"e":e,"g":g,"c":c}).groupby(["g","c"]).e.mean()
    return float(t.groupby(level=0).mean().mean())

def per_cond(e):
    t = pd.DataFrame({"e":e,"g":g,"c":c}).groupby(["g","c"]).e.mean()
    return t.groupby(level=0).mean()

def run(k, m=None, mode="full", reps=200):
    """m = max number of distinct donor cells (None -> unconstrained)."""
    out = np.zeros(reps); pcs = np.zeros((reps, len(np.unique(g))))
    for rep in range(reps):
        e = np.empty(len(y))
        for gid in np.unique(g):
            mg = g == gid
            cells = np.unique(c[mg]); yg, pg, cg = y[mg], p[mg], c[mg]
            eg = np.empty(mg.sum())
            for tc in cells:
                te = cg == tc; po = np.where(~te)[0]
                donor_cells = np.unique(cg[po])
                mm = len(donor_cells) if m is None else min(m, len(donor_cells))
                sel_cells = rng.choice(donor_cells, size=mm, replace=False)
                # allocate k labels evenly across sel_cells
                alloc = np.full(mm, k//mm); alloc[:k % mm] += 1
                idx = []
                for cc, na in zip(sel_cells, alloc):
                    pool = np.where((cg == cc))[0]
                    if len(pool) < na: na = len(pool)
                    idx.extend(rng.choice(pool, size=na, replace=False))
                idx = np.array(idx)
                if len(idx) < 2:
                    eg[te] = np.abs(pg[te]-yg[te]); continue
                if mode == "full":
                    A = np.c_[pg[idx], np.ones(len(idx))]
                    a,b = np.linalg.lstsq(A, yg[idx], rcond=None)[0]
                elif mode == "intercept":
                    a, b = 1.0, float(np.mean(yg[idx]-pg[idx]))
                eg[te] = np.abs(a*pg[te]+b-yg[te])
            e[mg] = eg
        out[rep] = cell_macro(e); pcs[rep] = per_cond(e).values
    return out, pcs

print("=== (k, m) grid: cell-macro MAE, mean over 200 draws (sd) ===")
print("m = max distinct donor cells; m=None = unconstrained (~5)")
hdr = "  k |" + "".join("   m=%d      " % m for m in [1,2,3,5]) + "  m=None"
print(hdr)
grid = {}
for k in [4,8,16,32,64]:
    row = " %2d |" % k
    for m in [1,2,3,5,None]:
        o,_ = run(k, m, "full", reps=200)
        grid[(k,m)] = o.mean()
        row += " %7.3f (%.3f)" % (o.mean(), o.std())
    print(row)

print("\n=== calibration mode at each k (m=None) ===")
print("  k |   full affine   |  intercept only | slope only")
for k in [2,4,8,16,32]:
    a,_ = run(k, None, "full", reps=200)
    b,_ = run(k, None, "intercept", reps=200)
    c_,_ = run(k, None, "slope", reps=200)
    print(" %2d |  %7.3f (%.3f) |  %7.3f (%.3f) | %7.3f (%.3f)" % (k, a.mean(), a.std(), b.mean(), b.std(), c_.mean(), c_.std()))
print(" k=0 baseline 6.5157")
