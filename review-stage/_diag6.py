
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
from sklearn.isotonic import IsotonicRegression
from scipy import stats
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df = pd.read_csv(P)
y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values
groups=np.unique(g); NG=len(groups)
rng=np.random.default_rng(4242)
KS=[4,8,16]; N=400
G={}
for gi in groups:
    m=g==gi; G[gi]=dict(p=p[m],y=y[m],c=c[m],cells=np.unique(c[m]))

def sel_of(pp,k):
    order=np.argsort(pp); q=np.linspace(0,1,k)
    return np.unique(order[np.round(q*(len(order)-1)).astype(int)])

def predict(ps,ys,pev,kind):
    if kind=="affine":
        pm=ps.mean(); ym=ys.mean(); Sxx=((ps-pm)**2).sum()
        a=((ps-pm)*(ys-ym)).sum()/Sxx if Sxx>1e-12 else 1.0
        return a*pev+(ym-a*pm)
    if kind=="iso":
        ir=IsotonicRegression(out_of_bounds="clip").fit(ps,ys)
        return ir.predict(pev)
    if kind=="1nn":
        out=np.empty(len(pev))
        for i,v in enumerate(pev):
            out[i]=ys[np.argmin(np.abs(ps-v))]
        return out

print("=== G. does the design advantage survive a change of calibrator family? ===")
print("  k | calibrator | spread | rand(mean) | delta   p")
for k in KS:
    for kind in ("affine","iso","1nn"):
        sp=[];rd=np.zeros((N,NG))
        for j,gi in enumerate(groups):
            d=G[gi]; s=[]; cd=[]
            for cc in d["cells"]:
                ev=d["c"]==cc; pool=np.where(~ev)[0]
                pp=d["p"][pool]; yy=d["y"][pool]; m=len(pool)
                s0=sel_of(pp,k)
                s.append(np.abs(predict(pp[s0],yy[s0],d["p"][ev],kind)-d["y"][ev]).mean())
                idx=np.argpartition(rng.random((N,m)),k-1,axis=1)[:,:k]
                e=np.empty(N)
                for i in range(N):
                    e[i]=np.abs(predict(pp[idx[i]],yy[idx[i]],d["p"][ev],kind)-d["y"][ev]).mean()
                cd.append(e)
            sp.append(np.mean(s)); rd[:,j]=np.nanmean(np.array(cd).T,axis=1)
        sp=np.array(sp); r=rd.mean(0)
        print(" %2d | %-10s | %6.3f | %9.3f | %+6.3f  %.4f"%(k,kind,sp.mean(),r.mean(),(sp-r).mean(),stats.wilcoxon(sp,r).pvalue))
