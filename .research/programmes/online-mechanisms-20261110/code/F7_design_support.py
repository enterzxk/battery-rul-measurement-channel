# -*- coding: utf-8 -*-
"""F7 · Design-support diagnostic: is a calendar/cycle/throughput decomposition identified?

Codex's objection (gate item 7): pooled correlations show the clocks are not
identical, but they do NOT show the effects are separable. Within one condition a
cell cycles at a nearly constant rate, so over any interval
        dN ~ r_c * dt   and   dQ ~ a_c * dt
and the exposure terms are then absorbed by condition-specific age effects.
Identifiability has to come from contrasts, so this script measures them BEFORE
any outcome model is fitted (no outcome is used for fitting here; dSOH is reported
only descriptively).

Outputs
  1. within-condition collinearity of (dt, dN, dQ)  -- the identifying variation
  2. between-condition collinearity of the same
  3. rank, singular values, condition number and VIF of the within-transformed
     design, equal-condition weighted, as Codex specified
  4. support for the three contrasts Codex named:
        (a) different elapsed time at comparable N and Q
        (b) different N at comparable time and Q
        (c) different Q at comparable time and N
  5. the same diagnostics restricted to Release 1.0

Run remotely.
"""
import os
import json

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO
COND_NUM_MAX = 30.0
VIF_MAX = 10.0


def vif(X):
    """VIF per column of a design matrix with no intercept."""
    out = []
    for j in range(X.shape[1]):
        y = X[:, j]
        Z = np.delete(X, j, axis=1)
        Z = np.column_stack([np.ones(len(Z)), Z])
        beta, *_ = np.linalg.lstsq(Z, y, rcond=None)
        resid = y - Z @ beta
        ss_res = float(resid @ resid)
        ss_tot = float(((y - y.mean()) ** 2).sum())
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
        out.append(1.0 / max(1e-12, 1.0 - r2) if r2 < 1 else np.inf)
    return np.array(out)


