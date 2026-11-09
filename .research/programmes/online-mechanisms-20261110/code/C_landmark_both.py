# -*- coding: utf-8 -*-
"""Question C, part 3: a COMMON landmark design on both cohorts.

The earlier two C analyses were not comparable:
  * UConn used "thin the whole schedule by k" (queries at life fractions);
  * ISU used "the first N reference tests" (a landmark design).
This script puts both cohorts on the same landmark design so the observation
budget can be compared directly:

  for each cell, use ONLY its first N reference tests to predict its
  end-of-life; leave-one-condition-out; condition-macro |log error|.

If the error is flat in N on both cohorts, then a small number of early
reference tests is sufficient for lifetime prediction - a decision-relevant
statement about testing cost. If it is flat on one and not the other, the
cohorts genuinely differ and must be reported separately.

UConn axis: cumulative cycles (cycle axis). ISU axis: calendar days.
"""
import os, json, zipfile, re
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")
RES = os.path.join(HERE, "..", "..", "..", "results")
RAW_ISU = r"E:\桌面\rul\data\external\isu_raw\RPT_json.zip"

NS = (2, 3, 4, 6, 8, 12)
FEATS = ["t", "soh_last", "soh0", "slope", "span"]

def run_cohort(name, cells, out):
    """cells: dict cell -> dict(cond, x=axis, soh=array, L, U)

    FIXED POPULATION: only cells with at least max(NS) reference tests are
    eligible, and the SAME cells are used at every N. Without this, the curve
    is confounded: at large N only long-lived cells survive, and their lifetime
    is systematically different. (This was the defect in the first C attempt.)
    """
    NMAX = max(NS)
    keep = {c: s for c, s in cells.items() if len(s["x"]) >= NMAX}
    print("  [%s] fixed population: %d of %d cells have >=%d reference tests" % (
        name, len(keep), len(cells), NMAX))
    rows = []
    for N in NS:
        recs = []
        for c, s in keep.items():
            x, soh = s["x"], s["soh"]
            idx = np.linspace(0, N - 1, N).round().astype(int)
            idx = np.unique(idx)
            if idx.size < N: continue
            xv, sv = x[idx], soh[idx]
            recs.append(dict(cell=c, cond=s["cond"], t=float(xv[-1]), soh_last=float(sv[-1]),
                             soh0=float(sv[0]),
                             slope=float((sv[-1]-sv[0])/max(xv[-1]-xv[0], 1e-12)),
                             span=float(xv[-1]-xv[0]), y=float(np.log(s["U"]))))
        Q = pd.DataFrame(recs)
        if len(Q) < 60:
            print("  N=%-2d only %d rows, skip" % (N, len(Q))); continue
        pred = np.full(len(Q), np.nan)
        for held in sorted(Q.cond.unique()):
            te = Q.cond == held; tr = ~te
            if tr.sum() < 40 or te.sum() == 0: continue
            m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
            m.fit(Q.loc[tr, FEATS].values, Q.loc[tr, "y"].values)
            pred[te.values] = m.predict(Q.loc[te, FEATS].values)
        ok = np.isfinite(pred)
        e = np.abs(pred[ok] - Q.y.values[ok])
        cm = pd.DataFrame({"e": e, "g": Q.cond.values[ok]}).groupby("g").e.mean()
        rows.append(dict(cohort=name, N=N, n_cells=int(Q[ok].cell.nunique()), n_cond=int(len(cm)),
                         cond_macro=float(cm.mean())))
        print("  N=%-2d cells %3d conds %2d  cond-macro |log err| %.4f" % (
            N, rows[-1]["n_cells"], rows[-1]["n_cond"], rows[-1]["cond_macro"]), flush=True)
    return pd.DataFrame(rows)

# ---------------- UConn ----------------
u = pd.read_csv(os.path.join(PROTO, "uconn_online_tidy.csv"))
u = u[np.isfinite(u.cum_cycles)]
eol = pd.read_csv(os.path.join(PROTO, "uconn_eol_intervals.csv"))
eol = eol[eol.kind == "interval"].set_index("cell")
uc = {}
for c, g in u.groupby("cell"):
    if c not in eol.index: continue
    g = g.sort_values("cum_cycles")
    uc[c] = dict(cond=int(g.cond.iloc[0]), x=g.cum_cycles.values.astype(float),
                 soh=g.soh.values.astype(float),
                 L=float(eol.loc[c, "L"]), U=float(eol.loc[c, "U"]))
print("UConn cells: %d" % len(uc))
A = run_cohort("UConn", uc, None)

# ---------------- ISU ----------------
def load_isu():
    z = zipfile.ZipFile(RAW_ISU); out = {}
    for n in sorted(x for x in z.namelist() if x.lower().endswith(".json")):
        cell = n.split("/")[-1].replace(".json", "")
        m = re.match(r"G(\d+)C(\d+)", cell)
        if not m: continue
        g = int(m.group(1))
        try: d = json.loads(json.loads(z.read(n).decode("utf-8")))
        except Exception: continue
        cap = d.get("capacity_discharge_C_5") or d.get("capacity_discharge_C_2")
        ts = (d.get("start_stop_time") or {}).get("start") or []
        if not isinstance(cap, list) or len(cap) < 3: continue
        v = []
        for x in cap:
            try: v.append(float(x))
            except Exception: v.append(np.nan)
        v = np.array(v, float)
        L = min(len(v), len(ts)) if ts else 0
        if L < 3: continue
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
        out[cell] = dict(cond=g, x=day, soh=soh, L=day[k-1], U=day[k])
    return out
ic = load_isu()
print("ISU cells: %d" % len(ic))
B = run_cohort("ISU", ic, None)

T = pd.concat([A, B], ignore_index=True)
T.to_csv(os.path.join(PROTO, "C_landmark_both.csv"), index=False)
json.dump(T.to_dict("records"), open(os.path.join(PROTO, "C_landmark_both.json"), "w"), indent=1)
print("\n=== common landmark design, both cohorts ===")
print(T.pivot(index="N", columns="cohort", values="cond_macro").to_string(float_format=lambda x: "%.4f" % x))
for coh in ("UConn", "ISU"):
    sub = T[T.cohort == coh]
    if len(sub) >= 3:
        base = sub[sub.N == sub.N.min()].cond_macro.iloc[0]
        last = sub[sub.N == sub.N.max()].cond_macro.iloc[0]
        print("  %-6s N=%d->%d : %.4f -> %.4f  (%+.1f%%)" % (
            coh, sub.N.min(), sub.N.max(), base, last, 100*(last/base-1)))
print("\nwrote C_landmark_both.csv / .json")
