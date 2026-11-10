# -*- coding: utf-8 -*-
"""D4 · The inspection-budget curve, with descriptors that can actually use k.

D3 v1 was degenerate: the inherited "health" features are soh_last, soh0 and the
two-point slope. Thinning that keeps the first and last observation leaves all
three EXACTLY unchanged, so every k produced identical numbers. That is not a
bug in the thinning, it is a property of the descriptor set: C's "health
information" was a two-point summary of the trajectory, not a trajectory.

Here the health descriptors are estimated from all k retained observations:
OLS slope, its standard error, R^2, residual sd, the fitted SOH at the query
time, a quadratic coefficient, and the fractional loss. With k=2 these collapse
to the old two-point summary, so the k=2 column is a direct bridge back to C.

Design (unchanged, and it is the point):
  * query time t is fixed and absolute, never built from L;
  * the evaluated cell set is fixed: a cell enters only if it has >= K_MAX
    observations by t and t < L, and is then evaluated at EVERY k;
  * thinning keeps the first and last available observation, so the observation
    window (span) is identical at every k.

Two metrics are reported:
  symmetric    : condition-macro mean |log error|      (comparable with C)
  asymmetric   : w_over*max(0,e) + w_under*max(0,-e)   (a DECISION loss, e =
                 log(Lhat) - log(L); w_over=3 penalises predicting a cell as
                 longer-lived than it is, which is the dangerous direction)

Writes protocol/D4_budget_curve.csv / .json / D4_predictions.csv
"""
import os
import json

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO
K_GRID = (2, 3, 4, 5, 6, 8)
W_OVER, W_UNDER = 3.0, 1.0

HEALTH_K = ["soh_first", "soh_last", "frac_loss",
            "ols_slope", "ols_se_slope", "ols_r2", "ols_resid_sd",
            "ols_soh_at_t", "ols_curv"]


def thin(xv, sv, k):
    """Keep k observations evenly spaced; first and last always retained."""
    n = len(xv)
    if k >= n:
        return xv, sv
    idx = np.unique(np.round(np.linspace(0, n - 1, k)).astype(int))
    return xv[idx], sv[idx]


def describe(xv, sv, t):
    """Health descriptors estimated from ALL retained observations."""
    k = len(xv)
    d = dict(soh_first=float(sv[0]), soh_last=float(sv[-1]),
             frac_loss=float(1.0 - sv[-1] / max(sv[0], 1e-12)),
             ols_slope=np.nan, ols_se_slope=np.nan, ols_r2=np.nan,
             ols_resid_sd=np.nan, ols_soh_at_t=np.nan, ols_curv=np.nan)
    span = float(xv[-1] - xv[0])
    if k < 2 or span <= 0:
        return d
    X = np.column_stack([np.ones(k), xv])
    beta, *_ = np.linalg.lstsq(X, sv, rcond=None)
    resid = sv - X @ beta
    d["ols_slope"] = float(beta[1])
    d["ols_soh_at_t"] = float(beta[0] + beta[1] * t)
    sst = float(((sv - sv.mean()) ** 2).sum())
    d["ols_r2"] = float(1.0 - (resid @ resid) / sst) if sst > 1e-18 else np.nan
    dof = k - 2
    if dof >= 1:
        s2 = float(resid @ resid) / dof
        d["ols_resid_sd"] = float(np.sqrt(s2))
        sxx = float(((xv - xv.mean()) ** 2).sum())
        d["ols_se_slope"] = float(np.sqrt(s2 / sxx)) if sxx > 1e-18 else np.nan
    if k >= 3:
        X2 = np.column_stack([np.ones(k), xv, xv ** 2])
        b2, *_ = np.linalg.lstsq(X2, sv, rcond=None)
        d["ols_curv"] = float(b2[2])
    return d


def rows_for(cells, ages, stress, k_max):
    recs = []
    for c, s in cells.items():
        if stress is not None and s["cond"] not in stress.index:
            continue
        for t in ages:
            if t <= 0 or t >= s["L"]:
                continue
            vis = s["x"] <= t
            n = int(vis.sum())
            if n < k_max:
                continue                      # fixed cohort across every k
            recs.append(dict(cell=c, cond=s["cond"], age=float(t),
                             xv=s["x"][vis], sv=s["soh"][vis],
                             L=float(s["L"]), U=float(s["U"]),
                             life_frac=float(t / s["L"])))
    return recs


def asym_loss(e):
    return W_OVER * np.maximum(0.0, e) + W_UNDER * np.maximum(0.0, -e)


