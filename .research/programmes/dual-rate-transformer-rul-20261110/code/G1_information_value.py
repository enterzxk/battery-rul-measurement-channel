# -*- coding: utf-8 -*-
"""G1 · Gate 1: does per-cycle operating information add value beyond Age+Stress+Health?

The brief's core hypothesis H1. This is deliberately BEFORE any Transformer: if the
extra information has no incremental value, no architecture is worth training.

Prediction task
    At RPT index k (so only RPTs 0..k are visible), predict the remaining PHYSICAL
    CYCLES to the 80% SOH crossing.
    Target y = log(RUL_cycles), RUL_cycles = N_EOL - N_k.
    EOL is interval-censored between the last RPT above 0.80 and the first below,
    so N_EOL is taken at the midpoint of [N_{j-1}, N_j] for the primary analysis and
    at both endpoints for a sensitivity check. Cells with no observed crossing are
    right-censored and excluded (count reported).

Feature groups (this separation is the whole point of the experiment)
    AGE      day_k                                   calendar time
    STRESS   charge_C, discharge_C, DoD              design condition
    HEALTH   soh_k, soh_0, RPT slope, span, n_rpt    independent RPT measurements
    EXPOSURE cum_cycles_k                            pure count, no capacity info
    CAPACITY cum_ah_charge_k, cum_ah_discharge_k     CAPACITY-DERIVED, see note

LEAKAGE NOTE (why CAPACITY is not "exposure"):
    per-cycle capacity_charge is measured delivered charge, i.e. approximately
    DoD x current cell capacity. Summing it therefore carries the capacity
    trajectory, so cumulative Ah is partly a HEALTH measurement, not a free BMS
    counter. It is therefore reported as a SEPARATE arm, never merged into
    "exposure". Whether it is genuinely capacity-derived in this data is being
    measured independently; this script reports it both ways so the claim can be
    made either way once that audit lands.

Models (all leave-one-condition-out, condition-macro aggregation)
    ConditionMedian  training-condition median log RUL  (no-information floor)
    E0               AGE + STRESS + HEALTH               (strong baseline)
    E1A_exp          E0 + EXPOSURE                       (pure exposure increment)
    E1A_cap          E0 + EXPOSURE + CAPACITY            (capacity-derived increment)

Pre-registered Gate 1 rule (fixed here, before running):
    H1 passes only if E1A_exp improves condition-macro MAE over E0 by >= 5%
    relative AND the paired condition-level bootstrap 95% CI upper bound is < 0
    for the MAE difference AND the improvement is not concentrated in one condition
    (leave-one-condition-out-of-the-gain check).

Run remotely.
"""
import os
import json

import numpy as np
import pandas as pd
import lightgbm as lgb

PROTO = os.environ.get("DLINE_PROTO", "/home/user/dline/prog/protocol")
RES = os.environ.get("DLINE_RES", "/home/user/dline/prog/results")
OUT = os.environ.get("DLINE_OUT", PROTO)

THRESH = 0.80
MIN_QUERY = 1          # need RPT 0 and 1 for a slope
SEED = 0
REL_GATE = 0.05


def load():
    T = pd.read_csv(os.path.join(PROTO, "F4_clock_table.csv"))
    stress = pd.read_csv(os.path.join(RES, "isu_conditions.csv"))
    stress.columns = ["cond", "charge_C", "discharge_C", "mean_DoD_pct"]
    stress["DoD"] = stress.mean_DoD_pct / 100.0
    T = T.merge(stress[["cond", "charge_C", "discharge_C", "DoD"]], on="cond", how="left")
    return T, stress


