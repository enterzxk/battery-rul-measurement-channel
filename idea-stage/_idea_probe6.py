
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
from scipy import stats
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df=pd.read_csv(P); y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values; rng=np.random.default_rng(31)
def cm(e):
    t=pd.DataFrame({"e":e,"g":g,"c":c}).groupby(["g","c"]).e.mean(); return float(t.groupby(level=0).mean().mean())
def pc(e):
    t=pd.DataFrame({"e":e,"g":g,"c":c}).groupby(["g","c"]).e.mean(); return t.groupby(level=0).mean().values
def sel(po,pg,k,how):
    if how=="random": return rng.choice(po,size=min(k,len(po)),replace=False)
    o=po[np.argsort(pg[po])]
    if how=="spread":
        pos=np.round(np.linspace(0,1,k)*(len(o)-1)).astype(int); return np.unique(o[pos])
    med=np.median(pg[po]); return po[np.argsort(np.abs(pg[po]-med))[:k]]
def run(k,how,reps=300):
    out=np.zeros(reps); Pc=np.zeros((reps,11)); rho=np.zeros(reps)
    for rep in range(reps):
        e=np.empty(len(y)); rh=[]
        for gid in np.unique(g):
            m=g==gid; cells=np.unique(c[m]); yg,pg,cg=y[m],p[m],c[m]
            eg=np.empty(m.sum())
            for tc in cells:
                te=cg==tc; po=np.where(~te)[0]; idx=sel(po,pg,k,how)
                A=np.c_[pg[idx],np.ones(len(idx))]
                a,b=np.linalg.lstsq(A,yg[idx],rcond=None)[0]
                eg[te]=np.abs(a*pg[te]+b-yg[te])
                rh.append(np.sum((pg[idx]-pg[idx].mean())**2)/np.sum((pg[po]-pg[po].mean())**2))
            e[m]=eg
        out[rep]=cm(e); Pc[rep]=pc(e); rho[rep]=np.mean(rh)
    return out,Pc,rho

print("=== risk profile: distribution of MAE over label draws (300 reps) ===")
print("  k | design | median   p5     p95     max   P(>k=0)  P(>2x)  rho")
base=6.5157
store={}
for k in [2,3,4,6,8,16,32]:
    for how in ["random","spread"]:
        o,Pc,rho=run(k,how); store[(k,how)]=(o,Pc,rho)
        print(" %2d | %-6s | %7.3f %6.3f %8.3f %8.1f   %.2f    %.2f   %.3f"
              %(k,how,np.median(o),np.percentile(o,5),np.percentile(o,95),o.max(),(o>base).mean(),(o>2*base).mean(),rho.mean()))

print("\n=== paired per-condition comparisons (mean over draws) ===")
def pair(a,b,label):
    d=a-b
    t=d.mean()/(d.std(ddof=1)/np.sqrt(11)); pv=stats.ttest_rel(a,b).pvalue
    try: wp=stats.wilcoxon(d).pvalue
    except Exception: wp=np.nan
    print("%-28s mean %+0.3f sd %.2f t %+.2f p %.3f wilcoxon %.4f  better %d/11"%(label,d.mean(),d.std(ddof=1),t,pv,wp,(d<0).sum()))
pair(store[(8,"spread")][1].mean(0), store[(16,"random")][1].mean(0), "spread k=8 vs random k=16")
pair(store[(4,"spread")][1].mean(0), store[(8,"random")][1].mean(0),  "spread k=4 vs random k=8")
pair(store[(4,"spread")][1].mean(0), store[(6,"random")][1].mean(0),  "spread k=4 vs random k=6")
pair(store[(2,"spread")][1].mean(0), store[(0,"random")][1].mean(0) if (0,"random") in store else pc(np.abs(p-y)), "spread k=2 vs k=0")
print("\nspread k=2 per-condition delta:", " ".join("%+.2f"%x for x in (store[(2,"spread")][1].mean(0)-pc(np.abs(p-y)))))

print("\n=== MDE arithmetic ===")
d16=store[(16,"random")][1].mean(0)-pc(np.abs(p-y))
sd=d16.std(ddof=1); n=11
tc,tp=stats.t.ppf(.975,n-1),stats.t.ppf(.80,n-1)
mde=(tc+tp)*sd/np.sqrt(n)
print("per-condition delta k=16: mean %+.3f sd %.3f  |  SE %.3f"%(d16.mean(),sd,sd/np.sqrt(n)))
print("MDE80 (n=11) = %.3f cycles = %.1f%% of baseline 6.516"%(mde,100*mde/6.5157))
from scipy.stats import nct
nc=d16.mean()/(sd/np.sqrt(n)); print("observed t=%.2f -> post-hoc power at this effect = %.2f"%(nc,1-nct.cdf(tc,10,nc)))
for eff in [0.10,0.20,0.31,0.50]:
    need=(2.802*sd/(eff*6.5157))**2; print("  effect %.0f%% of baseline -> conditions needed for 80%% power: %.1f"%(eff*100,need))
