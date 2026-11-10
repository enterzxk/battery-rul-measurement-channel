# -*- coding: utf-8 -*-
"""G1b · Gate 1 re-run on the CORRECTED cohort (63 conditions, measured DoD).

Two audit-found defects are fixed before this runs:
  * the loader no longer drops whole cells for one empty RPT record
    (recovers 40 cells / 10 conditions -> 250 cells / 63 conditions);
  * the stress covariate uses the MEASURED depth of discharge, not the tabulated
    `mean_DoD_pct`, which is not reproducible for 21 of 53 conditions.

Arms (identical query keys, identical folds, identical tuning budget):
    ConditionMedian  training-condition median log RUL           (floor)
    E0               AGE + STRESS_meas + HEALTH                  (strong baseline)
    E1A_exp          E0 + cum_cycles                             (LEGAL exposure only)
    E1A_x            E0 + cum_cycles + cum_cycles*DoD_meas       (legal, explicit interaction)
    E1A_cap          E0 + cum_cycles + cum_ah_ch + cum_ah_dis    (CONTAMINATED control)

The CAPACITY arm is retained ONLY as a positive control for the leakage: the audit
measured Spearman(capacity_charge, concurrent SOH) = 0.995 with
median(capacity_charge / concurrent capacity) = 0.300 = the protocol DoD, so
cumulative Ah is a low-pass-filtered SOH trajectory. If this arm wins, it is
reading health, not exposure, and must never be reported as an exposure result.

Pre-registered Gate 1 rule (unchanged, fixed before the first run):
    pass iff relative condition-macro MAE improvement >= 5% AND the paired
    condition-level bootstrap 95% CI upper bound is < 0 AND the gain is not
    concentrated in a single condition.

Run remotely.
"""
import os
import json

import numpy as np
import pandas as pd
import lightgbm as lgb

PROTO = os.environ.get("DLINE_PROTO", "/home/user/dline/prog/protocol")
OUT = os.environ.get("DLINE_OUT", PROTO)
MIN_QUERY = 1
SEED = 0
REL_GATE = 0.05


def build_queries(C):
    rows = []
    for cell, g in C.groupby("cell"):
        g = g.sort_values("rpt_idx").reset_index(drop=True)
        j = int(g.eol_rpt.iloc[0])
        if j < 2:
            continue
        N = g.cum_cycles.values
        n_eol = 0.5 * (float(g.N_L.iloc[0]) + float(g.N_U.iloc[0]))
        for k in range(MIN_QUERY, j):
            vis = g.iloc[:k + 1]
            days = vis.day.values.astype(float)
            sohs = vis.soh.values.astype(float)
            span = float(days[-1] - days[0])
            if span <= 0:
                continue
            slope = float(np.polyfit(days, sohs, 1)[0])
            rul = n_eol - N[k]
            if not np.isfinite(rul) or rul <= 0:
                continue
            rows.append(dict(
                cell=cell, cond=int(g.cond.iloc[0]), rpt_idx=int(k),
                y=np.log(rul), rul_cycles=float(rul),
                day=float(days[-1]),
                dod=float(g.dod_meas.iloc[0]),
                soh_k=float(sohs[-1]), soh_0=float(sohs[0]),
                rpt_slope=slope, rpt_span=span, n_rpt=int(len(vis)),
                cum_cycles=float(N[k]),
                cum_ah_ch=float(g.cum_ah_ch.values[k]),
                cum_ah_dis=float(g.cum_ah_dis.values[k])))
    Q = pd.DataFrame(rows)
    Q["cyc_x_dod"] = Q.cum_cycles * Q.dod
    return Q


BASE = ["day", "dod", "soh_k", "soh_0", "rpt_slope", "rpt_span", "n_rpt"]
ARMS = {
    "E0": BASE,
    "E1A_exp": BASE + ["cum_cycles"],
    "E1A_x": BASE + ["cum_cycles", "cyc_x_dod"],
    "E1A_cap": BASE + ["cum_cycles", "cum_ah_ch", "cum_ah_dis"],
}


def fit_loco(Q, feats, conds):
    p = np.full(len(Q), np.nan)
    for held in conds:
        te = (Q.cond == held).values
        tr = ~te
        if tr.sum() < 200 or te.sum() == 0:
            continue
        m = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.05, num_leaves=15,
                              min_child_samples=20, subsample=0.9, colsample_bytree=0.9,
                              random_state=SEED, verbose=-1)
        m.fit(Q.loc[tr, feats].values, Q.loc[tr, "y"].values)
        p[te] = m.predict(Q.loc[te, feats].values)
    return p


def cond_median_loco(Q, conds):
    p = np.full(len(Q), np.nan)
    for held in conds:
        te = (Q.cond == held).values
        tr = ~te
        if tr.sum() < 50 or te.sum() == 0:
            continue
        p[te] = float(np.median(Q.loc[tr, "y"].values))
    return p


