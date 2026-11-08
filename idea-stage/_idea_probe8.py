
# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
P = r"E:\桌面\rul\rul_v4_20261107\code\results\20261107-203233_e1_reproduce_full_table\preds.csv"
df=pd.read_csv(P); y=df.y_true.values.astype(float); p=df.pred_A_curve_logo.values.astype(float)
g=df.group_id.values; c=df.cell_id.values; r=df.rpt.values.astype(int)
def fit(idx, yg, pg):
    A=np.c_[pg[idx],np.ones(len(idx))]; return np.linalg.lstsq(A,yg[idx],rcond=None)[0]
print("=== censoring pilot: labels only from cells already dead at T ===")
print("T=frac*maxdeath | n_donor_cells(mean) | MAE censored | MAE oracle(all donors) | MAE k=0 | rows scored")
for frac in [0.70,0.80,0.90]:
    errs_c=[]; errs_o=[]; errs_0=[]; nd=[]; nr=[]
    for gid in np.unique(g):
        m=g==gid; cells=np.unique(c[m]); yg,pg,cg,rg=y[m],p[m],c[m],r[m]
        death={cc: rg[cg==cc].max() for cc in cells}
        T=frac*max(death.values())
        for tc in cells:
            if death[tc]<=T: continue          # target must be alive at T
            te=(cg==tc)&(rg>=T)                # prospective evaluation
            if te.sum()==0: continue
            don_c=[cc for cc in cells if cc!=tc and death[cc]<=T]     # available = dead
            don_a=[cc for cc in cells if cc!=tc]                      # oracle = any donor
            if len(don_c)==0: continue
            ic=np.where(np.isin(cg,don_c))[0]; ia=np.where(np.isin(cg,don_a))[0]
            if len(ic)<2 or len(ia)<2: continue
            ac,bc=fit(ic,yg,pg); ao,bo=fit(ia,yg,pg)
            errs_c.append(np.abs(ac*pg[te]+bc-yg[te]).mean())
            errs_o.append(np.abs(ao*pg[te]+bo-yg[te]).mean())
            errs_0.append(np.abs(pg[te]-yg[te]).mean())
            nd.append(len(don_c)); nr.append(te.sum())
    print("  %.2f           | %.2f                | %.3f        | %.3f                  | %.3f   | %.0f"
          %(frac,np.mean(nd),np.mean(errs_c),np.mean(errs_o),np.mean(errs_0),np.mean(nr)))
print("\n(per-cell means; unit = (condition,target cell) pair, clustered in 11 conditions)")

print("\n=== how biased are the available donors? mean donor lifetime vs target lifetime ===")
for frac in [0.70,0.80,0.90]:
    gap=[]; ratio=[]
    for gid in np.unique(g):
        m=g==gid; cells=np.unique(c[m]); rg=r[m]; cg=c[m]
        death={cc: rg[cg==cc].max() for cc in cells}; T=frac*max(death.values())
        for tc in cells:
            if death[tc]<=T: continue
            don=[cc for cc in cells if cc!=tc and death[cc]<=T]
            if not don: continue
            gap.append(np.mean([death[d] for d in don])-death[tc]); ratio.append(len(don))
    print(" T=%.2f: mean(donor_life - target_life) = %+.1f RPT ; donors/case %.2f ; cases %d"%(frac,np.mean(gap),np.mean(ratio),len(gap)))
