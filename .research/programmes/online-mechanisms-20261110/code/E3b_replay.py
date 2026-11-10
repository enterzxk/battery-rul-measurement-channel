# -*- coding: utf-8 -*-
"""E3b · Temporal policy replay, one (T, N, ratio) cell per process.

Implements PREREGISTRATION_E.md + PREREGISTRATION_E_ADDENDUM.md.

Usage:  python E3b_replay.py <T> <N> <ratio>

What is computed, per outer held-out condition g:

  * a quantile model q_tau(log M | subset features), tau = 1/(1+ratio), fitted on
    the training conditions only, over ALL admissible subsets (augmentation);
  * an expected-loss model, fitted on training conditions using inner 5-fold
    condition-grouped out-of-fold predictions (never touching g);
  * the STRONGEST FIXED schedule selected on the TRAINING conditions only;
  * six policies played sequentially on every held-out cell with a strict
    non-anticipating acquisition contract (addendum A1/A3): at step k the policy
    sees day-0 info, the purchased (time, SOH) pairs, the inspection calendar and
    the remaining budget. Future SOH values are only ever extrapolated.

Action rule in every arm AND in the oracle:  R = max(T, exp(q_tau)).

Output: protocol/E3_T{T}_N{N}_r{ratio}.json
"""
import os
import sys
import json
import pickle
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingRegressor as HGBR

import D_common as C
from D4_budget_curve import describe

OUT = C.PROTO
HEALTH = ["soh_first", "soh_last", "frac_loss", "ols_slope", "ols_se_slope",
          "ols_r2", "ols_resid_sd", "ols_soh_at_t", "ols_curv", "span", "n_obs"]
FEATS = ["logT", "DoD", "cc", "cd"] + HEALTH
MIN_AVAIL = 3
N_RANDOM = 20


# ---------------------------------------------------------------- utilities
def features_from_obs(xv, sv, T, srow):
    xv = np.asarray(xv, float)
    sv = np.asarray(sv, float)
    d = describe(xv, sv, T)
    d["span"] = float(xv[-1] - xv[0])
    d["n_obs"] = int(len(xv))
    d["logT"] = float(np.log(T))
    d["DoD"] = float(srow["DoD"])
    d["cc"] = float(srow["charge_C"])
    d["cd"] = float(srow["discharge_C"])
    return d


def extrapolate(xs, ss, t):
    """Addendum A3: shared by VoI and Candidate. Linear, clipped."""
    xs = np.asarray(xs, float)
    ss = np.asarray(ss, float)
    if len(xs) < 2 or np.ptp(xs) <= 0:
        return float(np.clip(ss[-1], 0.05, 1.05))
    a = np.polyfit(xs, ss, 1)
    return float(np.clip(np.polyval(a, t), 0.05, 1.05))


def loss_of(R, M, ratio):
    return np.maximum(0.0, M - R) + ratio * np.maximum(0.0, R - M)


def cohort(cells, T, stress):
    out = {}
    for name, s in cells.items():
        if s["cond"] not in stress.index:
            continue
        if not (T < s["L"]):
            continue
        x = s["x"]
        if x[0] != 0.0:
            continue
        avail = [i for i in range(1, len(x)) if x[i] <= T]
        if len(avail) < MIN_AVAIL:
            continue
        out[name] = dict(s=s, avail=avail, M=0.5 * (s["L"] + s["U"]))
    return out


def build_rows(co, T, N, stress):
    rows = []
    for name, d in co.items():
        s, avail, M = d["s"], d["avail"], d["M"]
        srow = stress.loc[s["cond"]]
        for sub in combinations(avail, N):
            idx = [0] + list(sub)
            f = features_from_obs(s["x"][idx], s["soh"][idx], T, srow)
            f["cell"] = name
            f["cond"] = s["cond"]
            f["sub_idx"] = tuple(int(i) for i in sub)
            f["y"] = float(np.log(M))
            f["M"] = float(M)
            rows.append(f)
    return pd.DataFrame(rows)


def fit_q(Q, feats, tau, cols=None):
    m = HistGradientBoostingRegressor(loss="quantile", quantile=tau, max_iter=300,
                                      learning_rate=0.05, random_state=0)
    m.fit(Q[feats].values if cols is None else Q[cols].values, Q["y"].values)
    return m


# ---------------------------------------------------------------- policies
def fixed_even(avail, N):
    pos = np.unique(np.round(np.linspace(0, len(avail) - 1, N)).astype(int))
    return sorted(int(avail[i]) for i in pos)


def fixed_late(avail, N):
    return sorted(int(v) for v in avail[-N:])


def fixed_early(avail, N):
    return sorted(int(v) for v in avail[:N])


def fixed_random(avail, N, seed):
    rng = np.random.default_rng(seed)
    return sorted(int(v) for v in rng.choice(avail, N, replace=False))


def sequential(avail, N, s, T, srow, choose_next):
    """Non-anticipating loop: buy one at a time, reveal the real SOH each time."""
    purchased = [0]
    for _ in range(N):
        remaining = [i for i in avail if i > max(purchased)]
        if not remaining:
            break
        nxt = choose_next(purchased, remaining, s, T, srow)
        purchased.append(int(nxt))
    return sorted(purchased)