def eval_k(rows, k, stress):
    Q = []
    for r in rows:
        xv, sv = thin(r["xv"], r["sv"], k)
        span = float(xv[-1] - xv[0])
        d = dict(cell=r["cell"], cond=r["cond"], age=r["age"],
                 logt=float(np.log(r["age"])), n_obs=int(len(xv)), span=span,
                 y=float(np.log(r["U"])), amp=float(1.0 - sv[-1]),
                 life_frac=r["life_frac"])
        d.update(describe(xv, sv, r["age"]))
        if stress is not None:
            d["DoD"] = float(stress.loc[r["cond"], "DoD"])
            d["cc"] = float(stress.loc[r["cond"], "charge_C"])
            d["cd"] = float(stress.loc[r["cond"], "discharge_C"])
        Q.append(d)
    Q = pd.DataFrame(Q)
    base = C.AGE + (C.STRESS if stress is not None else [])
    pb = C.fit_loco(Q, base)
    used = []
    ph = C.fit_loco(Q, base + HEALTH_K, used=used)
    kept = used[0] if used else []
    ok = np.isfinite(pb) & np.isfinite(ph)
    y = Q.y.values[ok]
    eb, eh = pb[ok] - y, ph[ok] - y
    cond = Q.cond.values[ok]
    cb = C.cond_macro(np.abs(eb), cond)
    ch = C.cond_macro(np.abs(eh), cond)
    g, lo, hi, p = C.paired_gain(cb, ch)
    ab = C.cond_macro(asym_loss(eb), cond)
    ah = C.cond_macro(asym_loss(eh), cond)
    ga, alo, ahi, ap = C.paired_gain(ab, ah)
    out = dict(k=int(k), n_cells=int(Q[ok].cell.nunique()), n_cond=int(len(cb)),
               n_queries=int(ok.sum()), span_med=float(Q[ok].span.median()),
               amp_med=float(Q[ok].amp.median()),
               life_frac_med=float(Q[ok].life_frac.median()),
               n_feat_used=len(kept), feats_used="|".join(kept),
               mae_base=float(cb.mean()), mae_health=float(ch.mean()),
               mae_gain=g, mae_lo=lo, mae_hi=hi, mae_p=p,
               dec_base=float(ab.mean()), dec_health=float(ah.mean()),
               dec_gain=ga, dec_lo=alo, dec_hi=ahi, dec_p=ap)
    Q2 = Q.loc[ok].copy()
    Q2["pred_base"] = pb[ok]
    Q2["pred_health"] = ph[ok]
    Q2["k"] = int(k)
    return out, Q2


def sweep(name, cells, ages, stress, k_max):
    print("\n" + "=" * 84)
    print("%s · fixed cohort (>= %d obs at every query age), fixed query times %s"
          % (name, k_max, list(ages)))
    print("=" * 84)
    rows = rows_for(cells, ages, stress, k_max)
    if not rows:
        print("  no rows"); return [], None
    print("  cohort: %d cells / %d conditions / %d (cell,age) rows" % (
        len({r["cell"] for r in rows}), len({r["cond"] for r in rows}), len(rows)))
    print("  %-2s %-6s %-5s %-7s %-7s %-7s %-8s %-8s %-20s | %-8s %-8s %-20s" % (
        "k", "cells", "cond", "spanMed", "ampMed", "lifeF", "MAE_base", "MAE_hlt",
        "MAE gain [95% CI]", "DEC_base", "DEC_hlt", "DEC gain [95% CI]"))
    out, preds = [], []
    for k in K_GRID:
        if k > k_max:
            continue
        r, Q = eval_k(rows, k, stress)
        r["cohort"] = name
        out.append(r)
        if Q is not None:
            Q["cohort"] = name
            preds.append(Q)
        print("  %-2d %-6d %-5d %-7.1f %-7.4f %-7.3f %-8.4f %-8.4f %+6.1f%% [%6.1f,%6.1f] | %-8.4f %-8.4f %+6.1f%% [%6.1f,%6.1f] | feat %d" % (
            r["k"], r["n_cells"], r["n_cond"], r["span_med"], r["amp_med"],
            r["life_frac_med"], r["mae_base"], r["mae_health"], r["mae_gain"],
            r["mae_lo"], r["mae_hi"], r["dec_base"], r["dec_health"],
            r["dec_gain"], r["dec_lo"], r["dec_hi"], r["n_feat_used"]))
    if len(out) >= 2:
        a, b = out[0], out[-1]
        print("  saturation check  k=%d -> k=%d :  MAE %+.1f%%   DECISION %+.1f%%   (health arm)" % (
            a["k"], b["k"], 100 * (b["mae_health"] / a["mae_health"] - 1),
            100 * (b["dec_health"] / a["dec_health"] - 1)))
    return out, (pd.concat(preds, ignore_index=True) if preds else None)


def main():
    print("=" * 84)
    print("D4 · inspection budget, with descriptors estimated from all k observations")
    print("=" * 84)
    uc = C.load_uconn()
    isu = C.load_isu()
    S = C.load_stress()
    r1, p1 = sweep("UConn", uc, (600, 1000), None, k_max=6)
    r2, p2 = sweep("ISU", isu, (49, 63), S, k_max=6)
    T = pd.DataFrame(r1 + r2)
    T.to_csv(os.path.join(OUT, "D4_budget_curve.csv"), index=False)
    json.dump(T.to_dict("records"), open(os.path.join(OUT, "D4_budget_curve.json"), "w"), indent=1)
    ps = [p for p in (p1, p2) if p is not None]
    if ps:
        pd.concat(ps, ignore_index=True).to_csv(
            os.path.join(OUT, "D4_predictions.csv"), index=False)
    print("\nwrote D4_budget_curve.csv / .json / D4_predictions.csv")


if __name__ == "__main__":
    main()
