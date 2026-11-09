# -*- coding: utf-8 -*-
"""Uncertainty on the ISU health-vs-age+stress gain.

The ablation gave a point estimate: adding the observed health trajectory to
age+stress reduces condition-macro |log error| by 19.4% on ISU. A point estimate
is not a claim. This script saves the per-condition errors and attaches a paired
cluster bootstrap over CONDITIONS (the independent unit), plus a paired Wilcoxon.

Also runs a small sensitivity check on the query ages, since they were chosen by
hand.
"""
import os, json, zipfile, re
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")
RES = os.path.join(HERE, "..", "..", "..", "results")
RAW_ISU = r"E:\桌面\rul\data\external\isu_raw\RPT_json.zip"
MIN_OBS = 3

cond = pd.read_csv(os.path.join(RES, "isu_conditions.csv"))
cond.columns = ["group", "charge_C", "discharge_C", "mean_DoD_pct"]
cond["DoD"] = cond.mean_DoD_pct / 100.0
S = cond.set_index("group")

z = zipfile.ZipFile(RAW_ISU); ic = {}
for n in sorted(x for x in z.namelist() if x.lower().endswith(".json")):
    cell = n.split("/")[-1].replace(".json", "")
    m = re.match(r"G(\d+)C(\d+)", cell)
    if not m: continue
    g = int(m.group(1))
    try: dd = json.loads(json.loads(z.read(n).decode("utf-8")))
    except Exception: continue
    cap = dd.get("capacity_discharge_C_5") or dd.get("capacity_discharge_C_2")
    ts = (dd.get("start_stop_time") or {}).get("start") or []
    if not isinstance(cap, list) or len(cap) < 4: continue
    v = []
    for x in cap:
        try: v.append(float(x))
        except Exception: v.append(np.nan)
    v = np.array(v, float); L = min(len(v), len(ts)) if ts else 0
    if L < 4: continue
    t = [pd.to_datetime(x, errors="coerce") for x in ts[:L]]
    if not all(pd.notna(x) for x in t): continue
    ref = np.nanmax(v[:L])
    if not np.isfinite(ref) or ref <= 0: continue
    soh = v[:L]/ref; day = np.array([(x-t[0]).total_seconds()/86400.0 for x in t])
    b = np.where(soh <= 0.80)[0]
    if b.size == 0: continue
    k = int(b[0])
    if k == 0: continue
    ic[cell] = dict(cond=g, x=day, soh=soh, L=day[k-1], U=day[k])
print("ISU cells: %d" % len(ic))

AS = ["logt", "DoD", "cc", "cd"]
HL = AS + ["soh_last", "soh0", "slope", "span", "n_obs"]

def build(ages):
    recs = []
    for c, s in ic.items():
        if s["cond"] not in S.index: continue
        for t in ages:
            if t <= 0 or t >= s["L"]: continue
            vis = s["x"] <= t
            if vis.sum() < MIN_OBS: continue
            xv, sv = s["x"][vis], s["soh"][vis]
            span = float(xv[-1]-xv[0])
            recs.append(dict(cell=c, cond=s["cond"], logt=float(np.log(t)),
                             n_obs=int(vis.sum()), soh_last=float(sv[-1]), soh0=float(sv[0]),
                             slope=float((sv[-1]-sv[0])/max(span, 1e-12)), span=span,
                             DoD=float(S.loc[s["cond"], "DoD"]),
                             cc=float(S.loc[s["cond"], "charge_C"]),
                             cd=float(S.loc[s["cond"], "discharge_C"]),
                             y=float(np.log(s["U"]))))
    return pd.DataFrame(recs)

def fit(Q, feats):
    p = np.full(len(Q), np.nan)
    for held in sorted(Q.cond.unique()):
        te = Q.cond == held; tr = ~te
        if tr.sum() < 40 or te.sum() == 0: continue
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
        m.fit(Q.loc[tr, feats].values, Q.loc[tr, "y"].values)
        p[te.values] = m.predict(Q.loc[te, feats].values)
    return p

def analyse(ages, tag):
    Q = build(ages)
    pa, ph = fit(Q, AS), fit(Q, HL)
    ok = np.isfinite(pa) & np.isfinite(ph)
    d = pd.DataFrame({"a": np.abs(pa[ok]-Q.y.values[ok]),
                      "h": np.abs(ph[ok]-Q.y.values[ok]),
                      "cond": Q.cond.values[ok]})
    cm = d.groupby("cond").mean()
    n = len(cm)
    gain = 100*(cm.h.mean()/cm.a.mean() - 1)
    # paired cluster bootstrap over conditions
    rng = np.random.default_rng(0)
    gs = []
    for _ in range(2000):
        idx = rng.integers(0, n, n)
        s = cm.iloc[idx]
        gs.append(100*(s.h.mean()/s.a.mean() - 1))
    lo, hi = np.percentile(gs, [2.5, 97.5])
    w = stats.wilcoxon(cm.h.values, cm.a.values)
    print("  %-22s conds %2d q %4d | age_stress %.4f health %.4f | gain %+.1f%% [%.1f, %.1f] | Wilcoxon p=%.3g" % (
        tag, n, int(ok.sum()), cm.a.mean(), cm.h.mean(), gain, lo, hi, w.pvalue), flush=True)
    return dict(tag=tag, n_cond=n, n_queries=int(ok.sum()),
                age_stress=float(cm.a.mean()), health=float(cm.h.mean()),
                gain_pct=float(gain), ci_lo=float(lo), ci_hi=float(hi),
                wilcoxon_p=float(w.pvalue)), cm

print("\n=== ISU: health vs age+stress, paired cluster bootstrap over conditions ===")
main, cm = analyse((21, 35, 49, 63), "primary ages")
sens = []
for ages, tag in [((14, 28, 42, 56), "shifted earlier"), ((28, 42, 56, 70), "shifted later"),
                  ((21, 42), "two ages only"), ((21, 28, 35, 42, 49, 56, 63), "seven ages")]:
    r, _ = analyse(ages, tag); sens.append(r)

out = dict(primary=main, sensitivity=sens)
json.dump(out, open(os.path.join(PROTO, "C_validity_ci.json"), "w"), indent=1)
cm.to_csv(os.path.join(PROTO, "C_validity_ci_percond.csv"))
print("\nwrote C_validity_ci.json / C_validity_ci_percond.csv")
print("\nverdict: gain %.1f%% CI [%.1f, %.1f] -> %s" % (
    main["gain_pct"], main["ci_lo"], main["ci_hi"],
    "EXCLUDES ZERO" if main["ci_hi"] < 0 else "does NOT exclude zero"))
