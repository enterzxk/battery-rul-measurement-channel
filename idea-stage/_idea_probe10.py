
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
from scipy import stats
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df=pd.read_csv(P); y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values; rng=np.random.default_rng(61)
def pc(e):
    t=pd.DataFrame({"e":e,"g":g,"c":c}).groupby(["g","c"]).e.mean(); return t.groupby(level=0).mean().values
def sel(po,pg,k,how):
    if how=="random": return rng.choice(po,size=min(k,len(po)),replace=False)
    o=po[np.argsort(pg[po])]; pos=np.round(np.linspace(0,1,k)*(len(o)-1)).astype(int); return np.unique(o[pos])
def run(k,how,reps=400):
    Pc=np.zeros((reps,11))
    for rep in range(reps):
        e=np.empty(len(y))
        for gid in np.unique(g):
            m=g==gid; cells=np.unique(c[m]); yg,pg,cg=y[m],p[m],c[m]
            eg=np.empty(m.sum())
            for tc in cells:
                te=cg==tc; po=np.where(~te)[0]; idx=sel(po,pg,k,how)
                A=np.c_[pg[idx],np.ones(len(idx))]; a,b=np.linalg.lstsq(A,yg[idx],rcond=None)[0]
                eg[te]=np.abs(a*pg[te]+b-yg[te])
            e[m]=eg
        Pc[rep]=pc(e)
    return np.median(Pc,0)
pc0=pc(np.abs(p-y))
print("=== harm curve: per-condition MEDIAN MAE vs k=0 (400 draws) ===")
print(" k  design | median-of-medians | worse/11 | wilcoxon p (2-sided) | sign 1-sided | sign 2-sided")
for k,how in [(2,"random"),(3,"random"),(4,"random"),(6,"random"),(8,"random"),(16,"random"),(32,"random"),(2,"spread"),(4,"spread"),(6,"spread"),(8,"spread")]:
    med=run(k,how); d=med-pc0; w=(d>0).sum()
    try: wp=stats.wilcoxon(med,pc0).pvalue
    except Exception: wp=float("nan")
    s1=stats.binomtest(w,11,0.5,alternative="greater").pvalue
    s2=stats.binomtest(w,11,0.5).pvalue
    print(" %2d %-6s | %8.3f          | %2d/11    | %.4f               | %.4f       | %.4f"%(k,how,np.median(med),w,wp,s1,s2))
print("\nk=0 per-condition MAE:", " ".join("%.2f"%x for x in pc0), "| median %.3f mean %.3f"%(np.median(pc0),pc0.mean()))
print("\n=== minimum detectable counts, n=11 (exact binomial) ===")
for w in [8,9,10,11]:
    print(" %2d/11: one-sided %.4f  two-sided %.4f"%(w,stats.binomtest(w,11,.5,alternative='greater').pvalue,stats.binomtest(w,11,.5).pvalue))
