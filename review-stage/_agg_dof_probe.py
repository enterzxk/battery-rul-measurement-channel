
import pandas as pd, numpy as np
p=r'E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv'
df=pd.read_csv(p).rename(columns={'pred_A_curve_logo':'yhat'})
L=df.groupby(['group_id','cell_id'])['rpt'].max().to_dict()
def fit(x,y):
    A=np.vstack([x,np.ones_like(x)]).T
    s,*_=np.linalg.lstsq(A,y,rcond=None); return s[0],s[1]
rng=np.random.default_rng(7)
D=300
out=[]
for g,gd in df.groupby('group_id'):
    cells=sorted(gd.cell_id.unique())
    for t in cells:
        tgt=gd[gd.cell_id==t]; donors=[c for c in cells if c!=t]
        if len(donors)<2: continue
        m1=[];m2=[]
        for _ in range(D):
            perm=rng.permutation(donors)
            for m,acc in ((1,m1),(2,m2)):
                cal=gd[gd.cell_id.isin(perm[:m])]
                a,b=fit(cal.yhat.values,cal.y_true.values)
                acc.append(np.abs(a*tgt.yhat.values+b-tgt.y_true.values).mean())
        out.append(dict(g=g,cell=t,m1_mean=np.mean(m1),m1_med=np.median(m1),m1_trim=np.mean(sorted(m1)[int(.05*D):int(.95*D)]),
                        m2_mean=np.mean(m2),m2_med=np.median(m2),m2_trim=np.mean(sorted(m2)[int(.05*D):int(.95*D)])))
R=pd.DataFrame(out)
def cell_macro(col):
    x=R.groupby('g')[col].mean(); return x.mean()
print('aggregation over MC draws -> cell-macro MAE (my impl, D=300, per-target-cell affine, all rows)')
for agg in ('mean','med','trim'):
    a=cell_macro('m1_'+agg); b=cell_macro('m2_'+agg)
    print('  agg=%-5s m=1 %.4f  m=2 %.4f  delta %.4f'%(agg,a,b,a-b))
print()
print('compare to published impls at m=1: EXP-004 4.509 | review 4.652 | EXP-001 k=16 4.505')
print('MC-draw distribution at m=1: mean %.3f median %.3f  p95 %.3f  max %.1f'%(
    R.m1_mean.mean(),R.m1_med.mean(),
    np.mean([np.percentile(v,95) for v in [R.m1_mean]]), R.m1_mean.max()))
