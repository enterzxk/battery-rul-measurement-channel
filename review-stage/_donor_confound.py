
import pandas as pd, numpy as np
from math import comb
p=r'E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv'
df=pd.read_csv(p)
cnt=df.groupby(['group_id','cell_id']).size().reset_index(name='n')
L=df.groupby(['group_id','cell_id'])['rpt'].max().to_dict()
print('E[distinct donors] under the standard random-row protocol (5 donors, cell-disjoint):')
print('  k    E[donors]   (avg over 64 target cells)')
for k in (2,4,8,16,32,64):
    vals=[]
    for g,sub in cnt.groupby('group_id'):
        ns=sub.n.tolist()
        for i,n_t in enumerate(ns):
            pool=[x for j,x in enumerate(ns) if j!=i]
            N=sum(pool)
            if N<k: continue
            e=sum(1-comb(N-x,k)/comb(N,k) for x in pool if N-x>=k)
            vals.append(e)
    print('  %3d   %.2f'%(k,np.mean(vals)))
print()
print('rows per cell: mean %.2f  min %d  max %d'%(cnt.n.mean(),cnt.n.min(),cnt.n.max()))
