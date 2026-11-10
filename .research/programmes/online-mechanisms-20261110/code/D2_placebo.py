# -*- coding: utf-8 -*-
"""D2 · Is the health gain INFORMATION or just extra feature capacity?

D1 showed that on ISU, adding pure health features to age+stress improves
condition-macro |log err| by 19.3% [-27.0,-11.3], and that on UConn the pure
health arm improves on age by 17.7% (CI wide, 11 conditions). But those arms add
three features to a one- or four-feature model. More features can improve a
boosted tree for reasons that have nothing to do with information.

This script runs the placebo controls that separate the two:

  real        : age(+stress) + [soh_last, soh0, slope]
  perm_global : the same three columns, shuffled across ALL rows
  perm_cond   : the same three columns, shuffled WITHIN each condition
                (keeps every condition's marginal distribution, destroys the
                 cell-level link between trajectory and lifetime)
  noise       : three independent N(0,1) columns

20 permutations give a null distribution of the measured "gain". The claim that
the health trajectory carries information requires the real gain to sit clearly
below that null distribution.

Also reports, for description only, how the gain varies with the observed
degradation amplitude at the query point (amp = 1 - soh_last). amp is computed
from visible data, so this is legitimate; L is NOT used.

Writes protocol/D2_placebo.csv / .json / D2_out.txt
"""
import os
import json

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO
N_PERM = 20


def arm_gain(Q, base_feats, add_feats, ok_mask=None):
    """Fit base and base+add with LOCO; return cond-macro MAEs and paired gain."""
    pb = C.fit_loco(Q, base_feats)
    ph = C.fit_loco(Q, base_feats + add_feats)
    ok = np.isfinite(pb) & np.isfinite(ph)
    if ok_mask is not None:
        ok &= ok_mask
    if ok.sum() < 60:
        return None
    cb = C.cond_macro(np.abs(pb[ok] - Q.y.values[ok]), Q.cond.values[ok])
    ch = C.cond_macro(np.abs(ph[ok] - Q.y.values[ok]), Q.cond.values[ok])
    g, lo, hi, p = C.paired_gain(cb, ch)
    return dict(base=float(cb.mean()), add=float(ch.mean()),
                gain=g, lo=lo, hi=hi, p=p, n_ok=int(ok.sum()))


