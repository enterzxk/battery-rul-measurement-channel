# -*- coding: utf-8 -*-
"""Corrected pipeline: ECM window fixed (start at ip+1, seconds), both label units,
both inference units, plus the baselines the auditor found missing."""
import pickle, numpy as np, json, time, warnings
from scipy.optimize import curve_fit
from sklearn.ensemble import HistGradientBoostingRegressor
warnings.filterwarnings("ignore")
P = r"E:\桌面\rul\data\external\uconn\data_slowpulse_1.pkl"
C = r"E:\桌面\rul\data\external\uconn\data_cc_1.pkl"
OUT = r"C:\Users\Administrator\AppData\Local\Temp\v2_main.json"
DT = 1.0   # seconds per sample (external evidence; flagged unverified)

def load(p):
    with open(p, "rb") as f: return pickle.load(f, encoding="latin1")

def ecm_fixed(v, kind):
    """Fit from the sample AFTER the current-carrying extremum; x in seconds."""
    v = np.asarray(v, float)
    ip = int(np.argmax(v)) if kind == "chg" else int(np.argmin(v))
    seg = v[ip + 1:]                      # <-- fix: exclude the current-carrying point
    if seg.size < 20: return (np.nan,)*5
    x = np.arange(seg.size, dtype=float) * DT
    y = seg
    p0 = [float(y[-1]), float(y[0]-y[-1])*0.7, 2.0, float(y[0]-y[-1])*0.3, 20.0]
    lo = [y.min()-0.2, -0.6, 0.5, -0.6, 5.0]
    hi = [y.max()+0.2,  0.6, 60.0, 0.6, 60.0]   # upper bound <= relaxation window
    try:
        popt, _ = curve_fit(lambda x, c, a1, t1, a2, t2: c + a1*np.exp(-x/t1) + a2*np.exp(-x/t2),
                            x, y, p0=p0, bounds=(lo, hi), maxfev=6000)
        return tuple(float(p) for p in popt)
    except Exception:
        return (np.nan,)*5

def desc(v, kind):
    v = np.asarray(v, float); v0 = v[0]
    ip = int(np.argmax(v)) if kind == "chg" else int(np.argmin(v))
    peak = v[ip]; dv = abs(peak - v0)
    tau = np.nan
    if dv > 1e-6:
        t = peak - 0.632*(peak - v0); a = v[ip:]
        idx = np.where(a <= t)[0] if kind == "chg" else np.where(a >= t)[0]
        if len(idx): tau = float(idx[0])
    resid = (v[-1]-peak)/(v0-peak) if abs(v0-peak) > 1e-9 else np.nan
    slope = float(v[min(ip+1, len(v)-1)] - v[ip])
    return dv, tau, resid, slope, ip

