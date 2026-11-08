
import pandas as pd, numpy as np
p=r'E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv'
df=pd.read_csv(p).rename(columns={'pred_A_curve_logo':'yhat'})
# EXP-001 style: k random rows pooled from all other cells of the condition (donor-averaged)
def fit(x,y):
    A=np.vstack([x,np.ones_like(x)]).T
    s,*_=np.linalg.lstsq(A,y,rcond=None); return s[0],s[1]
rng=np.random.default_rng(3); D=200
for k in (4,8,16,32):
    per_cond=[]
    for g,gd in df.groupby('group_id'):
        cells=sorted(gd.cell_id.unique()); cell_maes=[]
        for t in cells:
            tgt=gd[gd.cell_id==t]; pool=gd[gd.cell_id!=t]
            v=[]
            for _ in range(D):
                sel=pool.iloc[rng.choice(len(pool),k,replace=False)]
                a,b=fit(sel.yhat.values,sel.y_true.values)
                v.append(np.abs(a*tgt.yhat.values+b-tgt.y_true.values).mean())
            cell_maes.append(np.mean(v))
        per_cond.append(np.mean(cell_maes))
    print('  donor-averaged pool  k=%2d  cell-macro MAE = %.4f'%(k,np.mean(per_cond)))
