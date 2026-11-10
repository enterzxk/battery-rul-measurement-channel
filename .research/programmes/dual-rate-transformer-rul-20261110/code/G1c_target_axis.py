# -*- coding: utf-8 -*-
"""G1c · Is the Gate-1 gain real information, or target-axis alignment?

G1b found that adding cumulative cycle count to Age+Stress+Health improves
condition-macro MAE for REMAINING CYCLES by 18.6% [-39.5, -8.7].

That result has an obvious alternative explanation which this programme has been
caught by before: if the TARGET is measured in cycles and the new FEATURE is
cycles-so-far, the feature simply locates the cell on the axis that defines the
target. That is axis alignment, not new information.

Decisive control: change the target to a DIFFERENT axis and re-run.

    target = log(remaining CALENDAR DAYS)   -> cum_cycles must still help
    target = log(remaining charge Ah)       -> cum_cycles must still help

If cum_cycles helps only when the target is in cycles, the Gate-1 gain is an
axis artefact and must be withdrawn.

Also reported: the same test for cum_ah, which is capacity-derived, so that the
leakage arm is held to the same standard.

Run remotely.  usage: python G1c_target_axis.py [days|cycles|ah]
"""
import os
import sys
import json

import numpy as np
import pandas as pd
import lightgbm as lgb

PROTO = os.environ.get("DLINE_PROTO", "/home/user/dline/prog/protocol")
OUT = os.environ.get("DLINE_OUT", PROTO)
MIN_QUERY = 1
SEED = 0
REL_GATE = 0.05

TARGET = sys.argv[1] if len(sys.argv) > 1 else "days"


def build(C):
    rows = []
    for cell, g in C.groupby("cell"):
        g = g.sort_values("rpt_idx").reset_index(drop=True)
        j = int(g.eol_rpt.iloc[0])
        if j < 2:
            continue
        N = g.cum_cycles.values.astype(float)
        day = g.day.values.astype(float)
        ah = g.cum_ah_ch.values.astype(float)
        # interval-censored EOL on each axis, midpoint
        n_eol = 0.5 * (float(g.N_L.iloc[0]) + float(g.N_U.iloc[0]))
        d_eol = 0.5 * (float(g.L.iloc[0]) + float(g.U.iloc[0]))
        ah_eol = 0.5 * (float(g.cum_ah_ch.values[j - 1]) + float(g.cum_ah_ch.values[j]))
        for k in range(MIN_QUERY, j):
            vis = g.iloc[:k + 1]
            dd = vis.day.values.astype(float)
            ss = vis.soh.values.astype(float)
            span = float(dd[-1] - dd[0])
            if span <= 0:
                continue
            if TARGET == "days":
                rul = d_eol - day[k]
            elif TARGET == "cycles":
                rul = n_eol - N[k]
            else:
                rul = ah_eol - ah[k]
            if not np.isfinite(rul) or rul <= 0:
                continue
            rows.append(dict(
                cell=cell, cond=int(g.cond.iloc[0]), rpt_idx=int(k),
                y=np.log(rul), rul=float(rul),
                day=float(dd[-1]), dod=float(g.dod_meas.iloc[0]),
                soh_k=float(ss[-1]), soh_0=float(ss[0]),
                rpt_slope=float(np.polyfit(dd, ss, 1)[0]),
                rpt_span=span, n_rpt=int(len(vis)),
                cum_cycles=float(N[k]), cum_ah_ch=float(ah[k])))
    Q = pd.DataFrame(rows)
    Q["cyc_x_dod"] = Q.cum_cycles * Q.dod
    return Q


BASE = ["day", "dod", "soh_k", "soh_0", "rpt_slope", "rpt_span", "n_rpt"]
ARMS = {
    "E0": BASE,
    "E1A_exp": BASE + ["cum_cycles"],
    "E1A_cap": BASE + ["cum_cycles", "cum_ah_ch"],
}
# when the target IS cycles, drop cum_cycles from E0's competitor set? No: E0 never
# had it. But when the target is days, "day" is in E0 and is the analogous axis
# feature, so the comparison stays symmetric across targets.


def fit_loco(Q, feats, conds):
    p = np.full(len(Q), np.nan)
    for held in conds:
        te = (Q.cond == held).values
        tr = ~te
        if tr.sum() < 200 or te.sum() == 0:
            continue
        m = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.05, num_leaves=15,
                              min_child_samples=20, subsample=0.9, colsample_bytree=0.9,
                              random_state=SEED, verbose=-1, n_jobs=4)
        m.fit(Q.loc[tr, feats].values, Q.loc[tr, "y"].values)
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
    return float(g), float(lo), float(hi), n


def main():
    C = pd.read_csv(os.path.join(PROTO, "G0_cohort.csv"))
    Q = build(C)
    conds = sorted(Q.cond.unique())
    print("=== target axis: %s ===" % TARGET.upper())
    print("rows %d | cells %d | conditions %d" % (len(Q), Q.cell.nunique(), len(conds)))
    print("RUL median %.2f  IQR [%.2f, %.2f]" % (
        Q.rul.median(), Q.rul.quantile(.25), Q.rul.quantile(.75)))

    preds = {a: fit_loco(Q, f, conds) for a, f in ARMS.items()}
    ok = np.isfinite(preds["E0"])
    for a in preds:
        ok &= np.isfinite(preds[a])
    true_v = Q.rul.values[ok]
    cond = Q.cond.values[ok]
    cm = {}
    print("\n  %-10s %-12s %-10s %s" % ("arm", "condMAE", "med|log|", "vs E0"))
    for a, p in preds.items():
        pc = np.clip(np.expm1(p[ok]), 1e-6, None)
        cm[a] = cm_mae(pc, true_v, cond)
        ml = float(np.median(np.abs(np.log(pc / true_v))))
        print("  %-10s %-12.4g %-10.3f" % (a, cm[a].mean(), ml), end="")
        if a != "E0":
            g, lo, hi, n = paired_gain(cm["E0"], cm[a])
            print("  %+6.1f%% [%+6.1f,%+6.1f]" % (g, lo, hi))
        else:
            print("  -")

    out = dict(target=TARGET, n_cond=int(len(conds)), n_rows=int(len(Q)),
               cond_macro_mae={a: float(cm[a].mean()) for a in cm})
    for a in ["E1A_exp", "E1A_cap"]:
        g, lo, hi, n = paired_gain(cm["E0"], cm[a])
        out[a] = dict(gain=g, lo=lo, hi=hi,
                      passes=(g <= -100 * REL_GATE) and (hi < 0))
        print("  %-9s pre-registered rule: %s" % (a, "PASS" if out[a]["passes"] else "FAIL"))
    json.dump(out, open(os.path.join(OUT, "G1c_%s.json" % TARGET), "w"), indent=1, default=float)
    print("\nwrote G1c_%s.json" % TARGET)


if __name__ == "__main__":
    main()
