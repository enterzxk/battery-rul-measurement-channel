# -*- coding: utf-8 -*-
"""D1 · De-confound the C headline before anything is built on it.

The C result to be turned into a method is:

    ISU: health arm 0.1718 vs age+stress 0.2131 -> -19.4%, CI [-27.4,-11.2]

The problem: the arm called "health" in C_validity_ablation.py is

    ["logt","DoD","cc","cd","soh_last","soh0","slope","span","n_obs"]

and `span` and `n_obs` are PURE SCHEDULE quantities. A cell inspected more often
has a larger span and more observations at the same fixed calendar age. So the
-19.4% may be "schedule density beats a bare age term", not "health trajectory
beats age+stress". That is precisely the error class this programme has already
committed three times, so it must be removed before any decision rule is built.

This script splits the arm into SCHED and HEALTH and reports every combination on
IDENTICAL query keys (same cells, same ages, same targets, same folds).

Acceptance: the C arm must reproduce -19.4% (it is the same feature set).
Decision rule for what follows:
  * if HEALTH adds nothing once SCHED is in the model  -> the C headline is a
    schedule effect, the line has no information content, close it;
  * if HEALTH still adds materially                      -> there is a real
    information effect to build a decision rule on.

Writes protocol/D1_deconfound.csv / .json / per-query predictions.
"""
import os
import json

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO


def arms_for(has_stress):
    """name -> (feature list, human label). Order matters for reporting."""
    A = {}
    if has_stress:
        base = C.AGE + C.STRESS
        A["age"] = C.AGE
        A["as"] = base
        A["as_sched"] = base + C.SCHED
        A["as_health"] = base + C.HEALTH
        A["as_sched_health"] = base + C.SCHED + C.HEALTH  # == the C "health" arm
    else:
        A["age"] = C.AGE
        A["age_sched"] = C.AGE + C.SCHED
        A["age_health"] = C.AGE + C.HEALTH
        A["age_sched_health"] = C.AGE + C.SCHED + C.HEALTH
    return A


