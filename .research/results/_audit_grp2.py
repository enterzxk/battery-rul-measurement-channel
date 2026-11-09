import numpy as np, collections
z = np.load("isu_table.npz", allow_pickle=True)
X = z["X"]; cells = z["cells"]
grp = X[:, 0].astype(int); rpt = X[:, 1]; soh = X[:, 6]
# distinct cells per group
cell_cond = {}
for c, g in zip(cells.tolist(), grp.tolist()):
    cell_cond.setdefault(c, set()).add(g)
multi = {c: v for c, v in cell_cond.items() if len(v) > 1}
print("cells appearing in >1 group:", len(multi))
print("n unique cells:", len(cell_cond))
cg = collections.Counter([sorted(v)[0] for v in cell_cond.values()])
print("distinct cells per group distribution:", dict(sorted(collections.Counter(cg.values()).items())))
print("groups with <4 distinct cells:", sorted([g for g, v in cg.items() if v < 4]))
print("groups with 4 cells:", sum(1 for v in cg.values() if v == 4))
# EOL reach
per_cell = collections.defaultdict(list)
for g, r, s, c in zip(grp.tolist(), rpt.tolist(), soh.tolist(), cells.tolist()):
    per_cell[c].append((float(r), float(s)))
eol = {}
for c, rows in per_cell.items():
    rr = np.array([t[0] for t in rows]); ss = np.array([t[1] for t in rows])
    o = np.argsort(rr); rr, ss = rr[o], ss[o]
    hit = np.where(ss <= 0.80)[0]
    if len(hit):
        eol[c] = int(rr[hit[0]])
print("cells reaching 80%% SOH:", len(eol), "of", len(per_cell))
# usable rows per cell
usable_rows = {}
for c, rows in per_cell.items():
    if c not in eol: continue
    usable_rows[c] = sum(1 for r, s in rows if r <= eol[c])
ur = np.array(list(usable_rows.values()))
print("usable rows per cell: median %d max %d ; >=8 rows: %d" % (np.median(ur), ur.max(), (ur >= 8).sum()))
print("rpt max overall:", rpt.max(), " min:", rpt.min())
