# -*- coding: utf-8 -*-
"""D7 · Stability floor: how much of every number is model variance?

D5 produced two uncomfortable facts at once.

  * On ISU the parsimony ladder is flat and the capacity placebo is NEGATIVE
    (+1% to +9%, i.e. shuffling the descriptors makes the model worse), so the
    health gain is information, not extra capacity.
  * On UConn, `two_point` gives -0.2% but `full` gives -34.6% at the same k, and
    those two feature sets differ only by columns that are near-duplicates of
    soh_last on that cohort (soh_first is constant at 1.0). A 34-point swing
    between near-equivalent feature sets cannot be signal.

So before any claim is made, the model-variance floor must be measured: re-fit
the same arm under implementation choices that carry no information --

  * feature ORDER permutation (HGB scans features in order; duplicates change
    which split is chosen first),
  * estimator family (Ridge instead of HGB),
  * HGB random_state and iteration count.

If the spread across those choices is comparable to the effect being claimed,
the effect is not identifiable and must not be reported as a point estimate.

Writes protocol/D7_stability.csv / .json
"""
import os
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import D_common as C
from D4_budget_curve import HEALTH_K, describe, rows_for, thin

OUT = C.PROTO
N_ORDER = 8
KS = (2, 6)


def build_q(rows, k, stress):
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
    return pd.DataFrame(Q)


def fit_with(Q, feats, maker):
    return C.fit_loco(Q, feats, model=maker)


def score(Q, p, ok_ref=None):
    ok = np.isfinite(p) if ok_ref is None else (ok_ref & np.isfinite(p))
    cm = C.cond_macro(np.abs(p[ok] - Q.y.values[ok]), Q.cond.values[ok])
    return float(cm.mean()), cm


def run(name, cells, ages, stress, k_max):
    print("\n" + "=" * 92)
    print("%s · stability floor of the reported numbers" % name)
    print("=" * 92)
    rows = rows_for(cells, ages, stress, k_max)
    base = C.AGE + (C.STRESS if stress is not None else [])
    print("  cohort: %d cells / %d conds / %d rows" % (
        len({r["cell"] for r in rows}), len({r["cond"] for r in rows}), len(rows)))
    recs = []
    for k in KS:
        if k > k_max:
            continue
        Q = build_q(rows, k, stress)
        pb = C.fit_loco(Q, base)
        base_mae, _ = score(Q, pb)
        for arm, feats in [("two_point", ["soh_first", "soh_last"]),
                           ("full", HEALTH_K)]:
            cols = base + feats
            # 1. reference HGB
            ph = fit_with(Q, cols, None)
            ref, cm_ref = score(Q, ph)
            # 2. feature-order permutations
            rng = np.random.default_rng(3)
            order = []
            for _ in range(N_ORDER):
                perm = list(rng.permutation(len(cols)))
                Qp = Q.copy()
                Qp[cols] = Q[cols].values[:, perm]
                po = fit_with(Qp, cols, None)
                mo, _ = score(Qp, po)
                order.append(100.0 * (mo / base_mae - 1.0))
            ref_g = 100.0 * (ref / base_mae - 1.0)
            # 3. estimator family
            ridge = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
            Qr = Q.copy()
            Qr[cols] = np.nan_to_num(Q[cols].values)
            pr = fit_with(Qr, cols, lambda: make_pipeline(StandardScaler(), Ridge(alpha=1.0)))
            mr, _ = score(Qr, pr)
            # 4. HGB variants
            variants = []
            for rs, mi in [(1, 300), (2, 300), (0, 150), (0, 600)]:
                pv = fit_with(Q, cols, lambda rs=rs, mi=mi: HistGradientBoostingRegressor(
                    max_iter=mi, learning_rate=0.05, random_state=rs))
                mv, _ = score(Q, pv)
                variants.append(100.0 * (mv / base_mae - 1.0))
            spread = [min(order + variants + [ref_g, 100.0 * (mr / base_mae - 1.0)]),
                      max(order + variants + [ref_g, 100.0 * (mr / base_mae - 1.0)])]
            print("  k=%d %-10s ref %+6.1f%% | order-perm [%+6.1f, %+6.1f] | HGB variants [%+6.1f, %+6.1f] | Ridge %+6.1f%% | TOTAL SPREAD %.1f pp" % (
                k, arm, ref_g, min(order), max(order), min(variants), max(variants),
                100.0 * (mr / base_mae - 1.0), spread[1] - spread[0]))
            recs.append(dict(cohort=name, k=int(k), arm=arm, base_mae=base_mae,
                             ref_mae=ref, ref_gain_pct=ref_g,
                             order_min=min(order), order_max=max(order),
                             var_min=min(variants), var_max=max(variants),
                             ridge_gain_pct=100.0 * (mr / base_mae - 1.0),
                             spread_pp=spread[1] - spread[0]))
    return recs


def main():
    print("=" * 92)
    print("D7 · is any of this bigger than the model-variance floor?")
    print("=" * 92)
    isu = C.load_isu(); S = C.load_stress()
    uc = C.load_uconn()
    r = run("ISU", isu, (49, 63), S, k_max=6)
    r += run("UConn", uc, (600, 1000), None, k_max=6)
    T = pd.DataFrame(r)
    T.to_csv(os.path.join(OUT, "D7_stability.csv"), index=False)
    json.dump(r, open(os.path.join(OUT, "D7_stability.json"), "w"), indent=1)
    print("\n  VERDICT RULE: report a point estimate only if |ref_gain| exceeds the spread.")
    for _, x in T.iterrows():
        ok = abs(x.ref_gain_pct) > x.spread_pp
        print("  %-5s k=%d %-10s gain %+6.1f%%  spread %.1f pp  -> %s" % (
            x.cohort, x.k, x.arm, x.ref_gain_pct, x.spread_pp,
            "STABLE" if ok else "NOT IDENTIFIABLE"))
    print("\nwrote D7_stability.csv / .json")


if __name__ == "__main__":
    main()
