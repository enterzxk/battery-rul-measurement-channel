# -*- coding: utf-8 -*-
"""E1 + E2 rerun: ONE script, ONE configuration, multiple seeds, ONE output file.

Feature sets (all dimensions matched where compared):
  A_curve        54  discharge curve only
  A_curve+C_desc 74  + 20 waveform descriptors
  A_curve+C_d30  84  + 30 waveform descriptors  (dimension-matched to C_ecm)
  A_curve+C_ecm  84  + 30 two-RC parameters
  A_prefix       58  curve + capacity + SOH
  C_ecm_only     30
"""
import pickle, numpy as np, json, time, warnings, os
from scipy.optimize import curve_fit
from sklearn.ensemble import HistGradientBoostingRegressor
warnings.filterwarnings("ignore")
PULSE = r"E:\桌面\rul\data\external\uconn\data_slowpulse_1.pkl"
CC    = r"E:\桌面\rul\data\external\uconn\data_cc_1.pkl"
OUT   = r"C:\Users\Administrator\AppData\Local\Temp\e1_final.json"
SEEDS = [0, 1, 2, 3]

def load(p):
    with open(p, "rb") as f: return pickle.load(f, encoding="latin1")

def ecm_fit(v, kind, ip):
    seg = np.asarray(v[ip:], float)
    if seg.size < 15: return (np.nan,)*5
    x = np.arange(seg.size, dtype=float); y = seg
    p0 = [float(y[-1]), float(y[0]-y[-1])*.6, 5., float(y[0]-y[-1])*.4, 40.]
    lo = [y.min()-.2, -.6, 1., -.6, 10.]; hi = [y.max()+.2, .6, 60., .6, 400.]
    try:
        popt, _ = curve_fit(lambda x, c, a1, t1, a2, t2: c + a1*np.exp(-x/t1) + a2*np.exp(-x/t2),
                            x, y, p0=p0, bounds=(lo, hi), maxfev=4000)
        return tuple(float(p) for p in popt)
    except Exception:
        return (np.nan,)*5

def build():
    dp = load(PULSE)
    cell, rpt, soc, pt, V = dp["cell_id"], dp["rpt"], dp["soc"], dp["pulse_type"], dp["voltage"]
    soh = dp["soh"]
    gmap = {int(c): int(g) for c, g in zip(dp["cell_id"], dp["group_id"])}
    ecm, desc = {}, {}
    for i in range(len(cell)):
        k = (int(cell[i]), int(rpt[i]), int(soc[i]), str(pt[i]))
        v = np.asarray(V[i], float); v0 = v[0]
        ip = int(np.argmax(v)) if k[3] == "chg" else int(np.argmin(v))
        peak = v[ip]; dv = abs(peak - v0)
        tau = np.nan
        if dv > 1e-6:
            t = peak - 0.632*(peak - v0); a = v[ip:]
            idx = np.where(a <= t)[0] if k[3] == "chg" else np.where(a >= t)[0]
            if len(idx): tau = float(idx[0])
        resid = (v[-1]-peak)/(v0-peak) if abs(v0-peak) > 1e-9 else np.nan
        slope = float(v[min(ip+1, len(v)-1)] - v[ip])
        area = float(np.trapz(v[ip:]) / max(1, len(v)-ip))
        desc[k] = (dv, tau, resid, slope, area)
        ecm[k] = ecm_fit(v, k[3], ip)
    soh_map = {(int(c), int(r)): float(s) for c, r, s in zip(cell, rpt, soh)}
    keys = sorted({(k[0], k[1]) for k in desc})
    D20, D30, E30, K = [], [], [], []
    for (c, r) in keys:
        d20, d30, e30, ok = [], [], [], True
        for s in (20, 50, 90):
            for kk in ("chg", "dchg"):
                q = (c, r, s, kk)
                if q not in desc: ok = False; break
                d20 += list(desc[q][:3]); d30 += list(desc[q][:3]); e30 += list(ecm[q])
            if not ok: break
        if not ok: continue
        dvch = [desc[(c, r, s, "chg")][0] for s in (20, 50, 90)]
        dvdh = [desc[(c, r, s, "dchg")][0] for s in (20, 50, 90)]
        tach = [desc[(c, r, s, "chg")][1] for s in (20, 50, 90)]
        d20 += [np.nanstd(dvch), np.nanstd(dvdh)]
        # extend descriptors to 30 with 10 more waveform statistics
        d30 += [np.nanstd(dvch), np.nanstd(dvdh)]
        for s in (20, 50, 90):
            for kk in ("chg", "dchg"):
                d30 += [desc[(c, r, s, kk)][3]]           # initial slope
        d30 += [np.nanstd(tach), float(np.nanmean([desc[(c, r, s, "chg")][4] for s in (20, 50, 90)]))]
        D20.append(d20); D30.append(d30); E30.append(e30); K.append((c, r))
    D20 = np.array(D20); D30 = np.array(D30); E30 = np.array(E30)
    cells = np.array([k[0] for k in K]); rpts = np.array([k[1] for k in K])
    sh = np.array([soh_map[k] for k in K]); grp = np.array([gmap[c] for c in cells])

    dc = load(CC)
    cc_cell, cc_rpt, ccV = dc["cell_id"], dc["rpt"], dc["voltage"]
    buckets = {}
    for i in range(len(cc_cell)): buckets.setdefault((int(cc_cell[i]), int(cc_rpt[i])), []).append(i)
    pfeat = {}
    for k, idxs in buckets.items():
        idxs = sorted(idxs, key=lambda i: float(np.mean(ccV[i])))
        curve = np.concatenate([np.asarray(ccV[i], float) for i in idxs])
        bins = np.array_split(curve, 50)
        pfeat[k] = [b.mean() for b in bins] + [curve.mean(), curve.std(), curve.min(), curve.max()]
    keep = [i for i, k in enumerate(K) if k in pfeat]
    A = np.array([pfeat[K[i]] for i in keep])
    D20, D30, E30, cells, rpts, sh, grp = D20[keep], D30[keep], E30[keep], cells[keep], rpts[keep], sh[keep], grp[keep]
    eol = {}
    for c in np.unique(cells):
        m = cells == c; o = np.argsort(rpts[m]); rr, ss = rpts[m][o], sh[m][o]
        hit = np.where(ss <= 80.0)[0]
        if len(hit): eol[c] = int(rr[hit[0]])
    ok = np.array([c in eol and r <= eol[c] for c, r in zip(cells, rpts)])
    y = np.array([eol[c] - r for c, r in zip(cells[ok], rpts[ok])], float)
    return dict(A=A[ok], D20=D20[ok], D30=D30[ok], E30=E30[ok],
                cells=cells[ok], rpts=rpts[ok], grp=grp[ok], y=y)

