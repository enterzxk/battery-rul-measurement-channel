# -*- coding: utf-8 -*-
"""E0 · Feasibility probe for the temporal policy replay (ISU).

Answers only the questions that decide whether the Stage-E design is even
constructible, before any pre-registration is frozen:

  1. How many reference tests (RPTs) exist per cell before a candidate decision
     horizon T, and are there enough to define a non-trivial action space?
  2. Is the RPT grid synchronised across cells, so that "the j-th candidate
     inspection time" means the same thing for every cell?
  3. What are L, U and the midpoint EOL, and how wide is the censoring interval
     relative to life?
  4. How large is the subset space at N = 1, 2, 3?

No modelling, no policy, no claims. Read-only.

Run remotely (workspace compute rule).
"""
import os
import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO
HORIZONS = (42, 49, 56, 63, 70, 84)


def main():
    cells = C.load_isu()
    print("ISU cells loaded: %d" % len(cells))
    recs = []
    for name, s in cells.items():
        x, L, U = s["x"], s["L"], s["U"]
        d = dict(cell=name, cond=s["cond"], n_rpt=len(x),
                 x_first=float(x[0]), x_last=float(x[-1]),
                 L=float(L), U=float(U), mid=float((L + U) / 2.0),
                 width=float(U - L))
        gaps = np.diff(x)
        d["gap_med"] = float(np.median(gaps)) if len(gaps) else np.nan
        d["gap_min"] = float(gaps.min()) if len(gaps) else np.nan
        d["gap_max"] = float(gaps.max()) if len(gaps) else np.nan
        for T in HORIZONS:
            d["m_T%d" % T] = int((x <= T).sum())
            d["ok_T%d" % T] = bool(T < L and (x <= T).sum() >= 3)
        recs.append(d)
    D = pd.DataFrame(recs)

    print("\n=== 1. per-cell reference-test structure ===")
    print(D[["n_rpt", "gap_med", "gap_min", "gap_max", "L", "U", "width"]]
          .describe().T.to_string())
    print("\n  censoring interval width / life: median %.4f  p95 %.4f" % (
        (D.width / D.U).median(), (D.width / D.U).quantile(.95)))
    print("  life (U) days: median %.1f  IQR [%.1f, %.1f]" % (
        D.U.median(), D.U.quantile(.25), D.U.quantile(.75)))

    print("\n=== 2. candidate action space per horizon T ===")
    print("  %-4s %-8s %-8s %-8s %-10s %-10s %s" % (
        "T", "eligible", "conds", "m_med", "m_min", "m_max", "subsets N=1/2/3 (median C(m,N))"))
    for T in HORIZONS:
        sub = D[D["ok_T%d" % T]]
        m = sub["m_T%d" % T]
        if len(sub) == 0:
            print("  %-4d %-8d %-8d %s" % (T, 0, 0, "(no cells)"))
            continue
        def c(n, k):
            from math import comb
            return comb(int(n), k) if n >= k else 0
        s1 = np.median([c(v, 1) for v in m])
        s2 = np.median([c(v, 2) for v in m])
        s3 = np.median([c(v, 3) for v in m])
        print("  %-4d %-8d %-8d %-8.1f %-10d %-10d %.0f / %.0f / %.0f" % (
            T, len(sub), sub.cond.nunique(), m.median(), m.min(), m.max(), s1, s2, s3))

    print("\n=== 3. is the RPT grid synchronised across cells? ===")
    # compare the j-th RPT time across cells (relative to each cell's own first)
    maxj = 8
    mat = np.full((len(D), maxj), np.nan)
    for i, (name, s) in enumerate(cells.items()):
        x = s["x"]
        mat[i, :min(len(x), maxj)] = x[:maxj]
    for j in range(maxj):
        col = mat[:, j]
        col = col[np.isfinite(col)]
        if len(col) < 10:
            continue
        print("  RPT #%d : n=%3d  median %6.1f d  IQR [%5.1f, %5.1f]  CV %.3f" % (
            j, len(col), np.median(col), np.percentile(col, 25),
            np.percentile(col, 75), np.std(col) / np.mean(col)))

    print("\n=== 4. would a policy's choice actually change the observable history? ===")
    # how much do the candidate times differ from the evenly-spaced / endpoint picks
    T = 63
    sub = D[D["ok_T%d" % T]]
    diffs = []
    for name, s in cells.items():
        x = s["x"]
        cand = x[x <= T]
        if len(cand) < 3 or T >= s["L"]:
            continue
        diffs.append(len(cand))
    print("  at T=%d, candidate times per cell: median %.0f, min %d, max %d" % (
        T, np.median(diffs), min(diffs), max(diffs)))
    print("  -> a policy choosing N=1 of m has m distinct observable histories per cell")

    D.to_csv(os.path.join(OUT, "E0_feasibility.csv"), index=False)
    print("\nwrote E0_feasibility.csv")


if __name__ == "__main__":
    main()
