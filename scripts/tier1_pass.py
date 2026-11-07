# -*- coding: utf-8 -*-
"""Tier-1 first pass on UConn: prefix vs pulse(descriptive) vs pulse(ECM-fitted).

Fixes:
  * timeline = rpt index (num_cycles is non-monotone: 379 increasing-SOH steps vs 16 for rpt)
  * RUL in RPT units (remaining inspections to first SOH<=80%)
  * 2-exponential relaxation fit -> ECM-like parameters
  * cell-level paired bootstrap for the MAE difference
"""
import pickle, numpy as np, json, time, warnings
from scipy.optimize import curve_fit
from sklearn.ensemble import HistGradientBoostingRegressor

warnings.filterwarnings("ignore")
PULSE = r"E:\桌面\rul\data\external\uconn\data_slowpulse_1.pkl"
CC    = r"E:\桌面\rul\data\external\uconn\data_cc_1.pkl"
OUT   = r"C:\Users\Administrator\AppData\Local\Temp\tier1.json"
SEED  = 0

def load(p):
    with open(p, "rb") as f:
        return pickle.load(f, encoding="latin1")

def desc_feats(v, kind):
    v = np.asarray(v, float); v0 = v[0]
    ip = int(np.argmax(v)) if kind == "chg" else int(np.argmin(v))
    peak = v[ip]; dv = abs(peak - v0)
    tau = np.nan
    if dv > 1e-6:
        t = peak - 0.632 * (peak - v0); a = v[ip:]
        idx = np.where(a <= t)[0] if kind == "chg" else np.where(a >= t)[0]
        if len(idx): tau = float(idx[0])
    resid = (v[-1] - peak) / (v0 - peak) if abs(v0 - peak) > 1e-9 else np.nan
    return dv, tau, resid, ip

def ecm_fit(v, kind, ip):
    """Fit v(x) = c + a1*exp(-x/t1) + a2*exp(-x/t2) to the post-peak relaxation."""
    seg = np.asarray(v[ip:], float)
    if seg.size < 15:
        return (np.nan,) * 5
    x = np.arange(seg.size, dtype=float)
    y = seg
    c0 = float(y[-1]); a0 = float(y[0] - y[-1])
    p0 = [c0, a0 * 0.6, 5.0, a0 * 0.4, 40.0]
    lo = [y.min() - 0.2, -0.6, 1.0, -0.6, 10.0]
    hi = [y.max() + 0.2, 0.6, 60.0, 0.6, 400.0]
    try:
        popt, _ = curve_fit(lambda x, c, a1, t1, a2, t2: c + a1 * np.exp(-x / t1) + a2 * np.exp(-x / t2),
                            x, y, p0=p0, bounds=(lo, hi), maxfev=4000)
        return tuple(float(p) for p in popt)
    except Exception:
        return (np.nan,) * 5

def build():
    dp = load(PULSE)
    cell, rpt, soc, pt, V = dp["cell_id"], dp["rpt"], dp["soc"], dp["pulse_type"], dp["voltage"]
    soh, ncyc = dp["soh"], dp["num_cycles"]
    gmap = {}
    for c, g in zip(dp["cell_id"], dp["group_id"]):
        gmap[int(c)] = int(g)

    desc, ecm = {}, {}
    t0 = time.time()
    for i in range(len(cell)):
        k = (int(cell[i]), int(rpt[i]), int(soc[i]), str(pt[i]))
        d = desc_feats(V[i], k[3])
        desc[k] = d
        ecm[k] = ecm_fit(V[i], k[3], int(d[3]))
    print("ecm fit sec", round(time.time() - t0, 1), flush=True)

    soh_map = {}
    for c, r, s in zip(cell, rpt, soh):
        soh_map[(int(c), int(r))] = float(s)

    keys = sorted({(k[0], k[1]) for k in desc})
    D, E = [], []
    for (c, r) in keys:
        fd, fe = [], []
        ok = True
        for s in (20, 50, 90):
            for kk in ("chg", "dchg"):
                q = (c, r, s, kk)
                if q not in desc: ok = False; break
                fd += list(desc[q][:3])
                fe += list(ecm[q])
            if not ok: break
        if not ok: continue
        fd += [np.nanstd([desc[(c, r, s, "chg")][0] for s in (20, 50, 90)]),
               np.nanstd([desc[(c, r, s, "dchg")][0] for s in (20, 50, 90)])]
        E.append(fe); D.append(fd)
    keys = [k for k in keys if len(D) and True]
    # rebuild keys aligned (skip any that failed)
    keys2, D2, E2 = [], [], []
    for (c, r), d, e in zip(sorted({(k[0], k[1]) for k in desc}), D, E):
        keys2.append((c, r)); D2.append(d); E2.append(e)
    D = np.array(D2); E = np.array(E2)
    cells = np.array([k[0] for k in keys2]); rpts = np.array([k[1] for k in keys2])
    sh = np.array([soh_map[k] for k in keys2])
    grp = np.array([gmap[c] for c in cells])

    # prefix features from stitched CC curves
    dc = load(CC)
    cc_cell, cc_rpt, ccV = dc["cell_id"], dc["rpt"], dc["voltage"]
    dc_q, dc_s = dc["q_dchg"], dc["soh"]
    dcir = np.column_stack([dc[k] for k in ["dcir_chg_20","dcir_dchg_20","dcir_chg_50","dcir_dchg_50","dcir_chg_90","dcir_dchg_90"]])
    buckets = {}
    for i in range(len(cc_cell)):
        buckets.setdefault((int(cc_cell[i]), int(cc_rpt[i])), []).append(i)
    pfeat, dfeat = {}, {}
    for k, idxs in buckets.items():
        idxs = sorted(idxs, key=lambda i: float(np.mean(ccV[i])))
        curve = np.concatenate([np.asarray(ccV[i], float) for i in idxs])
        bins = np.array_split(curve, 50)
        pfeat[k] = [b.mean() for b in bins] + [curve.mean(), curve.std(), curve.min(), curve.max(),
                                               curve[-1] - curve[0], float(dc_q[idxs[0]]), float(dc_s[idxs[0]])]
        dfeat[k] = dcir[idxs[0]]

    keep = [i for i, k in enumerate(keys2) if k in pfeat]
    A = np.array([pfeat[keys2[i]] for i in keep])
    B = np.array([dfeat[keys2[i]] for i in keep])
    D = D[keep]; E = E[keep]; cells = cells[keep]; rpts = rpts[keep]; sh = sh[keep]; grp = grp[keep]

    # EOL in rpt units
    eol = {}
    for c in np.unique(cells):
        m = cells == c
        o = np.argsort(rpts[m])
        rr, ss = rpts[m][o], sh[m][o]
        hit = np.where(ss <= 80.0)[0]
        if len(hit): eol[c] = int(rr[hit[0]])
    ok = np.array([c in eol and r <= eol[c] for c, r in zip(cells, rpts)])
    return dict(A=A[ok], B=B[ok], D=D[ok], E=E[ok], cells=cells[ok], rpts=rpts[ok],
                grp=grp[ok], eol=eol, soh=sh[ok])