def build():
    dp = load(P)
    cell, rpt, soc, pt, V = dp["cell_id"], dp["rpt"], dp["soc"], dp["pulse_type"], dp["voltage"]
    soh, ncyc = dp["soh"], dp["num_cycles"]
    gmap = {int(c): int(g) for c, g in zip(dp["cell_id"], dp["group_id"])}
    E, D = {}, {}
    t0 = time.time()
    for i in range(len(cell)):
        k = (int(cell[i]), int(rpt[i]), int(soc[i]), str(pt[i]))
        v = np.asarray(V[i], float)
        E[k] = ecm_fixed(v, k[3]); D[k] = desc(v, k[3])
    print("ecm refit %.1fs" % (time.time()-t0), flush=True)

    segm, smap = {}, {}
    for c, r, y, s in zip(cell, rpt, ncyc, soh):
        segm.setdefault((int(c), int(r)), []).append(float(y))
        smap.setdefault((int(c), int(r)), []).append(float(s))
    segm = {k: float(np.nanmedian(v)) for k, v in segm.items()}
    smap = {k: float(np.nanmedian(v)) for k, v in smap.items()}

    cum, eol_rpt, eol_cum = {}, {}, {}
    for c in np.unique(cell):
        rr = sorted([r for (cc, r) in segm if cc == c])
        vals, last = [], 0.0
        for r in rr:
            v = segm[(c, r)]
            if not np.isfinite(v): v = last
            last = v; vals.append(v)
        cs = np.cumsum(vals)
        for r, v in zip(rr, cs): cum[(c, r)] = float(v)
        ss = np.array([smap[(c, r)] for r in rr])
        hit = np.where(ss <= 80.0)[0]
        if len(hit): eol_rpt[c] = rr[hit[0]]; eol_cum[c] = float(cs[hit[0]])

    keys = sorted({(k[0], k[1]) for k in E})
    rows = []
    for (c, r) in keys:
        fe, fd, ok = [], [], True
        for s in (20, 50, 90):
            for kk in ("chg", "dchg"):
                q = (c, r, s, kk)
                if q not in E: ok = False; break
                fe += list(E[q]); fd += list(D[q][:3])
            if not ok: break
        if not ok: continue
        fd += [np.nanstd([D[(c, r, s, "chg")][0] for s in (20, 50, 90)]),
               np.nanstd([D[(c, r, s, "dchg")][0] for s in (20, 50, 90)])]
        rows.append((c, r, fe, fd))
    cells = np.array([x[0] for x in rows]); rpts = np.array([x[1] for x in rows])
    Ec = np.array([x[2] for x in rows]); Dc = np.array([x[3] for x in rows])
    sh = np.array([smap[(c, r)] for c, r in zip(cells, rpts)])
    grp = np.array([gmap[c] for c in cells])
    cumv = np.array([cum[(c, r)] for c, r in zip(cells, rpts)])

    dc = load(C)
    cc_cell, cc_rpt, ccV = dc["cell_id"], dc["rpt"], dc["voltage"]
    dc_q, dc_s = dc["q_dchg"], dc["soh"]
    buckets = {}
    for i in range(len(cc_cell)): buckets.setdefault((int(cc_cell[i]), int(cc_rpt[i])), []).append(i)
    pf, qv = {}, {}
    for k, idxs in buckets.items():
        idxs = sorted(idxs, key=lambda i: float(np.mean(ccV[i])))
        curve = np.concatenate([np.asarray(ccV[i], float) for i in idxs])
        bins = np.array_split(curve, 50)
        pf[k] = [b.mean() for b in bins] + [curve.mean(), curve.std(), curve.min(), curve.max()]
        qv[k] = (float(dc_q[idxs[0]]), float(dc_s[idxs[0]]))
    keep = [i for i, (c, r) in enumerate(zip(cells, rpts)) if (c, r) in pf]
    A = np.array([pf[(cells[i], rpts[i])] for i in keep])
    Q = np.array([qv[(cells[i], rpts[i])] for i in keep])
    cells, rpts, Ec, Dc, sh, grp, cumv = (x[keep] for x in (cells, rpts, Ec, Dc, sh, grp, cumv))

    ok = np.array([(c in eol_rpt) and r <= eol_rpt[c] for c, r in zip(cells, rpts)])
    return dict(A=A[ok], E=Ec[ok], D=Dc[ok], Q=Q[ok], sh=sh[ok], cells=cells[ok],
                rpts=rpts[ok], grp=grp[ok], cum=cumv[ok], eol_rpt=eol_rpt, eol_cum=eol_cum)

def cell_macro(y, p, c):
    return float(np.mean([np.mean(np.abs(y[c == k] - p[c == k])) for k in np.unique(c)]))

def predict(X, y, cells, grp, protocol):
    pred = np.full(len(y), np.nan)
    folds = np.unique(grp) if protocol == "logo" else np.unique(cells)
    for f in folds:
        te = grp == f if protocol == "logo" else cells == f
        tr = ~te
        if tr.sum() < 100 or te.sum() == 0: continue
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
        m.fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
    return pred

def boot_cell(y, p, cells, B=5000):
    rng = np.random.default_rng(0)
    per = {c: np.abs(y[cells == c] - p[cells == c]) for c in np.unique(cells)}
    cs = np.array(sorted(per))
    d = np.array([per[c].mean() for c in cs])
    bs = np.array([np.mean(rng.choice(d, len(d), replace=True)) for _ in range(B)])
    return [round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)]

def boot_cond(y, p, cells, grp, B=5000):
    rng = np.random.default_rng(0)
    per = {}
    for g in np.unique(grp):
        m = grp == g
        per[g] = float(np.mean([np.mean(np.abs(y[m][cells[m] == c] - p[m][cells[m] == c]))
                                for c in np.unique(cells[m])]))
    gs = np.array(sorted(per)); d = np.array([per[g] for g in gs])
    bs = np.array([np.mean(rng.choice(d, len(d), replace=True)) for _ in range(B)])
    return [round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)]