def cm_mae(pred, true, cond):
    return pd.DataFrame({"e": np.abs(pred - true), "cond": cond}).groupby("cond").e.mean()


def paired_gain(a, b, n_boot=4000, seed=0):
    idx = a.index.intersection(b.index)
    x, y = a.loc[idx].values, b.loc[idx].values
    n = len(idx)
    g = 100.0 * (y.mean() / x.mean() - 1.0)
    rng = np.random.default_rng(seed)
    bs = np.array([100.0 * (y[k].mean() / x[k].mean() - 1.0)
                   for k in (rng.integers(0, n, n) for _ in range(n_boot))])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return float(g), float(lo), float(hi), n


def main():
    C = pd.read_csv(os.path.join(PROTO, "G0_cohort.csv"))
    Q = build_queries(C)
    conds = sorted(Q.cond.unique())
    print("=== Gate 1 (corrected cohort) ===")
    print("query rows %d | cells %d | conditions %d" % (len(Q), Q.cell.nunique(), len(conds)))
    print("measured DoD: median %.3f  IQR [%.3f, %.3f]" % (
        Q.dod.median(), Q.dod.quantile(.25), Q.dod.quantile(.75)))
    print("RUL cycles: median %.0f  IQR [%.0f, %.0f]" % (
        Q.rul_cycles.median(), Q.rul_cycles.quantile(.25), Q.rul_cycles.quantile(.75)))

    preds = {"ConditionMedian": cond_median_loco(Q, conds)}
    for a, f in ARMS.items():
        preds[a] = fit_loco(Q, f, conds)
    ok = np.isfinite(preds["E0"])
    for a in preds:
        ok &= np.isfinite(preds[a])
    print("scored rows: %d" % int(ok.sum()))

    true_c = Q.rul_cycles.values[ok]
    cond = Q.cond.values[ok]
    cm, rms, mlog = {}, {}, {}
    for a, p in preds.items():
        pc = np.clip(np.expm1(p[ok]), 1.0, None)
        cm[a] = cm_mae(pc, true_c, cond)
        r = pd.DataFrame({"e": (pc - true_c) ** 2, "cond": cond}).groupby("cond").e.mean()
        rms[a] = float(np.sqrt(r).mean())
        mlog[a] = float(np.median(np.abs(np.log(pc / true_c))))

    print("\n  %-16s %-10s %-10s %-9s %s" % ("arm", "condMAE", "condRMSE", "med|log|", "vs E0"))
    for a in preds:
        print("  %-16s %-10.1f %-10.1f %-9.3f" % (a, cm[a].mean(), rms[a], mlog[a]), end="")
        if a != "E0":
            g, lo, hi, n = paired_gain(cm["E0"], cm[a])
            print("  %+6.1f%% [%+6.1f,%+6.1f]" % (g, lo, hi))
        else:
            print("  -")

    print("\n=== pre-registered Gate 1 verdict (>= %.0f%% AND CI upper < 0) ===" % (100 * REL_GATE))
    verdict = {}
    for a in ["E1A_exp", "E1A_x", "E1A_cap"]:
        g, lo, hi, n = paired_gain(cm["E0"], cm[a])
        passed = (g <= -100 * REL_GATE) and (hi < 0)
        verdict[a] = dict(gain=g, lo=lo, hi=hi, passed=bool(passed))
        print("  %-9s %+6.2f%%  [%+6.2f, %+6.2f]  -> %s" % (
            a, g, lo, hi, "PASS" if passed else "FAIL"))

    print("\n=== concentration check ===")
    for a in ["E1A_exp", "E1A_x", "E1A_cap"]:
        gs = []
        for c in cm[a].index:
            idx = cm[a].index.difference([c])
            gs.append(100.0 * (cm[a].loc[idx].mean() / cm["E0"].loc[idx].mean() - 1.0))
        gs = np.array(gs)
        print("  %-9s leave-one-condition-out gain range [%+.1f, %+.1f]  frac<0 %.0f%%" % (
            a, gs.min(), gs.max(), 100 * (gs < 0).mean()))

    out = dict(n_rows=int(len(Q)), n_cells=int(Q.cell.nunique()), n_cond=int(len(conds)),
               cond_macro_mae={a: float(cm[a].mean()) for a in cm},
               verdict=verdict, rel_gate=REL_GATE)
    Q.to_csv(os.path.join(OUT, "G1b_queries.csv"), index=False)
    P = Q.loc[ok, ["cell", "cond", "rpt_idx", "rul_cycles"]].copy()
    for a, p in preds.items():
        P["pred_" + a] = p[ok]
    P.to_csv(os.path.join(OUT, "G1b_predictions.csv"), index=False)
    json.dump(out, open(os.path.join(OUT, "G1b_information_value.json"), "w"), indent=1, default=float)
    print("\nwrote G1b_queries.csv / G1b_predictions.csv / G1b_information_value.json")


if __name__ == "__main__":
    main()