def cell_mae(y, p, cells):
    out = {}
    for c in np.unique(cells):
        m = cells == c
        out[c] = float(np.mean(np.abs(y[m] - p[m])))
    return out

def predict(X, y, cells, grp, protocol):
    pred = np.full(len(y), np.nan)
    folds = np.unique(grp) if protocol == "logo" else np.unique(cells)
    for f in folds:
        te = grp == f if protocol == "logo" else cells == f
        tr = ~te
        if tr.sum() < 50 or te.sum() == 0: continue
        m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, random_state=SEED)
        m.fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
    return pred

def main():
    d = build()
    A, B, D, E = d["A"], d["B"], d["D"], d["E"]
    cells, grp, rpts = d["cells"], d["grp"], d["rpts"]
    y = np.array([d["eol"][c] - r for c, r in zip(cells, rpts)], float)
    Acurve = A[:, :54]
    sets = {
        "A_curve": Acurve,
        "A_curve+C_desc": np.hstack([Acurve, D]),
        "A_curve+C_ecm": np.hstack([Acurve, E]),
        "A_curve+C_both": np.hstack([Acurve, D, E]),
        "A_prefix": A,
        "A_prefix+C_both": np.hstack([A, D, E]),
        "C_ecm_only": E,
    }
    res = {"n_rows": int(len(y)), "n_cells": int(len(np.unique(cells))),
           "n_groups": int(len(np.unique(grp))),
           "rul_rpt_range": [float(y.min()), float(y.max())],
           "n_negative_rul": int((y < 0).sum()),
           "nan_rate_ecm": float(np.mean(~np.isfinite(E))), "sets": {}}
    preds = {}
    for name, X in sets.items():
        t0 = time.time()
        pl = predict(X, y, cells, grp, "logo")
        pc = predict(X, y, cells, grp, "loco")
        preds[name] = (pl, pc)
        ml = cell_mae(y[~np.isnan(pl)], pl[~np.isnan(pl)], cells[~np.isnan(pl)])
        mc = cell_mae(y[~np.isnan(pc)], pc[~np.isnan(pc)], cells[~np.isnan(pc)])
        res["sets"][name] = dict(logo=round(float(np.mean(list(ml.values()))), 3),
                                 loco=round(float(np.mean(list(mc.values()))), 3),
                                 sec=round(time.time() - t0, 1))
        print(name, res["sets"][name], flush=True)

    # paired bootstrap on LOGO difference vs A_curve
    rng = np.random.default_rng(0)
    base = preds["A_curve"][0]
    mbase = cell_mae(y, base, cells)
    for name in ["A_curve+C_desc", "A_curve+C_ecm", "A_curve+C_both"]:
        p = preds[name][0]
        mp = cell_mae(y, p, cells)
        cs = np.array(sorted(mbase.keys()))
        diffs = np.array([mp[c] - mbase[c] for c in cs])
        bs = np.array([np.mean(rng.choice(diffs, len(diffs), replace=True)) for _ in range(5000)])
        res["sets"][name]["bootstrap_vs_A_curve"] = dict(
            delta=round(float(diffs.mean()), 3),
            ci=[round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)],
            frac_cells_improved=round(float((diffs < 0).mean()), 3))
        print("boot", name, res["sets"][name]["bootstrap_vs_A_curve"], flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("done")

main()
