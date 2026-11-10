# -*- coding: utf-8 -*-
"""E9 · Matched-N defect: quantify it, fix it, re-run the primary setting.

DEFECT FOUND. In E3b's `sequential()`, a policy that picks the LAST available
calendar slot at step 1 leaves no future slot, so the loop breaks and the arm
buys fewer than N inspections. The E7 acquisition records show it directly:
VoI on G1C1 bought `0.00|60.26` — one purchase for N=2.

Consequences, stated precisely:
  * the comparison is then NOT "at matched N" as the addendum requires;
  * VoI/Candidate were charged c_insp*N while buying fewer, so they were
    OVER-charged, i.e. the defect biases AGAINST the adaptive arms;
  * their predictions also used fewer observations, which biases against them
    on accuracy.

So the defect cannot manufacture the observed negative; but the contract was
still violated and the primary result must be recomputed under a correct
implementation.

FIX. At step k (0-indexed, N steps) the candidate set is restricted to slots that
leave at least (N - k - 1) later slots, which guarantees exactly N purchases
whenever |avail| >= N (always true here, MIN_AVAIL = 3).

This script (a) quantifies the defect from the E7 records and (b) re-runs the
primary setting (T=63, N=2, c_f/c_w=5) with the fixed chooser.

Run remotely.
"""
import os
import json
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR

import D_common as C
from E3b_replay import (FEATS, build_rows, cohort, features_from_obs,
                        fixed_early, fixed_even, fixed_late, fixed_random, fit_q,
                        loss_of, make_cand_chooser, make_voi_chooser)

OUT = C.PROTO
T, N, RATIO = 63, 2, 5.0
TAU = 1.0 / (1.0 + RATIO)
N_RANDOM = 20


def sequential_matched(avail, N, s, T, srow, choose_next):
    """Guarantee exactly N purchases by reserving later slots."""
    purchased = [0]
    for k in range(N):
        remaining = [i for i in avail if i > max(purchased)]
        need = N - k - 1
        if need > 0:
            allowed = [i for i in remaining
                       if len([j for j in remaining if j > i]) >= need]
            if not allowed:
                allowed = remaining
        else:
            allowed = remaining
        if not allowed:
            break
        purchased.append(int(choose_next(purchased, allowed, s, T, srow)))
    return sorted(purchased)


