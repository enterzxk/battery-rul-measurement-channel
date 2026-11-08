
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
from scipy import stats
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df = pd.read_csv(P)
y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values
rng=np.random.default_rng(23)
def cm(e):
    t=pd.DataFrame({"e":e,"g":g,"c":c}).groupby(["g","c"]).e.mean(); return float(t.groupby(level=0).mean().mean())
def pc(e):
    t=pd.DataFrame({"e":e,"g":g,"c":c}).groupby(["g","c"]).e.mean(); return t.groupby(level=0).mean()

def design_idx(pool_idx, pg, k, how):
    if how=="random":
        return rng.choice(pool_idx,size=min(k,len(pool_idx)),replace=False)
    order = pool_idx[np.argsort(pg[pool_idx])]
    if how=="spread":                       # quantile-spaced along predicted axis
        q = np.linspace(0,1,k)
        pos = np.round(q*(len(order)-1)).astype(int)
        return np.unique(order[pos])
    if how=="clustered":                    # all near the median prediction
        med = np.median(pg[pool_idx])
        return pool_idx[np.argsort(np.abs(pg[pool_idx]-med))[:k]]
    raise ValueError

def run(k, how, reps=300, ret_draws=False):
    out=np.zeros(reps); P_=np.zeros((reps,11)); worse=0
    for rep in range(reps):
        e=np.empty(len(y))
        for gid in np.unique(g):
            mg=g==gid; cells=np.unique(c[mg]); yg,pg,cg=y[mg],p[mg],c[mg]
            eg=np.empty(mg.sum())
            for tc in cells:
                te=cg==tc; po=np.where(~te)[0]
                idx=design_idx(po,pg,k,how)
                A=np.c_[pg[idx],np.ones(len(idx))]
                a,b=np.linalg.lstsq(A,yg[idx],rcond=None)[0]
                eg[te]=np.abs(a*pg[te]+b-yg[te])
            e[mg]=eg
        out[rep]=cm(e); P_[rep]=pc(e).values
        if out[rep]>6.5157: worse+=1
    return out,P_,worse/reps

print("=== design of the label set (300 draws) ===")
print("  k |    random        |    spread(D-opt) |   clustered")
base={}
for k in [2,3,4,6,8,12,16,24,32]:
    r1,P1,w1=run(k,"random"); r2,P2,_=run(k,"spread"); r3,P3,_=run(k,"clustered")
    base[k]=(r1,r2,r3,P1,P2,P3,w1)
    print(" %2d | %6.3f (%.3f) p(worse)=%.2f | %6.3f (%.3f) | %6.3f (%.3f)"
          %(k,r1.mean(),r1.std(),w1,r2.mean(),r2.std(),r3.mean(),r3.std()))

print("\n=== per-condition k=0 baseline and relative delta (affine, random) ===")
pc0=pc(np.abs(p-y)).values
for k in [8,16,32]:
    P1=base[k][3]; d=P1.mean(0)-pc0; rel=d/pc0*100
    print("k=%2d baseline:"%k, " ".join("%5.2f"%x for x in pc0))
    print("      absdelta:", " ".join("%+5.2f"%x for x in d))
    print("      rel%%    :", " ".join("%+5.1f"%x for x in rel))
    print("      median rel %.1f%%  mean rel %.1f%%  |delta|>17%% of base in %d/11"%(np.median(rel),rel.mean(),(np.abs(rel)>17).sum()))

print("\n=== how much of the mean gain comes from the top-2 conditions (k=16) ===")
d=base[16][3].mean(0)-pc0
srt=np.sort(d)
print("sorted deltas:", " ".join("%+.2f"%x for x in srt))
print("mean all %+.3f | mean excluding 2 largest gains %+.3f"%(d.mean(), srt[:-2].mean()))
print("median %+.3f"%np.median(d))

print("\n=== paired: spread-k vs random-2k (does design halve the budget?) ===")
for k in [4,8,16]:
    a=base[k][1].mean(0); b=base[min(2*k,32)][0].mean(0)
    dd=a-b
    print("spread(k=%2d) %.3f vs random(k=%2d) %.3f -> paired mean %+.3f sd %.2f t %.2f p %.3f"
          %(k,base[k][1].mean(),2*k,base[2*k][0].mean(),dd.mean(),dd.std(ddof=1),dd.mean()/(dd.std(ddof=1)/np.sqrt(11)),stats.ttest_rel(a,b).pvalue))
