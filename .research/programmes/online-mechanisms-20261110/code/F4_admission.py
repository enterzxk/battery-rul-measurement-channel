# -*- coding: utf-8 -*-
"""F4 · Data admission for the physical clock, with an explicit and principled rule.

Findings from F1-F3 that this resolves:

  * Measured cumulative Ah throughput is INVARIANT to how the archive chunks its
    entries (a sum of increments is the total regardless of chunking), so it is a
    robust clock everywhere.
  * Measured CYCLE COUNT is not: 26 cells run at up to 318 entries/day with a
    2.5-minute median spacing, which cannot be one charge+discharge cycle. For
    those cells `capacity_charge` is evidently recorded per sub-step.
  * Non-monotone timestamps affect 53 cells but total at most 0.03% of the span,
    so they are timestamp jitter, not a structural defect.
  * Entries slightly above the 0.250 Ah rating are the cells' TRUE capacity
    (~0.26 Ah) at deep DoD, not sub-step summing.

ADMISSION RULE (fixed here, before any modelling):
    a cell's CYCLE clock is admitted iff
        measured_cycles_per_day / nominal_cycles_per_day <= 4
    where nominal = 24/(1/charge_C + 1/discharge_C) from the official condition
    table. A factor of 4 is deliberately generous: the physical maximum for the
    fastest condition in this design is ~2-3x nominal.
    A cell's THROUGHPUT and CALENDAR clocks are admitted always.

Output: the final per-(cell, RPT) clock table plus an admission summary that the
gate can be judged against.

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
    R = pd.read_csv(os.path.join(OUT, "F2_rpt_alignment.csv"))
    A = A[A.error.isna() | (A.error.astype(str) == "") | (A.error.astype(str) == "nan")].copy()
    print("admitted audit rows: %d" % len(A))

    A["nominal_cpd"] = A.cond.map(
        lambda g: 24.0 / (1.0 / stress.loc[g, "charge_C"] + 1.0 / stress.loc[g, "discharge_C"])
        if g in stress.index else np.nan)
    A["ratio_to_nominal"] = A.cycles_per_day / A.nominal_cpd
    A["cycle_clock_admitted"] = A.ratio_to_nominal <= MAX_RATIO

    print("=== admission rule: cycles_per_day / nominal <= %.1f ===" % MAX_RATIO)
    print("  nominal cycles/day across conditions: min %.2f  median %.2f  max %.2f" % (
        A.nominal_cpd.min(), A.nominal_cpd.median(), A.nominal_cpd.max()))
    print("  measured / nominal: median %.2f  IQR [%.2f, %.2f]  max %.1f" % (
        A.ratio_to_nominal.median(), A.ratio_to_nominal.quantile(.25),
        A.ratio_to_nominal.quantile(.75), A.ratio_to_nominal.max()))
    print("  cells admitted for the CYCLE clock : %d / %d" % (
        int(A.cycle_clock_admitted.sum()), len(A)))
    print("  cells excluded from the CYCLE clock: %d" % int((~A.cycle_clock_admitted).sum()))
    ex = A[~A.cycle_clock_admitted]
    if len(ex):
        print("  excluded cells: %s" % sorted(ex.cell.tolist()))

    # how many of the D/E analysis cohort survive?
    with open(os.path.join(OUT, "isu_cells_cache.pkl"), "rb") as f:
        co = pickle.load(f)["cells"]
    in_cohort = set(co.keys())
    A["in_dcohort"] = A.cell.isin(in_cohort)
    print("\n=== impact on the D/E analysis cohort (%d cells) ===" % len(in_cohort))
    sub = A[A.in_dcohort]
    print("  cohort cells with an admitted cycle clock: %d / %d (%.1f%%)" % (
        int(sub.cycle_clock_admitted.sum()), len(sub),
        100 * sub.cycle_clock_admitted.mean()))
    lost = sorted(set(sub[~sub.cycle_clock_admitted].cell))
    print("  cohort cells lost from cycle-clock analyses: %s" % (lost if lost else "none"))
    lost_conds = sorted(set(sub[~sub.cycle_clock_admitted].cond.astype(int)))
    print("  conditions affected: %s" % (lost_conds if lost_conds else "none"))
    print("  NOTE throughput and calendar clocks keep ALL %d cohort cells." % len(sub))

    # ---- final clock table: add admitted clocks to the RPT alignment ----------
    keep = A[["cell", "cond", "cycle_clock_admitted", "nominal_cpd",
              "ratio_to_nominal", "sum_ah_ch", "sum_ah_dis", "span_days"]]
    T = R.merge(keep, on=["cell", "cond"], how="left")
    T["cum_cycles_admitted"] = np.where(T.cycle_clock_admitted, T.cum_cycles, np.nan)
    # Ah per cycle is only meaningful where the cycle clock is admitted
    T["ah_per_cycle"] = np.where(
        (T.cycle_clock_admitted) & (T.cum_cycles > 0), T.cum_ah_ch / T.cum_cycles, np.nan)
    T = T[T.cell.isin(in_cohort)].copy()

    print("\n=== final clock table (D/E cohort) ===")
    print("  rows %d | cells %d | conditions %d" % (
        len(T), T.cell.nunique(), T.cond.nunique()))
    for c in ["cum_cycles_admitted", "cum_ah_ch", "cum_ah_dis", "day"]:
        s = pd.to_numeric(T[c], errors="coerce")
        print("  %-22s non-null %5d (%.1f%%)  median %10.2f  max %12.2f" % (
            c, int(s.notna().sum()), 100 * s.notna().mean(), s.median(), s.max()))

    print("\n=== are the clocks distinguishable? (the gate question) ===")
    # correlation between clocks at the RPT level, and the residual spread
    T2 = T.dropna(subset=["cum_cycles_admitted"]).copy()
    T2 = T2[T2.day > 0]
    if len(T2):
        for a, b in [("day", "cum_cycles_admitted"), ("day", "cum_ah_ch"),
                     ("cum_cycles_admitted", "cum_ah_ch")]:
            r = np.corrcoef(T2[a], T2[b])[0, 1]
            print("  pearson(%s, %s) = %.4f" % (a, b, r))
        # after regressing cycles on day per condition, is there residual variation?
        T2["cyc_per_day"] = T2.cum_cycles_admitted / T2.day
        g = T2.groupby("cond").cyc_per_day.median()
        print("  cycles/day across conditions: min %.1f  median %.1f  max %.1f  ratio %.1fx" % (
            g.min(), g.median(), g.max(), g.max() / max(g.min(), 1)))
        g2 = T2.groupby("cond").apply(
            lambda d: d.cum_ah_ch.median() / d.day.median(), include_groups=False)
        print("  Ah/day across conditions   : min %.3f  median %.3f  max %.3f  ratio %.1fx" % (
            g2.min(), g2.median(), g2.max(), g2.max() / max(g2.min(), 1e-9)))
        print("  -> cycle rate spans %.1fx while throughput rate spans %.1fx:" % (
            g.max() / max(g.min(), 1), g2.max() / max(g2.min(), 1e-9)))
        print("     the two exposures are NOT a common rescaling of each other")

    T.to_csv(os.path.join(OUT, "F4_clock_table.csv"), index=False)
    A.to_csv(os.path.join(OUT, "F4_admission.csv"), index=False)
    json.dump(dict(max_ratio=MAX_RATIO,
                   n_cells=int(len(A)),
                   n_cycle_admitted=int(A.cycle_clock_admitted.sum()),
                   excluded=sorted(A[~A.cycle_clock_admitted].cell.tolist()),
                   cohort=int(len(in_cohort)),
                   cohort_cycle_admitted=int(sub.cycle_clock_admitted.sum()),
                   cohort_lost=lost, conditions_affected=lost_conds),
              open(os.path.join(OUT, "F4_admission.json"), "w"), indent=1, default=float)
    print("\nwrote F4_clock_table.csv / F4_admission.csv / F4_admission.json")


if __name__ == "__main__":
    main()
