# -*- coding: utf-8 -*-
"""Evaluation harness for question A: predicting EOL on the PHYSICAL cycle axis
from observations available up to a censoring time t.

Design decisions frozen here (see protocol/PROTOCOL_LOCK.yaml once locked):

* Physical axis: cum_cycles (cumsum of segment lengths within a cell).
* Event: first observation with soh <= 80. True EOL is only known to lie in
  (L, U] = (cum at last above-threshold obs, cum at first below-threshold obs).
* Scoring against an interval: error = 0 if the prediction lies in [L, U],
  otherwise the distance to the nearest endpoint. This is the natural loss for
  interval-censored events and it is applied identically to every arm.
* Prediction times: at a fixed set of FRACTIONS of each cell's own observed
  life, so that every arm is asked at the same points.
* Leave-one-condition-out: a held-out condition's cells never enter fitting,
  preprocessing, or hyper-parameter choice.
* Inspection sub-sampling: S0 = all RPTs, S1 = every 2nd, S2 = every 4th,
  applied to the OBSERVATION SET only. The underlying cell trajectory is
  unchanged; we never zero-fill a missing inspection.
"""
import os, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")

def load():
    df = pd.read_csv(os.path.join(PROTO, "uconn_online_tidy.csv"))
    eol = pd.read_csv(os.path.join(PROTO, "uconn_eol_intervals.csv"))
    # keep only cells whose cumulative axis is finite up to their EOL crossing
    df = df[np.isfinite(df.cum_cycles)].copy()
    eol = eol[eol.kind == "interval"].copy()
    df = df[df.cell.isin(eol.cell)]
    return df, eol.set_index("cell")

def subsample(g, every):
    """S0 -> every=1, S1 -> 2, S2 -> 4. Always keep the first observation.
    The cell's real trajectory is untouched; we only restrict which
    inspections the model is allowed to see."""
    if every <= 1:
        return g
    idx = list(range(0, len(g), every))
    if idx[-1] != len(g) - 1:
        idx.append(len(g) - 1)   # the final observation is the one that may reveal the crossing
    return g.iloc[idx]

def make_queries(df, eol, every=1, fracs=(0.25, 0.5, 0.75)):
    """For each cell, at each life fraction, emit (visible history, L, U)."""
    out = []
    for c, g in df.groupby("cell"):
        if c not in eol.index:
            continue
        g = g.sort_values("cum_cycles").reset_index(drop=True)
        g = subsample(g, every)
        L, U = float(eol.loc[c, "L"]), float(eol.loc[c, "U"])
        if not np.isfinite(L) or not np.isfinite(U) or U <= L:
            continue
        cum = g.cum_cycles.values
        # the crossing observation is the first with soh <= 80; a query may not
        # see beyond it, so cap the visible window at that index
        below = np.where(g.soh.values <= 80.0)[0]
        stop = below[0] if below.size else len(g) - 1
        for f in fracs:
            t = cum[0] + f * (L - cum[0])
            vis = np.where(cum[:stop + 1] <= t)[0]
            if vis.size < 2:
                continue
            hist = g.iloc[vis]
            out.append(dict(cell=int(c), cond=int(g.cond.iloc[0]), frac=f,
                            t=float(hist.cum_cycles.values[-1]),
                            n_obs=int(len(hist)), L=L, U=U))
    return pd.DataFrame(out)

def interval_error(pred, L, U):
    pred, L, U = np.asarray(pred, float), np.asarray(L, float), np.asarray(U, float)
    e = np.where(pred < L, L - pred, np.where(pred > U, pred - U, 0.0))
    return e

def score(preds, q):
    e = interval_error(preds, q.L.values, q.U.values)
    return dict(n=len(e), mae=float(e.mean()), median=float(np.median(e)),
                hit_rate=float((e == 0).mean()))

if __name__ == "__main__":
    df, eol = load()
    print("cells with a finite cycle axis and an interval EOL: %d" % eol.shape[0])
    for every in (1, 2, 4):
        q = make_queries(df, eol, every=every)
        print("  subsample every=%d -> queries %5d | cells %2d | conds %2d | mean n_obs %.1f" % (
            every, len(q), q.cell.nunique(), q.cond.nunique(), q.n_obs.mean()))
    q = make_queries(df, eol, every=1)
    q.to_csv(os.path.join(PROTO, "queries_S0.csv"), index=False)
    for every, name in ((2, "S1"), (4, "S2")):
        make_queries(df, eol, every=every).to_csv(os.path.join(PROTO, "queries_%s.csv" % name), index=False)
    print("\nwrote queries_S0/S1/S2.csv")
    print(q.head(3).to_string(index=False))
