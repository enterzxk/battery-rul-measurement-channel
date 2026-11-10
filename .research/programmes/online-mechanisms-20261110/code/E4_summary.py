# -*- coding: utf-8 -*-
"""E4 · Summarise the 18 replay cells and apply the pre-registered verdict rule.

Verdict rule (PREREGISTRATION_E_ADDENDUM A6):
  support for timing value  <=>  one-sided 95% lower bound of Δ_CF > margin,
  where margin = 0.10 * J_strongest_fixed in days.
  An interval whose UPPER bound is below the margin is an informative negative.
  An interval spanning the margin is INCONCLUSIVE.

c_insp cancels from every paired delta at matched N, so the three c_insp values in
the original grid give identical Δ_CF; they only move the margin slightly.

NOTE ON NAMING: columns are `horizon` and `n_insp`, never `T` or `N`, because
Series.T is the transpose attribute and silently returns the row instead of the
column (this bit me once already in E1).
"""
import os
import glob
import json

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO
POLS = ["FixedEven", "FixedLate", "FixedEarly", "Random", "VoI", "Candidate"]
CINSP = (0.5, 1.0, 2.0)


def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(OUT, "E3_T*_N*_r*.json"))):
        d = json.load(open(f))
        dfl = d["delta_vs_strongest_fixed"]
        L_fixed = d["loss"]["VoI"] + dfl["VoI"]     # delta_p = L_fixed - L_p
        row = dict(horizon=d["T"], n_insp=d["N"], ratio=d["ratio"],
                   n_cond=d["n_cond"], L_fixed=L_fixed,
                   L_oracle=d["oracle_loss"],
                   headroom=float((L_fixed - d["oracle_loss"]) / L_fixed),
                   fixed_chosen=str(d["fixed_chosen"]))
        for p in POLS:
            row["d_" + p] = dfl[p]
            row["lo_" + p], row["hi_" + p] = d["delta_ci"][p]
        rows.append(row)
    D = pd.DataFrame(rows).sort_values(["horizon", "n_insp", "ratio"]).reset_index(drop=True)

    print("=" * 140)
    print("E4 · temporal policy replay, all 18 (T, N, c_f/c_w) cells · Δ_CF in days, + = policy better than strongest fixed")
    print("=" * 140)
    print("T  N  cf   n  | L_fix  L_orc  head% | VoI  Δ[lo,hi]            | Cand Δ[lo,hi]            | Late Δ[lo,hi]         | fixed chosen")
    for _, x in D.iterrows():
        print("%-2d %-2d %-4.0f %-2d | %6.2f %6.2f %5.1f | %5.2f %+6.2f[%+6.2f,%+6.2f] | %5.2f %+6.2f[%+6.2f,%+6.2f] | %+6.2f[%+6.2f,%+6.2f] | %s" % (
            x["horizon"], x["n_insp"], x["ratio"], x["n_cond"],
            x["L_fixed"], x["L_oracle"], 100 * x["headroom"],
            x["L_fixed"] - x["d_VoI"], x["d_VoI"], x["lo_VoI"], x["hi_VoI"],
            x["L_fixed"] - x["d_Candidate"], x["d_Candidate"], x["lo_Candidate"], x["hi_Candidate"],
            x["d_FixedLate"], x["lo_FixedLate"], x["hi_FixedLate"], x["fixed_chosen"]))

    print("\n" + "=" * 140)
    print("VERDICT per pre-registered rule (margin = 10% of J_fixed in days, c_insp = 1)")
    print("=" * 140)
    print("  %-2s %-2s %-4s | %-8s %-8s %-8s | %s" % ("T", "N", "cf", "margin", "VoI Δ", "VoI hi", "verdict"))
    verd = []
    for _, x in D.iterrows():
        m = 0.10 * (1.0 * x["n_insp"] + x["L_fixed"])
        if x["lo_VoI"] > m:
            v = "SUPPORTS timing value"
        elif x["hi_VoI"] < m:
            v = "NEGATIVE (upper bound < margin)"
        else:
            v = "INCONCLUSIVE"
        verd.append(v)
        print("  %-2d %-2d %-4.0f | %-8.2f %-8.2f %-8.2f | %s" % (
            x["horizon"], x["n_insp"], x["ratio"], m, x["d_VoI"], x["hi_VoI"], v))
    D["voi_verdict"] = verd
    D["margin"] = 0.10 * (1.0 * D["n_insp"] + D["L_fixed"])

    print("\n  counts: %s" % pd.Series(verd).value_counts().to_dict())
    print("  VoI Δ over 18 cells      : median %+.2f  min %+.2f  max %+.2f" % (
        D["d_VoI"].median(), D["d_VoI"].min(), D["d_VoI"].max()))
    print("  Candidate Δ over 18 cells: median %+.2f  min %+.2f  max %+.2f" % (
        D["d_Candidate"].median(), D["d_Candidate"].min(), D["d_Candidate"].max()))
    print("  Candidate − VoI (positive = VoI better): median %+.2f" % (
        (D["d_VoI"] - D["d_Candidate"]).median()))
    D["captured"] = D["d_VoI"] / (D["L_fixed"] - D["L_oracle"])
    print("  oracle headroom (days)   : median %.2f ; fraction captured by VoI: median %+.3f" % (
        (D["L_fixed"] - D["L_oracle"]).median(), D["captured"].median()))

    prim = D[(D["horizon"] == 63) & (D["n_insp"] == 2) & (D["ratio"] == 5.0)].iloc[0]
    m = 0.10 * (1.0 * prim["n_insp"] + prim["L_fixed"])
    print("\n" + "=" * 140)
    print("PRIMARY SETTING (Codex-designated: T=63, N=2, c_f/c_w=5, c_insp=1)")
    print("=" * 140)
    print("  strongest fixed selected on training conditions: %s" % prim["fixed_chosen"])
    print("  J_fixed = %.2f days   margin = %.2f days" % (prim["n_insp"] + prim["L_fixed"], m))
    print("  oracle loss %.2f -> hindsight headroom %.1f%% (%.2f days)" % (
        prim["L_oracle"], 100 * prim["headroom"], prim["L_fixed"] - prim["L_oracle"]))
    for p in ["VoI", "Candidate", "FixedLate", "Random", "FixedEarly"]:
        dv, lo, hi = prim["d_" + p], prim["lo_" + p], prim["hi_" + p]
        print("  %-11s Δ_CF %+6.2f  [%+6.2f, %+6.2f]  -> %s" % (
            p, dv, lo, hi,
            "SUPPORTS" if lo > m else ("NEGATIVE" if hi < m else "INCONCLUSIVE")))
    print("\n  margin under c_insp in {0.5, 1, 2}: %s days (verdict unaffected)" % (
        [round(0.10 * (ci * prim["n_insp"] + prim["L_fixed"]), 2) for ci in CINSP]))

    D.to_csv(os.path.join(OUT, "E4_summary.csv"), index=False)
    json.dump(D.to_dict("records"), open(os.path.join(OUT, "E4_summary.json"), "w"),
              indent=1, default=float)
    print("\nwrote E4_summary.csv / .json")


if __name__ == "__main__":
    main()
