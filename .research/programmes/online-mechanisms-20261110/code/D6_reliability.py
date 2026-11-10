# -*- coding: utf-8 -*-
"""D6 · The moderator that replaces "schedule density": rate-estimate reliability.

D1 killed the schedule-density story. D4/D5 ask whether extra observations add
anything at all. This script tests WHY they would or would not, with a mechanism
that is measurable from visible data and testable WITHIN one cohort.

Mechanism. EOL prediction needs the degradation RATE. A two-point estimate of the
rate is already unbiased; extra observations only shrink its standard error. So
the marginal value of the k-th observation is governed by how much of the spread
in estimated rates is estimation noise rather than real between-cell differences:

    reliability ratio   rho_c = s2_between / (s2_between + s2_est)

    s2_between : variance of the per-cell OLS slope WITHIN condition c
                 (real heterogeneity in how fast these cells fade)
    s2_est     : mean squared standard error of that slope at k=2
                 (how much of the spread is measurement noise)

Prediction (falsifiable):  conditions with LOW rho (noisy, short window) must gain
from extra observations; conditions with HIGH rho must not. If the gain from
k=2 -> k=6 is uncorrelated with (1 - rho) across conditions, the mechanism is
wrong and the flat average curve has no explanation.

Everything here uses quantities visible at prediction time except the gain, which
is the outcome. Unit of inference is the CONDITION.

Writes protocol/D6_reliability.csv / .json
"""
import os
import json

import numpy as np
import pandas as pd
from scipy import stats

import D_common as C
from D4_budget_curve import describe, rows_for, thin

OUT = C.PROTO
K_LO, K_HI = 2, 6


def slopes_at_k(rows, k):
    """Per (cell, age) OLS slope and its SE from k observations."""
    rec = []
    for r in rows:
        xv, sv = thin(r["xv"], r["sv"], k)
        d = describe(xv, sv, r["age"])
        rec.append(dict(cell=r["cell"], cond=r["cond"], age=r["age"],
                        slope=d["ols_slope"], se=d["ols_se_slope"],
                        span=float(xv[-1] - xv[0])))
    return pd.DataFrame(rec)


def per_cond_gain(rows, stress, k_lo, k_hi):
    """Per-condition change in |log err| of the health arm from k_lo to k_hi."""
    out = {}
    for k in (k_lo, k_hi):
        Q = []
        for r in rows:
            xv, sv = thin(r["xv"], r["sv"], k)
            span = float(xv[-1] - xv[0])
            d = dict(cell=r["cell"], cond=r["cond"], age=r["age"],
                     logt=float(np.log(r["age"])), n_obs=int(len(xv)), span=span,
                     y=float(np.log(r["U"])))
            d.update(describe(xv, sv, r["age"]))
            if stress is not None:
                d["DoD"] = float(stress.loc[r["cond"], "DoD"])
                d["cc"] = float(stress.loc[r["cond"], "charge_C"])
                d["cd"] = float(stress.loc[r["cond"], "discharge_C"])
            Q.append(d)
        Q = pd.DataFrame(Q)
        base = C.AGE + (C.STRESS if stress is not None else [])
        pb = C.fit_loco(Q, base)
        ph = C.fit_loco(Q, base + ["soh_first", "soh_last"])
        ok = np.isfinite(pb) & np.isfinite(ph)
        out[k] = C.cond_macro(np.abs(ph[ok] - Q.y.values[ok]), Q.cond.values[ok])
    idx = out[k_lo].index.intersection(out[k_hi].index)
    return out[k_lo].loc[idx], out[k_hi].loc[idx]


