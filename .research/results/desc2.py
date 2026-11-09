import numpy as np, collections
z = np.load("isu_table.npz", allow_pickle=True)
X = z["X"]; cells = z["cells"]
grp = X[:,0].astype(int); rpt = X[:,1]; feat = X[:,2:6]; soh = X[:,6]

# per-cell rows, chronologically ordered
per_cell = collections.defaultdict(list)
for g, r, f, c in zip(grp, rpt, feat, cells):
    per_cell[c].append((r, f))
cell_cond = {c: g for c, g in zip(cells, grp)}

# eol for the retrospective pool restriction (outcome-dependent -> pool level only)
eol = {}
for c in np.unique(cells):
    m = cells == c
    rr, ss = rpt[m], soh[m]
    o = np.argsort(rr); rr, ss = rr[o], ss[o]
    hit = np.where(ss <= 0.80)[0]
    if len(hit): eol[c] = int(rr[hit[0]])

cond_cells = collections.defaultdict(list)
for c, g in cell_cond.items(): cond_cells[g].append(c)

desc, kept, skipped = [], [], []
for g in sorted(cond_cells):
    cs = sorted(cond_cells[g])                    # frozen, outcome-independent ordering
    scout = cs[0]
    rows = sorted(per_cell[scout], key=lambda t: t[0])
    # first three DISTINCT chronologically ordered rows, no eol dependence
    rr, ff = [], []
    seen = set()
    for r, f in rows:
        if int(r) in seen: continue
        seen.add(int(r)); rr.append(float(r)); ff.append(np.asarray(f, float))
        if len(rr) == 3: break
    if len(rr) < 3 or not np.isfinite(ff[0][0]) or ff[0][0] <= 0:
        skipped.append(g); continue
    h = [np.asarray(ff[j], float)[0] / ff[0][0] for j in range(3)]
    if not all(np.isfinite(h)): skipped.append(g); continue
    fade = (h[0] - h[2]) / (rr[2] - rr[0])
    means = np.mean(np.array(ff), axis=0)          # 4 channel means over those 3 RPTs
    d = np.concatenate([[fade], means])
    if not np.isfinite(d).all(): skipped.append(g); continue
    desc.append(d); kept.append(g)

D = np.array(desc); kept = np.array(kept)
print("conditions with valid scout descriptors: %d / %d   skipped: %s" % (len(kept), len(cond_cells), skipped))
print("descriptor dim:", D.shape[1], " (fade + 4 channel means)")
Z = (D - D.mean(0)) / (D.std(0) + 1e-12)
print("per-dim std after standardisation:", np.round(Z.std(0), 3))
u, sv, vt = np.linalg.svd(Z - Z.mean(0), full_matrices=False)
ev = sv**2/(sv**2).sum()
print("PCA EVR:", np.round(ev, 3))
print("participation ratio: %.2f" % (1.0/np.sum(ev**2)))
from itertools import combinations
pd = np.array([np.linalg.norm(Z[i]-Z[j]) for i, j in combinations(range(len(Z)), 2)])
print("pairwise distance: min %.3f median %.3f max %.3f cv %.2f" % (pd.min(), np.median(pd), pd.max(), pd.std()/pd.mean()))
# feasibility of the four arms on the kept pool
cnt = {g: len(cond_cells[g]) for g in kept}
for need in (1, 2, 4):
    print("  conditions with >=%d cells: %d" % (need, sum(1 for v in cnt.values() if v >= need)))
np.save("scout_descriptors.npy", np.column_stack([kept, D]))
print("saved scout_descriptors.npy", np.column_stack([kept, D]).shape)
