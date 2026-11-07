# -*- coding: utf-8 -*-
"""Option D: does the 2-RC relaxation parameter family keep its degradation
trend across 24 operating conditions (6 temperatures x 4 C-rates)?

Criterion (pre-registered, from the decision proxy):
  * per condition: median |rho(param, SOH)| over its cells
  * sign consistency: fraction of conditions sharing the majority sign
  * FAILURE LINE: sign consistency < 75% -> negative result, no subset tuning
"""
import os, json, numpy as np, warnings, itertools
from scipy.optimize import curve_fit
from scipy.stats import spearmanr
import openpyxl
warnings.filterwarnings("ignore")

D = r"E:\桌面\rul\data\external\bayreuth\_parsed"
XLSX = r"E:\桌面\rul\data\external\bayreuth\extracted_degradation_metrics.xlsx"
OUT = r"C:\Users\Administrator\AppData\Local\Temp\bayreuth_D.json"

def meta():
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))[1:]
    m = {}
    for r in rows:
        if not r[1]: continue
        m[str(r[1])] = (float(r[2]), float(r[3]))
    return m

def fit2rc(t, v):
    if len(t) < 100: return None
    t = np.asarray(t, float); v = np.asarray(v, float)
    c0 = float(v[-1]); a0 = float(v[0] - v[-1])
    p0 = [c0, a0*0.6, 0.01, a0*0.4, 0.5]
    lo = [v.min()-0.2, -2.0, 1e-4, -2.0, 0.02]
    hi = [v.max()+0.2, 2.0, 0.5, 2.0, 6.0]
    try:
        popt, _ = curve_fit(lambda t, c, a1, t1, a2, t2: c + a1*np.exp(-t/t1) + a2*np.exp(-t/t2),
                            t, v, p0=p0, bounds=(lo, hi), maxfev=6000)
        return [float(x) for x in popt]
    except Exception:
        return None

NAMES = ["c", "a1", "tau1", "a2", "tau2"]

def main():
    m = meta()
    per_cond = {}
    detail = {}
    for f in sorted(os.listdir(D)):
        if not f.endswith(".npz"): continue
        cell = f[:-4]
        if cell not in m: continue
        T, C = m[cell]
        z = np.load(os.path.join(D, f), allow_pickle=True)
        cap = z["cap"]; cap_cyc = z["cap_cycle"]
        rel_v = z["rel_v"]; rel_t = z["rel_t"]; rel_cyc = z["rel_cycle"]
        if len(cap) < 20 or len(rel_v) < 20: continue
        cap0 = float(np.median(cap[1:6])) if len(cap) > 6 else float(cap[0])
        params, sohs = [], []
        for i in range(len(rel_v)):
            p = fit2rc(rel_t[i], rel_v[i])
            if p is None: continue
            # SOH at the cycle preceding this rest
            k = int(rel_cyc[i])
            sel = cap_cyc <= k
            if sel.sum() == 0: continue
            soh = float(cap[sel][-1]) / cap0 * 100.0
            params.append(p); sohs.append(soh)
        if len(params) < 15: continue
        P = np.array(params); S = np.array(sohs)
        rhos = {}
        for j, nm in enumerate(NAMES):
            if np.std(P[:, j]) < 1e-12: rhos[nm] = np.nan; continue
            rho, _ = spearmanr(S, P[:, j])
            rhos[nm] = float(rho)
        rhos["dV"] = float(spearmanr(S, np.abs(P[:, 1]) + np.abs(P[:, 3]))[0]) if np.std(np.abs(P[:,1])+np.abs(P[:,3])) > 1e-12 else np.nan
        key = (T, C)
        per_cond.setdefault(key, []).append(rhos)
        detail[cell] = dict(T=T, C=C, n=int(len(params)), rho=rhos)

    print("cells contributing:", len(detail), " conditions covered:", len(per_cond), flush=True)
    res = {"n_cells": len(detail), "n_conditions": len(per_cond),
           "condition_cells": {str(k): len(v) for k, v in per_cond.items()}, "params": {}}
    for nm in NAMES + ["dV"]:
        meds = []
        for k, lst in per_cond.items():
            vals = [d[nm] for d in lst if nm in d and np.isfinite(d[nm])]
            if vals: meds.append((k, float(np.median(vals))))
        if len(meds) < 6: continue
        signs = [np.sign(v) for _, v in meds]
        pos = sum(1 for s in signs if s > 0); neg = sum(1 for s in signs if s < 0)
        maj = max(pos, neg) / len(signs)
        res["params"][nm] = dict(
            n_cond=len(meds),
            sign_consistency=round(maj, 3),
            median_abs_rho=round(float(np.median([abs(v) for _, v in meds])), 3),
            majority_sign="+" if pos >= neg else "-",
            per_condition={str(k): round(v, 3) for k, v in meds})
        print("%-5s n_cond=%d sign=%.2f med|rho|=%.3f" % (nm, len(meds), maj, res["params"][nm]["median_abs_rho"]), flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"summary": res, "detail": detail}, f, ensure_ascii=False, indent=1)
    print("done")

main()
