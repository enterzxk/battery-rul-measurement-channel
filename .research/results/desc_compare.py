import numpy as np, csv, collections
z = np.load("isu_table.npz", allow_pickle=True)
X = z["X"]; cells = z["cells"]
grp = X[:,0].astype(int); rpt = X[:,1]; feat = X[:,2:6]; soh = X[:,6]

# true 3-factor descriptors
cond = {}
for r in csv.DictReader(open("isu_conditions.csv", encoding="utf-8")):
    cond[int(r["group"])] = (float(r["charge_C"]), float(r["discharge_C"]), float(r["mean_DoD_pct"]))

# eligibility identical to C3
per_cell = collections.defaultdict(list)
for g,r,f,s,c in zip(grp,rpt,feat,soh,cells): per_cell[c].append((float(r),np.asarray(f,float),float(s)))
eol={}
for c in np.unique(cells):
    rr=np.array([t[0] for t in per_cell[c]]); ss=np.array([t[2] for t in per_cell[c]])
    o=np.argsort(rr); rr,ss=rr[o],ss[o]
    h=np.where(ss<=0.80)[0]
    if len(h): eol[c]=int(rr[h[0]])
usable={c:[(r,f) for r,f,s in sorted(per_cell[c],key=lambda t:t[0]) if c in eol and r<=eol[c]] for c in per_cell}
cond_cells=collections.defaultdict(list)
for c,g in zip(cells,grp): cond_cells[int(g)].append(c)
for g in cond_cells: cond_cells[g]=sorted(cond_cells[g])
ELIG=[g for g in sorted(cond_cells) if g in cond and sum(1 for c in cond_cells[g] if len(usable[c])>=4)>=4]
print("eligible conditions with true descriptors:", len(ELIG))

def maximin(Z, start):
    n=len(Z); order=[start]; dmin=np.linalg.norm(Z-Z[start],axis=1)
    for _ in range(n-1):
        dmin[order]=-1.0; nxt=int(np.argmax(dmin)); order.append(nxt)
        dmin=np.minimum(dmin,np.linalg.norm(Z-Z[nxt],axis=1))
    return order

# TRUE 3-factor space
T = np.array([[cond[g][0], cond[g][1], cond[g][2]] for g in ELIG], float)
Tz = (T - T.mean(0)) / (T.std(0) + 1e-12)
u,sv,vt = np.linalg.svd(Tz - Tz.mean(0), full_matrices=False)
ev = sv**2/(sv**2).sum()
print("TRUE 3-factor PCA EVR:", np.round(ev,3), " participation ratio: %.2f" % (1.0/np.sum(ev**2)))
print("  pairwise dist: min %.2f median %.2f max %.2f" % tuple(np.percentile(
    [np.linalg.norm(Tz[i]-Tz[j]) for i in range(len(Tz)) for j in range(i+1,len(Tz))],[0,50,100])))

# C3's proxy (scout prefix) space, recomputed
def scout_desc(g):
    scout=cond_cells[g][0]; rr,ff,seen=[],[],set()
    for r,f,s in sorted(per_cell[scout],key=lambda t:t[0]):
        if int(r) in seen: continue
        seen.add(int(r)); rr.append(r); ff.append(np.asarray(f,float))
        if len(rr)==3: break
    if len(rr)<3 or not np.isfinite(ff[0][0]) or ff[0][0]<=0: return None
    h=[ff[j][0]/ff[0][0] for j in range(3)]
    if not np.all(np.isfinite(h)): return None
    return np.concatenate([[(h[0]-h[2])/(rr[2]-rr[0])], np.mean(np.array(ff),axis=0)])
P = np.array([scout_desc(g) for g in ELIG], float)
Pz = (P - P.mean(0))/(P.std(0)+1e-12)
u2,sv2,_ = np.linalg.svd(Pz - Pz.mean(0), full_matrices=False)
ev2 = sv2**2/(sv2**2).sum()
print("\nC3 PROXY PCA EVR:", np.round(ev2[:5],3), " participation ratio: %.2f" % (1.0/np.sum(ev2**2)))

# how different are the maximin orderings?
def jac(a,b): return len(a&b)/len(a|b)
J=[]
for d in range(20):
    rng=np.random.default_rng(20261109+d)
    oT=maximin(Tz,int(rng.integers(len(Tz)))); sT=set([ELIG[i] for i in oT[:24]])
    oP=maximin(Pz,int(rng.integers(len(Pz)))); sP=set([ELIG[i] for i in oP[:24]])
    J.append(jac(sT,sP))
print("\nmaximin first-24 sets: true-3factor vs C3-proxy  Jaccard mean %.3f  min %.3f  max %.3f" % (np.mean(J),min(J),max(J)))
