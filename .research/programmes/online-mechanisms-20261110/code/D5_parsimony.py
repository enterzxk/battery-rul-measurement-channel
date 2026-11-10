# -*- coding: utf-8 -*-
"""D5 · Is the flat budget curve real saturation, or descriptor overfitting?

D4 found that on ISU the health arm's error does not improve from k=2 to k=6
(-23.6% -> -23.8% over age+stress). Two explanations survive:

  H-inf   the second observation already carries the degradation-rate signal, and
          extra observations only re-measure the same thing;
  H-over  extra observations DO carry signal, but each extra observation also
          brings extra descriptors, and the descriptor noise cancels the gain.

They are separable. If H-inf holds, a single parsimonious rate estimator is as
good at k=2 as at k=6. If H-over holds, a single rate estimator must improve with
k, because averaging more points reduces its variance.

Ladder of arms, evaluated on the SAME fixed cohort and the SAME fixed query
times, at every k:

  base      age (+stress)
  two_point base + soh_first + soh_last          <- exactly C's information
  slope     base + ols_slope                     <- one rate estimate from all k
  slope_se  base + ols_slope + ols_se_slope      <- rate + its precision
  full      base + all nine descriptors
  perm      full, with the descriptors shuffled  <- capacity placebo, 3 draws

Writes protocol/D5_parsimony.csv / .json / D5_predictions.csv
"""
import os
import json

import numpy as np
import pandas as pd

import D_common as C
from D4_budget_curve import (HEALTH_K, K_GRID, describe, rows_for, thin)

OUT = C.PROTO
N_PERM = 3

LADDER = {
    "two_point": ["soh_first", "soh_last"],
    "slope": ["ols_slope"],
    "slope_se": ["ols_slope", "ols_se_slope"],
    "full": HEALTH_K,
}


def build_q(rows, k, stress):
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
    return pd.DataFrame(Q)


def run(name, cells, ages, stress, k_max):
    print("\n" + "=" * 96)
    print("%s · parsimony ladder on a fixed cohort, fixed query times %s" % (name, list(ages)))
    print("=" * 96)
    rows = rows_for(cells, ages, stress, k_max)
    if not rows:
        print("  no rows"); return [], None
    base = C.AGE + (C.STRESS if stress is not None else [])
    print("  cohort: %d cells / %d conds / %d rows" % (
        len({r["cell"] for r in rows}), len({r["cond"] for r in rows}), len(rows)))
    hdr = "  %-2s %-8s" % ("k", "ampMed") + "".join(
        "%-22s" % a for a in ["base", "two_point", "slope", "slope_se", "full", "perm"])
    print(hdr)
    out, preds = [], []
    rng = np.random.default_rng(11)
    for k in K_GRID:
        if k > k_max:
            continue
        Q = build_q(rows, k, stress)
        pb = C.fit_loco(Q, base)
        okb = np.isfinite(pb)
        cb = C.cond_macro(np.abs(pb[okb] - Q.y.values[okb]), Q.cond.values[okb])
        line = "  %-2d %-8.4f%-22.4f" % (k, Q.amp.median(), cb.mean())
        rec = dict(cohort=name, k=int(k), amp_med=float(Q.amp.median()),
                   base=float(cb.mean()))
        for arm, feats in LADDER.items():
            used = []
            ph = C.fit_loco(Q, base + feats, used=used)
            ok = okb & np.isfinite(ph)
            ch = C.cond_macro(np.abs(ph[ok] - Q.y.values[ok]), Q.cond.values[ok])
            g, lo, hi, p = C.paired_gain(cb, ch)
            rec[arm] = float(ch.mean())
            rec[arm + "_gain"] = g
            rec[arm + "_lo"] = lo
            rec[arm + "_hi"] = hi
            rec[arm + "_nfeat"] = len(used[0]) if used else 0
            line += "%-9.4f %-12s" % (ch.mean(), "%+5.1f%%" % g)
            if arm == "full":
                Qf = Q.loc[ok].copy()
                Qf["pred"] = ph[ok]
                Qf["arm"] = arm
                preds.append(Qf)
        # capacity placebo: shuffle the full descriptor block
        gl = []
        for _ in range(N_PERM):
            Qp = Q.copy()
            for f in HEALTH_K:
                Qp[f] = rng.permutation(Qp[f].values)
            pp = C.fit_loco(Qp, base + HEALTH_K)
            ok = okb & np.isfinite(pp)
            cp = C.cond_macro(np.abs(pp[ok] - Q.y.values[ok]), Q.cond.values[ok])
            gl.append(100.0 * (cp.mean() / cb.mean() - 1.0))
        rec["perm"] = float("nan")
        rec["perm_gain"] = float(np.median(gl))
        line += "%-9s %-12s" % ("-", "%+5.1f%%" % np.median(gl))
        print(line)
        out.append(rec)
    # saturation summary per arm
    print("\n  saturation, k=%d -> k=%d (relative change in that arm's error):" % (
        out[0]["k"], out[-1]["k"]))
    for arm in ["two_point", "slope", "slope_se", "full"]:
        d = 100.0 * (out[-1][arm] / out[0][arm] - 1.0)
        verdict = "SATURATED" if abs(d) < 5 else ("improves" if d < 0 else "degrades")
        print("    %-10s %+6.1f%%   %s   (features k=%d: %d, k=%d: %d)" % (
            arm, d, verdict, out[0]["k"], out[0][arm + "_nfeat"],
            out[-1]["k"], out[-1][arm + "_nfeat"]))
    return out, (pd.concat(preds, ignore_index=True) if preds else None)


def main():
    print("=" * 96)
    print("D5 · saturation vs descriptor overfitting")
    print("=" * 96)
    isu = C.load_isu()
    S = C.load_stress()
    uc = C.load_uconn()
    r1, p1 = run("ISU", isu, (49, 63), S, k_max=6)
    r2, p2 = run("UConn", uc, (600, 1000), None, k_max=6)
    T = pd.DataFrame(r1 + r2)
    T.to_csv(os.path.join(OUT, "D5_parsimony.csv"), index=False)
    json.dump(T.to_dict("records"), open(os.path.join(OUT, "D5_parsimony.json"), "w"), indent=1)
    ps = [p for p in (p1, p2) if p is not None]
    if ps:
        pd.concat(ps, ignore_index=True).to_csv(
            os.path.join(OUT, "D5_predictions.csv"), index=False)
    print("\nwrote D5_parsimony.csv / .json / D5_predictions.csv")


if __name__ == "__main__":
    main()
