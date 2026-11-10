# -*- coding: utf-8 -*-
"""F5 · Does the release-version split bias cell selection? (data gate item 6)

The archive ships two subfolders. F1 found Release 1.0 = 238 cells and
Release 2.0 = 13 cells, and the 13 match the official `process_data.py` batch2
list exactly. But the cycle-clock admission rule (F4) excluded 8 cells, and 3 of
them (G49C1-C3) are Release 2.0 — i.e. 23% of Release 2.0 versus ~2% of
Release 1.0. If the version split correlates with the exclusion, the admitted
cohort is version-selected and that must be stated.

Also reports whether the two releases differ on the measured clocks themselves.

Run remotely.
"""
import os
import json

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO


def main():
    F1 = pd.read_csv(os.path.join(OUT, "F1_cycling_cells.csv"))
    A = pd.read_csv(os.path.join(OUT, "F4_admission.csv"))
    F1["release_tag"] = F1.release.str.extract(r"(Release \d\.\d)")
    M = F1[["cell", "release_tag"]].merge(A, on="cell", how="inner")

    print("=== release composition ===")
    print(M.groupby("release_tag").agg(
        n=("cell", "size"),
        admitted=("cycle_clock_admitted", "sum"),
        excl=("cycle_clock_admitted", lambda s: int((~s.astype(bool)).sum())),
        cpd_med=("cycles_per_day", "median"),
        ratio_med=("ratio_to_nominal", "median"),
        span_med=("span_days", "median"),
        ah_med=("sum_ah_ch", "median")).to_string())

    print("\n=== exclusion rate by release ===")
    for rel, g in M.groupby("release_tag"):
        ex = int((~g.cycle_clock_admitted.astype(bool)).sum())
        print("  %-12s excluded %d / %d (%.1f%%)" % (rel, ex, len(g), 100 * ex / len(g)))
    r2 = M[M.release_tag == "Release 2.0"]
    r1 = M[M.release_tag == "Release 1.0"]
    print("  excluded cells in Release 2.0: %s" % sorted(
        r2[~r2.cycle_clock_admitted.astype(bool)].cell.tolist()))
    print("  excluded cells in Release 1.0: %s" % sorted(
        r1[~r1.cycle_clock_admitted.astype(bool)].cell.tolist()))

    print("\n=== do the releases differ on the measured clocks? (admitted cells only) ===")
    adm = M[M.cycle_clock_admitted.astype(bool)]
    for col in ["cycles_per_day", "ratio_to_nominal", "span_days", "sum_ah_ch"]:
        a = adm[adm.release_tag == "Release 1.0"][col].dropna()
        b = adm[adm.release_tag == "Release 2.0"][col].dropna()
        print("  %-18s R1 median %10.2f (n=%d) | R2 median %10.2f (n=%d)" % (
            col, a.median(), len(a), b.median(), len(b)))

    print("\n=== do the releases occupy different conditions? ===")
    print("  R2 conditions: %s" % sorted(r2.cond.astype(int).unique().tolist()))
    print("  conditions appearing ONLY in R2: %s" % sorted(
        set(r2.cond.astype(int)) - set(r1.cond.astype(int))))

    out = dict(
        r1=int(len(r1)), r2=int(len(r2)),
        r1_excl=int((~r1.cycle_clock_admitted.astype(bool)).sum()),
        r2_excl=int((~r2.cycle_clock_admitted.astype(bool)).sum()),
        r2_excluded_cells=sorted(r2[~r2.cycle_clock_admitted.astype(bool)].cell.tolist()),
        r2_conditions=sorted(int(x) for x in r2.cond.unique()),
        r2_only_conditions=sorted(int(x) for x in (set(r2.cond.astype(int)) - set(r1.cond.astype(int)))))
    json.dump(out, open(os.path.join(OUT, "F5_version.json"), "w"), indent=1, default=float)
    M.to_csv(os.path.join(OUT, "F5_version.csv"), index=False)
    print("\nwrote F5_version.csv / F5_version.json")


if __name__ == "__main__":
    main()
