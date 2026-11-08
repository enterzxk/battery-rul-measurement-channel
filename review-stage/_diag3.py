
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

def fit(a_cap=None,slope1=False):
    def f(ps,ys,pev,ye):
        pm=ps.mean(); ym=ys.mean()
        if slope1: return np.abs(pev+(ym-pm)-ye).mean()
        Sxx=((ps-pm)**2).sum(); Sxy=((ps-pm)*(ys-ym)).sum()
        a=Sxy/Sxx if Sxx>1e-12 else 1.0
        if a_cap is not None: a=float(np.clip(a,*a_cap))
        return np.abs(a*pev+(ym-a*pm)-ye).mean()
    return f
F=fit()

def sel_of(pp,k,how="spread"):
    order=np.argsort(pp); q=np.linspace(0,1,k)
    return np.unique(order[np.round(q*(len(order)-1)).astype(int)])

SP={}
for k in KS:
    a1=[]
    for gi in groups:
        d=G[gi]; s=[]
        for cc in d["cells"]:
            ev=d["c"]==cc; pool=np.where(~ev)[0]; pp=d["p"][pool]
            s.append(F(pp[sel_of(pp,k)],d["y"][pool][sel_of(pp,k)],d["p"][ev],d["y"][ev]))
        a1.append(np.mean(s))
    SP[k]=np.array(a1)

D={}
for k in KS:
    mat=np.zeros((N,NG))
    for j,gi in enumerate(groups):
        d=G[gi]; cd=[]
        for cc in d["cells"]:
            ev=d["c"]==cc; pool=np.where(~ev)[0]
            pp=d["p"][pool]; yy=d["y"][pool]; m=len(pool)
            idx=np.argpartition(rng.random((N,m)),k-1,axis=1)[:,:k]
            ps=pp[idx]; ys=yy[idx]
            pm=ps.mean(1,keepdims=True); ym=ys.mean(1,keepdims=True)
            Sxx=((ps-pm)**2).sum(1); Sxy=((ps-pm)*(ys-ym)).sum(1)
            a=np.where(Sxx>1e-12,Sxy/np.maximum(Sxx,1e-12),1.0); b=ym[:,0]-a*pm[:,0]
            cd.append(np.abs(a[:,None]*d["p"][ev][None,:]+b[:,None]-d["y"][ev][None,:]).mean(1))
        mat[:,j]=np.nanmean(np.array(cd).T,axis=1)
    D[k]=mat

print("=== A. CORRECTED TABLE (comparator = expectation over random draws, n=%d) ==="%N)
print("  k |  spread  rand(mean)   delta   p_wilcox   p_t     n_better")
for k in KS:
    r=D[k].mean(0); d=SP[k]-r
    print(" %2d | %7.3f %10.3f %+8.3f %10.4f %7.4f   %d/11"%(k,SP[k].mean(),r.mean(),d.mean(),
        stats.wilcoxon(SP[k],r).pvalue,stats.ttest_rel(SP[k],r).pvalue,int((d<0).sum())))

print("\n=== B. the claim 'better at EVERY k' as a single-draw event ===")
allk=np.ones(N,dtype=bool)
for k in KS: allk &= (SP[k][None,:] < D[k])
print("  P(spread < random at all 6 k, one draw) = %.3f"%(allk.mean()))
for k in KS:
    print("   k=%2d  P(spread<random) = %.3f  mean margin %+.3f"%(k,(SP[k][None,:]<D[k]).mean(),(SP[k][None,:]-D[k]).mean()))

print("\n=== C. 'k=2=200': is it the estimator or the data? ===")
for k in [2,3,4]:
    for name,ff in (("OLS",fit()),("clip|a|<=2",fit((0.5,2.0))),("slope=1",fit(slope1=True))):
        out=np.zeros((N,NG))
        for j,gi in enumerate(groups):
            d=G[gi]; cd=[]
            for cc in d["cells"]:
                ev=d["c"]==cc; pool=np.where(~ev)[0]
                pp=d["p"][pool]; yy=d["y"][pool]; m=len(pool)
                idx=np.argpartition(rng.random((N,m)),k-1,axis=1)[:,:k]
                ps=pp[idx]; ys=yy[idx]
                pm=ps.mean(1,keepdims=True); ym=ys.mean(1,keepdims=True)
                if name=="slope=1":
                    e=np.abs(ps+(ym-pm)-0)
                    pred=d["p"][ev][None,:]+(ym-pm)
                else:
                    Sxx=((ps-pm)**2).sum(1); Sxy=((ps-pm)*(ys-ym)).sum(1)
                    a=np.where(Sxx>1e-12,Sxy/np.maximum(Sxx,1e-12),1.0)
                    if name!="OLS": a=np.clip(a,0.5,2.0)
                    b=ym[:,0]-a*pm[:,0]
                    pred=a[:,None]*d["p"][ev][None,:]+b[:,None]
                cd.append(np.abs(pred-d["y"][ev][None,:]).mean(1))
            out[:,j]=np.nanmean(np.array(cd).T,axis=1)
        cm=out.mean(1)
        print("  k=%2d %-12s mean %8.2f median %7.3f p95 %8.2f max %9.1f"%(k,name,cm.mean(),np.median(cm),np.percentile(cm,95),cm.max()))
    sp=[]
    for gi in groups:
        d=G[gi]; s=[]
        for cc in d["cells"]:
            ev=d["c"]==cc; pool=np.where(~ev)[0]; pp=d["p"][pool]
            s.append(fit()(pp[sel_of(pp,k)],d["y"][pool][sel_of(pp,k)],d["p"][ev],d["y"][ev]))
        sp.append(np.mean(s))
    print("     %-12s %8.2f"%("spread",np.mean(sp)))

print("\n=== D. the '16' anchor: distribution of rand@k vs k=0 p over draws ===")
for k in [6,8,16]:
    pr=np.array([stats.wilcoxon(D[k][i],base).pvalue for i in range(N)])
    print("  k=%2d  median p=%.4f  P(p<.05)=%.2f  P(p<.01)=%.2f  median delta=%+.3f"%(
        k,np.median(pr),(pr<0.05).mean(),(pr<0.01).mean(),np.median(D[k].mean(1)-base.mean())))
