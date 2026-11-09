# -*- coding: utf-8 -*-
"""Question C, part 2: does the required inspection budget depend on the
operating stress?

ISU cells have too few reference tests to support a thinning curve, but the
question can be asked the other way round: hold the number of observations fixed
at N and ask whether the prediction error depends on the condition's stress
factors. If hard conditions (deep DoD, high rate) lose accuracy faster as N
shrinks, the inspection budget must be stress-dependent.

Design
  For N in {3,4,6,8}: for each cell, use its FIRST N reference tests to predict
  its end-of-life. Leave-one-condition-out; condition-macro |log error|.
  Then regress that per-condition error on DoD, charge rate and discharge rate.
  A significant stress coefficient means the budget requirement is not uniform.
"""
import os, json, zipfile, re
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")
RES = os.path.join(HERE, "..", "..", "..", "results")
RAW = r"E:\桌面\rul\data\external\isu_raw\RPT_json.zip"

def load():
    z = zipfile.ZipFile(RAW); out = []
    for n in sorted(x for x in z.namelist() if x.lower().endswith(".json")):
        cell = n.split("/")[-1].replace(".json", "")
        m = re.match(r"G(\d+)C(\d+)", cell)
        if not m: continue
        g = int(m.group(1))
        try: d = json.loads(json.loads(z.read(n).decode("utf-8")))
        except Exception: continue
        cap = d.get("capacity_discharge_C_5") or d.get("capacity_discharge_C_2")
        ts = (d.get("start_stop_time") or {}).get("start") or []
        if not isinstance(cap, list) or len(cap) < 6: continue
        v = []
        for x in cap:
            try: v.append(float(x))
            except Exception: v.append(np.nan)
        v = np.array(v, float)
        L = min(len(v), len(ts)) if ts else 0
        if L < 6: continue
        t = [pd.to_datetime(x, errors="coerce") for x in ts[:L]]
        if not all(pd.notna(x) for x in t): continue
        ref = np.nanmax(v[:L])
        if not np.isfinite(ref) or ref <= 0: continue
        soh = v[:L] / ref
        day = np.array([(x - t[0]).total_seconds()/86400.0 for x in t])
        below = np.where(soh <= 0.80)[0]
        if below.size == 0: continue
        u = int(below[0])
        if u == 0: continue
        out.append(dict(cell=cell, group=g, soh=soh, day=day, L=day[u-1], U=day[u]))
    return out

SER = load()
print("cells with >=6 RPTs and full timestamps: %d" % len(SER))
cond = pd.read_csv(os.path.join(RES, "isu_conditions.csv"))
cond.columns = ["group", "charge_C", "discharge_C", "mean_DoD_pct"]
cond["DoD"] = cond.mean_DoD_pct / 100.0
CMAP = cond.set_index("group")

def build(N):
    rows = []
    for s in SER:
        if s["group"] not in CMAP.index: continue
        soh, day = s["soh"], s["day"]
        stop = int(np.searchsorted(day, s["L"]))
        stop = min(max(stop, N), len(soh) - 1)
        idx = np.linspace(0, stop, N).round().astype(int)
        idx = np.unique(idx)
        if idx.size < N: continue
        sv, dv = soh[idx], day[idx]
        rows.append(dict(cell=s["cell"], group=s["group"], n_obs=N, t=float(dv[-1]),
                         soh_last=float(sv[-1]), soh0=float(sv[0]),
                         slope=float((sv[-1]-sv[0])/max(dv[-1]-dv[0], 1e-9)),
                         span=float(dv[-1]-dv[0]), y=float(np.log(s["U"]))))
    return pd.DataFrame(rows)

FEATS = ["t", "soh_last", "soh0", "slope", "span"]
out = []
for N in (3, 4, 6, 8):
    Q = build(N)
    if len(Q) < 60: 
        print("N=%d: only %d rows, skip" % (N, len(Q))); continue
    pred = np.full(len(Q), np.nan)
    for held in sorted(Q.group.unique()):
        te = Q.group == held; tr = ~te
        if tr.sum() < 40 or te.sum() == 0: continue
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
        m.fit(Q.loc[tr, FEATS].values, Q.loc[tr, "y"].values)
        pred[te.values] = m.predict(Q.loc[te, FEATS].values)
    ok = np.isfinite(pred)
    e = np.abs(pred[ok] - Q.y.values[ok])
    cm = pd.DataFrame({"e": e, "g": Q.group.values[ok]}).groupby("g").e.mean().rename("err").reset_index()
    cm = cm.merge(cond, on="group", how="left") if "group" in cm.columns else cm.merge(cond, left_on="g", right_on="group", how="left")
    # does the error depend on stress?
    r_dod = stats.spearmanr(cm.DoD, cm.err)
    r_cc = stats.spearmanr(cm.charge_C, cm.err)
    r_cd = stats.spearmanr(cm.discharge_C, cm.err)
    out.append(dict(N=N, n_cells=int(Q[ok].cell.nunique()), n_cond=int(cm.size),
                    cond_macro=float(cm.err.mean()),
                    rho_dod=float(r_dod.statistic), p_dod=float(r_dod.pvalue),
                    rho_cc=float(r_cc.statistic), p_cc=float(r_cc.pvalue),
                    rho_cd=float(r_cd.statistic), p_cd=float(r_cd.pvalue)))
    print("N=%-2d cells %3d conds %2d  cond-macro %.4f | rho(err,DoD) %+.3f p=%.3g | rho(err,Cc) %+.3f p=%.3g | rho(err,Cd) %+.3f p=%.3g" % (
        N, out[-1]["n_cells"], out[-1]["n_cond"], out[-1]["cond_macro"],
        out[-1]["rho_dod"], out[-1]["p_dod"], out[-1]["rho_cc"], out[-1]["p_cc"], out[-1]["rho_cd"], out[-1]["p_cd"]), flush=True)

T = pd.DataFrame(out)
T.to_csv(os.path.join(PROTO, "C_stress_budget.csv"), index=False)
json.dump(T.to_dict("records"), open(os.path.join(PROTO, "C_stress_budget.json"), "w"), indent=1)
print("\nwrote C_stress_budget.csv / .json")
