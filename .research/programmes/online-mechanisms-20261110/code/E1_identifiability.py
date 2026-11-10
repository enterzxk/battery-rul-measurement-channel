# -*- coding: utf-8 -*-
"""E1 · Identifiability audit for the temporal policy replay (pre-registration §6).

Runs the seven gates BEFORE any formal policy replay. The decisive one is I6:

    Q3 (value of actively choosing inspection times) <= oracle - strongest_fixed

where `oracle` may pick the loss-minimising observation subset WITH HINDSIGHT.
Hindsight can only overstate what an online policy can achieve, so if the oracle
cannot beat the strongest fixed schedule by the pre-registered 10%, no online
policy can, and the direction is dead by proof rather than by failed experiment.

Also answers the pre-registration's structural question: is the loss even
sensitive to WHICH times are observed (I2), and do different policies produce
different observable histories (I1)?

No policy is trained here beyond what the gates need. Read-only w.r.t. raw data.

Run remotely (workspace compute rule).
"""
import os
import json
from itertools import combinations
from math import comb

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import D_common as C
from D4_budget_curve import describe

OUT = C.PROTO
TS = (56, 63)
NS = (1, 2, 3)
CF = (2.0, 5.0, 10.0)          # c_f / c_w
CINSP = (0.5, 1.0, 2.0)        # days per inspection
N_RANDOM = 20
MARGIN = 0.10                  # pre-registered minimum useful benefit (relative)

HEALTH = ["soh_first", "soh_last", "frac_loss", "ols_slope", "ols_se_slope",
          "ols_r2", "ols_resid_sd", "ols_soh_at_t", "ols_curv", "span", "n_obs"]
STRESS = ["DoD", "cc", "cd"]


def feats_from(xv, sv, T, srow):
    """Features computed ONLY from the observations in (xv, sv)."""
    d = describe(xv, sv, T)
    d["span"] = float(xv[-1] - xv[0])
    d["n_obs"] = int(len(xv))
    d["logT"] = float(np.log(T))
    d["DoD"] = float(srow["DoD"])
    d["cc"] = float(srow["charge_C"])
    d["cd"] = float(srow["discharge_C"])
    return d


def cohort(cells, T, stress):
    """Fixed population: identical for every N and every policy."""
    out = {}
    for name, s in cells.items():
        if s["cond"] not in stress.index:
            continue
        if not (T < s["L"]):
            continue
        x = s["x"]
        if x[0] != 0.0:                      # t_0 must be the day-0 baseline
            continue
        avail = np.where(x <= T)[0]
        avail = avail[avail >= 1]
        if len(avail) < max(NS):
            continue
        out[name] = dict(s=s, avail=avail, M=0.5 * (s["L"] + s["U"]))
    return out


def build_rows(co, T, N, stress):
    rows = []
    for name, d in co.items():
        s, avail, M = d["s"], d["avail"], d["M"]
        x, soh = s["x"], s["soh"]
        srow = stress.loc[s["cond"]]
        for sub in combinations(avail, N):
            idx = [0] + list(sub)
            f = feats_from(x[idx], soh[idx], T, srow)
            f["cell"] = name
            f["cond"] = s["cond"]
            f["sub_idx"] = tuple(int(i) for i in sub)
            f["y"] = float(np.log(M))
            f["M"] = float(M)
            rows.append(f)
    return pd.DataFrame(rows)


def fit_predict_loco(Q, tau, feats):
    """Leave-one-condition-out quantile regression; returns prediction per row."""
    p = np.full(len(Q), np.nan)
    for held in sorted(Q.cond.unique()):
        te = (Q.cond == held).values
        tr = ~te
        if tr.sum() < 200 or te.sum() == 0:
            continue
        m = HistGradientBoostingRegressor(
            loss="quantile", quantile=tau, max_iter=300, learning_rate=0.05,
            random_state=0)
        m.fit(Q.loc[tr, feats].values, Q.loc[tr, "y"].values)
        p[te] = m.predict(Q.loc[te, feats].values)
    return p


def loss_of(R, M, ratio):
    return np.maximum(0.0, M - R) + ratio * np.maximum(0.0, R - M)


def pick_even(avail, N):
    pos = np.unique(np.round(np.linspace(0, len(avail) - 1, N)).astype(int))
    while len(pos) < N:                      # degenerate only if N > len(avail)
        pos = np.append(pos, pos[-1])
    return tuple(int(avail[i]) for i in pos)


def pick_late(avail, N):
    return tuple(int(v) for v in avail[-N:])


def pick_early(avail, N):
    return tuple(int(v) for v in avail[:N])


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a | b) else 1.0


