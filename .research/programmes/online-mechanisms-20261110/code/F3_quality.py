# -*- coding: utf-8 -*-
"""F3 · Data-quality investigation of the recovered cycling clock.

F1/F2 raised three flags that must be resolved before any gate or model:

  Q1 EXTREME CYCLE COUNTS. n_cap_charge ranges 62 .. 172,319. At a median
     inter-cycle gap of 0.04 d, 256 cycles/day is physically impossible, so for
     some cells `capacity_charge` is probably one entry per STEP, not per cycle.
     If that is true the cycle clock is NOT comparable across cells.

  Q2 NON-MONOTONE TIMESTAMPS in 50 cells. Where are the reversals, how large,
     and do they break the cumulative-throughput integration?

  Q3 PER-ENTRY AH PLAUSIBILITY. A 0.250 Ah rated cell cannot move more than
     ~0.25 Ah in one cycle; entries far above that indicate sub-step summing or
     a different quantity.

Method: for each cell compute the per-entry increments and gaps, then classify.

Run remotely (reads the compact F1 pickle, not the archive).
"""
import os
import json
import pickle

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO
RATED_AH = 0.250


def main():
    with open(os.path.join(OUT, "F1_cycling_arrays.pkl"), "rb") as f:
        cyc = pickle.load(f)
    F1 = pd.read_csv(os.path.join(OUT, "F1_cycling_cells.csv")).set_index("cell")
    stress = C.load_stress()

    rows = []
    for cell, info in sorted(cyc.items()):
        ts = np.asarray(info.get("_cycle_ts", []), dtype="int64")
        if ts.size < 2:
            continue
        days = (ts - ts[0]) / 86400e9
        gaps = np.diff(days)
        cum_ch = np.asarray(info.get("_cum_ah_ch", []), float)
        inc = np.diff(np.concatenate([[0.0], cum_ch])) if cum_ch.size else np.array([])

        n = ts.size
        span = float(days[-1])
        rev = gaps[gaps < 0]
        rows.append(dict(
            cell=cell, cond=int(F1.loc[cell, "release"].split()[-1] == "2.0") if False else 0,
            n_entries=int(n), span_days=span,
            entries_per_day=float(n / span) if span > 0 else np.nan,
            frac_zero_gap=float((gaps == 0).mean()) if gaps.size else np.nan,
            gap_med=float(np.median(gaps)) if gaps.size else np.nan,
            n_reversals=int(rev.size), rev_total_days=float(-rev.sum()) if rev.size else 0.0,
            rev_max_days=float(-rev.min()) if rev.size else 0.0,
            inc_med=float(np.median(inc[inc > 0])) if (inc > 0).any() else np.nan,
            inc_p95=float(np.percentile(inc[inc > 0], 95)) if (inc > 0).any() else np.nan,
            frac_inc_gt_rated=float((inc > RATED_AH * 1.05).mean()) if inc.size else np.nan,
            sum_ah=float(cum_ch[-1]) if cum_ch.size else np.nan))
    D = pd.DataFrame(rows)
    D["cond"] = D.cell.str.extract(r"G(\d+)").astype(int)
    D["ah_per_day"] = D.sum_ah / D.span_days

    print("=== Q1 · extreme cycle counts ===")
    print("  entries_per_day: min %.1f  median %.1f  p95 %.1f  max %.1f" % (
        D.entries_per_day.min(), D.entries_per_day.median(),
        D.entries_per_day.quantile(.95), D.entries_per_day.max()))
    print("  a real charge+discharge cycle cannot repeat faster than ~60/day at 0.5C/0.5C")
    print("\n  top 10 by entry count:")
    print(D.nlargest(10, "n_entries")[
        ["cell", "n_entries", "span_days", "entries_per_day", "frac_zero_gap", "gap_med"]
    ].to_string(index=False))

    print("\n=== Q2 · non-monotone timestamps ===")
    bad = D[D.n_reversals > 0]
    print("  cells with reversals: %d" % len(bad))
    if len(bad):
        print("  reversals per cell : median %.0f  max %.0f" % (
            bad.n_reversals.median(), bad.n_reversals.max()))
        print("  total reversed time: median %.3f d  max %.3f d" % (
            bad.rev_total_days.median(), bad.rev_total_days.max()))
        print("  reversed time as %% of span: median %.4f%%  max %.2f%%" % (
            100 * (bad.rev_total_days / bad.span_days).median(),
            100 * (bad.rev_total_days / bad.span_days).max()))
        print("\n  worst 8:")
        print(bad.nlargest(8, "rev_total_days")[
            ["cell", "n_reversals", "rev_total_days", "rev_max_days", "span_days"]].to_string(index=False))

    print("\n=== Q3 · per-entry Ah plausibility ===")
    print("  entries above 1.05x rated capacity: median fraction %.4f  max %.4f" % (
        D.frac_inc_gt_rated.median(), D.frac_inc_gt_rated.max()))
    print("  inc_med: median %.4f   inc_p95: median %.4f" % (
        D.inc_med.median(), D.inc_p95.median()))
    print("\n  cells where >5%% of entries exceed rated capacity:")
    over = D[D.frac_inc_gt_rated > 0.05]
    print("    count %d / %d" % (len(over), len(D)))
    if len(over):
        print(over.nlargest(8, "frac_inc_gt_rated")[
            ["cell", "n_entries", "inc_med", "inc_p95", "frac_inc_gt_rated"]].to_string(index=False))

    print("\n=== verdict inputs ===")
    # a cell is treated as "per-cycle" if entries/day is physically possible
    D["plausible_cycle_clock"] = D.entries_per_day <= 60
    print("  cells with a physically plausible per-cycle clock: %d / %d (%.1f%%)" % (
        int(D.plausible_cycle_clock.sum()), len(D), 100 * D.plausible_cycle_clock.mean()))
    print("  cells flagged implausible: %s" % D[~D.plausible_cycle_clock].cell.tolist()[:20])

    print("\n=== condition-level measured throughput rate (Ah/day) ===")
    g = D.groupby("cond").agg(n=("cell", "size"), ah_day_med=("ah_per_day", "median"),
                              cyc_day_med=("entries_per_day", "median")).reset_index()
    g = g.merge(stress.reset_index().rename(columns={"group": "cond"}), on="cond", how="left")
    print(g.head(20).to_string(index=False))

    D.to_csv(os.path.join(OUT, "F3_quality.csv"), index=False)
    g.to_csv(os.path.join(OUT, "F3_condition_exposure.csv"), index=False)
    json.dump(dict(n_cells=int(len(D)),
                   entries_per_day_max=float(D.entries_per_day.max()),
                   n_implausible=int((~D.plausible_cycle_clock).sum()),
                   n_reversal_cells=int((D.n_reversals > 0).sum()),
                   rev_frac_span_max=float((D.rev_total_days / D.span_days).max()),
                   n_over_rated=int((D.frac_inc_gt_rated > 0.05).sum())),
              open(os.path.join(OUT, "F3_quality.json"), "w"), indent=1, default=float)
    print("\nwrote F3_quality.csv / F3_condition_exposure.csv / F3_quality.json")


if __name__ == "__main__":
    main()
