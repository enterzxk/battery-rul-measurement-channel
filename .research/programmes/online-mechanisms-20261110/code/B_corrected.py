# -*- coding: utf-8 -*-
"""Question B, CORRECTED (fixes C4-C8, C10, C13 from CORRECTIONS.md).

Changes vs the voided first version:
  * uses ALL 250 interval cells in 63 conditions (was 211 / 53; the "40 right-
    censored" classification was wrong)
  * both correlations are computed at the SAME unit (cell)
  * condition-CLUSTERED standard errors, not cell-level IID
  * fits BOTH the classical power law (linear in log DoD) and the linear-in-DoD
    form, and reports which wins
  * leave-one-condition-out predicts PER CELL and scores condition-macro
    (the previous version compared one cell's prediction to a condition median)
"""
import os, json
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")
RES = os.path.join(HERE, "..", "..", "..", "results")

life = pd.read_csv(os.path.join(PROTO, "isu_lifetime_interval.csv"))
cond = pd.read_csv(os.path.join(RES, "isu_conditions.csv"))
cond.columns = ["group", "charge_C", "discharge_C", "mean_DoD_pct"]
cond["DoD"] = cond.mean_DoD_pct / 100.0

df = life.merge(cond, on="group", how="inner")
df = df[np.isfinite(df.day_L) & np.isfinite(df.day_U)].copy()
df["eol_day"] = (df.day_L + df.day_U) / 2.0
df = df[df.eol_day > 0].copy()
df["efc_day"] = 24.0 / (1.0 / df.charge_C + 1.0 / df.discharge_C)
df["eol_efc"] = df.eol_day * df.efc_day
df["logE"] = np.log(df.eol_efc)
print("cells: %d | conditions: %d" % (len(df), df.group.nunique()))

# ---------- correlations at ONE unit (cell) ----------
r1 = stats.spearmanr(df.DoD, df.eol_day)
r2 = stats.spearmanr(df.DoD, df.eol_efc)
print("\n=== DoD vs lifetime, BOTH at cell level (n=%d) ===" % len(df))
print("  DoD vs EOL_days : rho %+.3f  p=%.3g" % (r1.statistic, r1.pvalue))
print("  DoD vs EOL_EFC  : rho %+.3f  p=%.3g" % (r2.statistic, r2.pvalue))
print("  => normalisation %s the DoD association" % ("STRENGTHENS" if abs(r2.statistic) > abs(r1.statistic) else "WEAKENS/LEAVES"))
print("  CV of EOL_days %.3f | CV of EOL_EFC %.3f" % (df.eol_day.std()/df.eol_day.mean(), df.eol_efc.std()/df.eol_efc.mean()))

# ---------- two functional forms, condition-clustered SE ----------
def cluster_ols(y, X, clusters):
    X = np.asarray(X, float); y = np.asarray(y, float)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    XtXi = np.linalg.inv(X.T @ X)
    meat = np.zeros((X.shape[1], X.shape[1]))
    for g in np.unique(clusters):
        m = clusters == g
        u = (X[m].T @ e[m]).reshape(-1, 1)
        meat += u @ u.T
    G = len(np.unique(clusters)); n, k = X.shape
    scale = G / (G - 1) * (n - 1) / (n - k)
    V = scale * XtXi @ meat @ XtXi
    se = np.sqrt(np.diag(V))
    t = b / se
    pv = 2 * (1 - stats.t.cdf(np.abs(t), G - 1))
    rss = (e ** 2).sum(); tss = ((y - y.mean()) ** 2).sum()
    return b, se, pv, 1 - rss / tss, G

one = np.ones(len(df)); cl = df.group.values
forms = {
    "linear_DoD": np.column_stack([one, df.DoD, np.log(df.charge_C), np.log(df.discharge_C)]),
    "power_logDoD": np.column_stack([one, np.log(df.DoD), np.log(df.charge_C), np.log(df.discharge_C)]),
}
print("\n=== functional form, condition-clustered SE (G=%d clusters) ===" % df.group.nunique())
out_forms = {}
for name, Xm in forms.items():
    b, se, pv, r2f, G = cluster_ols(df.logE.values, Xm, cl)
    labels = (["intercept", "DoD", "log Cc", "log Cd"] if name == "linear_DoD"
              else ["intercept", "log DoD", "log Cc", "log Cd"])
    print("\n  %s   R2=%.3f" % (name, r2f))
    for nm, bb, ss, pp in zip(labels, b, se, pv):
        print("    %-10s %+8.4f  se %.4f  p %.3g" % (nm, bb, ss, pp))
    out_forms[name] = dict(r2=float(r2f), coefs=dict(zip(labels, b.tolist())),
                           p=dict(zip(labels, pv.tolist())))
print("\n  winner by R^2: %s" % max(out_forms, key=lambda k: out_forms[k]["r2"]))

# ---------- LOCO, per-cell prediction, condition-macro scoring ----------
FEATS_S = ["DoD", "charge_C", "discharge_C"]
rows = []
for held in sorted(df.group.unique()):
    tr = df[df.group != held]; te = df[df.group == held]
    if len(tr) < 40 or len(te) == 0: continue
    m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
    m.fit(tr[FEATS_S].values, tr.logE.values)
    pred = m.predict(te[FEATS_S].values)
    rows.append(dict(group=held, n_cells=len(te),
                     hgb=float(np.mean(np.abs(pred - te.logE.values))),
                     pooled=float(np.mean(np.abs(np.median(tr.logE.values) - te.logE.values)))))
R = pd.DataFrame(rows)
print("\n=== LOCO, per-cell prediction, condition-macro |log error| (n=%d folds) ===" % len(R))
print("  stress HGB   : %.4f" % R.hgb.mean())
print("  pooled median: %.4f" % R.pooled.mean())
print("  improvement  : %.1f%%" % (100 * (1 - R.hgb.mean() / R.pooled.mean())))
w = stats.wilcoxon(R.hgb, R.pooled)
print("  paired Wilcoxon p = %.3g" % w.pvalue)

json.dump(dict(n_cells=int(len(df)), n_conditions=int(df.group.nunique()),
               rho_dod_days=float(r1.statistic), rho_dod_efc=float(r2.statistic),
               forms=out_forms, loco_hgb=float(R.hgb.mean()), loco_pooled=float(R.pooled.mean()),
               loco_wilcoxon_p=float(w.pvalue)),
          open(os.path.join(PROTO, "B_corrected.json"), "w"), indent=1)
R.to_csv(os.path.join(PROTO, "B_corrected_loco.csv"), index=False)
print("\nwrote B_corrected.json / B_corrected_loco.csv")
