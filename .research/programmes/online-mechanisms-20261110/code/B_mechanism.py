# -*- coding: utf-8 -*-
"""Question B, step 1: does the operating stress act on lifetime THROUGH
exposure, or through a stress-dependent damage rate?

This is a mechanism test, not a model fit.

Exposure argument. For a cell cycled at charge rate Cc, discharge rate Cd and
depth of discharge d, one cycle takes about d*(1/Cc + 1/Cd) hours, so

    cycles per day   = 24 / (d * (1/Cc + 1/Cd))
    equivalent full cycles (EFC) per day = cycles/day * d = 24 / (1/Cc + 1/Cd)

which is INDEPENDENT of d. So if lifetime were limited purely by throughput
(EFC), the calendar lifetime would not depend on DoD at all.

Therefore:
  H0 (exposure-only): log(EOL_days) depends on the C-rates but NOT on DoD.
  H1 (stress rate)  : DoD carries an additional damage-rate effect.

We test this on the ISU-ILCC cohort using the recovered three-factor table and
the interval-censored EOL in days. No cycling data is required: the exposure
rate is a design-level quantity from the condition table.
"""
import os, json
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")
PROBE = os.path.join(PROTO, "_probe")

eol = pd.read_csv(os.path.join(PROBE, "isu_eol.csv"))
cond = pd.read_csv(os.path.join(HERE, "..", "..", "..", "results", "isu_conditions.csv"))
cond.columns = ["group", "charge_C", "discharge_C", "mean_DoD_pct"]
cond["DoD"] = cond.mean_DoD_pct / 100.0

df = eol.merge(cond, left_on="group", right_on="group", how="inner")
print("cells with EOL + condition table: %d / %d" % (len(df), len(eol)))

# midpoint of the interval-censored EOL in days, and in RPT counts
df["eol_day"] = (df.day_L + df.day_U) / 2.0
df["eol_rpt"] = (df.rpt_L + df.rpt_U) / 2.0
df = df[np.isfinite(df.eol_day) & (df.eol_day > 0)]
print("usable: %d cells, %d conditions" % (len(df), df.group.nunique()))

# exposure rate from the design table (independent of DoD)
df["efc_per_day"] = 24.0 / (1.0 / df.charge_C + 1.0 / df.discharge_C)
df["cyc_per_day"] = df.efc_per_day / df.DoD

# ---- H0 test: does log EOL_days depend on DoD after controlling for C-rates? ----
X = np.column_stack([
    np.ones(len(df)),
    np.log(df.efc_per_day.values),      # exposure rate
    df.DoD.values,                      # stress beyond exposure
    df.charge_C.values, df.discharge_C.values,
])
y = np.log(df.eol_day.values)
beta, res, rank, sv = np.linalg.lstsq(X, y, rcond=None)
yhat = X @ beta
ss_res = ((y - yhat) ** 2).sum(); ss_tot = ((y - y.mean()) ** 2).sum()
r2 = 1 - ss_res / ss_tot
n, p = X.shape
se = np.sqrt(ss_res / (n - p) * np.diag(np.linalg.inv(X.T @ X)))
names = ["intercept", "log(EFC/day)", "DoD", "charge_C", "discharge_C"]
print("\n=== OLS: log(EOL_days) ~ ===")
for nm, b, s in zip(names, beta, se):
    t = b / s
    pv = 2 * (1 - stats.t.cdf(abs(t), n - p))
    print("  %-14s coef %+8.4f  se %.4f  t %+6.2f  p %.4g" % (nm, b, s, t, pv))
print("  R^2 = %.3f   n = %d" % (r2, n))

# ---- univariate: DoD alone ----
rho, pv = stats.spearmanr(df.DoD, df.eol_day)
print("\nSpearman(DoD, EOL_days) = %+.3f  p=%.3g  n=%d" % (rho, pv, len(df)))
rho2, pv2 = stats.spearmanr(df.efc_per_day, df.eol_day)
print("Spearman(EFC/day, EOL_days) = %+.3f  p=%.3g" % (rho2, pv2))

# ---- the exposure-normalised lifetime ----
df["eol_efc"] = df.eol_day * df.efc_per_day
g = df.groupby("group").agg(n=("cell", "size"), DoD=("DoD", "first"),
                            efc_day=("efc_per_day", "first"),
                            eol_day=("eol_day", "median"),
                            eol_efc=("eol_efc", "median")).reset_index()
print("\n=== per-condition medians (63 conditions) ===")
print(g.sort_values("DoD").head(8).to_string(index=False, float_format=lambda x: "%.1f" % x))
print("...")
print(g.sort_values("DoD").tail(8).to_string(index=False, float_format=lambda x: "%.1f" % x))

# if exposure-driven, eol_efc should be flat across DoD
rho3, pv3 = stats.spearmanr(g.DoD, g.eol_efc)
print("\nSpearman(DoD, EOL_in_EFC) = %+.3f  p=%.3g  (H0 predicts ~0)" % (rho3, pv3))
cv_efc = g.eol_efc.std() / g.eol_efc.mean()
cv_day = g.eol_day.std() / g.eol_day.mean()
print("CV of EOL_days across conditions: %.2f" % cv_day)
print("CV of EOL_in_EFC across conditions: %.2f" % cv_efc)

out = dict(n_cells=int(len(df)), n_conditions=int(df.group.nunique()),
           ols_r2=float(r2),
           coefs={nm: float(b) for nm, b in zip(names, beta)},
           p_values={nm: float(2 * (1 - stats.t.cdf(abs(b / s), n - p)))
                     for nm, b, s in zip(names, beta, se)},
           spearman_dod_eolday=float(rho), p_dod_eolday=float(pv),
           spearman_dod_efc=float(rho3), p_dod_efc=float(pv3),
           cv_eol_day=float(cv_day), cv_eol_efc=float(cv_efc))
json.dump(out, open(os.path.join(PROTO, "B_mechanism_test.json"), "w"), indent=1)
g.to_csv(os.path.join(PROTO, "B_condition_summary.csv"), index=False)
print("\nwrote B_mechanism_test.json / B_condition_summary.csv")
