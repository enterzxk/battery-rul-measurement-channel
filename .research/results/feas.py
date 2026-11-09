import numpy as np, collections
z = np.load("isu_table.npz", allow_pickle=True)
X = z["X"]; cells = z["cells"]
grp = X[:,0].astype(int); rpt = X[:,1]; soh = X[:,6]

# cell -> condition (should be unique)
cc = {}
bad = 0
for c, g in zip(cells, grp):
    if c in cc and cc[c] != g: bad += 1
    cc[c] = g
print("cells with inconsistent condition assignment:", bad)

# EOL per cell
eol = {}
for c in np.unique(cells):
    m = cells == c
    rr, ss = rpt[m], soh[m]
    o = np.argsort(rr); rr, ss = rr[o], ss[o]
    hit = np.where(ss <= 0.80)[0]
    if len(hit): eol[c] = int(rr[hit[0]])
print("cells reaching 80%% SOH: %d / %d" % (len(eol), len(np.unique(cells))))

# usable rows per cell (rpt <= eol)
usable = collections.Counter()
for c, r in zip(cells, rpt):
    if c in eol and r <= eol[c]: usable[c] += 1

per_cond = collections.defaultdict(list)
for c, g in cc.items():
    per_cond[g].append(c)

ncell = np.array([len(v) for v in per_cond.values()])
print("\nconditions: %d | cells/condition: min %d max %d median %d mean %.2f" % (
    len(per_cond), ncell.min(), ncell.max(), int(np.median(ncell)), ncell.mean()))
print("distribution of cells/condition:", dict(sorted(collections.Counter(ncell).items())))

for thresh in (2, 3, 4, 5, 6):
    ok = sum(1 for g, v in per_cond.items() if sum(1 for c in v if usable[c] >= thresh) >= thresh)
    print("  conditions with >=%d cells having >=%d usable rows: %d" % (thresh, thresh, ok))

print("\nusable rows/cell: min %d max %d median %d" % (min(usable.values()), max(usable.values()), int(np.median(list(usable.values())))))
print("cells with >=8 usable rows: %d" % sum(1 for v in usable.values() if v >= 8))
print("total usable rows: %d" % sum(usable.values()))
