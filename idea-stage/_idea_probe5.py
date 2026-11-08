
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df = pd.read_csv(P)
y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values; rpt=df.rpt.values.astype(int)
print("=== per-condition cell lifetime structure (rpt units) ===")
rows=[]
for gid in np.unique(g):
    m=g==gid
    d = pd.DataFrame({"c":c[m],"r":rpt[m]}).groupby("c").r.max()
    rows.append((gid, len(d), d.min(), d.max(), d.max()-d.min(), np.median(d)))
t=pd.DataFrame(rows, columns=["cond","ncells","min_die","max_die","span","med_die"])
print(t.to_string(index=False))
print("total rows per cond:", pd.Series(c).groupby(g).size().values)

print("\n=== survival: fraction of cells dead by relative time ===")
for frac in [0.2,0.3,0.4,0.5,0.6,0.7]:
    fr=[]
    for gid in np.unique(g):
        m=g==gid
        d = pd.DataFrame({"c":c[m],"r":rpt[m]}).groupby("c").r.max().values
        T = frac*d.max()
        fr.append((d<=T).mean())
    print(" T=%.1f*max  dead fraction %.2f  (n conditions with >=1 dead: %d/11)"%(frac,np.mean(fr),sum(1 for x in fr if x>0)))
