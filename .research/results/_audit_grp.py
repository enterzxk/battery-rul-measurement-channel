import numpy as np, csv
z = np.load("isu_table.npz", allow_pickle=True)
print("keys:", list(z.keys()))
X = z["X"]; cells = z["cells"]
print("X shape:", X.shape, "cells:", cells.shape, "dtype:", X.dtype)
grp = X[:, 0].astype(int)
ug = sorted(set(grp.tolist()))
print("n groups in data:", len(ug))
print("groups:", ug)
csvg = []
for r in csv.DictReader(open("isu_conditions.csv", encoding="utf-8")):
    csvg.append(int(r["group"]))
print("n csv groups:", len(csvg))
print("csv sorted:", sorted(csvg))
s1, s2 = set(ug), set(csvg)
print("in data not csv:", sorted(s1 - s2))
print("in csv not data:", sorted(s2 - s1))
print("exact match:", s1 == s2)
print("n unique cells:", len(set(cells.tolist())))
# per-group cell counts
import collections
cc = collections.Counter(grp.tolist())
print("group cell-count distribution:", collections.Counter(cc.values()))
print("groups with <4 cells:", sorted([g for g, v in cc.items() if v < 4]))
