import numpy as np, time, collections, os
from sklearn.ensemble import HistGradientBoostingRegressor
z = np.load("isu_table.npz", allow_pickle=True)
X = z["X"]; cells = z["cells"]
grp = X[:,0].astype(int); rpt = X[:,1]; feat = X[:,2:6]; soh = X[:,6]
per_cell = collections.defaultdict(list)
for g,r,f,s,c in zip(grp,rpt,feat,soh,cells): per_cell[c].append((float(r),np.asarray(f,float),float(s)))
eol={}
for c in np.unique(cells):
    rr=np.array([t[0] for t in per_cell[c]]); ss=np.array([t[2] for t in per_cell[c]])
    o=np.argsort(rr); rr,ss=rr[o],ss[o]
    h=np.where(ss<=0.80)[0]
    if len(h): eol[c]=int(rr[h[0]])
usable={c:[(r,f) for r,f,s in sorted(per_cell[c],key=lambda t:t[0]) if c in eol and r<=eol[c]] for c in per_cell}
cs=sorted(per_cell)
tc=[c for c in cs if usable[c]][:24]
tr_f=[];tr_y=[]
for c in tc:
    for r,f in usable[c]: tr_f.append(f); tr_y.append(eol[c]-r)
tr_f=np.array(tr_f); tr_y=np.array(tr_y,float)
print("train rows:", len(tr_y), "features:", tr_f.shape[1])
t0=time.time()
for _ in range(5):
    m=HistGradientBoostingRegressor(max_iter=300,learning_rate=0.08,random_state=0)
    m.fit(tr_f,tr_y); m.predict(tr_f[:50])
dt=(time.time()-t0)/5
print("per-fit seconds: %.3f" % dt)
print("projected total for 5040 fits: %.1f min" % (5040*dt/60))
print("projected total for 1449 fits: %.1f min" % (1449*dt/60))
