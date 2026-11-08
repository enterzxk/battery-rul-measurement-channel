# -*- coding: utf-8 -*-
"""ISU: 2x2 joint specification space (fit scope x evaluation population)."""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")

z = np.load(r"C:\Users\Administrator\AppData\Local\Temp\isu_table.npz", allow_pickle=True)
X = z["X"]; cells = z["cells"]
grp = X[:, 0].astype(int); rpt = X[:, 1]; feat = X[:, 2:6]; soh = X[:, 6]
eol = {}
for c in np.unique(cells):
    m = cells == c
    rr, ss = rpt[m], soh[m]
    o = np.argsort(rr); rr, ss = rr[o], ss[o]
    hit = np.where(ss <= 0.80)[0]
    if len(hit): eol[c] = int(rr[hit[0]])
ok = np.array([c in eol and r <= eol[c] for c, r in zip(cells, rpt)])
cells, grp, rpt, feat = cells[ok], grp[ok], rpt[ok], feat[ok]
y = np.array([eol[c] - r for c, r in zip(cells, rpt)], float)
pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    if tr.sum() < 50 or te.sum() == 0: continue
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(feat[tr], y[tr]); pred[te] = mm.predict(feat[te])
print("rows %d groups %d" % (len(y), len(np.unique(grp))), flush=True)

NDRAW = 80; K = 8
def aff(ps, ys, p):
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

rng = np.random.default_rng(0); ug = np.unique(grp)

def contrast(scope, pop):
    out = {1: {}, 2: {}}
    for g in ug:
        mm = grp == g
        idx = np.where(mm)[0]
        c_g, p_g, y_g = cells[idx], pred[idx], y[idx]
        if not np.isfinite(p_g).all(): continue
        gc = np.unique(c_g)
        pool = [c for c in gc if (c_g == c).sum() >= K]
        q25 = np.quantile(y_g, 0.25)
        for m in (1, 2):
            cv = []
            for c in gc:
                ev = np.where(c_g == c)[0]
                if pop == "late":
                    ev = ev[y_g[ev] <= q25]
                    if ev.size == 0: continue
                donors = [x for x in pool if x != c]
                if len(donors) < m: continue
                if scope == "condition":
                    ds = rng.choice(donors, m, replace=False)
                    sel = np.concatenate([np.where(c_g == dd)[0] for dd in ds])
                    pr = [float(np.abs(y_g[j] - aff(p_g[sel], y_g[sel], np.array([p_g[j]]))[0])) for j in ev]
                    cv.append(float(np.mean(pr))); continue
                per_j = {j: [] for j in ev}
                for _ in range(NDRAW):
                    ds = rng.choice(donors, m, replace=False)
                    base = K // m; rem = K % m
                    takes = [base + (1 if i < rem else 0) for i in range(m)]
                    sel, okk = [], True
                    for dd, tk in zip(ds, takes):
                        q = np.where(c_g == dd)[0]
                        if len(q) < tk: okk = False; break
                        sel.extend(rng.choice(q, tk, replace=False))
                    if not okk: continue
                    sel = np.array(sel)
                    for j in ev:
                        per_j[j].append(float(np.abs(y_g[j] - aff(p_g[sel], y_g[sel], np.array([p_g[j]]))[0])))
                jm = [float(np.mean(v)) for v in per_j.values() if v]
                if jm: cv.append(float(np.mean(jm)))
            out[m][g] = float(np.mean(cv)) if cv else np.nan
    gs = [g for g in ug if np.isfinite(out[1].get(g, np.nan)) and np.isfinite(out[2].get(g, np.nan))]
    a = np.array([out[1][g] for g in gs]); b = np.array([out[2][g] for g in gs])
    t, p = stats.ttest_rel(a, b)
    return dict(n=len(gs), delta=float((a - b).mean()), p=float(p), better=int(((a - b) > 0).sum()))

print("\n=== ISU 2x2 joint specification space ===", flush=True)
g2 = {}
for scope in ("cell", "condition"):
    for pop in ("all", "late"):
        r = contrast(scope, pop); g2[(scope, pop)] = r
        print("%-20s contrast %+8.3f  p=%.4f  better %2d/%-2d" % (
            "%s / %s" % (scope, pop), r["delta"], r["p"], r["better"], r["n"]), flush=True)

ca, cl = g2[("cell","all")]["delta"], g2[("cell","late")]["delta"]
na, nl = g2[("condition","all")]["delta"], g2[("condition","late")]["delta"]
print("\nmain effect scope:      %+.3f" % (((na+nl)-(ca+cl))/2))
print("main effect population: %+.3f" % (((cl+nl)-(ca+na))/2))
print("interaction:            %+.3f" % ((ca-cl)-(na-nl)))
print("range across 4 cells:    %.3f" % (max(ca,cl,na,nl)-min(ca,cl,na,nl)))
json.dump({"%s/%s" % k: v for k,v in g2.items()}, open(r"C:\Users\Administrator\AppData\Local\Temp\isu_joint.json","w"), indent=1)