def make_voi_chooser(loss_model, feats):
    def choose(purchased, remaining, s, T, srow):
        xs = s["x"][purchased]
        ss = s["soh"][purchased]
        best, bestL = None, np.inf
        for t in remaining:
            hyp_x = np.append(xs, s["x"][t])
            hyp_s = np.append(ss, extrapolate(xs, ss, s["x"][t]))
            order = np.argsort(hyp_x)
            f = features_from_obs(hyp_x[order], hyp_s[order], T, srow)
            row = np.array([[f[k] for k in feats]], dtype=float)
            Lp = float(loss_model.predict(row)[0])
            if Lp < bestL:
                bestL, best = Lp, t
        return best if best is not None else remaining[-1]
    return choose


def make_cand_chooser():
    """Addendum A4: score(t) = (1 - shat(t)/soh_first) * (T - t)/T, maximise.

    The inverted-U is imposed by the product form, so it is BY CONSTRUCTION and
    is not evidence for the mechanism. Recorded in the addendum before running.
    """
    def choose(purchased, remaining, s, T, srow):
        xs = s["x"][purchased]
        ss = s["soh"][purchased]
        first = float(ss[0]) if ss[0] > 0 else 1.0
        best, bestS = None, -np.inf
        for t in remaining:
            sh = extrapolate(xs, ss, s["x"][t])
            amp = 1.0 - sh / first
            act = (T - s["x"][t]) / T
            sc = amp * act
            if sc > bestS:
                bestS, best = sc, t
        return best if best is not None else remaining[-1]
    return choose


