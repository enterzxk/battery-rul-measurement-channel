
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
from scipy import stats
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df=pd.read_csv(P); y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values; rng=np.random.default_rng(53)
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
    return Pc.mean(0), Pc
print("k | random | spread | paired diff (spread-random), sd, t, p, better")
for k in [2,3,4,6,8,16,32]:
    a,_=run(k,"random"); b,_=run(k,"spread"); d=b-a
    t=d.mean()/(d.std(ddof=1)/np.sqrt(11)); pv=stats.ttest_rel(b,a).pvalue
    try: wp=stats.wilcoxon(d).pvalue
    except Exception: wp=float("nan")
    tc,tp=stats.t.ppf(.975,10),stats.t.ppf(.80,10)
    print(" %2d | %.3f | %.3f | %+.3f  sd %.3f  t %+.2f  p %.4f  wilcox %.4f  better %d/11  MDE80=%.3f (%.1f%% base)"
          %(k,a.mean(),b.mean(),d.mean(),d.std(ddof=1),t,pv,wp,(d<0).sum(),(tc+tp)*d.std(ddof=1)/np.sqrt(11),100*(tc+tp)*d.std(ddof=1)/np.sqrt(11)/6.5157))
