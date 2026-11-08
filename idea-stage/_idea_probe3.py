
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df = pd.read_csv(P)
y  = df.y_true.values.astype(float); p = df.pred_A_curve_logo.values.astype(float)
g  = df.group_id.values; c = df.cell_id.values
rng = np.random.default_rng(11)
def cell_macro(e):
    t = pd.DataFrame({"e":e,"g":g,"c":c}).groupby(["g","c"]).e.mean()
    return float(t.groupby(level=0).mean().mean())
def per_cond(e):
    t = pd.DataFrame({"e":e,"g":g,"c":c}).groupby(["g","c"]).e.mean()
    return t.groupby(level=0).mean()

def run(k, mode, reps=300):
    out=np.zeros(reps); pcs=np.zeros((reps,len(np.unique(g))))
    for rep in range(reps):
        e=np.empty(len(y))
        for gid in np.unique(g):
            mg=g==gid; cells=np.unique(c[mg]); yg,pg,cg=y[mg],p[mg],c[mg]
            eg=np.empty(mg.sum())
            for tc in cells:
                te=cg==tc; po=np.where(~te)[0]
                idx=rng.choice(po,size=min(k,len(po)),replace=False)
                if mode=="affine":
                    A=np.c_[pg[idx],np.ones(len(idx))]
                    a,b=np.linalg.lstsq(A,yg[idx],rcond=None)[0]
                    pr=a*pg[te]+b
                elif mode=="intercept":
                    b=float(np.mean(yg[idx]-pg[idx])); pr=pg[te]+b
                elif mode=="nn_soh":
                    # 1-NN in predicted value (proxy for SOH rank): take label of nearest donor row
                    j=np.abs(pg[te][:,None]-pg[idx][None,:]).argmin(1)
                    pr=yg[idx][j]
                eg[te]=np.abs(pr-yg[te])
            e[mg]=eg
        out[rep]=cell_macro(e); pcs[rep]=per_cond(e).values
    return out,pcs

print("=== calibration mode comparison (cell-macro MAE, 300 draws) ===")
print("  k |  affine          |  intercept-only  |  1-NN(pred-space)")
store={}
for k in [2,4,8,16,32,64]:
    a,pa=run(k,"affine"); b,_=run(k,"intercept"); d,pd_=run(k,"nn_soh")
    store[k]=(a,b,d,pa,pd_)
    print(" %2d | %6.3f (%.3f) | %6.3f (%.3f) | %6.3f (%.3f)" % (k,a.mean(),a.std(),b.mean(),b.std(),d.mean(),d.std()))
print("  0 | 6.516 (fixed)  | 6.516          | 6.516")

print("\n=== per-condition delta vs k=0 (affine vs 1-NN at k=16) ===")
pc0=per_cond(np.abs(p-y)).values
for k in [8,16,32]:
    a,b,d,pa,pd_=store[k]
    da=pa.mean(0)-pc0; dd=pd_.mean(0)-pc0
    print("k=%2d affine : "%k + " ".join("%+.2f"%x for x in da) + "  improved %d/11 mean %+.2f sd %.2f"%( (da<0).sum(), da.mean(), da.std(ddof=1)))
    print("k=%2d 1NN    : "%k + " ".join("%+.2f"%x for x in dd) + "  improved %d/11 mean %+.2f sd %.2f"%( (dd<0).sum(), dd.mean(), dd.std(ddof=1)))

print("\n=== paired delta (1NN - affine) per condition at k=16 ===")
a,b,d,pa,pd_=store[16]
diff = pd_.mean(0)-pa.mean(0)
print(" ".join("%+.2f"%x for x in diff), "| mean %+.2f sd %.2f t %.2f"%(diff.mean(),diff.std(ddof=1),diff.mean()/(diff.std(ddof=1)/np.sqrt(11))))
from scipy import stats
print("wilcoxon p=%.4f  sign test improved %d/11"%(stats.wilcoxon(diff).pvalue,(diff<0).sum()))
