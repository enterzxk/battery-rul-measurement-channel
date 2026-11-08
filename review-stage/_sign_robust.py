
import pandas as pd, numpy as np
p=r'E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv'
df=pd.read_csv(p).rename(columns={'pred_A_curve_logo':'yhat'})
def fit(x,y):
    A=np.vstack([x,np.ones_like(x)]).T
    s,*_=np.linalg.lstsq(A,y,rcond=None); return s[0],s[1]
rng=np.random.default_rng(99); D=300
rows=[]
for g,gd in df.groupby('group_id'):
    cells=sorted(gd.cell_id.unique())
    for t in cells:
        tgt=gd[gd.cell_id==t]; donors=[c for c in cells if c!=t]
        if len(donors)<2: continue
        acc={1:[],2:[],3:[]}
        for _ in range(D):
            perm=rng.permutation(donors)
            for m in (1,2,3):
                cal=gd[gd.cell_id.isin(perm[:m])]
                a,b=fit(cal.yhat.values,cal.y_true.values)
                acc[m].append(np.abs(a*tgt.yhat.values+b-tgt.y_true.values).mean())
        rows.append(dict(g=g,cell=t,**{('m%d_%s'%(m,a)): (np.mean(v) if a=='mean' else np.median(v))
                                        for m,v in acc.items() for a in ('mean','med')}))
R=pd.DataFrame(rows)
print('per-condition cell-macro delta (m=1 -> m=2), two aggregation rules:')
print(' g   mean-agg   med-agg')
signs={'mean':0,'med':0}
for g,sub in R.groupby('g'):
    d1=sub.m1_mean.mean()-sub.m2_mean.mean(); d2=sub.m1_med.mean()-sub.m2_med.mean()
    signs['mean']+= d1>0; signs['med']+= d2>0
    print(' %-2d  %+8.4f  %+8.4f'%(g,d1,d2))
print()
print('positive conditions: mean-agg %d/11   med-agg %d/11'%(signs['mean'],signs['med']))
print('cell-macro effect: mean-agg %.4f   med-agg %.4f'%(
    R.m1_mean.mean()-R.m2_mean.mean(), R.m1_med.mean()-R.m2_med.mean()))
from math import comb
print('exact two-sided sign test at 11/11: p = %.5f'%(2/2**11))
print()
print('per-cell sign under mean-agg: %d/%d positive'%(( (R.m1_mean-R.m2_mean)>0).sum(), len(R)))
