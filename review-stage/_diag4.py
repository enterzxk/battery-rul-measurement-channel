
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
from scipy import stats
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df = pd.read_csv(P)
y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values
groups=np.unique(g); NG=len(groups)
rng=np.random.default_rng(777)
KS=[2,3,4,6,8,16]; N=2000
G={}
for gi in groups:
    m=g==gi; G[gi]=dict(p=p[m],y=y[m],c=c[m],cells=np.unique(c[m]))
base=np.array([np.mean([np.abs(G[gi]["y"][G[gi]["c"]==cc]-G[gi]["p"][G[gi]["c"]==cc]).mean() for cc in G[gi]["cells"]]) for gi in groups])

def sel_of(pp,k):
    order=np.argsort(pp); q=np.linspace(0,1,k)
    return np.unique(order[np.round(q*(len(order)-1)).astype(int)])

def run_rand(k,cap=None,slope1=False):
    out=np.zeros((N,NG))
    for j,gi in enumerate(groups):
        d=G[gi]; cd=[]
        for cc in d["cells"]:
            ev=d["c"]==cc; pool=np.where(~ev)[0]
            pp=d["p"][pool]; yy=d["y"][pool]; m=len(pool)
            idx=np.argpartition(rng.random((N,m)),k-1,axis=1)[:,:k]
            ps=pp[idx]; ys=yy[idx]
            pm=ps.mean(1,keepdims=True); ym=ys.mean(1,keepdims=True)
            if slope1:
                pred=d["p"][ev][None,:]+(ym-pm)
            else:
                Sxx=((ps-pm)**2).sum(1); Sxy=((ps-pm)*(ys-ym)).sum(1)
                a=np.where(Sxx>1e-12,Sxy/np.maximum(Sxx,1e-12),1.0)
                if cap is not None: a=np.clip(a,cap[0],cap[1])
                b=ym[:,0]-a*pm[:,0]
                pred=a[:,None]*d["p"][ev][None,:]+b[:,None]
            cd.append(np.abs(pred-d["y"][ev][None,:]).mean(1))
        out[:,j]=np.nanmean(np.array(cd).T,axis=1)
    return out

SP={}
for k in KS:
    a1=[]
    for gi in groups:
        d=G[gi]; s=[]
        for cc in d["cells"]:
            ev=d["c"]==cc; pool=np.where(~ev)[0]; pp=d["p"][pool]; s0=sel_of(pp,k)
            ps=pp[s0]; ys=d["y"][pool][s0]
            pm=ps.mean(); ym=ys.mean(); Sxx=((ps-pm)**2).sum()
            a=((ps-pm)*(ys-ym)).sum()/Sxx if Sxx>1e-12 else 1.0
            s.append(np.abs(a*d["p"][ev]+(ym-a*pm)-d["y"][ev]).mean())
        a1.append(np.mean(s))
    SP[k]=np.array(a1)

D={k:run_rand(k) for k in KS}

print("=== B. 'better at EVERY k' as a single-draw event ===")
allk=np.ones(N,dtype=bool)
for k in KS: allk &= (SP[k][None,:] < D[k]).all(axis=1)
print("  P(spread < random at ALL 6 k, single draw) = %.3f"%allk.mean())
for k in KS:
    print("   k=%2d  P(spread<random)=%.3f  mean margin %+.3f"%(k,(SP[k][None,:]<D[k]).mean(),(SP[k][None,:]-D[k]).mean()))

print("\n=== C. is 'k=2 -> 200' the data or the estimator? ===")
for k in [2,3,4]:
    for name,cap,s1 in (("OLS",None,False),("clip |a| in [0.5,2]",(0.5,2.0),False),("slope=1 (intercept only)",None,True)):
        cm=run_rand(k,cap,s1).mean(1)
        print("  k=%2d %-26s mean %9.2f median %7.3f p95 %8.2f max %10.1f"%(k,name,cm.mean(),np.median(cm),np.percentile(cm,95),cm.max()))
    sp=[]
    for gi in groups:
        d=G[gi]; s=[]
        for cc in d["cells"]:
            ev=d["c"]==cc; pool=np.where(~ev)[0]; pp=d["p"][pool]; s0=sel_of(pp,k)
            ps=pp[s0]; ys=d["y"][pool][s0]
            pm=ps.mean(); ym=ys.mean(); Sxx=((ps-pm)**2).sum()
            a=((ps-pm)*(ys-ym)).sum()/Sxx if Sxx>1e-12 else 1.0
            s.append(np.abs(a*d["p"][ev]+(ym-a*pm)-d["y"][ev]).mean())
        sp.append(np.mean(s))
    print("     %-26s %9.2f"%("spread (deterministic)",np.mean(sp)))

print("\n=== D. the '16' anchor ===")
for k in [6,8,16]:
    pr=np.array([stats.wilcoxon(D[k][i],base).pvalue for i in range(N)])
    print("  k=%2d  median p=%.4f  P(p<.05)=%.2f  P(p<.01)=%.2f  median delta=%+.3f"%(
        k,np.median(pr),(pr<0.05).mean(),(pr<0.01).mean(),np.median(D[k].mean(1)-base.mean())))
np.savez(r"E:\桌面\rul\rul_v4_20261107\review-stage\_diag.npz",**{"D%d"%k:D[k] for k in KS},**{"S%d"%k:SP[k] for k in KS},base=base)
