# -*- coding: utf-8 -*-
"""E2 · Data-admission audit: implausible capacity excursions in the ISU series.

An independent literature-scout agent, reading the raw capacity audit and the
lifetime tables, reported single-step SOH drops as large as 49.4 pp (G5C2) with
the cell then recovering, and a minimum SOH of 13.1 % on a cell whose final SOH
is ~83 %. A cell cannot lose 49 pp in one weekly reference test and recover, so
these are almost certainly failed or partial RPT records.

Why this matters for everything already reported:

  * `load_isu` defines EOL as the FIRST index with soh <= 0.80. A spurious dip
    below 0.80 therefore sets U too early, and every EOL target derived from it
    is wrong for that cell.
  * The health features (soh_last, ols_slope, frac_loss) are read off the same
    series, so a corrupt record also corrupts the predictor at any query time
    after it.

This script does NOT change any prior result. It measures the hazard, and it
freezes a defensible alternative endpoint rule so the sensitivity can be run:

  SIMPLE    : first index k with soh[k] <= 0.80                      (current)
  SUSTAINED : first index k with soh[j] <= 0.80 for ALL j >= k       (robust)

Run remotely (workspace compute rule).
"""
import os
import json

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO
THRESH = 0.80
DROP_FLAGS = (5.0, 10.0, 20.0)      # percentage points, single step


def crossings(soh, thr=THRESH):
    """Return (simple_index, sustained_index) or None."""
    below = soh <= thr
    if not below.any():
        return None, None
    simple = int(np.argmax(below))
    # sustained: last index from which everything stays below
    if below[-1]:
        # find the start of the trailing run of True
        j = len(below) - 1
        while j > 0 and below[j - 1]:
            j -= 1
        sustained = int(j)
    else:
        sustained = None
    return simple, sustained


def main():
    cells = C.load_isu()
    stress = C.load_stress()
    print("ISU cells loaded: %d   stress conditions in table: %d" % (len(cells), len(stress)))

    recs = []
    for name, s in cells.items():
        x, soh = s["x"], s["soh"]
        d = np.diff(soh)
        worst = float(np.nanmin(d)) if len(d) else 0.0        # most negative step
        recs.append(dict(
            cell=name, cond=s["cond"], n_rpt=len(soh),
            max_step_drop_pp=100.0 * (-worst),
            min_soh=float(np.nanmin(soh)), last_soh=float(soh[-1]),
            L=float(s["L"]), U=float(s["U"]),
            life=float(s["U"]),
        ))
    D = pd.DataFrame(recs)

    print("\n=== 1. single-step drop distribution (percentage points) ===")
    print(D.max_step_drop_pp.describe().to_string())
    for t in DROP_FLAGS:
        n = int((D.max_step_drop_pp > t).sum())
        print("  cells with a single-step drop > %4.1f pp : %3d (%.1f%%)  conditions: %d" % (
            t, n, 100.0 * n / len(D), D[D.max_step_drop_pp > t].cond.nunique()))
    top = D.sort_values("max_step_drop_pp", ascending=False).head(8)
    print("\n  worst offenders:")
    print(top[["cell", "cond", "n_rpt", "max_step_drop_pp", "min_soh", "last_soh"]]
          .to_string(index=False))

    print("\n=== 2. does a spurious dip break the EOL target? ===")
    rows = []
    for name, s in cells.items():
        si, su = crossings(s["soh"])
        rows.append(dict(cell=name, cond=s["cond"], simple=si, sustained=su,
                         n=len(s["soh"])))
    X = pd.DataFrame(rows)
    X["differs"] = X.simple != X.sustained
    n_no_sustained = int(X.sustained.isna().sum())
    print("  cells where SIMPLE != SUSTAINED : %d / %d (%.1f%%)" % (
        int(X.differs.sum()), len(X), 100.0 * X.differs.mean()))
    print("  cells with NO sustained crossing (never stays below 0.80): %d" % n_no_sustained)
    print("  affected conditions: %d" % X[X.differs].cond.nunique())
    if X.differs.any():
        sh = X[X.differs].merge(D[["cell", "life", "max_step_drop_pp"]], on="cell", how="left")
        sh["shift_days"] = np.nan
        for i, r in sh.iterrows():
            s = cells[r["cell"]]
            a, b = r["simple"], r["sustained"]
            if a is not None and b is not None:
                sh.at[i, "shift_days"] = float(s["x"][b] - s["x"][a])
        print("\n  shift of the EOL interval when using the sustained rule (days):")
        print(sh.shift_days.describe().to_string())
        print("\n  worst shifts:")
        print(sh.sort_values("shift_days", ascending=False)
              .head(8)[["cell", "cond", "simple", "sustained", "shift_days",
                        "max_step_drop_pp", "life"]].to_string(index=False))

    print("\n=== 3. condition reconciliation (63 in table vs 51 in the D-line analyses) ===")
    cond_cells = D.groupby("cond").size()
    missing = sorted(set(stress.index) - set(cond_cells.index))
    print("  conditions with >=1 loaded cell : %d" % len(cond_cells))
    print("  conditions in the table but with 0 loaded cells: %s" % (missing if missing else "none"))
    print("  cells per condition: min %d  median %.0f  max %d" % (
        cond_cells.min(), cond_cells.median(), cond_cells.max()))
    print("  NOTE: 250 raw cells -> %d loaded here; the gap is the capacity/timestamp" % len(D))
    print("        admission filter in load_isu (L<4 or unparseable timestamps).")

    D.to_csv(os.path.join(OUT, "E2_datahazard_cells.csv"), index=False)
    X.to_csv(os.path.join(OUT, "E2_crossing_rules.csv"), index=False)
    summary = dict(
        n_cells=int(len(D)),
        n_cond_with_cells=int(len(cond_cells)),
        cond_missing=sorted(int(m) for m in missing),
        drop_gt=  {str(t): int((D.max_step_drop_pp > t).sum()) for t in DROP_FLAGS},
        cells_rule_differs=int(X.differs.sum()),
        cells_no_sustained=n_no_sustained,
        conds_rule_differs=int(X[X.differs].cond.nunique()),
        rule=dict(SIMPLE="first index with soh<=0.80",
                  SUSTAINED="first index from which all later observations are <=0.80"),
    )
    json.dump(summary, open(os.path.join(OUT, "E2_datahazard.json"), "w"), indent=1)
    print("\nwrote E2_datahazard_cells.csv / E2_crossing_rules.csv / E2_datahazard.json")


if __name__ == "__main__":
    main()
