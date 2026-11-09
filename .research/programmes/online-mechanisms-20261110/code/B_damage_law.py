# -*- coding: utf-8 -*-
"""Question B, step 2: the functional form of the DoD damage law.

Step 1 showed that normalising lifetime by equivalent-full-cycle exposure does
NOT absorb the DoD effect - it sharpens it (Spearman -0.636 -> -0.815). So
damage per unit throughput is DoD-dependent.

Here we ask what form that dependence takes, and whether it is separable:

    log(EOL_EFC) = a + b*DoD + c*log(Cc) + d*log(Cd)          (separable)
    log(EOL_EFC) = a + b*DoD + c*log(Cc) + d*log(Cd) + e*DoD*log(Cc) + ...  (interacting)

If the DoD coefficient is stable and the interaction terms are negligible, then
a single "damage per EFC" scalar exp(b*DoD) carries the whole stress effect, and
it can be transplanted to an unseen condition.
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

df = eol.merge(cond, on="group", how="inner")
df["eol_day"] = (df.day_L + df.day_U) / 2.0
df = df[np.isfinite(df.eol_day) & (df.eol_day > 0)].copy()
df["efc_day"] = 24.0 / (1.0 / df.charge_C + 1.0 / df.discharge_C)
df["eol_efc"] = df.eol_day * df.efc_day
df["logE"] = np.log(df.eol_efc)
print("n=%d cells, %d conditions" % (len(df), df.group.nunique()))

def ols(X, y, names):
    X = np.asarray(X, float); y = np.asarray(y, float)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    yh = X @ b
    rss = ((y - yh) ** 2).sum(); tss = ((y - y.mean()) ** 2).sum()
    n, p = X.shape
    se = np.sqrt(rss / (n - p) * np.diag(np.linalg.inv(X.T @ X)))
    t = b / se
    pv = 2 * (1 - stats.t.cdf(np.abs(t), n - p))
    return b, se, pv, 1 - rss / tss, n

one = np.ones(len(df))
# M1: DoD only
b1, s1, p1, r1, n = ols(np.column_stack([one, df.DoD]), df.logE, ["int", "DoD"])
print("\n=== M1  log(EOL_EFC) ~ DoD ===")
for nm, bb, ss, pp in zip(["intercept", "DoD"], b1, s1, p1):
    print("  %-10s %+8.4f  se %.4f  p %.3g" % (nm, bb, ss, pp))
print("  R^2 = %.3f" % r1)

# M2: separable in log C-rates
X2 = np.column_stack([one, df.DoD, np.log(df.charge_C), np.log(df.discharge_C)])
b2, s2, p2, r2, _ = ols(X2, df.logE, [])
print("\n=== M2  log(EOL_EFC) ~ DoD + log Cc + log Cd ===")
for nm, bb, ss, pp in zip(["intercept", "DoD", "log Cc", "log Cd"], b2, s2, p2):
    print("  %-10s %+8.4f  se %.4f  p %.3g" % (nm, bb, ss, pp))
print("  R^2 = %.3f" % r2)

# M3: with DoD x log-rate interactions
X3 = np.column_stack([one, df.DoD, np.log(df.charge_C), np.log(df.discharge_C),
                      df.DoD * np.log(df.charge_C), df.DoD * np.log(df.discharge_C)])
b3, s3, p3, r3, _ = ols(X3, df.logE, [])
print("\n=== M3  + DoD x log-rate interactions ===")
for nm, bb, ss, pp in zip(["intercept", "DoD", "log Cc", "log Cd", "DoD:logCc", "DoD:logCd"], b3, s3, p3):
    print("  %-12s %+8.4f  se %.4f  p %.3g" % (nm, bb, ss, pp))
print("  R^2 = %.3f   (vs M2 %.3f; F-test for the two interactions)" % (r3, r2))
# nested F test M2 vs M3
rss2 = ((df.logE - X2 @ b2) ** 2).sum(); rss3 = ((df.logE - X3 @ b3) ** 2).sum()
F = ((rss2 - rss3) / 2) / (rss3 / (len(df) - 6))
pvF = 1 - stats.f.cdf(F, 2, len(df) - 6)
print("  F(2,%d) = %.3f  p = %.4f" % (len(df) - 6, F, pvF))

# implied damage multiplier per unit DoD
print("\n=== implied damage per EFC relative to DoD=0.2 ===")
for d in (0.2, 0.4, 0.6, 0.8, 1.0):
    print("  DoD %.1f : x%.2f" % (d, np.exp(b2[1] * (d - 0.2))))

json.dump(dict(
    M1=dict(coefs=dict(zip(["intercept", "DoD"], b1.tolist())), r2=float(r1)),
    M2=dict(coefs=dict(zip(["intercept", "DoD", "logCc", "logCd"], b2.tolist())),
            p=dict(zip(["intercept", "DoD", "logCc", "logCd"], p2.tolist())), r2=float(r2)),
    M3=dict(coefs=dict(zip(["intercept", "DoD", "logCc", "logCd", "DoD:logCc", "DoD:logCd"], b3.tolist())),
            r2=float(r3), F=float(F), pF=float(pvF)),
    n_cells=int(len(df)), n_conditions=int(df.group.nunique())),
    open(os.path.join(PROTO, "B_damage_law.json"), "w"), indent=1)
print("\nwrote B_damage_law.json")
