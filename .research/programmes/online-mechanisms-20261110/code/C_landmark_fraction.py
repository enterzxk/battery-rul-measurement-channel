# -*- coding: utf-8 -*-
"""Question C, part 4: landmark at a fixed LIFE FRACTION, both cohorts.

Parts 1-3 failed to be comparable because they fixed the number of inspections
N, and the same N is a very different point in life for the two cohorts
(a UConn reference test covers ~2% of a lifetime, an ISU test ~6%).

The dimensionless quantity is the observed LIFE FRACTION f. Here the landmark is
f, and every inspection before f*L is used. f is comparable across cohorts.

Design
  f in {0.25, 0.5, 0.75}
  fixed population: a cell is eligible only if it contributes >= MIN_OBS
  inspections by the EARLIEST landmark, so the same cells are scored at every f.
  leave-one-condition-out; condition-macro |log error| of the predicted EOL.

If the error falls with f on both cohorts, the two agree and the earlier
disagreement was an artefact of the N design. If it still disagrees, the
cohorts genuinely behave differently.
"""
import os, json, zipfile, re
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")
RAW_ISU = r"E:\桌面\rul\data\external\isu_raw\RPT_json.zip"

FRACS = (0.25, 0.5, 0.75)
MIN_OBS = 3
FEATS = ["t", "soh_last", "soh0", "slope", "span"]

def landmark_run(name, cells):
    # fixed population: enough observations by the earliest landmark
    keep = {}
    for c, s in cells.items():
        x, soh = s["x"], s["soh"]
        t0 = x[0] + FRACS[0] * (s["L"] - x[0])
        if (x <= t0).sum() < MIN_OBS: continue
        keep[c] = s
    print("  [%s] fixed population: %d of %d cells" % (name, len(keep), len(cells)), flush=True)
    rows = []
    for f in FRACS:
        recs = []
        for c, s in keep.items():
            x, soh = s["x"], s["soh"]
            t = x[0] + f * (s["L"] - x[0])
            vis = x <= t
            if vis.sum() < MIN_OBS: continue
            xv, sv = x[vis], soh[vis]
            recs.append(dict(cell=c, cond=s["cond"], f=f, n_obs=int(vis.sum()), t=float(xv[-1]),
                             soh_last=float(sv[-1]), soh0=float(sv[0]),
                             slope=float((sv[-1]-sv[0])/max(xv[-1]-xv[0], 1e-12)),
                             span=float(xv[-1]-xv[0]), y=float(np.log(s["U"]))))
        Q = pd.DataFrame(recs)
        if len(Q) < 40:
            print("    f=%.2f only %d rows, skip" % (f, len(Q))); continue
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
        rows.append(dict(cohort=name, f=f, n_cells=int(Q[ok].cell.nunique()),
                         n_cond=int(len(cm)), mean_nobs=float(Q.n_obs.mean()),
                         cond_macro=float(cm.mean()), cm=cm))
        print("    f=%.2f cells %3d conds %2d mean n_obs %5.1f  cond-macro %.4f" % (
            f, rows[-1]["n_cells"], rows[-1]["n_cond"], rows[-1]["mean_nobs"], rows[-1]["cond_macro"]), flush=True)
    return rows

# ---- UConn ----
u = pd.read_csv(os.path.join(PROTO, "uconn_online_tidy.csv"))
u = u[np.isfinite(u.cum_cycles)]
eol = pd.read_csv(os.path.join(PROTO, "uconn_eol_intervals.csv"))
eol = eol[eol.kind == "interval"].set_index("cell")
uc = {}
for c, g in u.groupby("cell"):
    if c not in eol.index: continue
    g = g.sort_values("cum_cycles")
    uc[c] = dict(cond=int(g.cond.iloc[0]), x=g.cum_cycles.values.astype(float),
                 soh=g.soh.values.astype(float), L=float(eol.loc[c, "L"]), U=float(eol.loc[c, "U"]))
print("UConn cells: %d" % len(uc))
A = landmark_run("UConn", uc)

# ---- ISU ----
z = zipfile.ZipFile(RAW_ISU); ic = {}
for n in sorted(x for x in z.namelist() if x.lower().endswith(".json")):
    cell = n.split("/")[-1].replace(".json", "")
    m = re.match(r"G(\d+)C(\d+)", cell)
    if not m: continue
    g = int(m.group(1))
    try: d = json.loads(json.loads(z.read(n).decode("utf-8")))
    except Exception: continue
    cap = d.get("capacity_discharge_C_5") or d.get("capacity_discharge_C_2")
    ts = (d.get("start_stop_time") or {}).get("start") or []
    if not isinstance(cap, list) or len(cap) < 4: continue
    v = []
    for x in cap:
        try: v.append(float(x))
        except Exception: v.append(np.nan)
    v = np.array(v, float)
    L = min(len(v), len(ts)) if ts else 0
    if L < 4: continue
    t = [pd.to_datetime(x, errors="coerce") for x in ts[:L]]
    if not all(pd.notna(x) for x in t): continue
    ref = np.nanmax(v[:L])
    if not np.isfinite(ref) or ref <= 0: continue
    soh = v[:L] / ref
    day = np.array([(x - t[0]).total_seconds()/86400.0 for x in t])
    below = np.where(soh <= 0.80)[0]
    if below.size == 0: continue
    k = int(below[0])
    if k == 0: continue
    ic[cell] = dict(cond=g, x=day, soh=soh, L=day[k-1], U=day[k])
print("ISU cells: %d" % len(ic))
B = landmark_run("ISU", ic)

allrows = A + B
T = pd.DataFrame([{k: v for k, v in r.items() if k != "cm"} for r in allrows])
T.to_csv(os.path.join(PROTO, "C_landmark_fraction.csv"), index=False)
json.dump(T.to_dict("records"), open(os.path.join(PROTO, "C_landmark_fraction.json"), "w"), indent=1)
print("\n=== landmark at a fixed LIFE FRACTION (comparable across cohorts) ===")
print(T.pivot(index="f", columns="cohort", values="cond_macro").to_string(float_format=lambda x: "%.4f" % x))
for coh in ("UConn", "ISU"):
    sub = T[T.cohort == coh]
    if len(sub) >= 2:
        a = sub[sub.f == sub.f.min()].cond_macro.iloc[0]
        b = sub[sub.f == sub.f.max()].cond_macro.iloc[0]
        print("  %-6s f=%.2f -> %.2f : %.4f -> %.4f (%+.1f%%)" % (
            coh, sub.f.min(), sub.f.max(), a, b, 100*(b/a-1)))
# paired comparison between cohorts at each f
print("\n  cohort gap at each f:")
for f in sorted(T.f.unique()):
    row = T[T.f == f]
    if len(row) == 2:
        uu = row[row.cohort == "UConn"].cond_macro.iloc[0]
        ii = row[row.cohort == "ISU"].cond_macro.iloc[0]
        print("    f=%.2f  UConn %.4f  ISU %.4f  (ISU %+.1f%% vs UConn)" % (f, uu, ii, 100*(ii/uu-1)))
print("\nwrote C_landmark_fraction.csv / .json")
