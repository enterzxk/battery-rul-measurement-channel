import numpy as np
z = np.load("isu_table.npz", allow_pickle=True)
print("KEYS:", list(z.keys()))
X = z["X"]; cells = z["cells"]
print("X shape:", X.shape, " cells shape:", cells.shape, " cells dtype:", cells.dtype)
print("X first 3 rows:\n", X[:3])
grp = X[:,0].astype(int)
print("\nconditions:", len(np.unique(grp)), " cells:", len(np.unique(cells)))
import collections
cnt = collections.Counter(grp)
print("cells per condition: min %d max %d mean %.2f" % (min(cnt.values()), max(cnt.values()), np.mean(list(cnt.values()))))
print("condition ids sample:", sorted(cnt)[:10], "...", sorted(cnt)[-5:])
# rows per cell
rc = collections.Counter(cells)
print("\nrows(cells) per cell: min %d max %d mean %.1f" % (min(rc.values()), max(rc.values()), np.mean(list(rc.values()))))
# is there any descriptor column?
print("\ncolumn stats (mean/std per column):")
for j in range(X.shape[1]):
    print("  col %d: mean %+.4f std %.4f min %+.4f max %+.4f" % (j, X[:,j].mean(), X[:,j].std(), X[:,j].min(), X[:,j].max()))
