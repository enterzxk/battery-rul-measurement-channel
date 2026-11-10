# -*- coding: utf-8 -*-
"""D3 · The inspection-budget experiment, done correctly this time.

C1 tried to answer this and was withdrawn: harness.py thinned the query table but
arms.py read the FULL history, so the arms never saw the thinning. C_landmark_both
then coupled "number of observations" to "life fraction observed", which is the
population/axis confound that killed it.

The design that avoids both defects:

  * query time t is FIXED and absolute (visible at prediction time, never built
    from L);
  * the evaluated cell set is FIXED: a cell enters only if it has at least
    K_MAX observations by t and t < L, and then it is evaluated at EVERY k;
  * only k changes. Thinning keeps the first and last available observation, so
    the span is identical at every k. Nothing else moves.

So the only thing that varies across the sweep is "how many inspections were
bought inside an unchanged window". That is the deployment decision.

Arms at each k:  age+stress  vs  age+stress+health(k)

Reports, for each (cohort, t, k): cohort size, mean amplitude, both MAEs, the
paired condition-cluster CI, and inspections-per-observation cost accounting.

Writes protocol/D3_budget_curve.csv / .json / D3_predictions.csv
"""
import os
import json

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO
K_GRID = (2, 3, 4, 5, 6, 8)


def thin(xv, sv, k):
    """Keep k observations evenly spaced over the available index range.

    First and last are always kept, so span(x_thin) == span(x_full) exactly.
    Thinning is therefore a pure reduction in the number of samples, with the
    observation window held fixed.
    """
    n = len(xv)
    if k >= n:
        return xv, sv
    idx = np.unique(np.round(np.linspace(0, n - 1, k)).astype(int))
    return xv[idx], sv[idx]


def rows_for(cells, ages, stress, k_max):
    """Fixed-cohort query rows: a cell is kept only if it survives every k."""
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
                continue                      # fixed cohort: needs K_MAX obs
            xv, sv = s["x"][vis], s["soh"][vis]
            recs.append(dict(cell=c, cond=s["cond"], age=float(t), xv=xv, sv=sv,
                             L=float(s["L"]), life_frac=float(t / s["L"])))
    return recs


def eval_k(rows, k, stress):
    Q = []
    for r in rows:
        xv, sv = thin(r["xv"], r["sv"], k)
        span = float(xv[-1] - xv[0])
        d = dict(cell=r["cell"], cond=r["cond"], age=r["age"], logt=float(np.log(r["age"])),
                 n_obs=int(len(xv)), span=span,
                 cadence=(span / (len(xv) - 1)) if len(xv) > 1 else 0.0,
                 soh_last=float(sv[-1]), soh0=float(sv[0]),
                 slope=float((sv[-1] - sv[0]) / max(span, 1e-12)),
                 y=float(np.log(r["U"])) if "U" in r else np.nan,
                 amp=float(1.0 - sv[-1]), life_frac=r["life_frac"], L=r["L"])
        if stress is not None:
            d["DoD"] = float(stress.loc[r["cond"], "DoD"])
            d["cc"] = float(stress.loc[r["cond"], "charge_C"])
            d["cd"] = float(stress.loc[r["cond"], "discharge_C"])
        Q.append(d)
    Q = pd.DataFrame(Q)
    base = C.AGE + (C.STRESS if stress is not None else [])
    pb = C.fit_loco(Q, base)
    ph = C.fit_loco(Q, base + C.HEALTH)
    ok = np.isfinite(pb) & np.isfinite(ph)
    cb = C.cond_macro(np.abs(pb[ok] - Q.y.values[ok]), Q.cond.values[ok])
    ch = C.cond_macro(np.abs(ph[ok] - Q.y.values[ok]), Q.cond.values[ok])
    g, lo, hi, p = C.paired_gain(cb, ch)
    out = dict(k=k, n_cells=int(Q[ok].cell.nunique()), n_cond=int(len(cb)),
               n_queries=int(ok.sum()), span_med=float(Q[ok].span.median()),
               amp_med=float(Q[ok].amp.median()),
               life_frac_med=float(Q[ok].life_frac.median()),
               base=float(cb.mean()), health=float(ch.mean()),
               gain_pct=g, ci_lo=lo, ci_hi=hi, wilcoxon_p=p)
    Q2 = Q.loc[ok].copy()
    Q2["pred_base"] = pb[ok]
    Q2["pred_health"] = ph[ok]
    Q2["k"] = k
    return out, Q2


def sweep(name, cells, ages, stress, k_max):
    print("\n" + "=" * 78)
    print("%s · fixed cohort needs >= %d observations at every query age" % (name, k_max))
    print("=" * 78)
    rows = rows_for(cells, ages, stress, k_max)
    if not rows:
        print("  no rows"); return [], None
    # attach U (upper crossing) which rows_for did not copy
    for r in rows:
        r["U"] = cells[r["cell"]]["U"]
    print("  cohort: %d cells / %d conditions / %d (cell,age) rows" % (
        len({r["cell"] for r in rows}), len({r["cond"] for r in rows}), len(rows)))
    print("  %-3s %-7s %-6s %-7s %-8s %-8s %-9s %-9s %-22s %s" % (
        "k", "cells", "conds", "spanMed", "ampMed", "lifeFrac", "base", "health",
        "gain [95% CI]", "p"))
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
        print("  %-3d %-7d %-6d %-7.1f %-8.4f %-8.3f %-9.4f %-9.4f %+6.1f%% [%6.1f,%6.1f] %.1e" % (
            r["k"], r["n_cells"], r["n_cond"], r["span_med"], r["amp_med"],
            r["life_frac_med"], r["base"], r["health"], r["gain_pct"],
            r["ci_lo"], r["ci_hi"], r["wilcoxon_p"]))
    if len(out) >= 2:
        a, b = out[0], out[-1]
        print("  marginal value of k=%d over k=%d (health arm): %+.1f%% ; base arm %+.1f%%" % (
            b["k"], a["k"], 100 * (b["health"] / a["health"] - 1),
            100 * (b["base"] / a["base"] - 1)))
    return out, (pd.concat(preds, ignore_index=True) if preds else None)


def main():
    print("=" * 78)
    print("D3 · inspection budget: how many observations, at a fixed window?")
    print("=" * 78)
    uc = C.load_uconn()
    isu = C.load_isu()
    S = C.load_stress()

    # UConn: query at fixed cycles; median obs at 300 cycles was 9, so K_MAX=6.
    r1, p1 = sweep("UConn", uc, (600, 1000), None, k_max=6)
    # ISU: median obs at 63 days was 6, so K_MAX=5 keeps a usable cohort.
    r2, p2 = sweep("ISU", isu, (35, 49, 63), S, k_max=5)

    T = pd.DataFrame(r1 + r2)
    T.to_csv(os.path.join(OUT, "D3_budget_curve.csv"), index=False)
    json.dump(T.to_dict("records"), open(os.path.join(OUT, "D3_budget_curve.json"), "w"), indent=1)
    ps = [p for p in (p1, p2) if p is not None]
    if ps:
        pd.concat(ps, ignore_index=True).to_csv(
            os.path.join(OUT, "D3_predictions.csv"), index=False)
    print("\nwrote D3_budget_curve.csv / .json / D3_predictions.csv")


if __name__ == "__main__":
    main()