def placebo_block(name, cells, ages, stress, base_name, base_feats):
    Q = C.build_queries(cells, ages, stress=stress)
    rng = np.random.default_rng(7)
    rows = []

    real = arm_gain(Q, base_feats, C.HEALTH)
    print("\n=== %s · base = %s (%d feat), add = HEALTH ===" % (name, base_name, len(base_feats)))
    print("  real        : %-9.4f -> %-9.4f  %+6.1f%% [%6.1f,%6.1f] p=%.2e" % (
        real["base"], real["add"], real["gain"], real["lo"], real["hi"], real["p"]))
    rows.append(dict(cohort=name, arm="real", **real))

    # --- global permutation ------------------------------------------------
    gl = []
    for i in range(N_PERM):
        Qp = Q.copy()
        for f in C.HEALTH:
            Qp[f] = rng.permutation(Qp[f].values)
        r = arm_gain(Qp, base_feats, C.HEALTH)
        gl.append(r["gain"])
    print("  perm_global : %+6.1f%% median (min %+.1f, max %+.1f), %d draws" % (
        np.median(gl), np.min(gl), np.max(gl), N_PERM))
    rows.append(dict(cohort=name, arm="perm_global", base=real["base"], add=float("nan"),
                     gain=float(np.median(gl)), lo=float(np.percentile(gl, 2.5)),
                     hi=float(np.percentile(gl, 97.5)), p=float("nan"), n_ok=real["n_ok"]))

    # --- within-condition permutation --------------------------------------
    wl = []
    for i in range(N_PERM):
        Qp = Q.copy()
        for f in C.HEALTH:
            v = Qp[f].values.copy()
            for _, idx in Qp.groupby("cond").groups.items():
                ii = np.asarray(idx)
                v[ii] = v[rng.permutation(ii)]
            Qp[f] = v
        r = arm_gain(Qp, base_feats, C.HEALTH)
        wl.append(r["gain"])
    print("  perm_cond   : %+6.1f%% median (min %+.1f, max %+.1f)" % (
        np.median(wl), np.min(wl), np.max(wl)))
    rows.append(dict(cohort=name, arm="perm_cond", base=real["base"], add=float("nan"),
                     gain=float(np.median(wl)), lo=float(np.percentile(wl, 2.5)),
                     hi=float(np.percentile(wl, 97.5)), p=float("nan"), n_ok=real["n_ok"]))

    # --- noise columns -----------------------------------------------------
    nl = []
    for i in range(N_PERM):
        Qn = Q.copy()
        for j, f in enumerate(C.HEALTH):
            Qn[f] = rng.standard_normal(len(Qn))
        r = arm_gain(Qn, base_feats, C.HEALTH)
        nl.append(r["gain"])
    print("  noise       : %+6.1f%% median (min %+.1f, max %+.1f)" % (
        np.median(nl), np.min(nl), np.max(nl)))
    rows.append(dict(cohort=name, arm="noise", base=real["base"], add=float("nan"),
                     gain=float(np.median(nl)), lo=float(np.percentile(nl, 2.5)),
                     hi=float(np.percentile(nl, 97.5)), p=float("nan"), n_ok=real["n_ok"]))

    null = np.concatenate([gl, wl, nl])
    pct = 100.0 * float((null <= real["gain"]).mean())
    print("  -> real gain sits at the %.1f-th percentile of the pooled null (lower = better)" % pct)
    print("  -> placebo-corrected verdict: %s" % (
        "INFORMATION" if pct < 5 else "NOT DISTINGUISHABLE FROM CAPACITY"))

    # --- does the gain track observed degradation amplitude? ---------------
    pb = C.fit_loco(Q, base_feats)
    ph = C.fit_loco(Q, base_feats + C.HEALTH)
    ok = np.isfinite(pb) & np.isfinite(ph)
    d = pd.DataFrame(dict(cell=Q.cell[ok], cond=Q.cond[ok], age=Q.age[ok],
                          amp=Q.amp[ok], eb=np.abs(pb[ok] - Q.y.values[ok]),
                          eh=np.abs(ph[ok] - Q.y.values[ok])))
    d["q"] = pd.qcut(d.amp, 4, labels=False, duplicates="drop")
    q = d.groupby("q").agg(amp_lo=("amp", "min"), amp_hi=("amp", "max"),
                           n=("amp", "size"), base=("eb", "mean"), health=("eh", "mean"))
    q["gain_pct"] = 100.0 * (q.health / q.base - 1.0)
    print("\n  gain by observed amplitude quartile (visible quantity, not L):")
    print("  %-3s %-9s %-9s %-5s %-9s %-9s %s" % ("q", "amp_lo", "amp_hi", "n", "base", "health", "gain"))
    for i, r in q.iterrows():
        print("  %-3d %-9.4f %-9.4f %-5d %-9.4f %-9.4f %+6.1f%%" % (
            i, r.amp_lo, r.amp_hi, r.n, r.base, r.health, r.gain_pct))
    q = q.reset_index()
    q.insert(0, "cohort", name)
    return rows, q


def main():
    print("=" * 78)
    print("D2 · placebo control: is the health gain information or capacity?")
    print("=" * 78)
    uc = C.load_uconn()
    isu = C.load_isu()
    S = C.load_stress()

    r1, q1 = placebo_block("UConn", uc, (300, 600, 1000, 1500), None, "age", C.AGE)
    r2, q2 = placebo_block("ISU", isu, (21, 35, 49, 63), S, "age+stress", C.AGE + C.STRESS)

    T = pd.DataFrame(r1 + r2)
    Q = pd.concat([q1, q2], ignore_index=True)
    T.to_csv(os.path.join(OUT, "D2_placebo.csv"), index=False)
    Q.to_csv(os.path.join(OUT, "D2_amp_quartiles.csv"), index=False)
    json.dump(dict(placebo=T.to_dict("records"), amp=Q.to_dict("records")),
              open(os.path.join(OUT, "D2_placebo.json"), "w"), indent=1)

    print("\n" + "=" * 78)
    print("SUMMARY (negative gain = adding the columns helps)")
    print("=" * 78)
    print(T[["cohort", "arm", "base", "add", "gain", "lo", "hi"]].to_string(index=False))
    print("\nwrote D2_placebo.csv / D2_placebo.json / D2_amp_quartiles.csv")


if __name__ == "__main__":
    main()
