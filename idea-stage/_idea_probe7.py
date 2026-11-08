
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
from scipy import stats
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df=pd.read_csv(P); y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values; rng=np.random.default_rng(41)
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
    return Pc
pc0=pc(np.abs(p-y))
print("cond:        ", " ".join("%6.2f"%x for x in pc0))
for k,how in [(2,"random"),(3,"random"),(4,"random"),(2,"spread"),(4,"spread"),(6,"spread"),(8,"spread")]:
    Pc=run(k,how)
    med=np.median(Pc,0); d=med-pc0
    print("k=%2d %-6s median:"%(k,how), " ".join("%+6.2f"%x for x in d), "| worse %d/11  mean%+.2f"%( (d>0).sum(), d.mean()))
print("\n=== concentration of the k=16 gain (random) ===")
Pc=run(16,"random"); d=np.median(Pc,0)-pc0
tot=d.sum(); print("total %+.2f; top2 (%d,%d) contribute %+.2f = %.0f%% of total"%(tot,np.argsort(d)[0]+1,np.argsort(d)[1]+1,d[np.argsort(d)[0]]+d[np.argsort(d)[1]],100*(d[np.argsort(d)[0]]+d[np.argsort(d)[1]])/tot))
print("median delta %+.2f (=%.1f%% of baseline)"%(np.median(d),100*np.median(d)/6.5157))
print("\n=== power simulation for k=16 effect (n=11, alpha=.05 two-sided) ===")
sd=2.892; eff=-2.025; n=11
sim=rng.normal(eff,sd,(200000,n)); t=sim.mean(1)/(sim.std(1,ddof=1)/np.sqrt(n))
print("power(t-test) = %.2f"%(np.abs(t)>stats.t.ppf(.975,n-1)).mean())
print("MDE80 = %.3f cycles = %.1f%% baseline"%((stats.t.ppf(.975,10)+stats.t.ppf(.80,10))*sd/np.sqrt(11),100*(stats.t.ppf(.975,10)+stats.t.ppf(.80,10))*sd/np.sqrt(11)/6.5157))
