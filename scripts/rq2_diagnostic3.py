# -*- coding: utf-8 -*-
"""RQ2 diagnostic v3: fix prefix features by stitching CC windows into full curves."""
import pickle, numpy as np, json
from scipy.stats import spearmanr

PULSE = r"E:\桌面\rul\data\external\uconn\data_slowpulse_1.pkl"
CC    = r"E:\桌面\rul\data\external\uconn\data_cc_1.pkl"
OUT   = r"C:\Users\Administrator\AppData\Local\Temp\rq2_diag3.json"

def load(p):
    with open(p, "rb") as f:
        return pickle.load(f, encoding="latin1")

def trace_features(v, kind):
    v = np.asarray(v, float); v0 = v[0]
    ip = int(np.argmax(v)) if kind == "chg" else int(np.argmin(v))
    peak = v[ip]; dv = abs(peak - v0)
    tau = np.nan
    if dv > 1e-6:
        target = peak - 0.632 * (peak - v0)
        after = v[ip:]
        idx = np.where(after <= target)[0] if kind == "chg" else np.where(after >= target)[0]
        if len(idx): tau = float(idx[0])
    resid = (v[-1] - peak) / (v0 - peak) if abs(v0 - peak) > 1e-9 else np.nan
    return dv, tau, resid

def eta2(X, g):
    g = np.asarray(g); out = []
    tot = X.var(axis=0) * len(X)
    for j in range(X.shape[1]):
        ssb = 0.0
        for u in np.unique(g):
            m = g == u
            ssb += m.sum() * (X[m, j].mean() - X[:, j].mean()) ** 2
        out.append(ssb / tot[j] if tot[j] > 1e-12 else np.nan)
    return np.array(out)

def main():
    dp = load(PULSE)
    cell, rpt, soc, pt, V = dp["cell_id"], dp["rpt"], dp["soc"], dp["pulse_type"], dp["voltage"]
    gmap = {}
    for c, g in zip(dp["cell_id"], dp["group_id"]):
        gmap[int(c)] = int(g)

    recs = {}
    for i in range(len(cell)):
        recs.setdefault((int(cell[i]), int(rpt[i])), {})[(int(soc[i]), str(pt[i]))] = trace_features(V[i], str(pt[i]))

    pulse_rows, pcells, prpts = [], [], []
    for (c, r), d in sorted(recs.items()):
        if len(d) < 6: continue
        f = []
        for s in (20, 50, 90):
            for k in ("chg", "dchg"):
                f += list(d[(s, k)])
        f += [np.nanstd([d[(s, "chg")][0] for s in (20, 50, 90)]),
              np.nanstd([d[(s, "dchg")][0] for s in (20, 50, 90)])]
        pulse_rows.append(f); pcells.append(c); prpts.append(r)
    Xp, cp, rp = np.array(pulse_rows), np.array(pcells), np.array(prpts)

    mono = {}
    for j in range(Xp.shape[1]):
        rhos = []
        for c in np.unique(cp):
            m = cp == c
            if m.sum() < 10: continue
            col = Xp[m, j]
            if np.nanstd(col) < 1e-12: continue
            rho, _ = spearmanr(rp[m], col)
            if not np.isnan(rho): rhos.append(abs(rho))
        mono[f"f{j}"] = round(float(np.median(rhos)), 3) if rhos else None

    # ---- stitch CC windows into one curve per (cell, rpt) ----
    dc = load(CC)
    cc_cell, cc_rpt, ccV = dc["cell_id"], dc["rpt"], dc["voltage"]
    ccq, ccs = dc["q_dchg"], dc["soh"]
    buckets = {}
    for i in range(len(cc_cell)):
        buckets.setdefault((int(cc_cell[i]), int(cc_rpt[i])), []).append(i)
    rows, cells, rpts = [], [], []
    for (c, r), idxs in sorted(buckets.items()):
        idxs = sorted(idxs, key=lambda i: float(np.mean(ccV[i])))
        curve = np.concatenate([np.asarray(ccV[i], float) for i in idxs])
        bins = np.array_split(curve, 50)
        f = [b.mean() for b in bins] + [curve.mean(), curve.std(), curve.min(), curve.max(),
                                        curve[-1] - curve[0], float(ccq[idxs[0]]), float(ccs[idxs[0]]), len(idxs)]
        rows.append(f); cells.append(c); rpts.append(r)
    Xc, cc, rc = np.array(rows), np.array(cells), np.array(rpts)

    res = dict(n_pulse_rows=int(Xp.shape[0]), n_prefix_rows=int(Xc.shape[0]),
               n_cells=int(len(np.unique(cp))), monotonicity=mono)
    mp = rp == 0; mc = rc == 0
    if mp.sum() > 20:
        e = eta2(Xp[mp], np.array([gmap[c] for c in cp[mp]]))
        res["eta2_pulse"] = dict(n=int(mp.sum()), dim=int(Xp.shape[1]),
                                 mean=round(float(np.nanmean(e)), 4), max=round(float(np.nanmax(e)), 4),
                                 top=sorted([round(x, 3) for x in np.nan_to_num(e)], reverse=True)[:5])
    if mc.sum() > 20:
        e = eta2(Xc[mc], np.array([gmap[c] for c in cc[mc]]))
        res["eta2_prefix"] = dict(n=int(mc.sum()), dim=int(Xc.shape[1]),
                                  mean=round(float(np.nanmean(e)), 4), max=round(float(np.nanmax(e)), 4),
                                  top=sorted([round(x, 3) for x in np.nan_to_num(e)], reverse=True)[:5])
    # monotonicity of prefix features too
    pm = {}
    for j in range(Xc.shape[1]):
        rhos = []
        for c in np.unique(cc):
            m = cc == c
            if m.sum() < 10: continue
            col = Xc[m, j]
            if np.nanstd(col) < 1e-12: continue
            rho, _ = spearmanr(rc[m], col)
            if not np.isnan(rho): rhos.append(abs(rho))
        pm[f"f{j}"] = round(float(np.median(rhos)), 3) if rhos else None
    res["monotonicity_prefix"] = pm
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("done")

main()
