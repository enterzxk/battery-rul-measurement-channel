# -*- coding: utf-8 -*-
"""RQ2 gate v2: LOGO vs LOCO predictive transfer on UConn.

Five feature sets, one fixed model (HGB), two protocols.
Metric: cell-macro MAE (cycles to first SOH<=80%).
"""
import pickle, numpy as np, json, time
from sklearn.ensemble import HistGradientBoostingRegressor

PULSE = r"E:\桌面\rul\data\external\uconn\data_slowpulse_1.pkl"
CC    = r"E:\桌面\rul\data\external\uconn\data_cc_1.pkl"
OUT   = r"C:\Users\Administrator\AppData\Local\Temp\rq2_gate.json"

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

def build():
    dp = load(PULSE)
    cell, rpt, soc, pt, V = dp["cell_id"], dp["rpt"], dp["soc"], dp["pulse_type"], dp["voltage"]
    ncyc, soh = dp["num_cycles"], dp["soh"]
    gmap = {}
    for c, g in zip(dp["cell_id"], dp["group_id"]):
        gmap[int(c)] = int(g)

    recs = {}
    meta = {}
    for i in range(len(cell)):
        k = (int(cell[i]), int(rpt[i]))
        recs.setdefault(k, {})[(int(soc[i]), str(pt[i]))] = trace_features(V[i], str(pt[i]))
        meta[k] = (float(ncyc[i]), float(soh[i]))

    keys, pf = [], []
    for k in sorted(recs):
        d = recs[k]
        if len(d) < 6: continue
        f = []
        for s in (20, 50, 90):
            for kk in ("chg", "dchg"):
                f += list(d[(s, kk)])
        f += [np.nanstd([d[(s, "chg")][0] for s in (20, 50, 90)]),
              np.nanstd([d[(s, "dchg")][0] for s in (20, 50, 90)])]
        keys.append(k); pf.append(f)
    Xpulse = np.array(pf)

    dc = load(CC)
    cc_cell, cc_rpt, ccV = dc["cell_id"], dc["rpt"], dc["voltage"]
    dc_q, dc_s = dc["q_dchg"], dc["soh"]
    dcir = np.column_stack([dc[k] for k in ["dcir_chg_20","dcir_dchg_20","dcir_chg_50","dcir_dchg_50","dcir_chg_90","dcir_dchg_90"]])
    buckets = {}
    for i in range(len(cc_cell)):
        buckets.setdefault((int(cc_cell[i]), int(cc_rpt[i])), []).append(i)
    pref, dcirc, pkeys = [], [], []
    for k, idxs in sorted(buckets.items()):
        idxs = sorted(idxs, key=lambda i: float(np.mean(ccV[i])))
        curve = np.concatenate([np.asarray(ccV[i], float) for i in idxs])
        bins = np.array_split(curve, 50)
        f = [b.mean() for b in bins] + [curve.mean(), curve.std(), curve.min(), curve.max(),
                                        curve[-1] - curve[0], float(dc_q[idxs[0]]), float(dc_s[idxs[0]]), len(idxs)]
        pref.append(f); dcirc.append(dcir[idxs[0]]); pkeys.append(k)
    Xpref = np.array(pref); Xdcir = np.array(dcirc)

    # align on keys
    idx_p = {k: i for i, k in enumerate(pkeys)}
    idx_q = {k: i for i, k in enumerate(keys)}
    common = [k for k in pkeys if k in idx_q]
    A = Xpref[[idx_p[k] for k in common]]
    B = Xdcir[[idx_p[k] for k in common]]
    C = Xpulse[[idx_q[k] for k in common]]
    cells = np.array([k[0] for k in common])
    rpts  = np.array([k[1] for k in common])
    cyc   = np.array([meta[k][0] for k in common])
    sh    = np.array([meta[k][1] for k in common])
    grp   = np.array([gmap[c] for c in cells])

    # EOL per cell: first rpt with soh <= 80
    eol_rpt, eol_cyc = {}, {}
    for c in np.unique(cells):
        m = cells == c
        o = np.argsort(rpts[m])
        rr, ss, yy = rpts[m][o], sh[m][o], cyc[m][o]
        hit = np.where(ss <= 80.0)[0]
        if len(hit):
            eol_rpt[c] = rr[hit[0]]; eol_cyc[c] = yy[hit[0]]
    keep = np.array([ (c in eol_rpt) and (r <= eol_rpt[c]) for c, r in zip(cells, rpts) ])
    # drop rows with non-finite cycle count
    fin = np.isfinite(cyc)
    keep = keep & fin
    return dict(A=A[keep], B=B[keep], C=C[keep], cells=cells[keep], rpts=rpts[keep],
                cyc=cyc[keep], grp=grp[keep], eol_cyc=eol_cyc,
                n_total=int(keep.sum()), n_cells=int(len(np.unique(cells[keep]))))

def cell_macro_mae(y, p, cells):
    errs = []
    for c in np.unique(cells):
        m = cells == c
        errs.append(np.mean(np.abs(y[m] - p[m])))
    return float(np.mean(errs))

def run(X, y, cells, grp, protocol):
    pred = np.full(len(y), np.nan)
    if protocol == "logo":
        for g in np.unique(grp):
            te = grp == g; tr = ~te
            if te.sum() == 0 or tr.sum() < 50: continue
            m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, random_state=0)
            m.fit(X[tr], y[tr])
            pred[te] = m.predict(X[te])
    else:
        for c in np.unique(cells):
            te = cells == c; tr = ~te
            if tr.sum() < 50: continue
            m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, random_state=0)
            m.fit(X[tr], y[tr])
            pred[te] = m.predict(X[te])
    ok = ~np.isnan(pred)
    return cell_macro_mae(y[ok], pred[ok], cells[ok]), int(ok.sum())

def main():
    d = build()
    A, B, C = d["A"], d["B"], d["C"]
    cells, grp, cyc = d["cells"], d["grp"], d["cyc"]
    y = np.array([d["eol_cyc"][c] - cc for c, cc in zip(cells, cyc)], float)
    good = np.isfinite(y)
    y = y[good]; cells = cells[good]; grp = grp[good]
    A = A[good]; B = B[good]; C = C[good]
    sets = {"A_prefix": A, "B_dcir": B, "C_pulse": C,
            "A+C": np.hstack([A, C]), "A+B+C": np.hstack([A, B, C])}
    res = {"n_rows": d["n_total"], "n_cells": d["n_cells"],
           "n_groups": int(len(np.unique(grp))), "y_range": [float(y.min()), float(y.max())]}
    for name, X in sets.items():
        t0 = time.time()
        m_logo, n_logo = run(X, y, cells, grp, "logo")
        m_loco, n_loco = run(X, y, cells, grp, "loco")
        res[name] = dict(logo=round(m_logo, 2), loco=round(m_loco, 2),
                         gap=round(m_logo - m_loco, 2), n_logo=n_logo, n_loco=n_loco,
                         sec=round(time.time() - t0, 1))
        print(name, res[name], flush=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("done")

main()
