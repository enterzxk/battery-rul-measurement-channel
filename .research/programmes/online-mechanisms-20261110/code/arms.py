# -*- coding: utf-8 -*-
"""Arms for question A, evaluated leave-one-condition-out.

The scientific contrast:
  RPT-STEP arm   : degradation advances one unit per *observed RPT*. Time-to-EOL
                   is predicted in RPT units and converted to cycles with the
                   cell's own observed mean cycles-per-RPT.
  EXPOSURE arm   : degradation advances per *cumulative cycle*. Time-to-EOL is
                   predicted directly in cycles; no conversion.

When the inspection cadence is constant these two are algebraically identical.
They diverge only when the RPT-index-to-cycles relation is non-linear, which is
exactly what the measured cadence irregularity (CV 0.23, 16x range) allows.

Arms implemented:
  rpt_naive      : per-RPT drift, linear extrapolation, cadence conversion
  exposure_naive : per-cycle drift, linear extrapolation
  exposure_kf    : per-cycle drift with a 2-state Kalman filter (level+rate),
                   measurement update only when an observation exists
  hgb_exposure   : gradient boosting on exposure/history features, target = EOL cycles
  last_obs       : predict EOL = current cycle (no extrapolation) - floor baseline

Every arm is given the same visible history. Scoring is against the interval
[L, U] of the true crossing (0 inside, distance to nearest endpoint outside).
"""
import os, json, argparse
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")
THRESH = 80.0
DEFICIT = 100.0 - THRESH     # 20 SOH points from 100% to EOL

def load_tidy():
    df = pd.read_csv(os.path.join(PROTO, "uconn_online_tidy.csv"))
    df = df[np.isfinite(df.cum_cycles)].copy()
    return df.sort_values(["cell", "cum_cycles"]).reset_index(drop=True)

def visible_hist(df, cell, t):
    g = df[df.cell == cell]
    g = g[g.cum_cycles <= t]
    return g

