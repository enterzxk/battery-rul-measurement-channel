# -*- coding: utf-8 -*-
"""E7 · Per-cell acquisition records for the primary setting.

The brief requires, per condition: the inspection records, the predictions and the
decision losses. E3b saved per-condition losses but not WHICH times each policy
bought, so this script re-runs the primary setting (T=63, N=2, c_f/c_w=5) and
dumps one row per (outer fold, cell, policy) with:

  chosen inspection indices and their calendar days
  the predicted replacement time R
  the true midpoint EOL M and the bracket [L, U]
  the decision loss

Same frozen machinery as E3b (imported, not re-implemented), so the numbers are
reproducible from the same code path.

Run remotely.
"""
import os
import json

import numpy as np
import pandas as pd

import D_common as C
from E3b_replay import (FEATS, MIN_AVAIL, build_rows, cohort, features_from_obs,
                        fixed_early, fixed_even, fixed_late, fixed_random, fit_q,
                        loss_of, make_cand_chooser, make_voi_chooser, sequential)
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR

OUT = C.PROTO
T, N, RATIO = 63, 2, 5.0
TAU = 1.0 / (1.0 + RATIO)


def main():
    import pickle
    with open(os.path.join(OUT, "isu_cells_cache.pkl"), "rb") as f:
        pay = pickle.load(f)
    cells, stress = pay["cells"], pay["stress"]
    co = cohort(cells, T, stress)
    conds = sorted({d["s"]["cond"] for d in co.values()})
    print("T=%d N=%d ratio=%.0f | %d cells / %d conditions" % (T, N, RATIO, len(co), len(conds)))

    rows = []
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

        # inner 5-fold OOF -> expected-loss model (identical to E3b)
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
        for n in te:
            d = co[n]
            s, srow = d["s"], stress.loc[d["s"]["cond"]]
            picks = {
                "FixedEven": sorted(set([0] + fixed_even(d["avail"], N))),
                "FixedLate": sorted(set([0] + fixed_late(d["avail"], N))),
                "FixedEarly": sorted(set([0] + fixed_early(d["avail"], N))),
                "Random": sorted(set([0] + fixed_random(d["avail"], N, 0))),
                "VoI": sequential(d["avail"], N, s, T, srow, voi),
                "Candidate": sequential(d["avail"], N, s, T, srow, cand),
            }
            for p, idx in picks.items():
                f = features_from_obs(s["x"][idx], s["soh"][idx], T, srow)
                R = max(T, float(np.exp(qm.predict(np.array([[f[k] for k in feats]]))[0])))
                rows.append(dict(
                    heldout_cond=g, cell=n, cond=s["cond"], policy=p,
                    n_insp=len(idx) - 1,
                    insp_idx="|".join(str(i) for i in idx),
                    insp_days="|".join("%.2f" % s["x"][i] for i in idx),
                    pred_R=float(R), M=float(d["M"]),
                    L=float(s["L"]), U=float(s["U"]),
                    loss=float(loss_of(R, d["M"], RATIO))))
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, "E7_inspection_records.csv"), index=False)
    print("rows: %d  (cells %d, conditions %d, policies %d)" % (
        len(D), D.cell.nunique(), D.cond.nunique(), D.policy.nunique()))
    print("\nmean loss by policy:")
    print(D.groupby("policy").loss.agg(["mean", "median", "size"]).round(3).to_string())
    print("\nexample rows:")
    print(D[D.heldout_cond == D.heldout_cond.iloc[0]]
          [["cell", "policy", "insp_days", "pred_R", "M", "loss"]].head(12).to_string(index=False))
    json.dump(dict(T=T, N=N, ratio=RATIO, n_rows=int(len(D)),
                   n_cells=int(D.cell.nunique()), n_cond=int(D.cond.nunique()),
                   mean_loss=D.groupby("policy").loss.mean().to_dict()),
              open(os.path.join(OUT, "E7_records.json"), "w"), indent=1, default=float)
    print("\nwrote E7_inspection_records.csv / E7_records.json")


if __name__ == "__main__":
    main()
