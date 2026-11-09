import numpy as np
z = np.load("isu_table.npz", allow_pickle=True)
X = z["X"]; cells = z["cells"]
grp = X[:,0].astype(int); rpt = X[:,1]; soh = X[:,6]
eol = {}
for c in np.unique(cells):
    m = cells == c
    rr, ss = rpt[m], soh[m]
    o = np.argsort(rr); rr, ss = rr[o], ss[o]
    hit = np.where(ss <= 0.80)[0]
    if len(hit): eol[c] = int(rr[hit[0]])
ok = np.array([c in eol and r <= eol[c] for c, r in zip(cells, rpt)])
cells, grp, rpt = cells[ok], grp[ok], rpt[ok]
K = 8
n1 = n2 = 0; diffs = []
for g in np.unique(grp):
    idx = np.where(grp == g)[0]
    c_g = cells[idx]; gc = np.unique(c_g)
    pool = [c for c in gc if (c_g == c).sum() >= K]
    e1, e2 = set(), set()
    for c in gc:
        d = [x for x in pool if x != c]
        if len(d) >= 1: e1.add(c)
        if len(d) >= 2: e2.add(c)
    n1 += len(e1); n2 += len(e2)
    if e1 != e2: diffs.append((int(g), sorted(e1-e2), sorted(e2-e1)))
print("rows=%d conditions=%d" % (len(cells), len(np.unique(grp))))
print("ISU evaluated cells  m=1: %d   m=2: %d   m1-m2: %d" % (n1, n2, n1-n2))
print("conditions with differing evaluated-cell sets: %d" % len(diffs))
for d in diffs[:12]:
    print("   cond %-4s only-m1: %-28s only-m2: %s" % (d[0], d[1], d[2]))
