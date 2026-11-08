
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
from scipy import stats
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df=pd.read_csv(P); y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values; rng=np.random.default_rng(71)
def pc(e):
    t=pd.DataFrame({"e":e,"g":g,"c":c}).groupby(["g","c"]).e.mean(); return t.groupby(level=0).mean().values
def run(k,reps=400):
    Pc=np.zeros((reps,11))
    for rep in range(reps):
        e=np.empty(len(y))
        for gid in np.unique(g):
            m=g==gid; cells=np.unique(c[m]); yg,pg,cg=y[m],p[m],c[m]
            eg=np.empty(m.sum())
            for tc in cells:
                te=cg==tc; po=np.where(~te)[0]; idx=rng.choice(po,size=min(k,len(po)),replace=False)
                A=np.c_[pg[idx],np.ones(len(idx))]; a,b=np.linalg.lstsq(A,yg[idx],rcond=None)[0]
                eg[te]=np.abs(a*pg[te]+b-yg[te])
            e[m]=eg
        Pc[rep]=pc(e)
    return Pc.mean(0)
for a,b in [(8,16),(16,32),(8,32)]:
    x=run(a); z=run(b); d=x-z
    print("k=%2d vs k=%2d: mean %.3f vs %.3f  diff %+.3f sd %.3f t %+.2f p %.4f wilcox %.4f  better %d/11"%(
        a,b,x.mean(),z.mean(),d.mean(),d.std(ddof=1),d.mean()/(d.std(ddof=1)/np.sqrt(11)),
        stats.ttest_rel(x,z).pvalue, stats.wilcoxon(d).pvalue,(d<0).sum()))
