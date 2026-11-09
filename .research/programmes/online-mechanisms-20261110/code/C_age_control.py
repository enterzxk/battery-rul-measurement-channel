# -*- coding: utf-8 -*-
"""Verify the reviewer's central objection: does a HEALTH-FREE age rule beat the
HGB landmark predictor?

The objection. In the landmark design the query time is t = x0 + f*(L - x0), so
the elapsed age t and the eventual crossing L are linked by construction. A
predictor that never looks at any health measurement,

    U_hat = t_last + (1/f - 1) * span

reconstructs the landmark geometry from the schedule alone. If that beats the
HGB, then the "25% of life -> 10-12% error" claim measures schedule
extrapolation, not degradation prediction.

This script computes, on the SAME fixed population and the SAME queries:
  age_only      : U_hat = t + (1/f - 1)*span
  age_only_simple: U_hat = t / f            (no span, pure proportional age)
  hgb           : the health-feature model used in C_landmark_fraction.py
and reports condition-macro |log error| for each.
"""
import os, json, zipfile, re
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")
RAW_ISU = r"E:\桌面\rul\data\external\isu_raw\RPT_json.zip"

FRACS = (0.25, 0.5, 0.75); MIN_OBS = 3
FEATS = ["t", "soh_last", "soh0", "slope", "span"]

# ---- UConn, repaired axis ----
u = pd.read_csv(os.path.join(PROTO, "uconn_tidy_fixed.csv"))
e = pd.read_csv(os.path.join(PROTO, "uconn_eol_fixed.csv"))
e = e[e.kind == "interval"].set_index("cell")
uc = {}
for c, g in u.groupby("cell"):
    if c not in e.index: continue
    g = g.sort_values("cum")
    uc[c] = dict(cond=int(g.cond.iloc[0]), x=g.cum.values.astype(float),
                 soh=g.soh.values.astype(float), L=float(e.loc[c, "L"]), U=float(e.loc[c, "U"]))

def evaluate(name, cells):
    keep = {c: s for c, s in cells.items()
            if (s["x"] <= s["x"][0] + FRACS[0]*(s["L"]-s["x"][0])).sum() >= MIN_OBS}
    rows = []
    for f in FRACS:
        recs = []
        for c, s in keep.items():
            x, soh = s["x"], s["soh"]
            t = x[0] + f*(s["L"]-x[0]); vis = x <= t
            if vis.sum() < MIN_OBS: continue
            xv, sv = x[vis], soh[vis]
            span = float(xv[-1]-xv[0]); tl = float(xv[-1])
            recs.append(dict(cell=c, cond=s["cond"], t=tl, span=span,
                             soh_last=float(sv[-1]), soh0=float(sv[0]),
                             slope=float((sv[-1]-sv[0])/max(span, 1e-12)),
                             y=float(np.log(s["U"])),
                             age_only=tl + (1.0/f - 1.0)*span,
                             age_prop=tl/f))
        Q = pd.DataFrame(recs)
        if len(Q) < 40: continue
        pred = np.full(len(Q), np.nan)
        for held in sorted(Q.cond.unique()):
            te = Q.cond == held; tr = ~te
            if tr.sum() < 30 or te.sum() == 0: continue
            m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
            m.fit(Q.loc[tr, FEATS].values, Q.loc[tr, "y"].values)
            pred[te.values] = m.predict(Q.loc[te, FEATS].values)
        ok = np.isfinite(pred)
        d = pd.DataFrame({
            "hgb": np.abs(pred[ok] - Q.y.values[ok]),
            "age_only": np.abs(np.log(Q.age_only.values[ok]) - Q.y.values[ok]),
            "age_prop": np.abs(np.log(Q.age_prop.values[ok]) - Q.y.values[ok]),
            "cond": Q.cond.values[ok]})
        cm = d.groupby("cond").mean()
        rows.append(dict(cohort=name, f=f, n_cells=int(Q[ok].cell.nunique()), n_cond=int(len(cm)),
                         hgb=float(cm.hgb.mean()), age_only=float(cm.age_only.mean()),
                         age_prop=float(cm.age_prop.mean())))
        print("  %-5s f=%.2f  HGB %.4f | age_only %.4f | age_prop %.4f   -> %s" % (
            name, f, rows[-1]["hgb"], rows[-1]["age_only"], rows[-1]["age_prop"],
            "AGE WINS" if rows[-1]["age_only"] < rows[-1]["hgb"] else "hgb wins"), flush=True)
    return rows

print("=== does a health-free age rule beat the model? ===")
out = evaluate("UConn", uc)

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
out += evaluate("ISU", ic)

T = pd.DataFrame(out)
T.to_csv(os.path.join(PROTO, "C_age_control.csv"), index=False)
json.dump(T.to_dict("records"), open(os.path.join(PROTO, "C_age_control.json"), "w"), indent=1)
print("\n=== verdict ===")
for coh in T.cohort.unique():
    s = T[T.cohort == coh]
    wins = (s.age_only < s.hgb).sum()
    print("  %-5s: age_only beats HGB at %d of %d fractions" % (coh, wins, len(s)))
print("\nwrote C_age_control.csv / .json")
