
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
from scipy import stats
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df = pd.read_csv(P)
y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values
groups=np.unique(g); NG=len(groups)
G={}
for gi in groups:
    m=g==gi; G[gi]=dict(p=p[m],y=y[m],c=c[m],cells=np.unique(c[m]))
base=np.array([np.mean([np.abs(G[gi]["y"][G[gi]["c"]==cc]-G[gi]["p"][G[gi]["c"]==cc]).mean() for cc in G[gi]["cells"]]) for gi in groups])

def sel_q(pp,k):
    o=np.argsort(pp); q=np.linspace(0,1,k)
    return np.unique(o[np.round(q*(len(o)-1)).astype(int)])
def sel_ext(pp,k):
    o=np.argsort(pp); h=k//2
    idx=np.r_[o[:h],o[len(o)-(k-h):]]
    return np.unique(idx)
def aff(ps,ys,pev):
    pm=ps.mean(); ym=ys.mean(); Sxx=((ps-pm)**2).sum()
    a=((ps-pm)*(ys-ym)).sum()/Sxx if Sxx>1e-12 else 1.0
    return a*pev+(ym-a*pm)

print("=== H. is 'quantile-spread' actually the optimal design? (D/A/slope-optimal = put half at each end) ===")
print("  k | quantile-spread | endpoints(rep) | delta   p  | Sxx_quant / Sxx_ext")
for k in [3,4,6,8,16]:
    a=[];b=[];r=[]
    for gi in groups:
        d=G[gi]; sa=[];sb=[]
        for cc in d["cells"]:
            ev=d["c"]==cc; pool=np.where(~ev)[0]; pp=d["p"][pool]; yy=d["y"][pool]
            s1=sel_q(pp,k); s2=sel_ext(pp,k)
            sa.append(np.abs(aff(pp[s1],yy[s1],d["p"][ev])-d["y"][ev]).mean())
            sb.append(np.abs(aff(pp[s2],yy[s2],d["p"][ev])-d["y"][ev]).mean())
            r.append((((pp[s1]-pp[s1].mean())**2).sum(), ((pp[s2]-pp[s2].mean())**2).sum()))
        a.append(np.mean(sa)); b.append(np.mean(sb))
    a=np.array(a); b=np.array(b); r=np.array(r)
    print(" %2d | %15.3f | %14.3f | %+6.3f  %.4f | %.2f"%(k,a.mean(),b.mean(),(a-b).mean(),stats.wilcoxon(a,b).pvalue,r[:,0].mean()/r[:,1].mean()))

print("\n=== I. count lever vs design lever (same units) ===")
print("  random arm: k0 6.516 -> k8 4.882 -> k16 4.484")
print("  count lever k=8->16 : %+.3f"%(4.484-4.882))
print("  design lever at k=8 : %+.3f"%(-0.472))
print("  ratio design/doubling: %.2f"%(0.472/(4.882-4.484)))
print("  total count lever 0->16: %+.3f ; max design lever: %+.3f ; ratio %.2f"%(4.484-6.516,-0.472,0.472/2.032))
