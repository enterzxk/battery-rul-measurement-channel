# -*- coding: utf-8 -*-
"""D8 · The audit Codex required before any line-D claim is written down.

Three items, none of which is a new hypothesis:

 1. NORMALIZATION TIMING. D_common.load_isu normalizes by ref = nanmax(v[:L]),
    i.e. the maximum over the WHOLE available trajectory. If that maximum occurs
    after a query time, the health features at that query are scaled by future
    information. This script records, for every cell, the DAY at which the
    normalization reference is attained, and checks it against the earliest query
    age actually used.

 2. EXACT ELIGIBILITY. The number of cells and conditions admitted at each query
    age, so the evaluation population is stated rather than implied.

 3. DIRECT PAIRED k=2 vs k=6 INTERVAL. D4/D5 reported each arm against the
    age+stress baseline. A difference of two such gains is NOT an interval for the
    k=2 vs k=6 difference. This computes the paired condition-level difference
    directly, from the saved per-query predictions, and states an explicit
    practical-equivalence margin.

Writes protocol/D8_audit.json / D8_eligibility.csv / D8_k2_vs_k6.csv
"""
import os
import json
import re
import zipfile

import numpy as np
import pandas as pd
from scipy import stats

import D_common as C
from D4_budget_curve import HEALTH_K, describe, rows_for, thin

OUT = C.PROTO
AGES = (21, 35, 49, 63)
K_LO, K_HI = 2, 6
# Practical-equivalence margin, stated BEFORE looking at the k2-vs-k6 interval:
# 10% of the age+stress baseline's condition-macro MAE, matching the ~11% MDE
# convention this programme has used throughout. Declared post hoc relative to
# the D4 run, so the equivalence verdict is labelled EXPLORATORY.
MARGIN_FRAC = 0.10


def normalization_timing():
    """Day at which each cell's normalization reference is attained."""
    z = zipfile.ZipFile(C.RAW_ISU)
    rows = []
    for n in sorted(x for x in z.namelist() if x.lower().endswith(".json")):
        name = n.split("/")[-1].replace(".json", "")
        if not re.match(r"G(\d+)C(\d+)", name):
            continue
        try:
            dd = json.loads(json.loads(z.read(n).decode("utf-8")))
        except Exception:
            continue
        cap = dd.get("capacity_discharge_C_5") or dd.get("capacity_discharge_C_2")
        ts = (dd.get("start_stop_time") or {}).get("start") or []
        if not isinstance(cap, list) or len(cap) < 4:
            continue
        v = []
        for x in cap:
            try:
                v.append(float(x))
            except Exception:
                v.append(np.nan)
        v = np.array(v, float)
        L = min(len(v), len(ts)) if ts else 0
        if L < 4:
            continue
        t = [pd.to_datetime(x, errors="coerce") for x in ts[:L]]
        if not all(pd.notna(x) for x in t):
            continue
        w = v[:L]
        if not np.isfinite(w).any():
            continue
        am = int(np.nanargmax(w))
        day = (t[am] - t[0]).total_seconds() / 86400.0
        rows.append(dict(cell=name, argmax_idx=am, ref_day=float(day),
                         n_rpt=L, max_cap=float(np.nanmax(w)),
                         first_cap=float(w[0])))
    T = pd.DataFrame(rows)
    earliest_query = min(AGES)
    bad = T[T.ref_day >= earliest_query]
    print("\n=== 1. normalization reference timing ===")
    print("  cells: %d" % len(T))
    print("  argmax index: %s" % T.argmax_idx.value_counts().sort_index().to_dict())
    print("  reference day: max %.2f, median %.2f, p95 %.2f" % (
        T.ref_day.max(), T.ref_day.median(), T.ref_day.quantile(.95)))
    print("  earliest query age used: %d days" % earliest_query)
    print("  cells whose reference is attained ON OR AFTER the earliest query: %d" % len(bad))
    if len(bad):
        print(bad.to_string(index=False))
    print("  -> %s" % ("NO future information enters the normalization"
                       if len(bad) == 0 else "LEAKAGE: must rebuild the loader"))
    T.to_csv(os.path.join(OUT, "D8_normalization_timing.csv"), index=False)
    return dict(n_cells=int(len(T)),
                argmax_counts={int(k): int(v) for k, v in T.argmax_idx.value_counts().items()},
                ref_day_max=float(T.ref_day.max()), ref_day_median=float(T.ref_day.median()),
                earliest_query=int(earliest_query), n_leaking=int(len(bad)))


def eligibility(cells, stress):
    print("\n=== 2. exact eligibility per query age ===")
    rows = []
    print("  %-5s %-7s %-7s %-9s %-9s" % ("age", "cells", "conds", "med n_obs", "t<L"))
    for a in AGES:
        cs, conds, nobs, tl = set(), set(), [], 0
        for c, s in cells.items():
            if s["cond"] not in stress.index:
                continue
            if a >= s["L"]:
                continue
            tl += 1
            n = int((s["x"] <= a).sum())
            if n < C.MIN_OBS:
                continue
            cs.add(c); conds.add(s["cond"]); nobs.append(n)
        print("  %-5d %-7d %-7d %-9.1f %-9d" % (a, len(cs), len(conds),
                                                 np.median(nobs) if nobs else float("nan"), tl))
        rows.append(dict(age=a, n_cells=len(cs), n_cond=len(conds),
                         med_n_obs=float(np.median(nobs)) if nobs else float("nan"),
                         n_cell_age_eligible=tl))
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(OUT, "D8_eligibility.csv"), index=False)
    return T


