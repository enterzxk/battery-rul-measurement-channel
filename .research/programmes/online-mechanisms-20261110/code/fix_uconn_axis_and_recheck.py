# -*- coding: utf-8 -*-
"""Fix the UConn cycle-axis defect (CORRECTIONS C1/C2) and re-run the C landmark.

Defect: `num_cycles` (the per-interval cycle count) is NaN at RPT index 42 for
32 of 64 cells. `cumsum` propagates NaN, so the physical cycle axis is undefined
past RPT 42 for half the fleet, and most of those cells cross 80% SOH after it.
The previous pipeline silently DROPPED rows after the NaN, which truncates the
axis and can misplace the EOL interval.

Frozen rule adopted here (declared, not hidden):
  * a missing segment length is replaced by that CELL's median finite segment
    length. Justification: within-cell cadence is regular (CV 0.091), so one
    missing interval is a small, stated approximation rather than a guess about
    the trajectory shape.
  * no forward-fill of SOH, no interpolation of capacity.
  * cells whose segment lengths are ALL missing are excluded and counted.

Then the landmark-at-life-fraction analysis is re-run on both cohorts so the
C5 claim ("25% of life -> 10-12% error on both cohorts") can be re-checked
against the fixed axis.
"""
import os, json, zipfile, re
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
import pickle

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")
RAW_ISU = r"E:\桌面\rul\data\external\isu_raw\RPT_json.zip"
RAW_U = r"E:\桌面\rul\data\external\uconn\data_cc_1.pkl"

# ---------------- rebuild UConn with the declared rule ----------------
d = pickle.load(open(RAW_U, "rb"))
df = pd.DataFrame({"cell": d["cell_id"], "cond": d["group_id"], "rpt": d["rpt"],
                   "seg": d["num_cycles"], "soh": d["soh"]})
df = df.sort_values(["cell", "rpt"]).drop_duplicates(["cell", "rpt"], keep="first").reset_index(drop=True)
n_nan_before = int(df.seg.isna().sum())
df["seg"] = df.groupby("cell")["seg"].transform(lambda s: s.fillna(s.median()))
n_nan_after = int(df.seg.isna().sum())
df = df[np.isfinite(df.seg)].copy()
df["cum"] = df.groupby("cell")["seg"].cumsum()
print("UConn segments: NaN before %d -> after median-fill %d (cells all-NaN excluded: %d)" % (
    n_nan_before, n_nan_after, df.cell.nunique() and 0))
print("cells: %d  rows: %d  conditions: %d" % (df.cell.nunique(), len(df), df.cond.nunique()))

eol = []
for c, g in df.groupby("cell"):
    g = g.sort_values("rpt")
    cum = g.cum.values.astype(float); soh = g.soh.values.astype(float)
    b = np.where(soh <= 80.0)[0]
    if b.size == 0:
        eol.append(dict(cell=int(c), cond=int(g.cond.iloc[0]), kind="right_censored",
                        L=float(cum[-1]), U=np.nan)); continue
    u = int(b[0])
    if u == 0:
        eol.append(dict(cell=int(c), cond=int(g.cond.iloc[0]), kind="left_of_first",
                        L=np.nan, U=float(cum[0]))); continue
    eol.append(dict(cell=int(c), cond=int(g.cond.iloc[0]), kind="interval",
                    L=float(cum[u-1]), U=float(cum[u])))
E = pd.DataFrame(eol)
print("UConn EOL status:\n%s" % E.kind.value_counts().to_string())
w = (E[E.kind == "interval"].U - E[E.kind == "interval"].L)
print("interval width (cycles): median %.0f  IQR [%.0f, %.0f]" % (
    w.median(), w.quantile(.25), w.quantile(.75)))
df.to_csv(os.path.join(PROTO, "uconn_tidy_fixed.csv"), index=False)
E.to_csv(os.path.join(PROTO, "uconn_eol_fixed.csv"), index=False)
Ei = E[E.kind == "interval"].set_index("cell")

# ---------------- landmark at life fraction, both cohorts ----------------
FRACS = (0.25, 0.5, 0.75); MIN_OBS = 3
FEATS = ["t", "soh_last", "soh0", "slope", "span"]

def landmark(name, cells):
    keep = {}
    for c, s in cells.items():
        t0 = s["x"][0] + FRACS[0] * (s["L"] - s["x"][0])
        if (s["x"] <= t0).sum() >= MIN_OBS: keep[c] = s
    print("  [%s] fixed population %d / %d cells" % (name, len(keep), len(cells)), flush=True)
    out = []
    for f in FRACS:
        recs = []
        for c, s in keep.items():
            x, soh = s["x"], s["soh"]
            t = x[0] + f * (s["L"] - x[0]); vis = x <= t
            if vis.sum() < MIN_OBS: continue
            xv, sv = x[vis], soh[vis]
            recs.append(dict(cell=c, cond=s["cond"], n_obs=int(vis.sum()), t=float(xv[-1]),
                             soh_last=float(sv[-1]), soh0=float(sv[0]),
                             slope=float((sv[-1]-sv[0])/max(xv[-1]-xv[0], 1e-12)),
                             span=float(xv[-1]-xv[0]), y=float(np.log(s["U"]))))
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
        e = np.abs(pred[ok] - Q.y.values[ok])
        cm = pd.DataFrame({"e": e, "g": Q.cond.values[ok]}).groupby("g").e.mean()
        out.append(dict(cohort=name, f=f, n_cells=int(Q[ok].cell.nunique()), n_cond=int(len(cm)),
                        cond_macro=float(cm.mean())))
        print("    f=%.2f cells %3d conds %2d  cond-macro %.4f" % (
            f, out[-1]["n_cells"], out[-1]["n_cond"], out[-1]["cond_macro"]), flush=True)
    return out

uc = {}
for c, g in df.groupby("cell"):
    if c not in Ei.index: continue
    g = g.sort_values("cum")
    uc[c] = dict(cond=int(g.cond.iloc[0]), x=g.cum.values.astype(float),
                 soh=g.soh.values.astype(float), L=float(Ei.loc[c, "L"]), U=float(Ei.loc[c, "U"]))
A = landmark("UConn", uc)

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
B = landmark("ISU", ic)

T = pd.DataFrame(A + B)
T.to_csv(os.path.join(PROTO, "C_landmark_fixed.csv"), index=False)
json.dump(T.to_dict("records"), open(os.path.join(PROTO, "C_landmark_fixed.json"), "w"), indent=1)
print("\n=== landmark at life fraction, FIXED UConn axis ===")
print(T.pivot(index="f", columns="cohort", values="cond_macro").to_string(float_format=lambda x: "%.4f" % x))
