# -*- coding: utf-8 -*-
"""G1d · The clock-equated endpoint control Codex demanded.

Why this is the decisive test of Gate 1:

    E1-A_exp predicts REMAINING cycles directly, with cumulative cycle count as a
    feature. But RUL = N_EOL - N_now. So a model that predicts the TOTAL endpoint
    N_EOL well, and then subtracts the observed N_now, obtains RUL "for free"
    through an arithmetic identity. If that simple route matches E1-A_exp, then
    the cumulative count contributed no information -- only the subtraction.

Arms (identical held-out queries, identical folds, identical tuning budget):
    E0_direct        E0 features -> log RUL directly            (no count feature)
    E1A_exp          E0 + cum_cycles -> log RUL directly        (Gate-1 winner)
    E0_endpoint      E0 features -> log N_EOL, then RUL_hat = N_EOL_hat - N_now
    E1A_endpoint     E0 + cum_cycles -> log N_EOL, then subtract

Pre-registered reading (fixed before running):
    If E0_endpoint matches E1A_exp (paired CI on the MAE difference includes 0),
    then Gate 1's gain is an arithmetic identity and the "exposure carries
    information" claim must be withdrawn.
    If E1A_exp still beats E0_endpoint by >=5% with CI excluding 0, the count
    carries information beyond clock subtraction.

Run remotely.
"""
import os
import json

import numpy as np
import pandas as pd
import lightgbm as lgb

PROTO = os.environ.get("DLINE_PROTO", "/home/user/dline/prog/protocol")
OUT = os.environ.get("DLINE_OUT", PROTO)
SEED = 0
REL = 0.05

BASE = ["day", "dod", "soh_k", "soh_0", "rpt_slope", "rpt_span", "n_rpt"]


def build(C):
    rows = []
    for cell, g in C.groupby("cell"):
        g = g.sort_values("rpt_idx").reset_index(drop=True)
        j = int(g.eol_rpt.iloc[0])
        if j < 2:
            continue
        N = g.cum_cycles.values.astype(float)
        n_eol = 0.5 * (float(g.N_L.iloc[0]) + float(g.N_U.iloc[0]))
        for k in range(1, j):
            vis = g.iloc[:k + 1]
            dd = vis.day.values.astype(float)
            ss = vis.soh.values.astype(float)
            span = float(dd[-1] - dd[0])
            if span <= 0:
                continue
            rul = n_eol - N[k]
            if not np.isfinite(rul) or rul <= 0:
                continue
            rows.append(dict(cell=cell, cond=int(g.cond.iloc[0]), rpt_idx=int(k),
                             y_rul=np.log(rul), y_eol=np.log(n_eol),
                             n_eol=n_eol, cum_cycles=float(N[k]), rul=float(rul),
                             day=float(dd[-1]), dod=float(g.dod_meas.iloc[0]),
                             soh_k=float(ss[-1]), soh_0=float(ss[0]),
                             rpt_slope=float(np.polyfit(dd, ss, 1)[0]),
                             rpt_span=span, n_rpt=int(len(vis))))
    return pd.DataFrame(rows)


def fit_loco(Q, feats, target, conds):
    p = np.full(len(Q), np.nan)
    for held in conds:
        te = (Q.cond == held).values
        tr = ~te
        if tr.sum() < 200 or te.sum() == 0:
            continue
        m = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.05, num_leaves=15,
                              min_child_samples=20, subsample=0.9, colsample_bytree=0.9,
                              random_state=SEED, verbose=-1, n_jobs=4)
        m.fit(Q.loc[tr, feats].values, Q.loc[tr, target].values)
        p[te] = m.predict(Q.loc[te, feats].values)
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
    return float(g), float(lo), float(hi)


def main():
    C = pd.read_csv(os.path.join(PROTO, "G0_cohort.csv"))
    Q = build(C)
    conds = sorted(Q.cond.unique())
    print("=== G1d · clock-equated endpoint control ===")
    print("rows %d | cells %d | conditions %d" % (len(Q), Q.cell.nunique(), len(conds)))

    N = Q.cum_cycles.values
    # direct RUL
    p_e0 = fit_loco(Q, BASE, "y_rul", conds)
    p_e1 = fit_loco(Q, BASE + ["cum_cycles"], "y_rul", conds)
    # endpoint, then subtract the observed count
    pe0 = fit_loco(Q, BASE, "y_eol", conds)
    pe1 = fit_loco(Q, BASE + ["cum_cycles"], "y_eol", conds)

    arms = {
        "E0_direct": np.clip(np.expm1(p_e0), 1.0, None),
        "E1A_exp": np.clip(np.expm1(p_e1), 1.0, None),
        "E0_endpoint": np.clip(np.exp(pe0) - N, 1.0, None),
        "E1A_endpoint": np.clip(np.exp(pe1) - N, 1.0, None),
    }
    ok = np.isfinite(list(arms.values())).all(axis=0)
    true_v = Q.rul.values[ok]
    cond = Q.cond.values[ok]
    print("scored rows %d" % int(ok.sum()))

    cm, mlog = {}, {}
    for a, p in arms.items():
        pc = p[ok]
        cm[a] = cm_mae(pc, true_v, cond)
        mlog[a] = float(np.median(np.abs(np.log(pc / true_v))))

    print("\n  %-14s %-12s %-10s %s" % ("arm", "condMAE", "med|log|", "vs E0_endpoint"))
    for a in arms:
        print("  %-14s %-12.4g %-10.3f" % (a, cm[a].mean(), mlog[a]), end="")
        if a != "E0_endpoint":
            g, lo, hi = paired_gain(cm["E0_endpoint"], cm[a])
            print("  %+6.1f%% [%+6.1f,%+6.1f]" % (g, lo, hi))
        else:
            print("  -")

    print("\n=== pre-registered reading ===")
    g, lo, hi = paired_gain(cm["E0_endpoint"], cm["E1A_exp"])
    print("  E1A_exp vs E0_endpoint: %+.2f%% [%+.2f, %+.2f]" % (g, lo, hi))
    if hi >= 0:
        verdict = ("ARITHMETIC: the count's value is the subtraction, not information. "
                   "WITHDRAW the exposure-information claim.")
    elif g <= -100 * REL:
        verdict = "INFORMATION: count beats clock-equated subtraction by >=5%%."
    else:
        verdict = "PARTIAL: count beats subtraction but below the 5% practical gate."
    print("  -> " + verdict)

    g2, lo2, hi2 = paired_gain(cm["E1A_endpoint"], cm["E1A_exp"])
    print("\n  E1A_exp vs E1A_endpoint: %+.2f%% [%+.2f, %+.2f]" % (g2, lo2, hi2))
    print("  (positive means direct RUL modelling beats endpoint-then-subtract)")

    out = dict(n_rows=int(ok.sum()), n_cond=int(len(cond)),
               cond_macro_mae={a: float(cm[a].mean()) for a in cm},
               e1a_vs_endpoint=dict(gain=g, lo=lo, hi=hi),
               e1a_vs_e1a_endpoint=dict(gain=g2, lo=lo2, hi=hi2),
               verdict=verdict)
    json.dump(out, open(os.path.join(OUT, "G1d_endpoint_control.json"), "w"), indent=1, default=float)
    print("\nwrote G1d_endpoint_control.json")


if __name__ == "__main__":
    main()
