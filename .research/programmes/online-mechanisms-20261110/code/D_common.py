# -*- coding: utf-8 -*-
"""Shared loaders for line D (decision rule).

Why this module exists: line C's ablation script (C_validity_ablation.py) mixes
SCHEDULE features (n_obs, span) into the arm it calls "health". That is the same
error class this programme has already committed three times: a change produced
automatically by the schedule being read as an information effect. Line D must
be able to separate the two, so every downstream script builds query rows from
here and names the feature groups explicitly.

Feature groups (all available at prediction time, none uses the eventual L):
    AGE      : logt
    SCHED    : n_obs, span, cadence          <- pure schedule, no health values
    HEALTH   : soh_last, soh0, slope         <- health values, no schedule
    STRESS   : DoD, cc, cd                   <- condition descriptors

soh is stored as a FRACTION (0-1) for both cohorts. The C scripts used percent
for UConn; HGB bins features by quantile, so the scaling is invariant and the
C arm must reproduce. D1 checks that reproduction explicitly.

Axis: UConn = cumulative cycles, ISU = calendar days.
"""
import os
import json
import re
import zipfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")
RES = os.path.join(HERE, "..", "..", "..", "results")
RAW_ISU = r"E:\桌面\rul\data\external\isu_raw\RPT_json.zip"

MIN_OBS = 3
EOL_SOH = 0.80

AGE = ["logt"]
SCHED = ["n_obs", "span", "cadence"]
HEALTH = ["soh_last", "soh0", "slope"]
STRESS = ["DoD", "cc", "cd"]


def load_uconn():
    """UConn 64 cells / 11 conditions. x = cumulative cycles, soh = fraction."""
    u = pd.read_csv(os.path.join(PROTO, "uconn_tidy_fixed.csv"))
    e = pd.read_csv(os.path.join(PROTO, "uconn_eol_fixed.csv"))
    e = e[e.kind == "interval"].set_index("cell")
    cells = {}
    for c, g in u.groupby("cell"):
        if c not in e.index:
            continue
        g = g.sort_values("cum")
        cells[c] = dict(
            cell=str(c),
            cond=int(g.cond.iloc[0]),
            x=g.cum.values.astype(float),
            soh=g.soh.values.astype(float) / 100.0,
            L=float(e.loc[c, "L"]),
            U=float(e.loc[c, "U"]),
        )
    return cells


def load_isu():
    """ISU 250 cells / 63 groups. x = calendar days, soh = fraction.

    Rebuilt from the raw 929 MB JSON exactly as C_validity_ablation.py does, so
    the numbers are comparable with the C result being audited.
    """
    z = zipfile.ZipFile(RAW_ISU)
    cells = {}
    for n in sorted(x for x in z.namelist() if x.lower().endswith(".json")):
        name = n.split("/")[-1].replace(".json", "")
        m = re.match(r"G(\d+)C(\d+)", name)
        if not m:
            continue
        g = int(m.group(1))
        try:
            dd = json.loads(json.loads(z.read(n).decode("utf-8")))
        except Exception:
            continue
        cap = dd.get("capacity_discharge_C_5") or dd.get("capacity_discharge_C_2")
        ts = (dd.get("start_stop_time") or {}).get("start") or []
        if not isinstance(cap, list) or len(cap) < 4:
            continue
        v = []
        for x in cap:
            try:
                v.append(float(x))
            except Exception:
                v.append(np.nan)
        v = np.array(v, float)
        L = min(len(v), len(ts)) if ts else 0
        if L < 4:
            continue
        t = [pd.to_datetime(x, errors="coerce") for x in ts[:L]]
        if not all(pd.notna(x) for x in t):
            continue
        ref = np.nanmax(v[:L])
        if not np.isfinite(ref) or ref <= 0:
            continue
        soh = v[:L] / ref
        day = np.array([(x - t[0]).total_seconds() / 86400.0 for x in t])
        b = np.where(soh <= EOL_SOH)[0]
        if b.size == 0:
            continue
        k = int(b[0])
        if k == 0:
            continue
        cells[name] = dict(cell=name, cond=g, x=day, soh=soh,
                           L=day[k - 1], U=day[k])
    return cells


def load_stress():
    c = pd.read_csv(os.path.join(RES, "isu_conditions.csv"))
    c.columns = ["group", "charge_C", "discharge_C", "mean_DoD_pct"]
    c["DoD"] = c.mean_DoD_pct / 100.0
    return c.set_index("group")


