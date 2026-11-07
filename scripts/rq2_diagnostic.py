# -*- coding: utf-8 -*-
"""RQ2 diagnostic (first cut): pulse-waveform features vs prefix features.

Outputs JSON to temp for inspection. No model training beyond a small RF.
"""
import pickle, numpy as np, json
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold

PULSE = r"E:\桌面\rul\data\external\uconn\data_slowpulse_1.pkl"
CC    = r"E:\桌面\rul\data\external\uconn\data_cc_1.pkl"
OUT   = r"C:\Users\Administrator\AppData\Local\Temp\rq2_diag.json"

def load(p):
    with open(p, "rb") as f:
        return pickle.load(f, encoding="latin1")

def trace_features(v, kind):
    """Descriptive physical features from one 101-point pulse trace."""
    v = np.asarray(v, dtype=float)
    v0 = v[0]
    if kind == "chg":
        ip = int(np.argmax(v)); peak = v[ip]; sign = 1.0
    else:
        ip = int(np.argmin(v)); peak = v[ip]; sign = -1.0
    dv = abs(peak - v0)
    # 63% recovery time after the peak (samples == seconds)
    tau = np.nan
    if dv > 1e-6:
        target = peak - 0.632 * (peak - v0)
        after = v[ip:]
        if kind == "chg":
            idx = np.where(after <= target)[0]
        else:
            idx = np.where(after >= target)[0]
        if len(idx):
            tau = float(idx[0])
    resid = (v[-1] - peak) / (v0 - peak) if abs(v0 - peak) > 1e-9 else np.nan
    return dict(dv=dv, tau=tau, resid=float(resid), peak_pos=float(ip))

def build_pulse_feats(d):
    cell, rpt, soc, pt, V = d["cell_id"], d["rpt"], d["soc"], d["pulse_type"], d["voltage"]
    rows = []
    for i in range(len(cell)):
        f = trace_features(V[i], str(pt[i]))
        rows.append((int(cell[i]), int(rpt[i]), int(soc[i]), str(pt[i]),
                     f["dv"], f["tau"], f["resid"], f["peak_pos"]))
    return np.array(rows, dtype=object)

def main():
    dp = load(PULSE)
    raw = build_pulse_feats(dp)
    cell = raw[:, 0].astype(int); rpt = raw[:, 1].astype(int)
    soc = raw[:, 2].astype(int); kind = raw[:, 3].astype(str)
    dv = raw[:, 4].astype(float); tau = raw[:, 5].astype(float)
    resid = raw[:, 6].astype(float); ppos = raw[:, 7].astype(float)

    # aggregate per (cell, rpt): mean over 3 SOC x 2 directions
    keys = {}
    for i in range(len(cell)):
        k = (cell[i], rpt[i])
        keys.setdefault(k, []).append(i)
    agg = []
    for (c, r), idxs in keys.items():
        idxs = np.array(idxs)
        agg.append((c, r, np.nanmean(dv[idxs]), np.nanmean(tau[idxs]),
                    np.nanmean(resid[idxs]), np.nanmean(ppos[idxs]),
                    np.nanstd(tau[idxs])))
    agg = np.array(agg, dtype=float)

    # --- diagnostic 1: monotonicity vs rpt, per cell ---
    names = ["mean_dv", "mean_tau", "mean_resid", "mean_peak_pos", "std_tau"]
    mono = {}
    for j, nm in enumerate(names):
        rhos = []
        for c in np.unique(agg[:, 0]):
            m = agg[:, 0] == c
            if m.sum() < 10:
                continue
            rho, _ = spearmanr(agg[m, 1], agg[m, 2 + j])
            if not np.isnan(rho):
                rhos.append(abs(rho))
        mono[nm] = dict(median_abs_rho=float(np.median(rhos)) if rhos else None,
                        n_cells=len(rhos))

    # --- diagnostic 2: condition separability at rpt == 0 ---
    base = agg[agg[:, 1] == 0]
    cells0 = base[:, 0].astype(int)
    gmap = {}
    cid = dp["cell_id"]; gid = dp["group_id"]
    for c, g in zip(cid, gid):
        gmap[int(c)] = int(g)
    y = np.array([gmap[c] for c in cells0])
    X_pulse = base[:, 2:7]

    dc = load(CC)
    cc_cell = dc["cell_id"]; cc_rpt = dc["rpt"]; ccV = dc["voltage"]
    ccq = dc["q_dchg"]; ccs = dc["soh"]
    m0 = cc_rpt == 0
    Xpref, ypref = [], []
    for i in np.where(m0)[0]:
        v = np.asarray(ccV[i], dtype=float)
        Xpref.append([v.mean(), v.std(), v.min(), v.max(), v[-1] - v[0],
                      float(ccq[i]), float(ccs[i])])
        ypref.append(gmap[int(cc_cell[i])])
    Xpref = np.array(Xpref); ypref = np.array(ypref)

    res = dict(
        n_pulses=int(len(cell)),
        n_cell_rpt=int(len(agg)),
        n_cells=int(len(np.unique(agg[:, 0]))),
        monotonicity=mono,
        sep_pulse=None, sep_prefix=None, n_class=dict(pulse=len(np.unique(y)), prefix=len(np.unique(ypref))),
    )
    if len(np.unique(y)) > 1 and len(y) > 20:
        clf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1)
        cv = StratifiedKFold(n_splits=min(5, int(np.bincount(y).min()) if np.bincount(y).min() >= 2 else 2), shuffle=True, random_state=0)
        s = cross_val_score(clf, X_pulse, y, cv=cv)
        res["sep_pulse"] = dict(mean=float(s.mean()), std=float(s.std()), n=len(y), n_features=X_pulse.shape[1])
    if len(np.unique(ypref)) > 1 and len(ypref) > 20:
        clf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1)
        k = int(np.bincount(ypref).min())
        cv = StratifiedKFold(n_splits=min(5, k) if k >= 2 else 2, shuffle=True, random_state=0)
        s = cross_val_score(clf, Xpref, ypref, cv=cv)
        res["sep_prefix"] = dict(mean=float(s.mean()), std=float(s.std()), n=len(ypref), n_features=Xpref.shape[1])

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("done")

main()
