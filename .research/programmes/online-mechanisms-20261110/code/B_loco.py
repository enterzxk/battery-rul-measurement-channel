# -*- coding: utf-8 -*-
"""Question B, step 3: does the stress damage law PREDICT a held-out condition?

Leave-one-condition-out over the ISU-ILCC cohort. For each held-out condition
we predict the lifetime of its cells from (a) the condition's stress factors and
(b) the cell's own early observations, and compare against strong baselines.

Arms
  global      : predict the training-set median lifetime (no stress information)
  stress_ols  : the damage law  log(EOL_EFC) = a + b*DoD + c*log Cc + d*log Cd
                fitted on the training conditions only
  stress_hgb  : gradient boosting on [DoD, Cc, Cd]
  stress_obs  : damage law + a cell-level update from its early observed fade
  hgb_all     : gradient boosting on [DoD, Cc, Cd] + early trajectory features

The cell-level update in `stress_obs` is the hierarchical part: the stress law
sets the prior rate for a condition, and the cell's own early fade multiplies it.
This is what a stress-conditioned dynamics model should buy over plain
regression - if it buys anything.

Metric: absolute log-error of predicted EOL (in EFC), and relative error.
Reported condition-macro (each held-out condition weighted equally).
"""
import os, json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")
PROBE = os.path.join(PROTO, "_probe")
RES = os.path.join(HERE, "..", "..", "..", "results")

eol = pd.read_csv(os.path.join(PROBE, "isu_eol.csv"))
cond = pd.read_csv(os.path.join(RES, "isu_conditions.csv"))
cond.columns = ["group", "charge_C", "discharge_C", "mean_DoD_pct"]
cond["DoD"] = cond.mean_DoD_pct / 100.0

df = eol.merge(cond, on="group", how="inner")
df["eol_day"] = (df.day_L + df.day_U) / 2.0
df = df[np.isfinite(df.eol_day) & (df.eol_day > 0)].copy()
df["efc_day"] = 24.0 / (1.0 / df.charge_C + 1.0 / df.discharge_C)
df["eol_efc"] = df.eol_day * df.efc_day
df["logE"] = np.log(df.eol_efc)

# ---- early-trajectory features from the processed table (RPT-index axis) ----
z = np.load(os.path.join(RES, "isu_table.npz"), allow_pickle=True)
X = z["X"]; cells = z["cells"]
feat = X[:, 2:6]; rpt = X[:, 1]; soh = X[:, 6]
traj = []
for c in np.unique(cells):
    m = cells == c
    o = np.argsort(rpt[m]); s = soh[m][o]; f = feat[m][o]
    if len(s) < 4: continue
    k = min(3, len(s) - 1)                       # first 3 retained observations
    slope = (s[k] - s[0]) / max(k, 1)
    traj.append(dict(cell=c, soh0=float(s[0]), soh_k=float(s[k]), early_slope=float(slope),
                     early_mean_cap=float(np.nanmean(f[:k + 1])),
                     early_std_cap=float(np.nanstd(f[:k + 1]))))
T = pd.DataFrame(traj)
df = df.merge(T, on="cell", how="left")
print("cells: %d | conditions: %d | with trajectory features: %d" % (
    len(df), df.group.nunique(), df.early_slope.notna().sum()))

FEATS_STRESS = ["DoD", "charge_C", "discharge_C"]
FEATS_ALL = FEATS_STRESS + ["soh0", "soh_k", "early_slope", "early_mean_cap", "early_std_cap"]

def fit_ols(Xtr, ytr):
    Xtr = np.column_stack([np.ones(len(Xtr)), Xtr])
    b, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    return b

def pred_ols(b, Xte):
    return np.column_stack([np.ones(len(Xte)), Xte]) @ b

def design(g):
    return np.column_stack([g.DoD.values, np.log(g.charge_C.values), np.log(g.discharge_C.values)])

rows = []
conds = sorted(df.group.unique())
for held in conds:
    tr = df[df.group != held]
    te = df[df.group == held]
    if len(tr) < 30 or len(te) == 0:
        continue
    out = {"group": held}
    out["global"] = float(np.median(tr.logE.values))
    b = fit_ols(design(tr), tr.logE.values)
    out["stress_ols"] = float(pred_ols(b, design(te))[0]) if len(te) else np.nan
    # hgb on stress
    m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
    m.fit(tr[FEATS_STRESS].values, tr.logE.values)
    out["stress_hgb"] = float(m.predict(te[FEATS_STRESS].values)[0])
    # hgb on stress + trajectory
    tr2 = tr.dropna(subset=["early_slope"]); te2 = te.dropna(subset=["early_slope"])
    if len(tr2) > 30 and len(te2):
        m2 = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
        m2.fit(tr2[FEATS_ALL].values, tr2.logE.values)
        out["hgb_all"] = float(m2.predict(te2[FEATS_ALL].values)[0])
    else:
        out["hgb_all"] = np.nan
    # stress law + cell-level update from early slope
    # prior rate from the stress law; cell multiplier from its early fade relative to
    # the training-set median early fade at the same number of observations
    med_slope = tr.early_slope.median()
    if np.isfinite(med_slope) and med_slope < -1e-9 and len(te2):
        ratio = (te2.early_slope / med_slope).clip(0.25, 4.0)
        out["stress_obs"] = float(pred_ols(b, design(te2))[0] - np.log(ratio.median()))
    else:
        out["stress_obs"] = np.nan
    out["y"] = float(te.logE.median())
    rows.append(out)

R = pd.DataFrame(rows)
print("held-out conditions evaluated: %d" % len(R))
print()
res = []
for arm in ["global", "stress_ols", "stress_hgb", "hgb_all", "stress_obs"]:
    e = (R[arm] - R.y).abs()
    ok = np.isfinite(e)
    res.append(dict(arm=arm, n=int(ok.sum()),
                    mae_log=float(e[ok].mean()),
                    med_log=float(e[ok].median()),
                    rel_err=float((np.exp(e[ok]) - 1).mean())))
res = pd.DataFrame(res).sort_values("mae_log")
print(res.to_string(index=False, float_format=lambda x: "%.4f" % x))
R.to_csv(os.path.join(PROTO, "B_loco_per_condition.csv"), index=False)
res.to_csv(os.path.join(PROTO, "B_loco_summary.csv"), index=False)
print("\nwrote B_loco_per_condition.csv / B_loco_summary.csv")
