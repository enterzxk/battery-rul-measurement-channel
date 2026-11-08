
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
from scipy import stats
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df = pd.read_csv(P)
y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values
groups=np.unique(g); NG=len(groups)
print("rows %d cells %d groups %d"%(len(y),len(np.unique(c)),NG))
rng=np.random.default_rng(20261108)
KS=[2,3,4,6,8,16]; N=1500
G={}
for gi in groups:
    m=g==gi; G[gi]=dict(p=p[m],y=y[m],c=c[m],cells=np.unique(c[m]))
base=np.array([np.mean([np.abs(G[gi]["y"][G[gi]["c"]==cc]-G[gi]["p"][G[gi]["c"]==cc]).mean() for cc in G[gi]["cells"]]) for gi in groups])
print("k=0 cell-macro MAE = %.3f"%base.mean())

def aff_err(ps,ys,pev,ye):
    pm=ps.mean(); ym=ys.mean()
    Sxx=((ps-pm)**2).sum(); Sxy=((ps-pm)*(ys-ym)).sum()
    a=Sxy/Sxx if Sxx>1e-12 else 1.0
    return np.abs(a*pev+(ym-a*pm)-ye).mean(), a

def sel_of(pp,yy,k,how):
    if how=="cluster":
        med=np.median(pp); return np.argsort(np.abs(pp-med))[:k]
    key = pp if how=="spread" else yy
    order=np.argsort(key); q=np.linspace(0,1,k)
    pos=np.round(q*(len(order)-1)).astype(int)
    return np.unique(order[pos])

# ---- random draws, per-group matrix ----
D={}; A={}
for k in KS:
    mat=np.zeros((N,NG)); slopes=[]
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
            b=ym[:,0]-a*pm[:,0]
            e=np.abs(a[:,None]*d["p"][ev][None,:]+b[:,None]-d["y"][ev][None,:]).mean(1)
            cd.append(e); slopes.append(np.abs(a))
        mat[:,j]=np.nanmean(np.array(cd).T,axis=1)
    D[k]=mat; A[k]=np.concatenate(slopes)

print("\n=== 1. RANDOM arm over %d draws (cell-macro MAE) ==="%N)
print("  k |    mean   median     p05     p95       max  P(>k0)  mean|a|  P(|a|>5)")
for k in KS:
    cm=D[k].mean(1)
    print(" %2d | %8.3f %8.3f %7.3f %7.3f %9.1f  %.3f   %6.2f   %.3f"%(
        k,cm.mean(),np.median(cm),np.percentile(cm,5),np.percentile(cm,95),cm.max(),
        (cm>base.mean()).mean(),A[k].mean(),(A[k]>5).mean()))

print("\n=== 2. deterministic designs (group-macro) ===")
print("  k |  spread  y-oracle  cluster | rand-median rand-mean  rand-p95")
SP={};YQ={};CL={}
for k in KS:
    acc={"spread":[],"yquant":[],"cluster":[]}
    for gi in groups:
        d=G[gi]; per={"spread":[],"yquant":[],"cluster":[]}
        for cc in d["cells"]:
            ev=d["c"]==cc; pool=np.where(~ev)[0]
            pp=d["p"][pool]; yy=d["y"][pool]
            for how in per:
                s=sel_of(pp,yy,k,how); e,_=aff_err(pp[s],yy[s],d["p"][ev],d["y"][ev]); per[how].append(e)
        for how in per: acc[how].append(np.mean(per[how]))
    SP[k]=np.mean(acc["spread"]);YQ[k]=np.mean(acc["yquant"]);CL[k]=np.mean(acc["cluster"])
    print(" %2d | %7.3f %9.3f %8.3f | %11.3f %9.3f %9.3f"%(k,SP[k],YQ[k],CL[k],np.median(D[k].mean(1)),D[k].mean(1).mean(),np.percentile(D[k].mean(1),95)))

print("\n=== 3. one-draw lottery: distribution of Wilcoxon p ===")
print("  k | p(SP vs rand): median  frac<.05  frac<.0083 | p(SP vs k0) | frac rand<k0 @.05")
for k in KS:
    ps=np.array([stats.wilcoxon(SP[k],D[k][i]).pvalue for i in range(N)])
    p0=stats.wilcoxon(SP[k],base).pvalue
    pr=np.array([stats.wilcoxon(D[k][i],base).pvalue for i in range(N)])
    print(" %2d | %18.4f %8.2f %11.2f | %11.4f | %.2f"%(k,np.median(ps),(ps<0.05).mean(),(ps<0.05/6).mean(),p0,(pr<0.05).mean()))

print("\n=== 4. first k where RANDOM beats k=0 (p<.05, right direction) ===")
first=[]
for i in range(N):
    f=99
    for k in KS:
        pv=stats.wilcoxon(D[k][i],base).pvalue
        if pv<0.05 and (D[k][i]-base).mean()<0: f=k;break
    first.append(f)
first=np.array(first)
for kk in KS+[99]:
    print("  %s : %5.1f%%"%("none" if kk==99 else "k=%d"%kk,(first==kk).mean()*100))
np.save(r"E:\桌面\rul\rul_v4_20261107\review-stage\_D.npy",np.array([D[k] for k in KS]))