def build_queries(T):
    """One row per (cell, query RPT k) with strictly as-of-k features."""
    rows = []
    n_nocross = 0
    for cell, g in T.groupby("cell"):
        g = g.sort_values("rpt_idx").reset_index(drop=True)
        soh = g.soh.values
        below = np.where(soh <= THRESH)[0]
        if below.size == 0:
            n_nocross += 1
            continue
        j = int(below[0])
        if j < 2:
            continue
        N = g.cum_cycles.values
        # interval-censored EOL in cycles
        n_lo = N[j - 1]
        n_hi = N[j]
        n_eol = 0.5 * (n_lo + n_hi)
        for k in range(MIN_QUERY, j):
            vis = g.iloc[:k + 1]
            days = vis.day.values
            sohs = vis.soh.values
            span = float(days[-1] - days[0])
            if span <= 0:
                continue
            slope = float(np.polyfit(days, sohs, 1)[0])
            rul = n_eol - N[k]
            if not np.isfinite(rul) or rul <= 0:
                continue
            rows.append(dict(
                cell=cell, cond=int(g.cond.iloc[0]), rpt_idx=int(k),
                y=np.log(rul),
                rul_cycles=float(rul),
                rul_lo=float(n_lo - N[k]), rul_hi=float(n_hi - N[k]),
                # AGE
                day=float(days[-1]),
                # STRESS
                charge_C=float(g.charge_C.iloc[0]),
                discharge_C=float(g.discharge_C.iloc[0]),
                DoD=float(g.DoD.iloc[0]),
                # HEALTH (RPT only)
                soh_k=float(sohs[-1]), soh_0=float(sohs[0]),
                rpt_slope=slope, rpt_span=span, n_rpt=int(len(vis)),
                # EXPOSURE (pure count)
                cum_cycles=float(N[k]),
                # CAPACITY-DERIVED
                cum_ah_ch=float(g.cum_ah_ch.values[k]),
                cum_ah_dis=float(g.cum_ah_dis.values[k]),
                # bookkeeping
                eol_rpt=j))
    Q = pd.DataFrame(rows)
    return Q, n_nocross


GROUPS = {
    "AGE": ["day"],
    "STRESS": ["charge_C", "discharge_C", "DoD"],
    "HEALTH": ["soh_k", "soh_0", "rpt_slope", "rpt_span", "n_rpt"],
    "EXPOSURE": ["cum_cycles"],
    "CAPACITY": ["cum_ah_ch", "cum_ah_dis"],
}
ARMS = {
    "E0": ["AGE", "STRESS", "HEALTH"],
    "E1A_exp": ["AGE", "STRESS", "HEALTH", "EXPOSURE"],
    "E1A_cap": ["AGE", "STRESS", "HEALTH", "EXPOSURE", "CAPACITY"],
}


def feats_of(groups):
    out = []
    for g in groups:
        out += GROUPS[g]
    return out


def fit_loco(Q, feats, conds):
    """Leave-one-condition-out LightGBM; returns prediction for every row."""
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


def cond_macro_mae(pred_cycles, true_cycles, cond):
    d = pd.DataFrame({"e": np.abs(pred_cycles - true_cycles), "cond": cond})
    return d.groupby("cond").e.mean()


def paired_gain(cm_a, cm_b, n_boot=4000, seed=0):
    idx = cm_a.index.intersection(cm_b.index)
    a = cm_a.loc[idx].values
    b = cm_b.loc[idx].values
    n = len(idx)
    gain = 100.0 * (b.mean() / a.mean() - 1.0)
    rng = np.random.default_rng(seed)
    bs = np.empty(n_boot)
    for i in range(n_boot):
        k = rng.integers(0, n, n)
        bs[i] = 100.0 * (b[k].mean() / a[k].mean() - 1.0)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return float(gain), float(lo), float(hi), n