def k2_vs_k6(cells, stress, k_max=6):
    """Direct paired condition-level difference between the k=2 and k=6 arms."""
    print("\n=== 3. direct paired k=2 vs k=6 interval (same arm, same cohort) ===")
    rows = rows_for(cells, AGES, stress, k_max)
    print("  fixed cohort: %d cells / %d conds / %d rows" % (
        len({r["cell"] for r in rows}), len({r["cond"] for r in rows}), len(rows)))
    base = C.AGE + C.STRESS
    errs, preds = {}, {}
    for k in (K_LO, K_HI):
        Q = []
        for r in rows:
            xv, sv = thin(r["xv"], r["sv"], k)
            d = dict(cell=r["cell"], cond=r["cond"], age=r["age"],
                     logt=float(np.log(r["age"])), n_obs=int(len(xv)),
                     span=float(xv[-1] - xv[0]), y=float(np.log(r["U"])))
            d.update(describe(xv, sv, r["age"]))
            d["DoD"] = float(stress.loc[r["cond"], "DoD"])
            d["cc"] = float(stress.loc[r["cond"], "charge_C"])
            d["cd"] = float(stress.loc[r["cond"], "discharge_C"])
            Q.append(d)
        Q = pd.DataFrame(Q)
        pb = C.fit_loco(Q, base)
        ph = C.fit_loco(Q, base + HEALTH_K)
        ok = np.isfinite(pb) & np.isfinite(ph)
        errs[k] = C.cond_macro(np.abs(ph[ok] - Q.y.values[ok]), Q.cond.values[ok])
        preds[k] = Q.loc[ok, ["cell", "cond", "age", "y"]].assign(
            pred_health=ph[ok], pred_base=pb[ok], k=k)
        base_mae = float(C.cond_macro(np.abs(pb[ok] - Q.y.values[ok]),
                                      Q.cond.values[ok]).mean())
    idx = errs[K_LO].index.intersection(errs[K_HI].index)
    e2, e6 = errs[K_LO].loc[idx].values, errs[K_HI].loc[idx].values
    n = len(idx)
    diff = e6.mean() - e2.mean()
    rng = np.random.default_rng(0)
    ds = np.empty(4000)
    for i in range(4000):
        j = rng.integers(0, n, n)
        ds[i] = e6[j].mean() - e2[j].mean()
    lo, hi = np.percentile(ds, [2.5, 97.5])
    try:
        p = float(stats.wilcoxon(e6, e2).pvalue)
    except ValueError:
        p = float("nan")
    margin = MARGIN_FRAC * base_mae
    within = (hi < margin) and (lo > -margin)
    print("  conditions: %d | base MAE %.4f | k=2 %.4f | k=6 %.4f" % (n, base_mae, e2.mean(), e6.mean()))
    print("  paired difference (k=6 minus k=2): %+.4f  [95%% CI %+.4f, %+.4f]  Wilcoxon p=%.3g" % (
        diff, lo, hi, p))
    print("  practical-equivalence margin: +/- %.4f  (%.0f%% of base MAE)" % (margin, 100 * MARGIN_FRAC))
    print("  -> equivalence at this margin: %s" % ("YES (EXPLORATORY, margin declared post hoc)" if within
                                                    else "NOT ESTABLISHED"))
    T = pd.DataFrame(dict(cond=idx, err_k2=e2, err_k6=e6))
    T.to_csv(os.path.join(OUT, "D8_k2_vs_k6.csv"), index=False)
    pd.concat(preds.values(), ignore_index=True).to_csv(
        os.path.join(OUT, "D8_predictions_k2_k6.csv"), index=False)
    return dict(n_cond=int(n), base_mae=base_mae, err_k2=float(e2.mean()),
                err_k6=float(e6.mean()), diff=float(diff), ci_lo=float(lo),
                ci_hi=float(hi), wilcoxon_p=p, margin=float(margin),
                equivalent_at_margin=bool(within))


def main():
    print("=" * 84)
    print("D8 · audit required before any line-D claim")
    print("=" * 84)
    isu = C.load_isu()
    S = C.load_stress()
    out = dict(normalization=normalization_timing())
    eligibility(isu, S)
    out["k2_vs_k6"] = k2_vs_k6(isu, S)
    json.dump(out, open(os.path.join(OUT, "D8_audit.json"), "w"), indent=1)
    print("\nwrote D8_audit.json / D8_eligibility.csv / D8_k2_vs_k6.csv / D8_predictions_k2_k6.csv")


if __name__ == "__main__":
    main()