def diagnose(T, tag):
    print("\n" + "=" * 78)
    print("%s · %d intervals / %d cells / %d conditions" % (
        tag, len(T), T.cell.nunique(), T.cond.nunique()))
    print("=" * 78)
    X3 = T[["dt", "dN", "dQ"]].values.astype(float)
    ok = np.isfinite(X3).all(axis=1) & (T.dt.values > 0)
    T = T[ok].copy(); X3 = X3[ok]
    print("  usable intervals: %d" % len(T))

    print("\n  1. WITHIN-condition correlations (the identifying variation)")
    for a, b in [("dt", "dN"), ("dt", "dQ"), ("dN", "dQ")]:
        rs = []
        for g, d in T.groupby("cond"):
            if len(d) < 8:
                continue
            r = np.corrcoef(d[a], d[b])[0, 1]
            if np.isfinite(r):
                rs.append(r)
        print("    corr(%s,%s): median %.4f  IQR [%.4f, %.4f]  n_cond %d" % (
            a, b, np.median(rs), np.percentile(rs, 25), np.percentile(rs, 75), len(rs)))

    print("\n  2. BETWEEN-condition correlations (condition-median level)")
    g = T.groupby("cond")[["dt", "dN", "dQ"]].median()
    for a, b in [("dt", "dN"), ("dt", "dQ"), ("dN", "dQ")]:
        print("    corr(%s,%s) = %.4f" % (a, b, g[a].corr(g[b])))

    print("\n  3. within-transformed design (condition means removed)")
    Xw = X3.copy()
    for j in range(3):
        Xw[:, j] -= T.groupby("cond")[["dt", "dN", "dQ"]].transform("mean").values[:, j]
    sd = Xw.std(axis=0)
    Z = Xw / np.where(sd > 0, sd, 1.0)
    s = np.linalg.svd(Z, compute_uv=False)
    cn = float(s[0] / s[-1]) if s[-1] > 0 else np.inf
    rk = int(np.linalg.matrix_rank(Z))
    V = vif(Z)
    print("    column sd (raw units): dt %.4f  dN %.2f  dQ %.4f" % tuple(sd))
    print("    singular values: %s" % np.round(s, 6).tolist())
    print("    rank %d / 3 | condition number %.2f (screen <= %.0f)" % (rk, cn, COND_NUM_MAX))
    print("    VIF: dt %.2f  dN %.2f  dQ %.2f (screen <= %.0f)" % (
        V[0], V[1], V[2], VIF_MAX))
    verdict = "IDENTIFIED" if (rk == 3 and cn <= COND_NUM_MAX and V.max() <= VIF_MAX) \
        else "NOT IDENTIFIED"
    print("    -> within-condition design: %s" % verdict)

    print("\n  4. support for the three contrasts (condition medians, 2-D matching)")
    g2 = g.reset_index()
    def contrast(a, b, tol=0.25):
        """count condition PAIRS where a differs by >tol (log) while b matches <tol"""
        n = 0; best = 0.0
        for i in range(len(g2)):
            for j in range(i + 1, len(g2)):
                da = abs(np.log(max(g2[a].iloc[i], 1e-9) / max(g2[a].iloc[j], 1e-9)))
                db = abs(np.log(max(g2[b].iloc[i], 1e-9) / max(g2[b].iloc[j], 1e-9)))
                if da > np.log(2) and db < tol:
                    n += 1
                    best = max(best, da)
        return n, best
    for a, b, label in [("dt", "dN", "(a) different dt at comparable dN"),
                        ("dN", "dt", "(b) different dN at comparable dt"),
                        ("dQ", "dt", "(c) different dQ at comparable dt")]:
        n, best = contrast(a, b)
        print("    %-42s pairs: %3d   max log-difference %.2f" % (label, n, best))

    print("\n  5. descriptive: does dSOH track any single clock better? (no fitting)")
    if "dSOH" in T.columns:
        for c in ["dt", "dN", "dQ"]:
            r = np.corrcoef(T[c], T.dSOH)[0, 1]
            print("    corr(%s, dSOH) = %+.4f" % (c, r))
    return dict(n=len(T), rank=rk, cond_num=cn, vif=V.tolist(), verdict=verdict)


def main():
    T = pd.read_csv(os.path.join(OUT, "F4_clock_table.csv"))
    T = T.sort_values(["cell", "rpt_idx"])
    T["dt"] = T.groupby("cell").day.diff()
    T["dN"] = T.groupby("cell").cum_cycles.diff()
    T["dQ"] = T.groupby("cell").cum_ah_ch.diff()
    T["dSOH"] = T.groupby("cell").soh.diff()
    T = T[(T.dt > 0) & (T.dN >= 0) & (T.dQ >= 0)].copy()
    T = T.dropna(subset=["dt", "dN", "dQ"])
    print("interval table: %d rows, %d cells, %d conditions" % (
        len(T), T.cell.nunique(), T.cond.nunique()))

    r1 = diagnose(T, "ALL releases")
    rel = pd.read_csv(os.path.join(OUT, "F5_version.csv"))[["cell", "release_tag"]]
    T2 = T.merge(rel, on="cell", how="left")
    r2 = diagnose(T2[T2.release_tag == "Release 1.0"], "Release 1.0 only")

    out = dict(all_releases=r1, release1_only=r2,
               cond_num_max=COND_NUM_MAX, vif_max=VIF_MAX)
    json.dump(out, open(os.path.join(OUT, "F7_design_support.json"), "w"), indent=1, default=float)
    T.to_csv(os.path.join(OUT, "F7_intervals.csv"), index=False)
    print("\n=== GATE VERDICT (item 7) ===")
    print("  within-condition design: %s" % r1["verdict"])
    print("  Release 1.0 only       : %s" % r2["verdict"])
    print("\nwrote F7_intervals.csv / F7_design_support.json")


if __name__ == "__main__":
    main()