def main():
    T, stress = load()
    Q, n_nocross = build_queries(T)
    conds = sorted(Q.cond.unique())
    print("=== Gate 1 · information value ===")
    print("cells with an observed 80%% crossing: %d | right-censored (no crossing): %d" % (
        T.cell.nunique() - n_nocross, n_nocross))
    print("query rows: %d | cells: %d | conditions: %d" % (
        len(Q), Q.cell.nunique(), len(conds)))
    print("RUL in cycles: median %.0f  IQR [%.0f, %.0f]" % (
        Q.rul_cycles.median(), Q.rul_cycles.quantile(.25), Q.rul_cycles.quantile(.75)))
    print("cells per condition: min %d  median %.0f  max %d" % (
        Q.groupby("cond").cell.nunique().min(), Q.groupby("cond").cell.nunique().median(),
        Q.groupby("cond").cell.nunique().max()))

    preds = {}
    preds["ConditionMedian"] = cond_median_loco(Q, conds)
    for arm, groups in ARMS.items():
        feats = feats_of(groups)
        preds[arm] = fit_loco(Q, feats, conds)
        print("  fitted %-8s with %2d features: %s" % (arm, len(feats), feats))

    ok = np.isfinite(preds["E0"])
    for a in preds:
        ok &= np.isfinite(preds[a])
    print("\nscored rows: %d" % int(ok.sum()))

    true_c = Q.rul_cycles.values[ok]
    cond = Q.cond.values[ok]
    cm, rmse, mlog = {}, {}, {}
    for a, p in preds.items():
        pc = np.clip(np.expm1(p[ok]), 1.0, None)
        cm[a] = cond_macro_mae(pc, true_c, cond)
        r = pd.DataFrame({"e": (pc - true_c) ** 2, "cond": cond}).groupby("cond").e.mean()
        rmse[a] = float(np.sqrt(r).mean())
        mlog[a] = float(np.median(np.abs(np.log(pc / true_c))))

    print("\n  %-16s %-14s %-14s %-12s %s" % (
        "arm", "condMacro MAE", "condMacro RMSE", "med |log err|", "vs E0"))
    for a in preds:
        print("  %-16s %-14.1f %-14.1f %-12.3f" % (
            a, cm[a].mean(), rmse[a], mlog[a]), end="")
        if a != "E0":
            g, lo, hi, n = paired_gain(cm["E0"], cm[a])
            print("  %+6.1f%% [%+6.1f,%+6.1f] n=%d" % (g, lo, hi, n))
        else:
            print("  -")

    print("\n=== pre-registered Gate 1 verdict (needs >= %.0f%% AND CI upper < 0) ===" % (100 * REL_GATE))
    for a in ["E1A_exp", "E1A_cap"]:
        g, lo, hi, n = paired_gain(cm["E0"], cm[a])
        passed = (g <= -100 * REL_GATE) and (hi < 0)
        print("  %-9s gain %+6.2f%%  95%% CI [%+6.2f, %+6.2f]  -> %s" % (
            a, g, lo, hi, "PASS" if passed else "FAIL"))

    # concentration check: drop each condition and re-evaluate the gain
    print("\n=== concentration check (drop one condition, recompute the gain) ===")
    for a in ["E1A_exp", "E1A_cap"]:
        gains = []
        for c in cm[a].index:
            idx = cm[a].index.difference([c])
            g = 100.0 * (cm[a].loc[idx].mean() / cm["E0"].loc[idx].mean() - 1.0)
            gains.append(g)
        gains = np.array(gains)
        print("  %-9s gain range across leave-one-out: [%+.1f, %+.1f]  share still < 0: %.0f%%" % (
            a, gains.min(), gains.max(), 100 * (gains < 0).mean()))

    # endpoint sensitivity of the censored EOL
    print("\n=== censoring sensitivity (EOL at N_lo vs midpoint vs N_hi) ===")
    for tag, col in [("N_lo", "rul_lo"), ("mid", "rul_cycles"), ("N_hi", "rul_hi")]:
        y = Q[col].values[ok]
        y = np.clip(y, 1.0, None)
        for a in ["E0", "E1A_exp"]:
            pc = np.clip(np.expm1(preds[a][ok]), 1.0, None)
            m = cond_macro_mae(pc, y, cond).mean()
            print("  %-4s %-8s condMacro MAE %8.1f" % (tag, a, m), end="")
        print()

    out = dict(n_rows=int(len(Q)), n_cells=int(Q.cell.nunique()), n_cond=int(len(conds)),
               n_right_censored=int(n_nocross),
               cond_macro_mae={a: float(cm[a].mean()) for a in cm},
               rel_gate=REL_GATE)
    for a in ["E1A_exp", "E1A_cap"]:
        g, lo, hi, n = paired_gain(cm["E0"], cm[a])
        out[a] = dict(gain_pct=g, ci_lo=lo, ci_hi=hi, n_cond=n)
    Q.to_csv(os.path.join(OUT, "G1_queries.csv"), index=False)
    P = Q.loc[ok, ["cell", "cond", "rpt_idx", "rul_cycles", "rul_lo", "rul_hi"]].copy()
    for a, p in preds.items():
        P["pred_" + a] = p[ok]
    P.to_csv(os.path.join(OUT, "G1_predictions.csv"), index=False)
    json.dump(out, open(os.path.join(OUT, "G1_information_value.json"), "w"), indent=1, default=float)
    print("\nwrote G1_queries.csv / G1_predictions.csv / G1_information_value.json")


if __name__ == "__main__":
    main()
