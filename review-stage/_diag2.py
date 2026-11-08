
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
from scipy import stats
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df = pd.read_csv(P)
y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values
groups=np.unique(g); NG=len(groups)
rng=np.random.default_rng(20261108)
KS=[2,3,4,6,8,16]; N=1200
G={}
for gi in groups:
    m=g==gi; G[gi]=dict(p=p[m],y=y[m],c=c[m],cells=np.unique(c[m]))
base=np.array([np.mean([np.abs(G[gi]["y"][G[gi]["c"]==cc]-G[gi]["p"][G[gi]["c"]==cc]).mean() for cc in G[gi]["cells"]]) for gi in groups])

def sel_of(pp,yy,k,how):
    if how=="cluster":
        med=np.median(pp); return np.argsort(np.abs(pp-med))[:k]
    key = pp if how=="spread" else yy
    order=np.argsort(key); q=np.linspace(0,1,k)
    return np.unique(order[np.round(q*(len(order)-1)).astype(int)])

SP={};YQ={}
for k in KS:
    a1=[];a2=[]
    for gi in groups:
        d=G[gi]; s1=[];s2=[]
        for cc in d["cells"]:
            ev=d["c"]==cc; pool=np.where(~ev)[0]; pp=d["p"][pool]; yy=d["y"][pool]
            for how,acc in (("spread",s1),("yquant",s2)):
                s=sel_of(pp,yy,k,how); ps=pp[s]; ys=yy[s]
                pm=ps.mean(); ym=ys.mean(); Sxx=((ps-pm)**2).sum()
                a=(Sxx>1e-12)*((ps-pm)*(ys-ym)).sum()/max(Sxx,1e-12)+(Sxx<=1e-12)
                acc.append(np.abs(a*d["p"][ev]+(ym-a*pm)-d["y"][ev]).mean())
        a1.append(np.mean(s1)); a2.append(np.mean(s2))
    SP[k]=np.array(a1); YQ[k]=np.array(a2)

# random draws per group
D={}; SXX={}
for k in KS:
    mat=np.zeros((N,NG)); sx=np.zeros((N,NG))
    for j,gi in enumerate(groups):
        d=G[gi]; cd=[]; sd=[]
        for cc in d["cells"]:
            ev=d["c"]==cc; pool=np.where(~ev)[0]
            pp=d["p"][pool]; yy=d["y"][pool]; m=len(pool)
            idx=np.argpartition(rng.random((N,m)),k-1,axis=1)[:,:k]
            ps=pp[idx]; ys=yy[idx]
            pm=ps.mean(1,keepdims=True); ym=ys.mean(1,keepdims=True)
            Sxx=((ps-pm)**2).sum(1); Sxy=((ps-pm)*(ys-ym)).sum(1)
            a=np.where(Sxx>1e-12,Sxy/np.maximum(Sxx,1e-12),1.0); b=ym[:,0]-a*pm[:,0]
            cd.append(np.abs(a[:,None]*d["p"][ev][None,:]+b[:,None]-d["y"][ev][None,:]).mean(1))
            sd.append(Sxx)
        mat[:,j]=np.nanmean(np.array(cd).T,axis=1); sx[:,j]=np.nanmean(np.array(sd).T,axis=1)
    D[k]=mat; SXX[k]=sx

print("=== 3. ONE-DRAW LOTTERY: if the random arm were a single draw (n=%d) ==="%N)
print("  k | p(SP vs rand) median  frac<.05  frac<.0083 | p(SP vs k0) | frac(rand vs k0)<.05")
for k in KS:
    ps=np.array([stats.wilcoxon(SP[k],D[k][i]).pvalue for i in range(N)])
    p0=stats.wilcoxon(SP[k],base).pvalue
    pr=np.array([stats.wilcoxon(D[k][i],base).pvalue for i in range(N)])
    print(" %2d | %20.4f %9.2f %11.2f | %11.4f | %.2f"%(k,np.median(ps),(ps<0.05).mean(),(ps<0.05/6).mean(),p0,(pr<0.05).mean()))

print("\n=== 4. first k where RANDOM beats k=0 (p<.05 & right direction) ===")
first=[]
for i in range(N):
    f=99
    for k in KS:
        if stats.wilcoxon(D[k][i],base).pvalue<0.05 and (D[k][i]-base).mean()<0: f=k;break
    first.append(f)
first=np.array(first)
for kk in KS+[99]: print("  %-6s : %5.1f%%"%("none" if kk==99 else "k=%d"%kk,(first==kk).mean()*100))

print("\n=== 5. is the whole thing just the leverage S_xx? (per-draw, k=2 and k=4) ===")
for k in [2,4,8]:
    x=np.log(SXX[k].mean(1)); yy=np.log(D[k].mean(1))
    r=np.corrcoef(x,yy)[0,1]
    print("  k=%2d  corr(log S_xx, log MAE) = %.3f  R2 = %.3f"%(k,r,r*r))
print("  spread S_xx vs random S_xx (median over draws), ratio:")
for k in [2,4,8,16]:
    sxx_sp=[]
    for gi in groups:
        d=G[gi]
        for cc in d["cells"]:
            ev=d["c"]==cc; pool=np.where(~ev)[0]; pp=d["p"][pool]
            s=sel_of(pp,d["y"][pool],k,"spread"); sxx_sp.append(((pp[s]-pp[s].mean())**2).sum())
    print("   k=%2d  spread %.1f  random(median) %.1f  ratio %.1fx"%(k,np.mean(sxx_sp),np.median(SXX[k]),np.mean(sxx_sp)/np.median(SXX[k])))

print("\n=== 6. leave-one-condition-out, spread vs random(mean) at k=4 ===")
rmean=D[4].mean(0); dlt=SP[4]-rmean
for j in range(NG):
    keep=[i for i in range(NG) if i!=j]
    pv=stats.wilcoxon(SP[4][keep],rmean[keep]).pvalue
    print("  drop g%-2d  mean delta %+6.3f  p=%.4f"%(groups[j],dlt[keep].mean(),pv))
print("  full      mean delta %+6.3f  p=%.4f"%(dlt.mean(),stats.wilcoxon(SP[4],rmean).pvalue))