def build_queries(cells, ages, stress=None, min_obs=MIN_OBS):
    """Query rows on FIXED ABSOLUTE AGES, chosen without reference to any EOL.

    Eligibility is the only place the population can drift, so it is explicit:
    a (cell, age) row exists iff age < L and the cell has >= min_obs observations
    by that age. Within one age the cell set is therefore identical for every
    arm, which is the discipline requirement.
    """
    recs = []
    for c, s in cells.items():
        if stress is not None and s["cond"] not in stress.index:
            continue
        for t in ages:
            if t <= 0 or t >= s["L"]:
                continue
            vis = s["x"] <= t
            if vis.sum() < min_obs:
                continue
            xv, sv = s["x"][vis], s["soh"][vis]
            span = float(xv[-1] - xv[0])
            n_obs = int(vis.sum())
            r = dict(
                cell=c, cond=s["cond"], age=float(t), logt=float(np.log(t)),
                n_obs=n_obs, span=span,
                cadence=(span / (n_obs - 1)) if n_obs > 1 else 0.0,
                soh_last=float(sv[-1]), soh0=float(sv[0]),
                slope=float((sv[-1] - sv[0]) / max(span, 1e-12)),
                y=float(np.log(s["U"])),
                # post-hoc only, NEVER a feature: used for mechanism description
                L=float(s["L"]), life_frac=float(t / s["L"]),
                amp=float(1.0 - sv[-1]),
            )
            if stress is not None:
                r["DoD"] = float(stress.loc[s["cond"], "DoD"])
                r["cc"] = float(stress.loc[s["cond"], "charge_C"])
                r["cd"] = float(stress.loc[s["cond"], "discharge_C"])
            recs.append(r)
    return pd.DataFrame(recs)


def fit_loco(Q, feats, model=None):
    """Leave-one-condition-out. Returns predictions aligned to Q.index."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    p = np.full(len(Q), np.nan)
    for held in sorted(Q.cond.unique()):
        te = (Q.cond == held).values
        tr = ~te
        if tr.sum() < 40 or te.sum() == 0:
            continue
        m = model() if model is not None else HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.05, random_state=0)
        m.fit(Q.loc[tr, feats].values, Q.loc[tr, "y"].values)
        p[te] = m.predict(Q.loc[te, feats].values)
    return p


def cond_macro(abs_err, cond):
    """Condition-macro mean absolute error. Condition is the independent unit."""
    d = pd.DataFrame({"e": abs_err, "cond": np.asarray(cond)})
    return d.groupby("cond").e.mean()


def paired_gain(cm_a, cm_h, n_boot=2000, seed=0):
    """Relative gain of arm h over arm a, paired at condition level.

    Returns (gain_pct, lo, hi, wilcoxon_p). Negative gain = h is better.
    Bootstrap resamples CONDITIONS, which is the unit that is independent.
    """
    from scipy import stats
    idx = cm_a.index.intersection(cm_h.index)
    a = cm_a.loc[idx].values
    h = cm_h.loc[idx].values
    n = len(idx)
    gain = 100.0 * (h.mean() / a.mean() - 1.0)
    rng = np.random.default_rng(seed)
    gs = np.empty(n_boot)
    for i in range(n_boot):
        k = rng.integers(0, n, n)
        gs[i] = 100.0 * (h[k].mean() / a[k].mean() - 1.0)
    lo, hi = np.percentile(gs, [2.5, 97.5])
    try:
        p = float(stats.wilcoxon(h, a).pvalue)
    except ValueError:
        p = float("nan")
    return float(gain), float(lo), float(hi), p


def mde_pct(baseline_mae, n_cond, alpha=0.05, power=0.80):
    """Minimum detectable relative effect for a paired comparison, rough.

    Uses the paired-difference standard deviation implied by nothing better than
    a rule of thumb is NOT acceptable, so callers pass an observed paired SD.
    Kept here only for the reported 'MDE = 11% of baseline' convention from C,
    which was n_cond-based; see D1 for the recomputed version.
    """
    z_a = 1.959963984540054
    z_b = 0.8416212335729143
    return 100.0 * (z_a + z_b) * np.sqrt(2.0 / max(n_cond, 1))
