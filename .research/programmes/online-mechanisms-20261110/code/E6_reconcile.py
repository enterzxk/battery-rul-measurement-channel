# -*- coding: utf-8 -*-
"""E6 · Reporting reconciliations demanded by the adjudication.

Codex flagged three reporting defects in E4. This script fixes two of them
numerically (the third is a labelling issue handled in the write-up):

1. ORACLE HEADROOM LABELLING. 27.80 is the oracle's DECISION LOSS, excluding the
   inspection cost. So J_oracle = c_insp*N + 27.80 and J_fixed = c_insp*N + 40.47.
   The gap of 12.67 days is 31.3% of the decision loss but 29.8% of the total J.
   Both must be labelled; reporting only the larger fraction overstates it.

2. CANDIDATE minus VOI. The difference of two marginal medians is NOT the median
   of the paired difference. This computes the paired condition-level difference
   (Candidate loss minus VoI loss, positive = VoI better) with a paired cluster
   bootstrap over conditions, per setting, from the saved per-condition losses.

Run remotely.
"""
import os
import glob
import json

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO


def boot_ci(v, n_boot=10000, seed=0):
    v = np.asarray(v, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), (n_boot, len(v)))
    m = v[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(OUT, "E3_T*_N*_r*.json"))):
        d = json.load(open(f))
        pc = d["per_cond_loss"]
        voi = np.asarray(pc["VoI"], float)
        can = np.asarray(pc["Candidate"], float)
        late = np.asarray(pc["FixedLate"], float)
        even = np.asarray(pc["FixedEven"], float)
        n = len(voi)
        assert len(can) == n and len(late) == n

        paired_cv = can - voi            # >0 => VoI better
        lo, hi = boot_ci(paired_cv)
        lo2, hi2 = boot_ci(late - even)  # FixedLate vs FixedEven, paired
        N = d["N"]
        L_fix = d["loss"]["VoI"] + d["delta_vs_strongest_fixed"]["VoI"]
        L_or = d["oracle_loss"]
        rows.append(dict(
            horizon=d["T"], n_insp=N, ratio=d["ratio"], n_cond=n,
            L_fixed=L_fix, L_oracle=L_or,
            gap_days=L_fix - L_or,
            headroom_frac_of_loss=float((L_fix - L_or) / L_fix),
            headroom_frac_of_J=float(((N + L_fix) - (N + L_or)) / (N + L_fix)),
            paired_cv_mean=float(paired_cv.mean()),
            paired_cv_median=float(np.median(paired_cv)),
            paired_cv_lo=lo, paired_cv_hi=hi,
            paired_late_even_mean=float((late - even).mean()),
            paired_late_even_lo=lo2, paired_late_even_hi=hi2,
        ))
    D = pd.DataFrame(rows).sort_values(["horizon", "n_insp", "ratio"]).reset_index(drop=True)

    print("=" * 118)
    print("E6 · reconciliations: oracle headroom labelling, and PAIRED Candidate-vs-VoI")
    print("=" * 118)
    print("  %-2s %-2s %-4s | %-7s %-8s %-8s | %-9s %-24s | %s" % (
        "T", "N", "cf", "gap d", "head/loss", "head/J", "Cand-VoI", "paired 95% CI", "VoI better?"))
    for _, x in D.iterrows():
        sig = "YES" if x["paired_cv_lo"] > 0 else ("no" if x["paired_cv_hi"] < 0 else "unclear")
        print("  %-2d %-2d %-4.0f | %-7.2f %-8.1f%% %-8.1f%% | %+9.2f %-24s | %s" % (
            x["horizon"], x["n_insp"], x["ratio"], x["gap_days"],
            100 * x["headroom_frac_of_loss"], 100 * x["headroom_frac_of_J"],
            x["paired_cv_mean"],
            "[%+6.2f, %+6.2f]" % (x["paired_cv_lo"], x["paired_cv_hi"]), sig))

    print("\n  --- the two labelling corrections, stated once ---")
    p = D[(D["horizon"] == 63) & (D["n_insp"] == 2) & (D["ratio"] == 5.0)].iloc[0]
    print("  PRIMARY: L_fixed %.2f d, L_oracle %.2f d, gap %.2f d" % (
        p["L_fixed"], p["L_oracle"], p["gap_days"]))
    print("    gap as a fraction of DECISION LOSS : %.1f%%" % (100 * p["headroom_frac_of_loss"]))
    print("    gap as a fraction of TOTAL J       : %.1f%%  <- the honest denominator" % (
        100 * p["headroom_frac_of_J"]))
    print("\n  PAIRED Candidate-minus-VoI at the primary setting: mean %+.2f d, median %+.2f d,"
          " 95%% CI [%+.2f, %+.2f]  -> %s" % (
              p["paired_cv_mean"], p["paired_cv_median"], p["paired_cv_lo"],
              p["paired_cv_hi"],
              "VoI better, CI excludes zero" if p["paired_cv_lo"] > 0 else
              "CI includes zero: inferiority NOT statistically established"))
    print("\n  PAIRED FixedLate-minus-FixedEven at the primary setting: %+.2f d [%+.2f, %+.2f]" % (
        p["paired_late_even_mean"], p["paired_late_even_lo"], p["paired_late_even_hi"]))

    D.to_csv(os.path.join(OUT, "E6_reconcile.csv"), index=False)
    json.dump(D.to_dict("records"), open(os.path.join(OUT, "E6_reconcile.json"), "w"),
              indent=1, default=float)
    print("\nwrote E6_reconcile.csv / .json")


if __name__ == "__main__":
    main()