def cm(y, p, c):
    return float(np.mean([np.mean(np.abs(y[c == k] - p[c == k])) for k in np.unique(c)]))

def predict(X, y, cells, grp, protocol, seed):
    pred = np.full(len(y), np.nan)
    folds = np.unique(grp) if protocol == "logo" else np.unique(cells)
    for f in folds:
        te = grp == f if protocol == "logo" else cells == f
        tr = ~te
        if tr.sum() < 100 or te.sum() == 0: continue
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=seed)
        m.fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
    return pred

def main():
    t0 = time.time()
    d = build()
    A, D20, D30, E30 = d["A"], d["D20"], d["D30"], d["E30"]
    cells, grp, y = d["cells"], d["grp"], d["y"]
    print("rows", len(y), "cells", len(np.unique(cells)), "dims A/D20/D30/E30 =", A.shape[1], D20.shape[1], D30.shape[1], E30.shape[1], flush=True)
    sets = {
        "A_curve": A,
        "A_curve+C_desc20": np.hstack([A, D20]),
        "A_curve+C_desc30": np.hstack([A, D30]),
        "A_curve+C_ecm": np.hstack([A, E30]),
        "C_ecm_only": E30,
    }
    res = {"n_rows": int(len(y)), "n_cells": int(len(np.unique(cells))),
           "dims": {k: int(v.shape[1]) for k, v in sets.items()}, "seeds": SEEDS, "sets": {}}
    store = {}
    for name, X in sets.items():
        logo_runs, loco_runs, preds0 = [], [], None
        for s in SEEDS:
            pl = predict(X, y, cells, grp, "logo", s)
            m = ~np.isnan(pl)
            logo_runs.append(cm(y[m], pl[m], cells[m]))
            if s == 0: preds0 = pl
        pc = predict(X, y, cells, grp, "loco", 0)
        mc = ~np.isnan(pc)
        loco_runs.append(cm(y[mc], pc[mc], cells[mc]))
        store[name] = preds0
        res["sets"][name] = dict(logo_mean=round(float(np.mean(logo_runs)), 3),
                                 logo_std=round(float(np.std(logo_runs)), 3),
                                 logo_runs=[round(v, 3) for v in logo_runs],
                                 loco=round(loco_runs[0], 3))
        print(name, res["sets"][name], flush=True)

    # bootstrap vs A_curve on seed 0 predictions
    rng = np.random.default_rng(0)
    base = store["A_curve"]
    mb = {c: np.mean(np.abs(y[cells == c] - base[cells == c])) for c in np.unique(cells)}
    for name in ["A_curve+C_desc20", "A_curve+C_desc30", "A_curve+C_ecm"]:
        p = store[name]
        mp = {c: np.mean(np.abs(y[cells == c] - p[cells == c])) for c in np.unique(cells)}
        cs = np.array(sorted(mb.keys()))
        diffs = np.array([mp[c] - mb[c] for c in cs])
        bs = np.array([np.mean(rng.choice(diffs, len(diffs), replace=True)) for _ in range(5000)])
        res["sets"][name]["boot"] = dict(delta=round(float(diffs.mean()), 3),
                                         ci=[round(float(np.percentile(bs, 2.5)), 3),
                                             round(float(np.percentile(bs, 97.5)), 3)],
                                         frac_improved=round(float((diffs < 0).mean()), 3))
        print("boot", name, res["sets"][name]["boot"], flush=True)

    res["elapsed_s"] = round(time.time()-t0, 1)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("done", res["elapsed_s"], "s")

main()