def run(name, cells, ages, stress, ref_arm):
    Q = C.build_queries(cells, ages, stress=stress)
    if len(Q) < 60:
        print("  %s: only %d rows" % (name, len(Q)))
        return None
    arms = arms_for(stress is not None)
    preds = {}
    for a, feats in arms.items():
        preds[a] = C.fit_loco(Q, feats)
    ok = np.isfinite(preds[ref_arm])
    for a in arms:
        ok &= np.isfinite(preds[a])

    rows = []
    cm = {}
    for a in arms:
        e = np.abs(preds[a][ok] - Q.y.values[ok])
        cm[a] = C.cond_macro(e, Q.cond.values[ok])
        rows.append(dict(cohort=name, arm=a, n_feat=len(arms[a]),
                         cond_macro_mae=float(cm[a].mean()),
                         n_cond=int(len(cm[a])), n_queries=int(ok.sum()),
                         n_cells=int(Q[ok].cell.nunique())))
    T = pd.DataFrame(rows)
    ref = float(cm[ref_arm].mean())

    print("\n=== %s ===  (%d cells / %d cond / %d queries; ref arm = %s, %.4f)" % (
        name, T.n_cells.iloc[0], T.n_cond.iloc[0], T.n_queries.iloc[0],
        ref_arm, ref))
    print("  %-18s %-6s %-9s %-22s %s" % ("arm", "feat", "condMAE", "gain vs ref", "Wilcoxon p"))
    contrasts = []
    for a in arms:
        g, lo, hi, p = C.paired_gain(cm[ref_arm], cm[a])
        tag = "" if a == ref_arm else "%+6.1f%% [%6.1f,%6.1f]" % (g, lo, hi)
        print("  %-18s %-6d %-9.4f %-22s %s" % (a, len(arms[a]), cm[a].mean(), tag,
                                                "" if a == ref_arm else "%.2e" % p))
        if a != ref_arm:
            contrasts.append(dict(cohort=name, arm=a, ref=ref_arm,
                                  mae=float(cm[a].mean()), ref_mae=ref,
                                  gain_pct=g, ci_lo=lo, ci_hi=hi, wilcoxon_p=p))

    # --- the two decisive contrasts -----------------------------------------
    print("\n  --- decisive contrasts (negative = arm better) ---")
    decisive = []
    for h, a in [("as_sched_health", "as_sched"),   # does HEALTH add over SCHED?
                 ("as_health", "as"),               # does HEALTH add over AS alone?
                 ("as_sched", "as"),                # does SCHED add over AS alone?
                 ("age_sched_health", "age_sched"),
                 ("age_health", "age"),
                 ("age_sched", "age")]:
        if h in cm and a in cm:
            g, lo, hi, p = C.paired_gain(cm[a], cm[h])
            sig = "YES" if hi < 0 else ("NO" if lo > 0 else "no")
            print("  %-18s over %-12s : %+6.1f%% [%6.1f,%6.1f]  p=%.2e  -> %s" % (
                h, a, g, lo, hi, p, sig))
            decisive.append(dict(cohort=name, health_arm=h, base_arm=a,
                                 gain_pct=g, ci_lo=lo, ci_hi=hi,
                                 wilcoxon_p=p, excludes_zero=bool(hi < 0)))

    # --- confound diagnostics ----------------------------------------------
    print("\n  --- schedule/health separability on these queries ---")
    sub = Q[ok]
    for a, b in [("n_obs", "soh_last"), ("span", "soh_last"),
                 ("n_obs", "slope"), ("cadence", "slope")]:
        r = np.corrcoef(sub[a].values, sub[b].values)[0, 1]
        print("  spearman(%s, %s) = %+.3f" % (a, b, pd.Series(sub[a]).corr(
            pd.Series(sub[b]), method="spearman")))
        _ = r
    print("  n_obs: min %d med %.1f max %d | span: med %.1f | amp=1-soh_last: med %.4f" % (
        sub.n_obs.min(), sub.n_obs.median(), sub.n_obs.max(),
        sub.span.median(), sub.amp.median()))

    # --- save per-query predictions (discipline: no CI without them) --------
    keep = Q.loc[ok, ["cell", "cond", "age", "logt", "n_obs", "span", "cadence",
                      "soh_last", "soh0", "slope", "y", "L", "life_frac", "amp"]].copy()
    for a in arms:
        keep["pred_" + a] = preds[a][ok]
    keep["cohort"] = name
    return dict(table=T, contrasts=contrasts, decisive=decisive, preds=keep)


def main():
    print("=" * 78)
    print("D1 · de-confounding the C health-vs-age+stress headline")
    print("=" * 78)

    uc = C.load_uconn()
    print("UConn cells loaded: %d" % len(uc))
    isu = C.load_isu()
    print("ISU cells loaded: %d" % len(isu))
    S = C.load_stress()

    ru = run("UConn", uc, ages=(300, 600, 1000, 1500), stress=None, ref_arm="age")
    ri = run("ISU", isu, ages=(21, 35, 49, 63), stress=S, ref_arm="as")

    tables, contrasts, decisive, preds = [], [], [], []
    for r in (ru, ri):
        if r is None:
            continue
        tables.append(r["table"])
        contrasts += r["contrasts"]
        decisive += r["decisive"]
        preds.append(r["preds"])

    T = pd.concat(tables, ignore_index=True)
    T.to_csv(os.path.join(OUT, "D1_deconfound.csv"), index=False)
    pd.concat(preds, ignore_index=True).to_csv(
        os.path.join(OUT, "D1_predictions.csv"), index=False)
    json.dump(dict(table=T.to_dict("records"), contrasts=contrasts,
                   decisive=decisive),
              open(os.path.join(OUT, "D1_deconfound.json"), "w"), indent=1)

    print("\n" + "=" * 78)
    print("REPRODUCTION CHECK: the C arm (as_sched_health) should be ~0.1718 on ISU")
    print("=" * 78)
    print(T[T.cohort == "ISU"][["arm", "n_feat", "cond_macro_mae"]].to_string(index=False))
    print("\nwrote D1_deconfound.csv / D1_deconfound.json / D1_predictions.csv")


if __name__ == "__main__":
    main()
