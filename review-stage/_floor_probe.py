
import pandas as pd, numpy as np
p=r'E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv'
df=pd.read_csv(p).rename(columns={'pred_A_curve_logo':'yhat'})
L=df.groupby(['group_id','cell_id'])['rpt'].max().to_dict()
def fit(x,y):
    A=np.vstack([x,np.ones_like(x)]).T
    s,*_=np.linalg.lstsq(A,y,rcond=None); return s[0],s[1]
rng=np.random.default_rng(11); D=200
KS=[16,32,48,64]
rows=[]
for g,gd in df.groupby('group_id'):
    cells=sorted(gd.cell_id.unique())
    for t in cells:
        tgt=gd[gd.cell_id==t]; donors=[c for c in cells if c!=t]
        for j in donors:
            Lj=L[(g,j)]
            if Lj<64: continue                      # only donors able to supply k=64
            dcal=gd[gd.cell_id==j]
            for k in KS:
                vals=[]
                for _ in range(D):
                    sel=dcal.iloc[rng.choice(len(dcal),k,replace=False)]
                    a,b=fit(sel.yhat.values,sel.y_true.values)
                    vals.append(np.abs(a*tgt.yhat.values+b-tgt.y_true.values).mean())
                rows.append(dict(g=g,cell=t,donor=j,Lj=Lj,k=k,mae=np.median(vals)))
R=pd.DataFrame(rows)
print('restricted to donors with L>=64 (within-donor row sweep, no donor-selection confound)')
print('units:',R.groupby(['g','cell','donor']).ngroups,'rows:',len(R))
piv=R.groupby('k').mae.mean()
print('\n  k : MAE (cell-macro over this subset)')
for k in KS: print('  %3d : %.4f'%(k,piv[k]))
print('\n  paired within (g,cell,donor):')
for a,b in zip(KS[:-1],KS[1:]):
    w=R[R.k==a].set_index(['g','cell','donor']).mae
    v=R[R.k==b].set_index(['g','cell','donor']).mae
    d=(w-v); d=d.dropna()
    print('   k=%2d -> %2d : delta %.4f  sd %.4f  n %d  pos %d/%d  t=%.2f'%(
        a,b,d.mean(),d.std(),len(d),(d>0).sum(),len(d), d.mean()/(d.std()/np.sqrt(len(d))) if d.std()>0 else 0))
print('\n  per-condition k=16 vs k=64:')
x=R[R.k==16].groupby('g').mae.mean(); y=R[R.k==64].groupby('g').mae.mean()
for g in x.index: print('   g%-2d k16 %.3f  k64 %.3f  delta %+.3f'%(g,x[g],y[g],x[g]-y[g]))