# ---------------------------------------------------------------- main
def main():
    T = int(sys.argv[1]); N = int(sys.argv[2]); ratio = float(sys.argv[3])
    tau = 1.0 / (1.0 + ratio)
    with open(os.path.join(OUT, "isu_cells_cache.pkl"), "rb") as f:
        pay = pickle.load(f)
    cells, stress = pay["cells"], pay["stress"]
    co = cohort(cells, T, stress)
    conds = sorted({d["s"]["cond"] for d in co.values()})
    print("T=%d N=%d ratio=%.1f tau=%.4f | cohort %d cells / %d conditions" % (
        T, N, ratio, tau, len(co), len(conds)), flush=True)

    pol_names = ["FixedEven", "FixedLate", "FixedEarly", "Random", "VoI", "Candidate"]
    per_cond = {p: [] for p in pol_names}
    per_cond_fixed_chosen = []
    oracle_vals = []

    for gi, g in enumerate(conds):
        tr_names = [n for n, d in co.items() if d["s"]["cond"] != g]
        te_names = [n for n, d in co.items() if d["s"]["cond"] == g]
        if len(tr_names) < 60 or not te_names:
            continue
        tr_co = {n: co[n] for n in tr_names}
        Q = build_rows(tr_co, T, N, stress)
        if len(Q) < 300:
            continue
        feats = C.usable_features(Q, FEATS)
        qm = fit_q(Q, feats, tau)

        # inner 5-fold condition-grouped OOF -> expected-loss model
        tc = sorted({d["s"]["cond"] for d in tr_co.values()})
        rng = np.random.default_rng(0)
        perm = rng.permutation(len(tc))
        folds = np.array_split(perm, 5)
        Q["oof_R"] = np.nan
        for k in range(5):
            hold = {tc[i] for i in folds[k]}
            a = Q[Q.cond.isin(hold)]
            b = Q[~Q.cond.isin(hold)]
            if len(a) == 0 or len(b) < 200:
                continue
            m = fit_q(b, feats, tau)
            Q.loc[a.index, "oof_R"] = np.exp(m.predict(a[feats].values))
        Q["oof_R"] = Q["oof_R"].clip(lower=T)
        Q["oof_loss"] = loss_of(Q["oof_R"].values, Q["M"].values, ratio)
        ok = np.isfinite(Q["oof_loss"])
        lm = HGBR(max_iter=300, learning_rate=0.05, random_state=0)
        lm.fit(Q.loc[ok, feats].values, Q.loc[ok, "oof_loss"].values)

        # ---- strongest fixed chosen on TRAINING conditions only -------------
        def J_fixed_on(names, pol, seed=None):
            vals = []
            for n in names:
                d = co[n]
                idx = ([0] + pol(d["avail"], N)) if seed is None else \
                      ([0] + fixed_random(d["avail"], N, seed))
                idx = sorted(set(idx))
                f = features_from_obs(d["s"]["x"][idx], d["s"]["soh"][idx], T,
                                      stress.loc[d["s"]["cond"]])
                R = max(T, float(np.exp(qm.predict(np.array([[f[k] for k in feats]]))[0])))
                vals.append(float(loss_of(R, d["M"], ratio)))
            return float(np.mean(vals))

        cand = {"FixedEven": J_fixed_on(tr_names, fixed_even),
                "FixedLate": J_fixed_on(tr_names, fixed_late),
                "FixedEarly": J_fixed_on(tr_names, fixed_early),
                "Random": float(np.mean([J_fixed_on(tr_names, fixed_random, s)
                                         for s in range(N_RANDOM)]))}
        best_fixed = min(cand, key=cand.get)
        per_cond_fixed_chosen.append(best_fixed)

        # ---- evaluate every arm on the held-out condition -------------------
        voi_choose = make_voi_chooser(lm, feats)
        cand_choose = make_cand_chooser()
        acc = {p: [] for p in pol_names}
        orc = []
        for n in te_names:
            d = co[n]
            s = d["s"]
            srow = stress.loc[s["cond"]]
            for p in pol_names:
                if p == "Random":
                    # average over 5 pre-registered seeds for a stable baseline
                    vs = []
                    for sd in range(5):
                        idx = sorted(set([0] + fixed_random(d["avail"], N, sd)))
                        f = features_from_obs(s["x"][idx], s["soh"][idx], T, srow)
                        R = max(T, float(np.exp(qm.predict(
                            np.array([[f[k] for k in feats]]))[0])))
                        vs.append(float(loss_of(R, d["M"], ratio)))
                    acc[p].append(float(np.mean(vs)))
                    continue
                if p in ("FixedEven", "FixedLate", "FixedEarly"):
                    fn = {"FixedEven": fixed_even, "FixedLate": fixed_late,
                          "FixedEarly": fixed_early}[p]
                    idx = sorted(set([0] + fn(d["avail"], N)))
                elif p == "VoI":
                    idx = sequential(d["avail"], N, s, T, srow, voi_choose)
                else:
                    idx = sequential(d["avail"], N, s, T, srow, cand_choose)
                f = features_from_obs(s["x"][idx], s["soh"][idx], T, srow)
                R = max(T, float(np.exp(qm.predict(np.array([[f[k] for k in feats]]))[0])))
                acc[p].append(float(loss_of(R, d["M"], ratio)))
            # constrained oracle for reference (hindsight, same action rule)
            best = np.inf
            for sub in combinations(d["avail"], N):
                idx = [0] + list(sub)
                f = features_from_obs(s["x"][idx], s["soh"][idx], T, srow)
                R = max(T, float(np.exp(qm.predict(np.array([[f[k] for k in feats]]))[0])))
                best = min(best, float(loss_of(R, d["M"], ratio)))
            orc.append(best)
        for p in pol_names:
            per_cond[p].append(float(np.mean(acc[p])))
        oracle_vals.append(float(np.mean(orc)))
        if gi % 10 == 0:
            print("  outer %d/%d cond=%s best_fixed=%s" % (gi + 1, len(conds), g, best_fixed),
                  flush=True)

    n = len(per_cond["VoI"])
    res = dict(T=T, N=N, ratio=ratio, tau=tau, n_cond=n,
               loss={p: float(np.mean(per_cond[p])) for p in pol_names},
               oracle_loss=float(np.mean(oracle_vals)),
               fixed_chosen=pd.Series(per_cond_fixed_chosen).value_counts().to_dict(),
               per_cond_loss=per_cond)
    # paired condition-level deltas vs the train-selected strongest fixed
    bf = per_cond_fixed_chosen
    d_vs_fixed = {}
    for p in pol_names:
        diffs = [per_cond[bf[i]][i] - per_cond[p][i] for i in range(n)]
        d_vs_fixed[p] = diffs
    res["delta_vs_strongest_fixed"] = {p: float(np.mean(v)) for p, v in d_vs_fixed.items()}
    res["per_cond_delta"] = d_vs_fixed

    def boot_ci(v, n_boot=10000, seed=0):
        v = np.asarray(v, float)
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, len(v), (n_boot, len(v)))
        m = v[idx].mean(axis=1)
        return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))

    res["delta_ci"] = {p: boot_ci(d_vs_fixed[p]) for p in pol_names}
    res["delta_vs_voi"] = {
        p: float(np.mean([per_cond[p][i] - per_cond["VoI"][i] for i in range(n)]))
        for p in pol_names}
    res["J"] = {p: 1.0 * N + res["loss"][p] for p in pol_names}

    fn = os.path.join(OUT, "E3_T%d_N%d_r%s.json" % (T, N, str(ratio).replace(".", "p")))
    json.dump(res, open(fn, "w"), indent=1, default=float)
    print("\nT=%d N=%d ratio=%.0f  (n_cond=%d)" % (T, N, ratio, n))
    for p in pol_names:
        lo, hi = res["delta_ci"][p]
        print("  %-11s loss %7.3f  J %7.3f  Δvs-fixed %+7.3f [%+7.3f,%+7.3f]" % (
            p, res["loss"][p], res["J"][p], res["delta_vs_strongest_fixed"][p], lo, hi))
    print("  oracle      loss %7.3f   (hindsight, constrained R>=T)" % res["oracle_loss"])
    print("  strongest fixed chosen per fold: %s" % res["fixed_chosen"])
    print("wrote %s" % fn)


if __name__ == "__main__":
    main()