def slope(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    if x.size < 2 or np.ptp(x) <= 0:
        return np.nan
    return float(np.polyfit(x, y, 1)[0])

# ---------------------------------------------------------------- arms
def arm_last_obs(h):
    return float(h.cum_cycles.values[-1])

def arm_rpt_naive(h):
    """Drift per observed RPT; remaining RPTs; convert with observed cadence."""
    if len(h) < 3:
        return float(h.cum_cycles.values[-1])
    c = h.cum_cycles.values.astype(float)
    d = (100.0 - h.soh.values).astype(float)          # deficit
    k = np.arange(len(h), dtype=float)                 # RPT index (observed)
    g_rpt = slope(k, d)
    cadence = (c[-1] - c[0]) / max(len(h) - 1, 1)      # cycles per observed RPT
    if not np.isfinite(g_rpt) or g_rpt <= 1e-9:
        return float(c[-1])
    rem_rpt = max(DEFICIT - d[-1], 0.0) / g_rpt
    return float(c[-1] + rem_rpt * cadence)

def arm_exposure_naive(h):
    """Drift per cycle; remaining cycles directly."""
    if len(h) < 3:
        return float(h.cum_cycles.values[-1])
    c = h.cum_cycles.values.astype(float)
    d = (100.0 - h.soh.values).astype(float)
    g = slope(c, d)
    if not np.isfinite(g) or g <= 1e-12:
        return float(c[-1])
    return float(c[-1] + max(DEFICIT - d[-1], 0.0) / g)

def arm_exposure_kf(h, q_level=1e-4, q_rate=1e-8, r_obs=1e-2):
    """2-state Kalman filter over (deficit, rate-per-cycle).
    State propagates with delta cycles; measurement update ONLY at observations."""
    c = h.cum_cycles.values.astype(float)
    d = (100.0 - h.soh.values).astype(float)
    if len(c) < 3:
        return float(c[-1])
    x = np.array([d[0], max(slope(c, d) if np.isfinite(slope(c, d)) else 1e-4, 1e-8)])
    P = np.diag([1.0, 1e-6])
    F = np.eye(2); F[0, 1] = 0.0          # rate applied below with dt
    Q = np.diag([q_level, q_rate])
    H = np.array([[1.0, 0.0]])
    for i in range(1, len(c)):
        dt = c[i] - c[i - 1]
        if dt <= 0:
            continue
        x = np.array([x[0] + x[1] * dt, x[1]])       # predict
        Fd = np.array([[1.0, dt], [0.0, 1.0]])
        P = Fd @ P @ Fd.T + Q * max(dt, 1.0)
        y = d[i] - (H @ x)[0]                        # update on arrival only
        S = (H @ P @ H.T)[0, 0] + r_obs
        K = (P @ H.T).flatten() / S
        x = x + K * y
        P = (np.eye(2) - np.outer(K, H)) @ P
    rate = max(x[1], 1e-12)
    return float(c[-1] + max(DEFICIT - x[0], 0.0) / rate)

def arm_exposure_kf_noupdate(h, **kw):
    """Same filter but the measurement update is skipped after the first
    observation: pure propagation from the initial rate estimate."""
    c = h.cum_cycles.values.astype(float)
    d = (100.0 - h.soh.values).astype(float)
    if len(c) < 3:
        return float(c[-1])
    g0 = slope(c, d)
    if not np.isfinite(g0) or g0 <= 1e-12:
        return float(c[-1])
    d_now = d[0] + g0 * (c[-1] - c[0])
    return float(c[-1] + max(DEFICIT - d_now, 0.0) / g0)

FEATS = ["t", "n_obs", "soh_last", "deficit_last", "slope_cyc", "slope_rpt",
         "cadence", "span_cycles", "dcir20c_last", "dcir20d_last"]

def featurize(h, t):
    c = h.cum_cycles.values.astype(float)
    s = h.soh.values.astype(float)
    d = 100.0 - s
    n = len(h)
    cad = (c[-1] - c[0]) / max(n - 1, 1) if n > 1 else np.nan
    return dict(t=t, n_obs=n, soh_last=s[-1], deficit_last=d[-1],
                slope_cyc=slope(c, d), slope_rpt=slope(np.arange(n), d),
                cadence=cad, span_cycles=c[-1] - c[0],
                dcir20c_last=h.dcir_chg_20.values[-1],
                dcir20d_last=h.dcir_dchg_20.values[-1])

def build_feature_table(df, queries):
    rows = []
    for _, q in queries.iterrows():
        h = visible_hist(df, q.cell, q.t)
        if len(h) < 2:
            continue
        f = featurize(h, q.t)
        f.update(dict(cell=q.cell, cond=q.cond, frac=q.frac, L=q.L, U=q.U))
        rows.append(f)
    return pd.DataFrame(rows)

def interval_err(pred, L, U):
    pred = np.asarray(pred, float)
    e = np.where(pred < L, L - pred, np.where(pred > U, pred - U, 0.0))
    return e

def summarize(name, pred, L, U, cond):
    e = interval_err(pred, L, U)
    d = pd.DataFrame({"e": e, "cond": cond})
    macro = d.groupby("cond").e.mean().mean()
    return dict(arm=name, n=len(e), mae=float(e.mean()), cond_macro=float(macro),
                median=float(np.median(e)), hit=float((e == 0).mean()),
                worst_cond=float(d.groupby("cond").e.mean().max()))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sub", default="S0")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    df = load_tidy()
    q = pd.read_csv(os.path.join(PROTO, "queries_%s.csv" % a.sub))
    print("subsample %s: %d queries, %d cells, %d conditions" % (a.sub, len(q), q.cell.nunique(), q.cond.nunique()))

    # ---- point arms (no fitting, so no leakage risk) ----
    res = []
    preds = {}
    for name, fn in [("last_obs", arm_last_obs), ("rpt_naive", arm_rpt_naive),
                     ("exposure_naive", arm_exposure_naive),
                     ("exposure_kf", arm_exposure_kf),
                     ("exposure_kf_noupdate", arm_exposure_kf_noupdate)]:
        p = []
        for _, row in q.iterrows():
            h = visible_hist(df, row.cell, row.t)
            p.append(fn(h) if len(h) >= 1 else row.t)
        preds[name] = np.array(p)
        res.append(summarize(name, preds[name], q.L.values, q.U.values, q.cond.values))

    # ---- HGB, leave-one-condition-out ----
    F = build_feature_table(df, q)
    pred_hgb = np.full(len(F), np.nan)
    for cond in sorted(F.cond.unique()):
        te = F.cond == cond
        tr = ~te
        if tr.sum() < 20 or te.sum() == 0:
            continue
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
        m.fit(F.loc[tr, FEATS].values, F.loc[tr, "U"].values)   # target = U (upper endpoint)
        pred_hgb[te.values] = m.predict(F.loc[te, FEATS].values)
    ok = np.isfinite(pred_hgb)
    res.append(summarize("hgb_exposure", pred_hgb[ok], F.L.values[ok], F.U.values[ok], F.cond.values[ok]))

    out = pd.DataFrame(res).sort_values("cond_macro")
    print(out.to_string(index=False, float_format=lambda x: "%.1f" % x))
    if a.out:
        out.to_csv(a.out, index=False)
        print("\nwrote", a.out)