def main():
    # ---------------- (a) quantify the defect from E7 ----------------
    D = pd.read_csv(os.path.join(OUT, "E7_inspection_records.csv"))
    D["n_bought"] = D.n_insp
    print("=== (a) how often did an adaptive arm buy fewer than N=%d? ===" % N)
    tab = D.groupby("policy").n_bought.agg(
        mean="mean", min="min", max="max",
        n_short=lambda x: int((x < N).sum()), n="size")
    tab["pct_short"] = 100.0 * tab.n_short / tab.n
    print(tab.round(2).to_string())
    print("\n  -> the matched-N contract was violated for the adaptive arms above;")
    print("     fixed arms are unaffected (they choose all N at once).")

    # ---------------- (b) re-run the primary setting, fixed ----------------
    with open(os.path.join(OUT, "isu_cells_cache.pkl"), "rb") as f:
        pay = pickle.load(f)
    cells, stress = pay["cells"], pay["stress"]
    co = cohort(cells, T, stress)
    conds = sorted({d["s"]["cond"] for d in co.values()})
    print("\n=== (b) re-running T=%d N=%d ratio=%.0f with matched-N chooser ===" % (
        T, N, RATIO))

    pols = ["FixedEven", "FixedLate", "FixedEarly", "Random", "VoI", "Candidate"]
    per_cond = {p: [] for p in pols}
    fixed_chosen = []
    nshort = {p: 0 for p in pols}

    for g in conds:
        tr = [n for n, d in co.items() if d["s"]["cond"] != g]
        te = [n for n, d in co.items() if d["s"]["cond"] == g]
        if len(tr) < 60 or not te:
            continue
        Q = build_rows({n: co[n] for n in tr}, T, N, stress)
        if len(Q) < 300:
            continue
        feats = C.usable_features(Q, FEATS)
        qm = fit_q(Q, feats, TAU)

        tc = sorted({co[n]["s"]["cond"] for n in tr})
        rng = np.random.default_rng(0)
        folds = np.array_split(rng.permutation(len(tc)), 5)
        Q["oof_R"] = np.nan
        for k in range(5):
            hold = {tc[i] for i in folds[k]}
            a = Q[Q.cond.isin(hold)]
            b = Q[~Q.cond.isin(hold)]
            if len(a) == 0 or len(b) < 200:
                continue
            m = fit_q(b, feats, TAU)
            Q.loc[a.index, "oof_R"] = np.exp(m.predict(a[feats].values))
        Q["oof_R"] = Q["oof_R"].clip(lower=T)
        Q["oof_loss"] = loss_of(Q["oof_R"].values, Q["M"].values, RATIO)
        ok = np.isfinite(Q["oof_loss"])
        lm = HGBR(max_iter=300, learning_rate=0.05, random_state=0)
        lm.fit(Q.loc[ok, feats].values, Q.loc[ok, "oof_loss"].values)

        voi = make_voi_chooser(lm, feats)
        cand = make_cand_chooser()

        def J_on(names, fn):
            vals = []
            for n in names:
                d = co[n]
                idx = sorted(set([0] + fn(d["avail"], N)))
                f = features_from_obs(d["s"]["x"][idx], d["s"]["soh"][idx], T,
                                      stress.loc[d["s"]["cond"]])
                R = max(T, float(np.exp(qm.predict(np.array([[f[k] for k in feats]]))[0])))
                vals.append(float(loss_of(R, d["M"], RATIO)))
            return float(np.mean(vals))

        candJ = {"FixedEven": J_on(tr, fixed_even),
                 "FixedLate": J_on(tr, fixed_late),
                 "FixedEarly": J_on(tr, fixed_early)}
        candJ["Random"] = float(np.mean(
            [J_on(tr, lambda a, k, sd=s: fixed_random(a, k, sd)) for s in range(5)]))
        best = min(candJ, key=candJ.get)
        fixed_chosen.append(best)

        acc = {p: [] for p in pols}
        for n in te:
            d = co[n]
            s, srow = d["s"], stress.loc[d["s"]["cond"]]
            picks = {
                "FixedEven": sorted(set([0] + fixed_even(d["avail"], N))),
                "FixedLate": sorted(set([0] + fixed_late(d["avail"], N))),
                "FixedEarly": sorted(set([0] + fixed_early(d["avail"], N))),
                "Random": sorted(set([0] + fixed_random(d["avail"], N, 0))),
                "VoI": sequential_matched(d["avail"], N, s, T, srow, voi),
                "Candidate": sequential_matched(d["avail"], N, s, T, srow, cand),
            }
            for p, idx in picks.items():
                if len(idx) - 1 < N:
                    nshort[p] += 1
                f = features_from_obs(s["x"][idx], s["soh"][idx], T, srow)
                R = max(T, float(np.exp(qm.predict(np.array([[f[k] for k in feats]]))[0])))
                acc[p].append(float(loss_of(R, d["M"], RATIO)))
        for p in pols:
            per_cond[p].append(float(np.mean(acc[p])))

    n = len(fixed_chosen)
    Lf = np.array([per_cond[fixed_chosen[i]][i] for i in range(n)])
    print("  folds %d | strongest fixed chosen: %s | short-purchase counts: %s" % (
        n, pd.Series(fixed_chosen).value_counts().to_dict(),
        {k: v for k, v in nshort.items() if v}))
    print("\n  %-11s %-10s %-12s %-24s %s" % ("policy", "loss", "Δ_CF", "paired 95% CI", "verdict"))
    res = {}
    for p in pols:
        Lp = np.array(per_cond[p])
        d = Lf - Lp
        rng = np.random.default_rng(0)
        bs = d[rng.integers(0, n, (10000, n))].mean(axis=1)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        m = 0.10 * (N + Lf.mean())
        v = "SUPPORTS" if lo > m else ("NEGATIVE" if hi < m else "INCONCLUSIVE")
        res[p] = dict(loss=float(Lp.mean()), delta=float(d.mean()), lo=float(lo),
                      hi=float(hi), verdict=v)
        print("  %-11s %-10.3f %+12.3f [%+8.2f, %+8.2f]  %s" % (
            p, Lp.mean(), d.mean(), lo, hi, v))
    m = 0.10 * (N + Lf.mean())
    print("\n  margin = %.2f d | J_fixed = %.2f d" % (m, N + Lf.mean()))
    json.dump(dict(T=T, N=N, ratio=RATIO, n_folds=n, margin=float(m),
                   n_short=nshort, results=res,
                   fixed_chosen=pd.Series(fixed_chosen).value_counts().to_dict()),
              open(os.path.join(OUT, "E9_matched_n.json"), "w"), indent=1, default=float)
    print("\nwrote E9_matched_n.json")



if __name__ == "__main__":
    main()
