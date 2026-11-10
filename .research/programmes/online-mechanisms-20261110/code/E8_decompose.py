# -*- coding: utf-8 -*-
"""E8 · Why no timing policy could help: decompose the decision loss.

E7's inspection records show the quantile model recommending replacement far
before the true EOL (e.g. R ~ 187 d against M ~ 346 d on G1C1). If the loss is
dominated by a systematic early-replacement bias driven by the predictive spread,
then the binding constraint is model uncertainty, not WHICH inspections were
bought — which would explain the flat policy comparison mechanistically rather
than merely reporting it.

Decomposition, per policy, on the primary setting:

  mean signed error      e = pred_R - M            (negative = too early)
  mean wasted life       mean max(0, M - pred_R)   (weight 1)
  mean failure exposure  mean max(0, pred_R - M)   (weight ratio = 5)
  share of loss from early replacement
  mean |log(pred_R/M)|   (scale-free bias measure)

Also: the spread the model implies. With R = exp(q_tau) and tau = 1/6, the
implied log-space standard deviation is sigma = (log M - log R) / z_tau for a
Gaussian approximation, reported for scale.

Run remotely.
"""
import os
import json

import numpy as np
import pandas as pd
from scipy import stats

import D_common as C

OUT = C.PROTO
RATIO = 5.0


def main():
    D = pd.read_csv(os.path.join(OUT, "E7_inspection_records.csv"))
    print("rows %d | cells %d | conditions %d | policies %s" % (
        len(D), D.cell.nunique(), D.cond.nunique(), sorted(D.policy.unique())))

    D["early"] = np.maximum(0.0, D.M - D.pred_R)
    D["late"] = np.maximum(0.0, D.pred_R - D.M)
    D["loss_check"] = D.early + RATIO * D.late
    D["logratio"] = np.log(D.pred_R / D.M)

    print("\n=== loss decomposition by policy (days) ===")
    print("  %-11s %-9s %-10s %-10s %-12s %-10s %s" % (
        "policy", "mean loss", "mean e", "wasted", "failure exp", "early %", "mean log(R/M)"))
    for p, g in D.groupby("policy"):
        tot = g.loss.mean()
        share = g.early.mean() / tot if tot > 0 else np.nan
        print("  %-11s %-9.2f %-10.1f %-10.1f %-12.1f %-10.1f %+.3f" % (
            p, tot, g.logratio.mean() * 0 + (g.pred_R - g.M).mean(),
            g.early.mean(), g.late.mean(), 100 * share, g.logratio.mean()))

    print("\n=== how much of the loss is the same for every policy? ===")
    # condition-level paired comparison of each policy against FixedEven
    piv = D.pivot_table(index=["heldout_cond", "cell"], columns="policy", values="loss")
    base = piv["FixedEven"]
    print("  %-11s %-12s %-26s %s" % ("policy", "mean Δ vs Even", "paired 95% CI", "spread across policies"))
    for p in piv.columns:
        d = (piv[p] - base).values
        rng = np.random.default_rng(0)
        bs = d[rng.integers(0, len(d), (10000, len(d)))].mean(axis=1)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        print("  %-11s %+12.2f [%+8.2f, %+8.2f]      (cell level, n=%d)" % (
            p, d.mean(), lo, hi, len(d)))

    # within-cell spread across the six policies: how much does timing even move?
    within = piv.max(axis=1) - piv.min(axis=1)
    print("\n  within-cell spread of loss across the 6 policies: "
          "median %.2f d, mean %.2f d, 90th pct %.2f d" % (
              within.median(), within.mean(), within.quantile(0.90)))
    print("  mean loss level: %.2f d  -> within-cell policy spread is %.1f%% of it" % (
        D.loss.mean(), 100 * within.mean() / D.loss.mean()))

    # the dominant term
    print("\n=== dominant term ===")
    print("  mean wasted life (early replacement) : %.1f d" % D.early.mean())
    print("  mean failure exposure x %.0f          : %.1f d" % (RATIO, RATIO * D.late.mean()))
    print("  -> early replacement accounts for %.1f%% of the total loss" % (
        100 * D.early.mean() / D.loss.mean()))
    print("  mean |log(pred_R / M)| = %.3f  (median %.3f)" % (
        D.logratio.abs().mean(), D.logratio.abs().median()))
    print("  implied log-sd under a Gaussian quantile rule (tau=1/6, z=-0.967): "
          "median %.3f" % float(np.median(-D.logratio / -0.9674)))

    out = dict(mean_loss=D.groupby("policy").loss.mean().to_dict(),
               mean_wasted=float(D.early.mean()),
               mean_failure_exposure=float(RATIO * D.late.mean()),
               early_share=float(D.early.mean() / D.loss.mean()),
               mean_abs_log_ratio=float(D.logratio.abs().mean()),
               within_cell_policy_spread_mean=float(within.mean()),
               within_cell_policy_spread_median=float(within.median()),
               loss_level=float(D.loss.mean()))
    json.dump(out, open(os.path.join(OUT, "E8_decomposition.json"), "w"), indent=1)
    D.to_csv(os.path.join(OUT, "E8_decomposition.csv"), index=False)
    print("\nwrote E8_decomposition.csv / .json")


if __name__ == "__main__":
    main()
