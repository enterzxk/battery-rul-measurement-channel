# -*- coding: utf-8 -*-
"""F0 · Re-examine Stage E's 46.6% early-replacement share (brief §7).

Stage E found that 46.6% of the decision loss came from replacing EARLY, with a
mean log(R/M) of -0.10 (systematic early bias), and concluded that the binding
constraint was predictive spread rather than inspection timing. The brief asks
three questions about that finding, which this script answers with existing data
(no cycling data needed):

  Q1  Is it distributional miscalibration, the decision-loss setting, or both?
  Q2  Is the relation between interval width, coverage and early-replacement loss
      identifiable?
  Q3  Do standard calibration / quantile prediction / simple risk-decision
      baselines already solve the main problem?

Design. Exactly the Stage-E primary setting (T=63, N=2, c_f/c_w=5, c_insp=1) on
the fixed cohort, with the FixedEven schedule held constant so that only the
predictive distribution varies. For a grid of tau we fit the quantile model
leave-one-condition-out and measure:

    empirical coverage  = P(M <= R_tau)          should equal tau if calibrated
    loss                = mean[ max(0,M-R) + ratio*max(0,R-M) ]

The optimal action for this loss is the tau* = 1/(1+ratio) quantile. So:
  * if coverage(tau*) ~= tau*, the early replacement is OPTIMAL RISK AVERSION,
    not an error, and "fixing" it would increase loss;
  * if coverage(tau*) >> tau*, the model is over-conservative and standard
    calibration should recover loss.

Q3 then applies the cheapest standard fix: a conformal/split recalibration that
shifts log R by the empirical quantile of (log M - log R) computed on training
conditions only, so target coverage is achieved without touching the test folds.

Run remotely.
"""
import os
import json
import pickle

import numpy as np
import pandas as pd

import D_common as C
from E3b_replay import (FEATS, build_rows, cohort, features_from_obs,
                        fixed_even, fit_q, loss_of)

OUT = C.PROTO
T, N = 63, 2
RATIO = 5.0
TAU_STAR = 1.0 / (1.0 + RATIO)
TAUS = [0.05, 0.10, TAU_STAR, 0.25, 1.0 / 3.0, 0.5, 0.75]


