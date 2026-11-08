
import numpy as np
from scipy import stats
z=np.load(r"E:\桌面\rul\rul_v4_20261107\review-stage\_diag.npz")
KS=[2,3,4,6,8,16]
D={k:z["D%d"%k] for k in KS}; SP={k:z["S%d"%k] for k in KS}; base=z["base"]
print("=== J. 'k=6 spread  ==  k=16 random' : non-inferiority check ===")
a=SP[6]; b=D[16].mean(0)
print("  spread@6 mean %.3f | random@16 mean %.3f | delta %+.3f"%(a.mean(),b.mean(),(a-b).mean()))
print("  wilcoxon p=%.4f ; paired t p=%.4f ; %d/11 conditions spread@6 better"%(
    stats.wilcoxon(a,b).pvalue, stats.ttest_rel(a,b).pvalue, int(((a-b)<0).sum())))
print("  spread@8 vs random@16: %.3f vs %.3f delta %+.3f p=%.4f"%(SP[8].mean(),b.mean(),(SP[8]-b).mean(),stats.wilcoxon(SP[8],b).pvalue))
print("\n=== K. where does EXP-002's 200.477 sit? ===")
cm=D[2].mean(1)
print("  percentile of 200.477 in random@k=2 : %.1f%%"%((cm<200.477).mean()*100))
print("  median %.2f  mean %.2f  p95 %.2f  p99 %.2f  max %.1f"%(np.median(cm),cm.mean(),np.percentile(cm,95),np.percentile(cm,99),cm.max()))
print("  fraction of draws > 2x k0 : %.3f ; > 10x k0 : %.3f"%((cm>2*base.mean()).mean(),(cm>10*base.mean()).mean()))
print("\n=== L. EXP-002 random column vs the true distribution (percentile of each reported value) ===")
rep={2:200.477,3:6.214,4:5.903,6:5.208,8:4.688,16:4.528}
for k in KS:
    c=D[k].mean(1)
    print("  k=%2d reported %8.3f  -> percentile %5.1f%%   (median %.3f)"%(k,rep[k],(c<rep[k]).mean()*100,np.median(c)))