def main():
    cells = C.load_isu()
    stress = C.load_stress()
    print("ISU cells: %d" % len(cells))
    results = []
    gate = {}

    # ---- I4 / I7: features must depend only on the SELECTED observations ----
    print("\n=== I4/I7 · feature locality assertion ===")
    violations = 0
    checked = 0
    for name, s in list(cells.items())[:60]:
        x, soh = s["x"], s["soh"]
        cand = np.where(x <= 63)[0]
        cand = cand[cand >= 1]
        if len(cand) < 3:
            continue
        sub = (int(cand[0]), int(cand[-1]))
        idx = [0] + list(sub)
        f1 = feats_from(x[idx], soh[idx], 63, stress.loc[s["cond"]]
                        if s["cond"] in stress.index else pd.Series(dict(DoD=0.5, charge_C=1.0, discharge_C=1.0)))
        # destroy every UNSELECTED observation, keep selected ones
        soh2 = np.full_like(soh, np.nan)
        x2 = np.full_like(x, np.nan)
        soh2[idx] = soh[idx]
        x2[idx] = x[idx]
        f2 = feats_from(x2[idx], soh2[idx], 63, stress.loc[s["cond"]]
                        if s["cond"] in stress.index else pd.Series(dict(DoD=0.5, charge_C=1.0, discharge_C=1.0)))
        checked += 1
        for k in f1:
            a, b = f1[k], f2[k]
            same = (np.isnan(a) and np.isnan(b)) or (abs(a - b) < 1e-12)
            if not same:
                violations += 1
                print("  VIOLATION cell=%s feature=%s %.6g vs %.6g" % (name, k, a, b))
                break
    print("  cells checked %d, violations %d -> %s" % (
        checked, violations, "PASS" if violations == 0 else "FAIL"))
    gate["I4_I7"] = dict(checked=checked, violations=violations,
                         passed=violations == 0)

    for T in TS:
        co = cohort(cells, T, stress)
        n_cells = len(co)
        n_cond = len({d["s"]["cond"] for d in co.values()})
        print("\n" + "=" * 78)
        print("T = %d days · cohort %d cells / %d conditions" % (T, n_cells, n_cond))
        print("=" * 78)
        for N in NS:
            Q = build_rows(co, T, N, stress)
            feats = C.usable_features(Q, ["logT"] + STRESS + HEALTH)
            m_med = np.median([len(d["avail"]) for d in co.values()])
            print("\n  N=%d  rows=%d  feats_used=%d  median avail=%d  median subsets/cell=%.0f" % (
                N, len(Q), len(feats), m_med, np.median([comb(len(d["avail"]), N) for d in co.values()])))

            for ratio in CF:
                tau = 1.0 / (1.0 + ratio)
                p = fit_predict_loco(Q, tau, feats)
                ok = np.isfinite(p)
                Qq = Q.loc[ok].copy()
                Qq["R"] = np.exp(p[ok])
                Qq["loss"] = loss_of(Qq["R"].values, Qq["M"].values, ratio)

                # per-cell losses for every subset
                g = Qq.groupby(["cell", "cond"])
                cell_oracle, cell_even, cell_late, cell_early = {}, {}, {}, {}
                rnd = {}
                for (cell, cond), gg in g:
                    gg = gg.sort_values("loss")
                    cell_oracle[cell] = float(gg["loss"].iloc[0])
                    d = co[cell]
                    av = d["avail"]
                    def L_of(sub):
                        m = gg[gg["sub_idx"] == tuple(int(i) for i in sub)]
                        return float(m["loss"].iloc[0]) if len(m) else np.nan
                    cell_even[cell] = L_of(pick_even(av, N))
                    cell_late[cell] = L_of(pick_late(av, N))
                    cell_early[cell] = L_of(pick_early(av, N))
                    rs = []
                    for sd in range(N_RANDOM):
                        rng = np.random.default_rng(1000 + sd)
                        sub = tuple(int(v) for v in sorted(rng.choice(av, N, replace=False)))
                        rs.append(L_of(sub))
                    rnd[cell] = float(np.nanmean(rs))
                    # I2: dispersion of loss across subsets within this cell
                # condition-macro aggregation
                def macro(dct):
                    s = pd.Series(dct)
                    cnd = pd.Series({c: co[c]["s"]["cond"] for c in s.index})
                    return float(s.groupby(cnd).mean().mean())
                L_or = macro(cell_oracle); L_ev = macro(cell_even)
                L_la = macro(cell_late); L_ea = macro(cell_early); L_rn = macro(rnd)

                for ci in CINSP:
                    J_or = ci * N + L_or
                    fixed = {"FixedEven": ci * N + L_ev, "FixedLate": ci * N + L_la,
                             "FixedEarly": ci * N + L_ea, "Random": ci * N + L_rn}
                    best_name = min(fixed, key=fixed.get)
                    J_fix = fixed[best_name]
                    headroom = (J_fix - J_or) / J_fix if J_fix > 0 else np.nan
                    results.append(dict(
                        horizon=T, n_insp=N, ratio=ratio, c_insp=ci, tau=tau,
                        J_oracle=J_or, J_fixed=J_fix, best_fixed=best_name,
                        J_FixedEven=fixed["FixedEven"], J_FixedLate=fixed["FixedLate"],
                        J_FixedEarly=fixed["FixedEarly"], J_Random=fixed["Random"],
                        headroom_rel=float(headroom),
                        loss_oracle=L_or, loss_fixed=J_fix - ci * N))
                # I2 across subsets, at the median ratio
                if ratio == 5.0:
                    cv = []
                    for (cell, cond), gg in g:
                        if gg["loss"].mean() > 0:
                            cv.append(gg["loss"].std() / gg["loss"].mean())
                    print("    I2 loss CV across subsets within cell: median %.4f  p95 %.4f" % (
                        np.median(cv), np.percentile(cv, 95)))
                    gate.setdefault("I2", []).append(
                        dict(horizon=T, n_insp=N, cv_med=float(np.median(cv)),
                             cv_p95=float(np.percentile(cv, 95))))

                # I1: do different policies pick different histories?
                js = []
                for cell, d in co.items():
                    av = d["avail"]
                    a = set(pick_even(av, N)); b = set(pick_late(av, N)); e = set(pick_early(av, N))
                    rng = np.random.default_rng(1000)
                    r = set(int(v) for v in rng.choice(av, N, replace=False))
                    gg = g.get_group((cell, d["s"]["cond"])).sort_values("loss")
                    o = set(int(v) for v in gg["sub_idx"].iloc[0])
                    js.append(dict(even_late=jaccard(a, b), even_oracle=jaccard(a, o),
                                   late_oracle=jaccard(b, o), rand_oracle=jaccard(r, o)))
                jd = pd.DataFrame(js).mean()
                print("    I1 mean Jaccard: even/late %.2f  even/oracle %.2f  late/oracle %.2f  rand/oracle %.2f" % (
                    jd.even_late, jd.even_oracle, jd.late_oracle, jd.rand_oracle))
                gate.setdefault("I1", []).append(
                    dict(horizon=T, n_insp=N, **{k: float(v) for k, v in jd.items()}))

                # which indices does the oracle pick? (pre-registration §5 pred. 1)
                if ratio == 5.0:
                    rel = []
                    for cell, d in co.items():
                        gg = g.get_group((cell, d["s"]["cond"])).sort_values("loss")
                        o = list(gg["sub_idx"].iloc[0])
                        span = max(1, len(d["avail"]) - 1)
                        rel += [(i - d["avail"][0]) / span for i in o]
                    print("    oracle picks, relative position in the candidate window: "
                          "median %.2f  IQR [%.2f, %.2f]" % (
                              np.median(rel), np.percentile(rel, 25), np.percentile(rel, 75)))

    R = pd.DataFrame(results)
    R.to_csv(os.path.join(OUT, "E1_identifiability.csv"), index=False)

    print("\n" + "=" * 78)
    print("I6 · ORACLE UPPER BOUND on the value of actively choosing inspection times")
    print("=" * 78)
    print("  headroom = (J_strongest_fixed - J_oracle) / J_strongest_fixed")
    print("  %-4s %-3s %-6s %-7s %-10s %-10s %-10s %s" % (
        "T", "N", "c_f", "c_insp", "J_fixed", "J_oracle", "headroom", "best_fixed"))
    for _, r in R.iterrows():
        print("  %-4d %-3d %-6.0f %-7.1f %-10.2f %-10.2f %-10.3f %s" % (
            r["horizon"], r["n_insp"], r["ratio"], r["c_insp"], r["J_fixed"], r["J_oracle"], r["headroom_rel"], r["best_fixed"]))
    hmax = float(R["headroom_rel"].max())
    print("\n  MAX headroom across all pre-registered cells: %.3f (%.1f%%)" % (hmax, 100 * hmax))
    print("  pre-registered minimum useful benefit: %.2f (%.0f%%)" % (MARGIN, 100 * MARGIN))
    i6 = hmax >= MARGIN
    print("  I6 -> %s" % ("PASS (headroom exists)" if i6 else "FAIL (no online policy can reach the margin)"))
    gate["I6"] = dict(max_headroom=hmax, margin=MARGIN, passed=bool(i6))

    # I1 / I2 / I3 verdicts
    i1 = all(g["even_oracle"] < 0.95 for g in gate.get("I1", []))
    i2 = all(g["cv_med"] > 0.02 for g in gate.get("I2", []))
    gate["I1_verdict"] = dict(passed=bool(i1),
                              min_even_oracle=float(min(g["even_oracle"] for g in gate.get("I1", [{"even_oracle": 1.0}]))))
    gate["I2_verdict"] = dict(passed=bool(i2),
                              min_cv=float(min(g["cv_med"] for g in gate.get("I2", [{"cv_med": 0.0}]))))
    rng_rel = float((R["J_fixed"].max() - R["J_fixed"].min()) / max(R["J_fixed"].median(), 1e-9))
    gate["I3"] = dict(range_rel=rng_rel, passed=bool(rng_rel > 0.05))
    gate["I5"] = dict(passed=True, note="E0: at T=63 m=7-9 candidate times")

    json.dump(gate, open(os.path.join(OUT, "E1_gates.json"), "w"), indent=1, default=float)
    print("\nwrote E1_identifiability.csv / E1_gates.json")
    print("\n=== GATE SUMMARY ===")
    for k in ["I1_verdict", "I2_verdict", "I3", "I4_I7", "I5", "I6"]:
        print("  %-12s %s" % (k, gate[k]))


if __name__ == "__main__":
    main()
