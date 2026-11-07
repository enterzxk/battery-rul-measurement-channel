# -*- coding: utf-8 -*-
"""RQ2 diagnostic v2.

(1) Monotonicity of pulse-waveform descriptors vs RPT (per cell, Spearman).
(2) Condition separability: eta^2 (between-group variance share) per feature,
    for pulse descriptors vs prefix (discharge-curve) descriptors.
    eta^2 mirrors the r=0.53-0.66 group-separability measure used earlier.
"""
import pickle, numpy as np, json
from scipy.stats import spearmanr

PULSE = r"E:\桌面\rul\data\external\uconn\data_slowpulse_1.pkl"
CC    = r"E:\桌面\rul\data\external\uconn\data_cc_1.pkl"
OUT   = r"C:\Users\Administrator\AppData\Local\Temp\rq2_diag2.json"

def load(p):
    with open(p, "rb") as f:
        return pickle.load(f, encoding="latin1")

def trace_features(v, kind):
    v = np.asarray(v, dtype=float)
    v0 = v[0]
    if kind == "chg":
        ip = int(np.argmax(v)); peak = v[ip]
    else:
        ip = int(np.argmin(v)); peak = v[ip]
    dv = abs(peak - v0)
    tau = np.nan
    if dv > 1e-6:
        target = peak - 0.632 * (peak - v0)
        after = v[ip:]
        idx = np.where(after <= target)[0] if kind == "chg" else np.where(after >= target)[0]
        if len(idx):
            tau = float(idx[0])
    resid = (v[-1] - peak) / (v0 - peak) if abs(v0 - peak) > 1e-9 else np.nan
    return dv, tau, resid

def eta2(X, groups):
    """Between-group variance share per column."""
    out = []
    g = np.asarray(groups)
    total = X.var(axis=0) * len(X)
    for j in range(X.shape[1]):
        ssb = 0.0
        for u in np.unique(g):
            m = g == u
            if m.sum() == 0:
                continue
            ssb += m.sum() * (X[m, j].mean() - X[:, j].mean()) ** 2
        out.append(ssb / total[j] if total[j] > 1e-12 else np.nan)
    return np.array(out)

def main():
    dp = load(PULSE)
    cell = dp["cell_id"]; rpt = dp["rpt"]; soc = dp["soc"]; pt = dp["pulse_type"]; V = dp["voltage"]
    gmap = {}
    for c, g in zip(dp["cell_id"], dp["group_id"]):
        gmap[int(c)] = int(g)

    # ---- pulse descriptors: 3 SOC x 2 dir x 3 features, per (cell, rpt) ----
    recs = {}
    for i in range(len(cell)):
        c, r, s, k = int(cell[i]), int(rpt[i]), int(soc[i]), str(pt[i])
        dv, tau, resid = trace_features(V[i], k)
        recs.setdefault((c, r), {})[(s, k)] = (dv, tau, resid)

    pulse_rows, pulse_cells, pulse_rpts = [], [], []
    for (c, r), d in sorted(recs.items()):
        if len(d) < 6:
            continue
        f = []
        for s in (20, 50, 90):
            for k in ("chg", "dchg"):
                dv, tau, resid = d[(s, k)]
                f += [dv, tau, resid]
        f = np.array(f, dtype=float)
        # cross-SOC consistency of dv (ohmic-ish): std across the 3 SOCs per direction
        f = np.append(f, [np.nanstd([d[(s, "chg")][0] for s in (20, 50, 90)]),
                          np.nanstd([d[(s, "dchg")][0] for s in (20, 50, 90)])])
        pulse_rows.append(f); pulse_cells.append(c); pulse_rpts.append(r)
    Xp = np.array(pulse_rows); cp = np.array(pulse_cells); rp = np.array(pulse_rpts)

    # monotonicity per cell
    mono = {}
    for j in range(Xp.shape[1]):
        rhos = []
        for c in np.unique(cp):
            m = cp == c
            if m.sum() < 10:
                continue
            col = Xp[m, j]
            if np.nanstd(col) < 1e-12:
                continue
            rho, _ = spearmanr(rp[m], col)
            if not np.isnan(rho):
                rhos.append(abs(rho))
        mono[f"f{j}"] = float(np.median(rhos)) if rhos else None

    # ---- prefix descriptors from CC discharge curves ----
    dc = load(CC)
    cc_cell = dc["cell_id"]; cc_rpt = dc["rpt"]; ccV = dc["voltage"]
    ccq = dc["q_dchg"]; ccs = dc["soh"]
    rows, cells, rpts = [], [], []
    for i in range(len(cc_cell)):
        v = np.asarray(ccV[i], dtype=float)
        if v.size < 100:
            continue
        bins = np.array_split(v, 50)
        f = [b.mean() for b in bins] + [v.mean(), v.std(), v.min(), v.max(),
                                        v[-1] - v[0], float(ccq[i]), float(ccs[i])]
        rows.append(f); cells.append(int(cc_cell[i])); rpts.append(int(cc_rpt[i]))
    Xc = np.array(rows); cc = np.array(cells); rc = np.array(rpts)

    # ---- eta^2 at a fixed early RPT (rpt == 0), both feature sets ----
    mp = rp == 0
    mc = rc == 0
    res = dict(
        n_pulse_rows=int(Xp.shape[0]), n_prefix_rows=int(Xc.shape[0]),
        n_cells=int(len(np.unique(cp))),
        monotonicity_median_abs_rho=mono,
        eta2_pulse=None, eta2_prefix=None,
    )
    if mp.sum() > 20:
        gp = np.array([gmap[c] for c in cp[mp]])
        e = eta2(Xp[mp], gp)
        res["eta2_pulse"] = dict(n=int(mp.sum()), dim=int(Xp.shape[1]),
                                 mean=float(np.nanmean(e)), max=float(np.nanmax(e)),
                                 top=sorted(np.nan_to_num(e).tolist(), reverse=True)[:5])
    if mc.sum() > 20:
        gc = np.array([gmap[c] for c in cc[mc]])
        e = eta2(Xc[mc], gc)
        res["eta2_prefix"] = dict(n=int(mc.sum()), dim=int(Xc.shape[1]),
                                  mean=float(np.nanmean(e)), max=float(np.nanmax(e)),
                                  top=sorted(np.nan_to_num(e).tolist(), reverse=True)[:5])

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("done")

main()