def main():
    t0 = time.time(); d = build()
    A, E, D, Q, sh = d["A"], d["E"], d["D"], d["Q"], d["sh"]
    cells, rpts, grp = d["cells"], d["rpts"], d["grp"]
    y_rpt = np.array([d["eol_rpt"][c] - r for c, r in zip(cells, rpts)], float)
    y_cyc = np.array([d["eol_cum"][c] - v for c, v in zip(cells, d["cum"])], float)
    y_frac = np.array([1.0 - r / d["eol_rpt"][c] for c, r in zip(cells, rpts)], float)
    print("rows %d cells %d groups %d" % (len(y_rpt), len(np.unique(cells)), len(np.unique(grp))), flush=True)
    print("corr(rpt,cyc) row-level = %.3f" % np.corrcoef(y_rpt, y_cyc)[0,1], flush=True)
    print("ecm finite rate: %.4f" % np.mean(np.isfinite(E)), flush=True)
    t1 = E[:, [2,7,12,17,22,27]]; t2 = E[:, [4,9,14,19,24,29]]
    a1 = E[:, [1,6,11,16,21,26]]; a2 = E[:, [3,8,13,18,23,28]]
    print("tau1: min %.2f med %.2f max %.2f | at lower bound %.1f%%" % (
        np.nanmin(t1), np.nanmedian(t1), np.nanmax(t1), 100*np.mean(t1 <= 0.51)), flush=True)
    print("tau2: min %.2f med %.2f max %.2f" % (np.nanmin(t2), np.nanmedian(t2), np.nanmax(t2)), flush=True)
    print("a1 negative: %.1f%%  a2 negative: %.1f%%" % (100*np.mean(a1 < 0), 100*np.mean(a2 < 0)), flush=True)

    sets = {
        "A_curve": A,
        "A_curve+C_ecm": np.hstack([A, E]),
        "A_curve+C_desc": np.hstack([A, D]),
        "A_prefix": np.hstack([A, Q]),
        "C_ecm_only": E,
        "rpt_only": np.array([rpts], float).T,
        "soh_only": np.array([sh], float).T,
        "soh+rpt": np.column_stack([sh, rpts]).astype(float),
    }
    res = {"n_rows": int(len(y_rpt)), "n_cells": int(len(np.unique(cells))),
           "n_groups": int(len(np.unique(grp))),
           "corr_row_rpt_cyc": round(float(np.corrcoef(y_rpt, y_cyc)[0,1]), 3),
           "targets": {}}
    for tname, y in [("rpt", y_rpt), ("cycle", y_cyc)]:
        res["targets"][tname] = {}
        for nm, X in sets.items():
            p = predict(X, y, cells, grp, "logo")
            m = ~np.isnan(p)
            val = cell_macro(y[m], p[m], cells[m])
            res["targets"][tname][nm] = round(val, 3)
            print(tname, nm, round(val, 3), flush=True)
        b = res["targets"][tname]["A_curve"]; g = res["targets"][tname]["A_curve+C_ecm"]
        res["targets"][tname]["gain_pct"] = round((b - g) / b * 100, 2)
        res["targets"][tname]["gain_abs"] = round(b - g, 3)

    # inference for the headline pair on the cycle target
    y = y_cyc
    p0 = predict(sets["A_curve"], y, cells, grp, "logo")
    p1 = predict(sets["A_curve+C_ecm"], y, cells, grp, "logo")
    m = ~np.isnan(p0) & ~np.isnan(p1)
    d_cell = np.abs(y[m] - p1[m]).mean() - np.abs(y[m] - p0[m]).mean()
    rng = np.random.default_rng(0)
    per = {c: (np.abs(y[m][cells[m]==c]-p1[m][cells[m]==c]).mean() - np.abs(y[m][cells[m]==c]-p0[m][cells[m]==c]).mean())
           for c in np.unique(cells[m])}
    cs = np.array(sorted(per)); dv = np.array([per[c] for c in cs])
    bs = np.array([np.mean(rng.choice(dv, len(dv), replace=True)) for _ in range(5000)])
    perG = {}
    for g in np.unique(grp[m]):
        mm = grp[m] == g
        perG[g] = float(np.mean([np.abs(y[m][mm][cells[m][mm]==c]-p1[m][mm][cells[m][mm]==c]).mean()
                                 - np.abs(y[m][mm][cells[m][mm]==c]-p0[m][mm][cells[m][mm]==c]).mean()
                                 for c in np.unique(cells[m][mm])]))
    gs = np.array(sorted(perG)); dg = np.array([perG[g] for g in gs])
    bg = np.array([np.mean(rng.choice(dg, len(dg), replace=True)) for _ in range(5000)])
    res["headline_cycle"] = dict(
        delta=round(float(d_cell), 3),
        cell_ci=[round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)],
        cond_ci=[round(float(np.percentile(bg, 2.5)), 3), round(float(np.percentile(bg, 97.5)), 3)],
        groups_improved=int((dg < 0).sum()), n_groups=int(len(dg)))
    res["elapsed_s"] = round(time.time()-t0, 1)
    with open(OUT, "w", encoding="utf-8") as f: json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res["headline_cycle"], indent=1))
    print("done %.0fs" % res["elapsed_s"])

main()
