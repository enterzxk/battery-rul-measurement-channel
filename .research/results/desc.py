import numpy as np, collections
z = np.load("isu_table.npz", allow_pickle=True)
X = z["X"]; cells = z["cells"]
grp = X[:,0].astype(int); rpt = X[:,1]; feat = X[:,2:6]; soh = X[:,6]

# observable-at-decision-time descriptors: use only the FIRST 3 RPTs of each condition
# (no outcome information; a practitioner observes the condition's early behaviour before investing)
rows = collections.defaultdict(list)
for g, r, f, s in zip(grp, rpt, feat, soh):
    rows[g].append((r, f, s))

desc, ok = [], []
for g in sorted(rows):
    rr = sorted(rows[g], key=lambda t: t[0])
    early = rr[:3]
    if len(early) < 2: continue
    s0 = early[0][2]; s1 = early[-1][2]
    r0 = early[0][0]; r1 = early[-1][0]
    rate = (s0 - s1) / max(1, (r1 - r0))          # early SOH fade per RPT
    fm = np.mean([e[1] for e in early], axis=0)   # mean early capacity channels
    d = np.concatenate([[rate, s0], fm])
    if not np.isfinite(d).all(): continue
    desc.append(d); ok.append(g)

D = np.array(desc); ok = np.array(ok)
print("conditions with usable early descriptors: %d / %d" % (len(ok), len(rows)))
print("descriptor dim:", D.shape[1])
Z = (D - D.mean(0)) / (D.std(0) + 1e-12)
print("\nper-dimension spread across conditions (std of standardised):")
print("  ", np.round(Z.std(0), 3))
# effective dimensionality
u, sv, vt = np.linalg.svd(Z - Z.mean(0), full_matrices=False)
ev = sv**2 / (sv**2).sum()
print("\nPCA explained variance ratio:", np.round(ev[:6], 3))
print("participation ratio (effective dims): %.2f" % (1.0/np.sum(ev**2)))
# pairwise distance spread -> is a maximin ordering meaningful?
from itertools import combinations
pd = [np.linalg.norm(Z[i]-Z[j]) for i,j in combinations(range(len(Z)),2)]
pd = np.array(pd)
print("\npairwise descriptor distance: min %.2f median %.2f max %.2f  (cv %.2f)" % (
    pd.min(), np.median(pd), pd.max(), pd.std()/pd.mean()))
np.save("cond_descriptors.npy", np.column_stack([ok, D]))
print("\nsaved cond_descriptors.npy  shape", np.column_stack([ok,D]).shape)
