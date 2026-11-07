# -*- coding: utf-8 -*-
"""Tier 2a: handcrafted trajectory descriptors of ECM parameters + HGB (the agreed baseline)."""
import pickle, numpy as np, json, warnings
from scipy.optimize import curve_fit
from sklearn.ensemble import HistGradientBoostingRegressor
warnings.filterwarnings("ignore")
PULSE = r"E:\桌面\rul\data\external\uconn\data_slowpulse_1.pkl"
CC    = r"E:\桌面\rul\data\external\uconn\data_cc_1.pkl"
OUT   = r"C:\Users\Administrator\AppData\Local\Temp\tier2a.json"

def load(p):
    with open(p, "rb") as f: return pickle.load(f, encoding="latin1")

def ecm_fit(v, kind, ip):
    seg = np.asarray(v[ip:], float)
    if seg.size < 15: return (np.nan,) * 5
    x = np.arange(seg.size, dtype=float); y = seg
    p0 = [float(y[-1]), float(y[0]-y[-1])*.6, 5., float(y[0]-y[-1])*.4, 40.]
    lo = [y.min()-.2, -.6, 1., -.6, 10.]; hi = [y.max()+.2, .6, 60., .6, 400.]
    try:
        popt, _ = curve_fit(lambda x, c, a1, t1, a2, t2: c + a1*np.exp(-x/t1) + a2*np.exp(-x/t2),
                            x, y, p0=p0, bounds=(lo, hi), maxfev=4000)
        return tuple(float(p) for p in popt)
    except Exception:
        return (np.nan,) * 5

def build():
    dp = load(PULSE)
    cell, rpt, soc, pt, V = dp["cell_id"], dp["rpt"], dp["soc"], dp["pulse_type"], dp["voltage"]
    soh = dp["soh"]
    gmap = {int(c): int(g) for c, g in zip(dp["cell_id"], dp["group_id"])}
    ecm = {}
    for i in range(len(cell)):
        k = (int(cell[i]), int(rpt[i]), int(soc[i]), str(pt[i]))
        v = np.asarray(V[i], float); v0 = v[0]
        ip = int(np.argmax(v)) if k[3] == "chg" else int(np.argmin(v))
        ecm[k] = ecm_fit(v, k[3], ip)
    soh_map = {(int(c), int(r)): float(s) for c, r, s in zip(cell, rpt, soh)}
    keys = sorted({(k[0], k[1]) for k in ecm})
    E, K = [], []
    for (c, r) in keys:
        fe, ok = [], True
        for s in (20, 50, 90):
            for kk in ("chg", "dchg"):
                q = (c, r, s, kk)
                if q not in ecm: ok = False; break
                fe += list(ecm[q])
            if not ok: break
        if ok: E.append(fe); K.append((c, r))
    E = np.array(E); cells = np.array([k[0] for k in K]); rpts = np.array([k[1] for k in K])
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
    E, cells, rpts, sh, grp = E[keep], cells[keep], rpts[keep], sh[keep], grp[keep]

    eol = {}
    for c in np.unique(cells):
        m = cells == c; o = np.argsort(rpts[m]); rr, ss = rpts[m][o], sh[m][o]
        hit = np.where(ss <= 80.0)[0]
        if len(hit): eol[c] = int(rr[hit[0]])
    ok = np.array([c in eol and r <= eol[c] for c, r in zip(cells, rpts)])
    return dict(E=E[ok], A=A[ok], cells=cells[ok], rpts=rpts[ok], grp=grp[ok], eol=eol)

def traj_feats(E, cells, rpts):
    """History-only descriptors: first value, current value, slope, range."""
    order = {}
    for i, c in enumerate(cells): order.setdefault(c, []).append(i)
    pos = {}
    for c, ids in order.items():
        ids = sorted(ids, key=lambda i: rpts[i])
        for j, i in enumerate(ids): pos[i] = j
    out = []
    for i in range(len(cells)):
        ids = sorted(order[cells[i]], key=lambda k: rpts[k])
        j = pos[i]
        hist = E[ids[:j + 1]]
        first = hist[0]
        cur = hist[-1]
        t = np.arange(len(hist), dtype=float)
        if len(hist) > 1:
            slope = np.polyfit(t, hist, 1)[0]
        else:
            slope = np.zeros(E.shape[1])
        rng = hist.max(0) - hist.min(0)
        out.append(np.concatenate([first, cur, slope, rng]))
    return np.array(out)

def cell_macro(y, p, cells):
    return float(np.mean([np.mean(np.abs(y[cells == c] - p[cells == c])) for c in np.unique(cells)]))

def logo(X, y, cells, grp):
    pred = np.full(len(y), np.nan)
    for g in np.unique(grp):
        te = grp == g; tr = ~te
        if tr.sum() < 100: continue
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
        m.fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
    return pred

def main():
    d = build()
    E, A, cells, rpts, grp = d["E"], d["A"], d["cells"], d["rpts"], d["grp"]
    y = np.array([d["eol"][c] - r for c, r in zip(cells, rpts)], float)
    T = traj_feats(E, cells, rpts)
    sets = {
        "A_curve": A,
        "A_curve+C_ecm": np.hstack([A, E]),
        "A_curve+T_traj": np.hstack([A, T]),
        "A_curve+C_ecm+T_traj": np.hstack([A, E, T]),
        "T_traj_only": T,
    }
    res = {"n": int(len(y)), "n_cells": int(len(np.unique(cells))), "sets": {}}
    for name, X in sets.items():
        p = logo(X, y, cells, grp)
        m = ~np.isnan(p)
        res["sets"][name] = round(cell_macro(y[m], p[m], cells[m]), 3)
        print(name, res["sets"][name], flush=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("done")

main()
