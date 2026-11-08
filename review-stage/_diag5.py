
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

def run_rand(k,cap=None):
    out=np.zeros((N,NG))
    for j,gi in enumerate(groups):
        d=G[gi]; cd=[]
        for cc in d["cells"]:
            ev=d["c"]==cc; pool=np.where(~ev)[0]
            pp=d["p"][pool]; yy=d["y"][pool]; m=len(pool)
            idx=np.argpartition(rng.random((N,m)),k-1,axis=1)[:,:k]
            ps=pp[idx]; ys=yy[idx]
            pm=ps.mean(1,keepdims=True); ym=ys.mean(1,keepdims=True)
            Sxx=((ps-pm)**2).sum(1); Sxy=((ps-pm)*(ys-ym)).sum(1)
            a=np.where(Sxx>1e-12,Sxy/np.maximum(Sxx,1e-12),1.0)
            if cap is not None: a=np.clip(a,cap[0],cap[1])
            b=ym[:,0]-a*pm[:,0]
            cd.append(np.abs(a[:,None]*d["p"][ev][None,:]+b[:,None]-d["y"][ev][None,:]).mean(1))
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
DC={k:run_rand(k,(0.5,2.0)) for k in KS}

print("=== B2. 'better at EVERY k' on the MEAN (single draw) ===")
allk=np.ones(N,dtype=bool)
for k in KS: allk &= (SP[k].mean() < D[k].mean(axis=1))
print("  P(mean_spread < mean_random at ALL 6 k) = %.3f"%allk.mean())
for k in KS: print("   k=%2d P=%.3f"%(k,(SP[k].mean()<D[k].mean(axis=1)).mean()))

print("\n=== E. the honest table: same design test, but against a REGULARIZED random arm ===")
print("  k | spread | OLS-rand | delta_OLS  p_OLS | clip-rand | delta_clip  p_clip | share of delta that is OLS instability")
for k in KS:
    r=D[k].mean(0); rc=DC[k].mean(0)
    d=r.mean()-rc.mean()
    print(" %2d | %6.3f | %8.3f | %+8.3f %6.4f | %9.3f | %+9.3f %6.4f | %5.0f%%"%(
        k,SP[k].mean(),r.mean(),SP[k].mean()-r.mean(),stats.wilcoxon(SP[k],r).pvalue,
        rc.mean(),SP[k].mean()-rc.mean(),stats.wilcoxon(SP[k],rc).pvalue,
        100*(1-abs(SP[k].mean()-rc.mean())/max(abs(SP[k].mean()-r.mean()),1e-9))))

print("\n=== F. does the design still beat k=0 once the arm is regularized? ===")
for k in [2,3,4,6,8,16]:
    pr=np.array([stats.wilcoxon(DC[k][i],base).pvalue for i in range(N)])
    print("  clip-rand k=%2d median MAE %.3f  median p vs k0 %.4f  P(p<.05) %.2f"%(k,np.median(DC[k].mean(1)),np.median(pr),(pr<0.05).mean()))
