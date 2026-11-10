# -*- coding: utf-8 -*-
"""F6 · Repair the cycle-clock admission with a DoD-aware rate, and re-audit.

WHY THIS EXISTS. F4 screened cells with
        nominal = 24/(1/Cc + 1/Cd)
which is the rate for FULL-DEPTH cycling. ISU varies depth of discharge down to
4.16%, and a partial cycle of depth d takes about d*(1/Cc + 1/Cd) hours, so the
legitimate cycle rate is larger by 1/d:

        nominal_dod = 24 / ( d * (1/Cc + 1/Cd) ),   d = mean_DoD_pct/100

The F4 screen therefore rejected shallow-DoD cells that cycle legitimately many
times per day. Condition 26 has d = 0.0416, so its legitimate rate is ~493
cycles/day, and G26C3's observed 318/day is below that.

This script re-derives the admission with the DoD-aware denominator, keeps the
same generous factor-of-4 margin, and reports exactly which cells (if any) remain
implausible. It also re-audits timestamp reversals at the CORRECT scale (relative
to the inter-cycle gap, not to lifetime span), and withdraws the F4 EFC
"undercount" claim, which compared different quantities.

Run remotely.
"""
import os
import json
import pickle

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO
MAX_RATIO = 4.0


def main():
    stress = C.load_stress()
    A = pd.read_csv(os.path.join(OUT, "F2_cell_audit.csv"))
    A = A[A.error.isna() | (A.error.astype(str).isin(["", "nan"]))].copy()
    with open(os.path.join(OUT, "F1_cycling_arrays.pkl"), "rb") as f:
        cyc = pickle.load(f)

    A["dod"] = A.cond.map(lambda g: stress.loc[g, "mean_DoD_pct"] / 100.0
                          if g in stress.index else np.nan)
    A["cc"] = A.cond.map(lambda g: stress.loc[g, "charge_C"] if g in stress.index else np.nan)
    A["cd"] = A.cond.map(lambda g: stress.loc[g, "discharge_C"] if g in stress.index else np.nan)

    A["nominal_full"] = 24.0 / (1.0 / A.cc + 1.0 / A.cd)
    A["nominal_dod"] = 24.0 / (A.dod * (1.0 / A.cc + 1.0 / A.cd))
    A["ratio_full"] = A.cycles_per_day / A.nominal_full
    A["ratio_dod"] = A.cycles_per_day / A.nominal_dod

    print("=== DoD-aware repair of the cycle admission ===")
    print("  DoD across conditions: min %.2f%%  median %.2f%%  max %.2f%%" % (
        100 * A.dod.min(), 100 * A.dod.median(), 100 * A.dod.max()))
    print("  nominal_full (cycles/day): median %.1f" % A.nominal_full.median())
    print("  nominal_dod  (cycles/day): min %.1f  median %.1f  max %.1f" % (
        A.nominal_dod.min(), A.nominal_dod.median(), A.nominal_dod.max()))
    print("\n  measured/nominal_FULL : median %.2f  max %.2f   -> %d cells above %.0fx" % (
        A.ratio_full.median(), A.ratio_full.max(), int((A.ratio_full > MAX_RATIO).sum()), MAX_RATIO))
    print("  measured/nominal_DOD  : median %.2f  max %.2f   -> %d cells above %.0fx" % (
        A.ratio_dod.median(), A.ratio_dod.max(), int((A.ratio_dod > MAX_RATIO).sum()), MAX_RATIO))

    A["cycle_clock_admitted"] = A.ratio_dod <= MAX_RATIO
    print("\n  ADMITTED (DoD-aware, <=%.0fx): %d / %d" % (
        MAX_RATIO, int(A.cycle_clock_admitted.sum()), len(A)))
    still = A[~A.cycle_clock_admitted]
    if len(still):
        print("  still implausible:")
        print(still[["cell", "cond", "dod", "cycles_per_day", "nominal_dod", "ratio_dod"]]
              .to_string(index=False))
    else:
        print("  -> every cell now has a physically plausible per-cycle clock")

    print("\n  the previously excluded cells, re-judged:")
    prev = ["G42C1", "G42C2", "G42C3", "G42C4", "G49C1", "G49C2", "G49C3", "G59C4"]
    sub = A[A.cell.isin(prev)]
    print(sub[["cell", "cond", "dod", "cycles_per_day", "nominal_full", "nominal_dod",
               "ratio_full", "ratio_dod", "cycle_clock_admitted"]].to_string(index=False))

    # ---------- reversal audit at the correct scale ----------
    print("\n=== reversal audit at the correct scale (vs the inter-cycle gap) ===")
    rows = []
    for cell in A.cell:
        ts = np.asarray(cyc.get(cell, {}).get("_cycle_ts", []), dtype="int64")
        if ts.size < 3:
            continue
        days = (ts - ts[0]) / 86400e9
        gaps = np.diff(days)
        pos = gaps[gaps > 0]
        rev = gaps[gaps < 0]
        if rev.size == 0:
            rows.append(dict(cell=cell, n_rev=0, rev_max=0.0, gap_med=float(np.median(pos)),
                             rev_over_gap=0.0))
        else:
            gm = float(np.median(pos)) if pos.size else np.nan
            rows.append(dict(cell=cell, n_rev=int(rev.size), rev_max=float(-rev.min()),
                             gap_med=gm, rev_over_gap=float(-rev.min() / gm)))
    R = pd.DataFrame(rows)
    print("  cells with reversals: %d / %d" % (int((R.n_rev > 0).sum()), len(R)))
    print("  largest reversal / median inter-cycle gap: median %.2f  p95 %.2f  max %.2f" % (
        R.rev_over_gap.median(), R.rev_over_gap.quantile(.95), R.rev_over_gap.max()))
    print("  largest reversal (days): median %.4f  max %.4f" % (R.rev_max.median(), R.rev_max.max()))
    print("  -> a reversal comparable to one inter-cycle gap means the ORDER of two")
    print("     adjacent records is ambiguous, not that exposure is lost. Exposure")
    print("     is assigned by timestamp, so an ordering ambiguity moves at most one")
    print("     cycle's Ah across an RPT boundary.")

    # ---------- withdraw the EFC claim ----------
    print("\n=== EFC claim: WITHDRAWN ===")
    print("  F4 compared a MEASURED PARTIAL-CYCLE COUNT against a NOMINAL")
    print("  FULL-EQUIVALENT-CYCLE rate. Those are different quantities, so the")
    print("  '1.8x undercount' figure is not a bias estimate and is retracted.")
    print("  Correct definitions, both reported below:")
    # charge-based EFC with a fixed reference capacity Q_ref = rated 0.250 Ah
    QREF = 0.250
    A["efc_ch"] = A.sum_ah_ch / QREF
    A["efc_2sided"] = (A.sum_ah_ch + A.sum_ah_dis) / (2.0 * QREF)
    print("    EFC_charge = cum charge Ah / Q_ref        : median %.0f" % A.efc_ch.median())
    print("    EFC_2sided = (ch+dis) Ah / (2 Q_ref)      : median %.0f" % A.efc_2sided.median())
    print("    physical cycle count                      : median %.0f" % A.n_cycles.median())
    print("  The earlier B-line conclusion about nominal EFC must be re-derived with")
    print("  one of these explicit conventions, not reversed by assertion.")

    A.to_csv(os.path.join(OUT, "F6_admission_dod.csv"), index=False)
    R.to_csv(os.path.join(OUT, "F6_reversal_audit.csv"), index=False)
    out = dict(max_ratio=MAX_RATIO,
               dod_min=float(A.dod.min()), dod_max=float(A.dod.max()),
               n_cells=int(len(A)),
               n_admitted_full=int((A.ratio_full <= MAX_RATIO).sum()),
               n_admitted_dod=int(A.cycle_clock_admitted.sum()),
               still_implausible=sorted(still.cell.tolist()),
               rev_over_gap_max=float(R.rev_over_gap.max()),
               rev_cells=int((R.n_rev > 0).sum()),
               efc_withdrawn=True,
               efc_charge_median=float(A.efc_ch.median()),
               efc_2sided_median=float(A.efc_2sided.median()),
               cycles_median=float(A.n_cycles.median()))
    json.dump(out, open(os.path.join(OUT, "F6_admission_dod.json"), "w"), indent=1, default=float)
    print("\nwrote F6_admission_dod.csv / F6_reversal_audit.csv / F6_admission_dod.json")


if __name__ == "__main__":
    main()
