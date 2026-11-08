# -*- coding: utf-8 -*-
"""M1 — floor (E1.1), donor axis (E1.2), complementarity (E1.3).
CD-004 corrections applied: mean primary + median sensitivity; condition-level
clustering for all CIs (no pseudo-replication); interaction sign per CD-005.
"""
import numpy as np, json, warnings
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
warnings.filterwarnings("ignore")
src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "v2_main.py"), encoding="utf-8").read().split("def main():")[0]
exec(src)
OUT = r"C:\Users\Administrator\AppData\Local\Temp\m1.json"
D = 200
d = build()
A, cells, grp = d["A"], d["cells"], d["grp"]
y = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, d["rpts"])], float)
pred = np.full(len(y), np.nan)
for g in np.unique(grp):
    te = grp == g; tr = ~te
    mm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    mm.fit(A[tr], y[tr]); pred[te] = mm.predict(A[te])
print("preds ready", flush=True)

def affine(ps, ys, p):
    if ps.size < 2 or np.std(ps) < 1e-12: return p + (ys.mean() - ps.mean())
    a = np.cov(ps, ys, bias=True)[0, 1] / np.var(ps)
    return a * p + (ys.mean() - a * ps.mean())

def mae(pr, yv): return float(np.abs(yv - pr).mean())
GROUPS = list(np.unique(grp))

# ---------- E1.1 floor: one fixed donor, scan k ----------
KS = [4, 8, 16, 32, 48, 64]
def e1_1(agg, seed):
    rng = np.random.default_rng(seed); out = {}
    for g in GROUPS:
        mm = grp == g
        p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
        gc = np.unique(c_g)
        per_k = {k: [] for k in KS}
        for c in gc:
            ev = c_g == c
            donors = [x for x in gc if x != c and (c_g == x).sum() >= 64]
            if not donors: continue
            dd = rng.choice(donors)
            pool = np.where(c_g == dd)[0]
            for k in KS:
                if len(pool) < k: continue
                vals = [mae(affine(p_g[s], y_g[s], p_g[ev]), y_g[ev])
                        for s in (rng.choice(pool, k, replace=False) for _ in range(D))]
                per_k[k].append(float(np.mean(vals) if agg == "mean" else np.median(vals)))
        out[g] = {k: (float(np.mean(v)) if v else np.nan) for k, v in per_k.items()}
    return out

# ---------- E1.2 donor axis: full trajectory, nested ----------
MS = [1, 2, 3, 4, 5]
def e1_2(agg, seed):
    rng = np.random.default_rng(seed); out = {}
    for g in GROUPS:
        mm = grp == g
        p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
        gc = np.unique(c_g)
        per_m = {m: [] for m in MS}
        for c in gc:
            ev = c_g == c
            donors = [x for x in gc if x != c]
            order = list(rng.permutation(donors))   # nested: m uses first m of order
            for m in MS:
                if m > len(donors): continue
                ds = order[:m]
                sel = np.concatenate([np.where(c_g == dd)[0] for dd in ds])
                if len(sel) < 2: continue
                per_m[m].append(mae(affine(p_g[sel], y_g[sel], p_g[ev]), y_g[ev]))
        out[g] = {m: (float(np.mean(v) if agg == "mean" else np.median(v)) if v else np.nan)
                  for m, v in per_m.items()}
    return out

def cond_vec(per_cond, key):
    return np.array([per_cond[g][key] for g in GROUPS], float)

def report(name, per_cond, k1, k2, agg):
    a = cond_vec(per_cond, k1); b = cond_vec(per_cond, k2)
    ok = np.isfinite(a) & np.isfinite(b)
    dlt = (a - b)[ok]
    rng = np.random.default_rng(0)
    bs = np.array([np.mean(rng.choice(dlt, len(dlt), replace=True)) for _ in range(5000)])
    t, p = stats.ttest_rel(a[ok], b[ok])
    print("  %-14s %s->%s  delta %+.3f  CI [%+.3f, %+.3f]  t=%.2f p=%.3f  better %d/%d" % (
        name, k1, k2, dlt.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5),
        t, p, int((dlt > 0).sum()), ok.sum()), flush=True)
    return dict(delta=float(dlt.mean()),
                ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                p=float(p), better=int((dlt > 0).sum()), n=int(ok.sum()))

res = {}
print("\n=== E1.1 floor: one fixed donor, scan k (aggregation x seed) ===", flush=True)
for agg in ("mean", "median"):
    for s in (0, 1):
        pc = e1_1(agg, s)
        report("floor/" + agg + "/s" + str(s), pc, 16, 64, agg)

print("\n=== E1.2 donor axis (nested, full trajectory) ===", flush=True)
e12 = {}
for agg in ("mean", "median"):
    pc = e1_2(agg, 0)
    res["E1.2_" + agg] = {
        "m" + str(m): float(np.nanmean(cond_vec(pc, m))) for m in MS}
    for m in MS:
        print("    %s m=%d  %.3f" % (agg, m, res["E1.2_" + agg]["m" + str(m)]), flush=True)
    report("E1.2/" + agg, pc, 1, 2, agg)
    report("E1.2/" + agg, pc, 2, 3, agg)
    report("E1.2/" + agg, pc, 3, 4, agg)
    e12[agg] = pc

print("\n=== E1.3 complementarity (interaction sign per CD-005) ===", flush=True)
KX = [4, 16, 64]; MX = [1, 5]
def e1_3(agg, seed):
    rng = np.random.default_rng(seed); out = {}
    for g in GROUPS:
        mm = grp == g
        p_g, y_g, c_g = pred[mm], y[mm], cells[mm]
        gc = np.unique(c_g)
        cell = {}
        for k in KX:
            for m in MX:
                vals = []
                for c in gc:
                    ev = c_g == c
                    donors = [x for x in gc if x != c]
                    if m > len(donors): continue
                    acc = []
                    for _ in range(D):
                        ds = rng.choice(donors, m, replace=False)
                        sel = np.concatenate([np.where(c_g == dd)[0] for dd in ds])
                        if len(sel) < k: continue
                        sub = rng.choice(sel, k, replace=False)
                        acc.append(mae(affine(p_g[sub], y_g[sub], p_g[ev]), y_g[ev]))
                    if acc: vals.append(float(np.mean(acc) if agg == "mean" else np.median(acc)))
                cell[(k, m)] = float(np.mean(vals)) if vals else np.nan
        out[g] = cell
    return out

pc = e1_3("mean", 0)
d4 = np.array([pc[g][(4,1)] - pc[g][(4,5)] for g in GROUPS])
d64 = np.array([pc[g][(64,1)] - pc[g][(64,5)] for g in GROUPS])
inter = d4 - d64
ok = np.isfinite(inter)
rng = np.random.default_rng(0)
bs = np.array([np.mean(rng.choice(inter[ok], ok.sum(), replace=True)) for _ in range(5000)])
print("  d(k=4) mean %+.3f   d(k=64) mean %+.3f" % (np.nanmean(d4), np.nanmean(d64)))
print("  interaction = d(k=4) - d(k=64) = %+.3f  CI [%+.3f, %+.3f]" % (
    inter[ok].mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)))
print("  CD-005 expected sign: NEGATIVE if donor benefit grows with k")
res["E1.3"] = dict(d4=float(np.nanmean(d4)), d64=float(np.nanmean(d64)),
                   interaction=float(inter[ok].mean()),
                   ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)
print("\nsaved", OUT)