def main():
    with open(os.path.join(OUT, "isu_cells_cache.pkl"), "rb") as f:
        pay = pickle.load(f)
    cells, stress = pay["cells"], pay["stress"]
    co = cohort(cells, T, stress)
    conds = sorted({d["s"]["cond"] for d in co.values()})
    print("T=%d N=%d ratio=%.0f tau*=%.4f | %d cells / %d conditions" % (
        T, N, RATIO, TAU_STAR, len(co), len(conds)))
    print("schedule held fixed = FixedEven, so only the predictive distribution varies\n")

    # one row per (cell, subset) is overkill here: use the FixedEven subset only
    def qrows(names):
        rows = []
        for n in names:
            d = co[n]
            s = d["s"]
            idx = sorted(set([0] + fixed_even(d["avail"], N)))
            f = features_from_obs(s["x"][idx], s["soh"][idx], T, stress.loc[s["cond"]])
            f["cell"] = n
            f["cond"] = s["cond"]
            f["y"] = float(np.log(d["M"]))
            f["M"] = float(d["M"])
            rows.append(f)
        return pd.DataFrame(rows)

    res = []
    rec = {}
    for tau in TAUS:
        preds, Ms, conds_l = [], [], []
        shifts = []
        for g in conds:
            tr = [n for n, d in co.items() if d["s"]["cond"] != g]
            te = [n for n, d in co.items() if d["s"]["cond"] == g]
            if len(tr) < 60 or not te:
                continue
            # train on the SAME single-subset rows as test (no augmentation needed here)
            Qtr = qrows(tr)
            Qte = qrows(te)
            feats = C.usable_features(Qtr, FEATS)
            m = fit_q(Qtr, feats, tau)
            p = m.predict(Qte[feats].values)
            # split-conformal shift from TRAINING residuals only
            ptr = m.predict(Qtr[feats].values)
            resid = Qtr["y"].values - ptr
            shift = float(np.quantile(resid, tau)) if len(resid) else 0.0
            shifts.append(shift)
            preds.append(p); Ms.append(Qte["M"].values); conds_l += list(Qte["cond"].values)
            rec.setdefault(tau, []).append((Qte, p, shift))
        p = np.concatenate(preds); M = np.concatenate(Ms)
        R = np.maximum(T, np.exp(p))
        cov = float(np.mean(M <= R))
        L = float(np.mean(loss_of(R, M, RATIO)))
        res.append(dict(tau=tau, coverage=cov, loss=L,
                        med_log_ratio=float(np.median(np.log(R / M))),
                        frac_early=float(np.mean(R < M))))
        print("  tau=%.4f  coverage=%.4f  mean loss=%8.3f  med log(R/M)=%+.3f  frac early=%.3f" % (
            tau, cov, L, np.median(np.log(R / M)), np.mean(R < M)))

    D = pd.DataFrame(res)
    print("\n=== Q1: is tau* = %.4f calibrated? ===" % TAU_STAR)
    row = D[np.isclose(D.tau, TAU_STAR)].iloc[0]
    print("  target coverage %.4f  ->  empirical %.4f  (gap %+.4f)" % (
        TAU_STAR, row.coverage, row.coverage - TAU_STAR))
    if row.coverage > TAU_STAR + 0.05:
        verdict = "OVER-CONSERVATIVE: model replaces too early, calibration should help"
    elif row.coverage < TAU_STAR - 0.05:
        verdict = "OVER-AGGRESSIVE: model replaces too late"
    else:
        verdict = "CALIBRATED: the early replacement is OPTIMAL risk aversion for this loss"
    print("  -> %s" % verdict)

    print("\n=== Q2: is loss monotone in coverage, i.e. is the optimum identifiable? ===")
    best = D.loc[D.loss.idxmin()]
    print("  loss-minimising tau in the grid: %.4f (coverage %.4f, loss %.3f)" % (
        best.tau, best.coverage, best.loss))
    print("  loss at tau* %.3f vs at the grid optimum %.3f  (difference %.3f d)" % (
        row.loss, best.loss, row.loss - best.loss))

    print("\n=== Q3: does split-conformal recalibration to tau* recover loss? ===")
    # apply the training-only shift and re-evaluate at tau*
    allp, allM = [], []
    for (Qte, p, shift) in rec[TAU_STAR]:
        R2 = np.maximum(T, np.exp(p + shift))
        allp.append(R2); allM.append(Qte["M"].values)
    R2 = np.concatenate(allp); M2 = np.concatenate(allM)
    cov2 = float(np.mean(M2 <= R2))
    L2 = float(np.mean(loss_of(R2, M2, RATIO)))
    print("  raw       coverage %.4f  loss %.3f" % (row.coverage, row.loss))
    print("  conformal coverage %.4f  loss %.3f  (change %+.3f d)" % (cov2, L2, L2 - row.loss))

    print("\n=== decomposition of the loss at tau* ===")
    # recompute components at tau*
    p = np.concatenate([x[1] for x in rec[TAU_STAR]])
    M = np.concatenate([x[0]["M"].values for x in rec[TAU_STAR]])
    R = np.maximum(T, np.exp(p))
    early = np.maximum(0.0, M - R)
    late = np.maximum(0.0, R - M)
    tot = (early + RATIO * late).mean()
    print("  mean early (wasted life)      : %.2f d  (%.1f%% of loss)" % (early.mean(), 100 * early.mean() / tot))
    print("  mean late x %.0f (failure exp.) : %.2f d  (%.1f%%)" % (RATIO, RATIO * late.mean(), 100 * RATIO * late.mean() / tot))
    print("  NOTE: with a CALIBRATED tau* the early share is a property of the LOSS")
    print("        function (risk aversion), not an error to be removed.")

    out = dict(tau_star=TAU_STAR, grid=D.to_dict("records"),
               calibrated_verdict=verdict,
               conformal=dict(coverage=cov2, loss=L2, delta_vs_raw=L2 - row.loss),
               early_share=float(early.mean() / tot),
               late_share=float(RATIO * late.mean() / tot))
    D.to_csv(os.path.join(OUT, "F0_calibration.csv"), index=False)
    json.dump(out, open(os.path.join(OUT, "F0_calibration.json"), "w"), indent=1, default=float)
    print("\nwrote F0_calibration.csv / .json")


if __name__ == "__main__":
    main()
