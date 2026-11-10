# -*- coding: utf-8 -*-
"""F0b · Can a standard calibration fix recover the Stage-E early-replacement loss?

F0 established:
  * the tau* = 1/(1+ratio) quantile is OVER-CONSERVATIVE (coverage 0.245 vs 0.167);
  * a global split-conformal SHIFT is a no-op (delta -0.002 d), because a quantile
    model already centres its residuals at tau, so the tau-quantile of residuals
    is ~0 and the shift cancels;
  * the loss has an interior minimum in tau, so the miscalibration is at least
    partly correctable in principle.

This tests the two standard fixes, both fitted on TRAINING folds only:

  (A) SCALE SHRINKAGE toward the conditional median, a standard conformalised
      quantile-regression correction:
          log R' = m + lam * (log R - m)
      with m the tau=0.5 model and lam chosen on training folds so that the
      held-out-target coverage hits tau*.

  (B) NESTED TAU SELECTION: choose tau on training folds by minimising the
      training loss, then apply that tau to the test fold. This is the honest
      "just tune the hyperparameter" baseline. If it recovers the loss, there is
      no method here, only a hyperparameter choice.

Run remotely.
"""
import os
import json
import pickle

import numpy as np
import pandas as pd

import D_common as C
from E3b_replay import (FEATS, cohort, features_from_obs, fixed_even, fit_q, loss_of)

OUT = C.PROTO
T, N, RATIO = 63, 2, 5.0
TAU_STAR = 1.0 / (1.0 + RATIO)
LAMS = np.linspace(0.2, 1.6, 29)


def qrows(co, names, stress):
    rows = []
    for n in names:
        d = co[n]; s = d["s"]
        idx = sorted(set([0] + fixed_even(d["avail"], N)))
        f = features_from_obs(s["x"][idx], s["soh"][idx], T, stress.loc[s["cond"]])
        f["cell"] = n; f["cond"] = s["cond"]
        f["y"] = float(np.log(d["M"])); f["M"] = float(d["M"])
        rows.append(f)
    return pd.DataFrame(rows)


def main():
    with open(os.path.join(OUT, "isu_cells_cache.pkl"), "rb") as f:
        pay = pickle.load(f)
    cells, stress = pay["cells"], pay["stress"]
    co = cohort(cells, T, stress)
    conds = sorted({d["s"]["cond"] for d in co.values()})
    print("T=%d N=%d ratio=%.0f tau*=%.4f | %d cells / %d conds" % (
        T, N, RATIO, TAU_STAR, len(co), len(conds)))

    raw_p, raw_M, scale_p, scale_M, nest_p, nest_M = [], [], [], [], [], []
    lam_used, tau_used = [], []

    for g in conds:
        tr = [n for n, d in co.items() if d["s"]["cond"] != g]
        te = [n for n, d in co.items() if d["s"]["cond"] == g]
        if len(tr) < 60 or not te:
            continue
        Qtr = qrows(co, tr, stress); Qte = qrows(co, te, stress)
        feats = C.usable_features(Qtr, FEATS)

        mq = fit_q(Qtr, feats, TAU_STAR)
        mm = fit_q(Qtr, feats, 0.5)
        p_te = mq.predict(Qte[feats].values)
        p_tr = mq.predict(Qtr[feats].values)
        med_tr = mm.predict(Qtr[feats].values)
        med_te = mm.predict(Qte[feats].values)

        raw_p.append(p_te); raw_M.append(Qte["M"].values)

        # (A) scale shrinkage: pick lam on TRAINING coverage
        best_lam, best_gap = 1.0, np.inf
        for lam in LAMS:
            pr = med_tr + lam * (p_tr - med_tr)
            cov = float(np.mean(Qtr["y"].values <= pr))
            gap = abs(cov - TAU_STAR)
            if gap < best_gap:
                best_gap, best_lam = gap, lam
        lam_used.append(best_lam)
        scale_p.append(med_te + best_lam * (p_te - med_te)); scale_M.append(Qte["M"].values)

        # (B) nested tau: pick tau on TRAINING loss
        cand = [0.05, 0.075, 0.10, 0.125, TAU_STAR, 0.25, 1.0 / 3.0]
        best_tau, best_L = TAU_STAR, np.inf
        for tau in cand:
            mk = fit_q(Qtr, feats, tau)
            pk = mk.predict(Qtr[feats].values)
            Lk = float(np.mean(loss_of(np.maximum(T, np.exp(pk)), Qtr["M"].values, RATIO)))
            if Lk < best_L:
                best_L, best_tau = Lk, tau
        tau_used.append(best_tau)
        mk2 = fit_q(Qtr, feats, best_tau)
        nest_p.append(mk2.predict(Qte[feats].values)); nest_M.append(Qte["M"].values)

    def rep(name, p, M):
        R = np.maximum(T, np.exp(np.concatenate(p)))
        Mv = np.concatenate(M)
        return dict(arm=name, coverage=float(np.mean(Mv <= R)),
                    loss=float(np.mean(loss_of(R, Mv, RATIO))),
                    med_log=float(np.median(np.log(R / Mv))))

    rows = [rep("raw tau*", raw_p, raw_M),
            rep("scale-shrunk", scale_p, scale_M),
            rep("nested tau", nest_p, nest_M)]
    D = pd.DataFrame(rows)
    print("\n  %-14s %-10s %-10s %s" % ("arm", "coverage", "loss", "med log(R/M)"))
    for _, x in D.iterrows():
        print("  %-14s %-10.4f %-10.3f %+.3f" % (x.arm, x.coverage, x.loss, x.med_log))
    print("\n  lam chosen per fold : median %.2f  (range %.2f-%.2f)" % (
        np.median(lam_used), min(lam_used), max(lam_used)))
    print("  tau chosen per fold : %s" % pd.Series(tau_used).value_counts().to_dict())

    base = D.iloc[0].loss
    print("\n=== Q3 verdict ===")
    for _, x in D.iloc[1:].iterrows():
        print("  %-14s change %+7.3f d  (%+.1f%%)" % (
            x.arm, x.loss - base, 100 * (x.loss / base - 1)))
    print("\n  If nested-tau selection alone matches the calibration gain, then the")
    print("  'early replacement' problem is a HYPERPARAMETER issue, not a mechanism.")

    D.to_csv(os.path.join(OUT, "F0b_calibration_fix.csv"), index=False)
    json.dump(dict(rows=D.to_dict("records"),
                   lam_median=float(np.median(lam_used)),
                   tau_counts={str(k): int(v) for k, v in pd.Series(tau_used).value_counts().items()}),
              open(os.path.join(OUT, "F0b_calibration_fix.json"), "w"), indent=1, default=float)
    print("\nwrote F0b_calibration_fix.csv / .json")


if __name__ == "__main__":
    main()