def analyse(name, cells, ages, stress, k_max):
    print("\n" + "=" * 88)
    print("%s · reliability of the rate estimate as the moderator of marginal value" % name)
    print("=" * 88)
    rows = rows_for(cells, ages, stress, k_max)
    if not rows:
        print("  no rows"); return []
    print("  cohort: %d cells / %d conds / %d rows" % (
        len({r["cell"] for r in rows}), len({r["cond"] for r in rows}), len(rows)))

    # reliability computed at k=2, i.e. from what a two-inspection deployment sees
    s2 = slopes_at_k(rows, K_LO)
    g = s2.groupby("cond")
    agg = g.agg(slope_var=("slope", "var"), slope_mean=("slope", "mean"),
                se2=("se", "mean"), n=("slope", "size"), span=("span", "median"))
    # mean squared SE: at k=2 se is undefined (0 residual dof), so estimate the
    # measurement noise from the k>=3 fits and propagate to k=2 analytically.
    s3 = slopes_at_k(rows, 4)
    se4 = s3.groupby("cond").se.mean() ** 2            # var of slope at k=4
    # slope SE scales as 1/sqrt(k) at fixed window, so var(4) = var(2)/2
    agg["s2_est"] = (se4 * 2.0).reindex(agg.index)
    agg["s2_between"] = agg.slope_var - agg.s2_est
    agg["s2_between"] = agg.s2_between.clip(lower=0.0)
    agg["rho"] = agg.s2_between / (agg.s2_between + agg.s2_est).replace(0, np.nan)

    e_lo, e_hi = per_cond_gain(rows, stress, K_LO, K_HI)
    idx = agg.index.intersection(e_lo.index)
    T = pd.DataFrame(dict(rho=agg.loc[idx, "rho"],
                          s2_est=agg.loc[idx, "s2_est"],
                          s2_between=agg.loc[idx, "s2_between"],
                          n_cells=agg.loc[idx, "n"],
                          span=agg.loc[idx, "span"],
                          err_k2=e_lo.loc[idx], err_k6=e_hi.loc[idx]))
    T["gain_pct"] = 100.0 * (T.err_k6 / T.err_k2 - 1.0)
    T["unreliability"] = 1.0 - T.rho
    T = T.reset_index().rename(columns={"index": "cond"})
    T.insert(0, "cohort", name)

    print("  rho: median %.3f  IQR [%.3f, %.3f]  (n=%d conditions)" % (
        T.rho.median(), T.rho.quantile(.25), T.rho.quantile(.75), len(T)))
    print("  gain k2->k6: median %+.1f%%  IQR [%+.1f, %+.1f]" % (
        T.gain_pct.median(), T.gain_pct.quantile(.25), T.gain_pct.quantile(.75)))

    r, p = stats.spearmanr(T.unreliability, T.gain_pct)
    print("\n  HYPOTHESIS: low reliability -> extra observations help (gain more negative)")
    print("  spearman(1-rho, gain) = %+.3f   p = %.3g   n = %d conditions" % (r, p, len(T)))
    q = pd.qcut(T.unreliability, 4, labels=False, duplicates="drop")
    tab = T.groupby(q).agg(rho_lo=("rho", "min"), rho_hi=("rho", "max"),
                           n=("gain_pct", "size"), gain=("gain_pct", "median"))
    print("  %-3s %-8s %-8s %-4s %s" % ("q", "rho_lo", "rho_hi", "n", "median gain k2->k6"))
    for i, row in tab.iterrows():
        print("  %-3d %-8.3f %-8.3f %-4d %+.1f%%" % (i, row.rho_lo, row.rho_hi, row.n, row.gain))
    if len(tab) >= 2:
        a, b = tab.gain.iloc[0], tab.gain.iloc[-1]
        print("  -> most-reliable quartile %+.1f%% vs least-reliable %+.1f%% (difference %+.1f pp)" % (
            a, b, b - a))
    return T.to_dict("records")


def main():
    print("=" * 88)
    print("D6 · does rate-estimate reliability explain the marginal value of observations?")
    print("=" * 88)
    isu = C.load_isu(); S = C.load_stress()
    uc = C.load_uconn()
    rows = analyse("ISU", isu, (49, 63), S, k_max=K_HI)
    rows += analyse("UConn", uc, (600, 1000), None, k_max=K_HI)
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(OUT, "D6_reliability.csv"), index=False)
    json.dump(rows, open(os.path.join(OUT, "D6_reliability.json"), "w"), indent=1)
    print("\nwrote D6_reliability.csv / .json")


if __name__ == "__main__":
    main()
