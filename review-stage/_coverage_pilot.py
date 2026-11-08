
import pandas as pd, numpy as np, itertools, json
p=r'E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv'
df=pd.read_csv(p)
df=df.rename(columns={'pred_A_curve_logo':'yhat'})
L=df.groupby(['group_id','cell_id'])['rpt'].max().to_dict()

def fit_affine(x,y):
    A=np.vstack([x,np.ones_like(x)]).T
    sol,*_=np.linalg.lstsq(A,y,rcond=None)
    return sol[0],sol[1]

rng=np.random.default_rng(20261108)
D=40
recs=[]
for g,gd in df.groupby('group_id'):
    cells=sorted(gd.cell_id.unique())
    for t in cells:
        tgt=gd[gd.cell_id==t]
        donors=[c for c in cells if c!=t]
        if len(donors)<2: continue
        Lt=L[(g,t)]
        for _ in range(D):
            perm=rng.permutation(donors)
            mae={}
            cover={}
            for m in (1,2):
                sel=perm[:m]
                cal=gd[gd.cell_id.isin(sel)]
                a,b=fit_affine(cal.yhat.values, cal.y_true.values)
                pred=a*tgt.yhat.values+b
                mae[m]=np.abs(pred-tgt.y_true.values).mean()
                cover[m]=max(L[(g,c)] for c in sel)>=Lt
            recs.append(dict(g=g,cell=t,Lt=Lt,Ld1=L[(g,perm[0])],mae1=mae[1],mae2=mae[2],
                             cov1=int(cover[1]),cov2=int(cover[2]),delta=mae[1]-mae[2]))
R=pd.DataFrame(recs)
print('draws:',len(R),'pairs:',R.groupby(['g','cell']).ngroups)
print('mean MAE m=1 %.4f  m=2 %.4f  delta %.4f'%(R.mae1.mean(),R.mae2.mean(),R.delta.mean()))
print()
print('--- split by coverage at m=1 (L_donor1 >= L_target) ---')
for c,sub in R.groupby('cov1'):
    print(' cov1=%d  n_draws=%5d (%.1f%%)  MAE m1=%.4f m2=%.4f  delta=%.4f  sd(delta)=%.4f'%(
        c,len(sub),100*len(sub)/len(R),sub.mae1.mean(),sub.mae2.mean(),sub.delta.mean(),sub.delta.std()))
print()
print('--- dose-response: delta vs kappa = Lt/Ld1 bins ---')
R['kappa']=R.Lt/R.Ld1
R['bin']=pd.cut(R.kappa,[0,0.8,0.95,1.0,1.1,1.3,10],include_lowest=True)
print(R.groupby('bin').agg(n=('delta','size'),delta=('delta','mean'),m1=('mae1','mean'),m2=('mae2','mean')))
print()
print('share of total delta mass from uncovered draws: %.1f%%'%(100*R[R.cov1==0].delta.sum()/R.delta.sum()))
