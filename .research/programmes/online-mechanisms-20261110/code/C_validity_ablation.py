# -*- coding: utf-8 -*-
"""Bounded C validity comparison (Codex review, priority 2).

The defect being removed: the earlier landmark used t = x0 + f*(L - x0), so the
query time was built from the eventual crossing L. That lets a health-free age
rule reconstruct the answer, which is what refuted the UConn headline.

Here query times are FIXED AGES chosen without looking at any cell's EOL. Every
predictor is scored on the same query keys. The question is an ablation:

    age        : log U ~ log t                     (no health, no stress)
    stress     : log U ~ condition stress factors   (no health, no age)
    age_stress : both
    health     : age + stress + observed health trajectory

Health information has value only if `health` beats `age_stress` on identical
queries. Leave-one-condition-out throughout.

UConn axis: cumulative cycles. ISU axis: calendar days.
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

def run(name, cells, ages, stress_map=None):
    recs = []
    for c, s in cells.items():
        for t in ages:
            if t <= 0 or t >= s["L"]:          # query must precede the crossing
                continue
            vis = s["x"] <= t
            if vis.sum() < MIN_OBS:
                continue
            xv, sv = s["x"][vis], s["soh"][vis]
            span = float(xv[-1] - xv[0])
            r = dict(cell=c, cond=s["cond"], t=float(t), logt=float(np.log(t)),
                     n_obs=int(vis.sum()), soh_last=float(sv[-1]), soh0=float(sv[0]),
                     slope=float((sv[-1]-sv[0])/max(span, 1e-12)), span=span,
                     y=float(np.log(s["U"])))
            if stress_map is not None and s["cond"] in stress_map.index:
                r["DoD"] = float(stress_map.loc[s["cond"], "DoD"])
                r["cc"] = float(stress_map.loc[s["cond"], "charge_C"])
                r["cd"] = float(stress_map.loc[s["cond"], "discharge_C"])
            recs.append(r)
    Q = pd.DataFrame(recs)
    if len(Q) < 60:
        print("  %s: only %d rows" % (name, len(Q))); return []
    has_stress = "DoD" in Q.columns
    sets = {"age": ["logt"]}
    if has_stress:
        sets["stress"] = ["DoD", "cc", "cd"]
        sets["age_stress"] = ["logt", "DoD", "cc", "cd"]
    sets["health"] = (["logt", "DoD", "cc", "cd"] if has_stress else ["logt"]) + \
                     ["soh_last", "soh0", "slope", "span", "n_obs"]
    out = []
    preds = {}
    for arm, feats in sets.items():
        p = np.full(len(Q), np.nan)
        for held in sorted(Q.cond.unique()):
            te = Q.cond == held; tr = ~te
            if tr.sum() < 40 or te.sum() == 0: continue
            m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
            m.fit(Q.loc[tr, feats].values, Q.loc[tr, "y"].values)
            p[te.values] = m.predict(Q.loc[te, feats].values)
        preds[arm] = p
    ok = np.isfinite(preds["age"])
    d = pd.DataFrame({a: np.abs(preds[a][ok] - Q.y.values[ok]) for a in sets})
    d["cond"] = Q.cond.values[ok]
    cm = d.groupby("cond").mean()
    row = dict(cohort=name, n_cells=int(Q[ok].cell.nunique()), n_cond=int(len(cm)),
               n_queries=int(ok.sum()))
    for a in sets: row[a] = float(cm[a].mean())
    print("  %-5s cells %3d conds %2d q %4d | age %.4f | stress %s | age_stress %s | health %.4f" % (
        name, row["n_cells"], row["n_cond"], row["n_queries"], row["age"],
        ("%.4f" % row["stress"]) if "stress" in row else "  -   ",
        ("%.4f" % row["age_stress"]) if "age_stress" in row else "  -   ", row["health"]), flush=True)
    if "age_stress" in row:
        row["health_vs_age_stress_pct"] = 100*(row["health"]/row["age_stress"] - 1)
        print("        -> health vs age_stress: %+.1f%%" % row["health_vs_age_stress_pct"], flush=True)
    return [row]

# ---- UConn ----
u = pd.read_csv(os.path.join(PROTO, "uconn_tidy_fixed.csv"))
e = pd.read_csv(os.path.join(PROTO, "uconn_eol_fixed.csv"))
e = e[e.kind == "interval"].set_index("cell")
uc = {}
for c, g in u.groupby("cell"):
    if c not in e.index: continue
    g = g.sort_values("cum")
    uc[c] = dict(cond=int(g.cond.iloc[0]), x=g.cum.values.astype(float),
                 soh=g.soh.values.astype(float), L=float(e.loc[c, "L"]), U=float(e.loc[c, "U"]))
print("=== query ages fixed WITHOUT reference to EOL ===")
rows = run("UConn", uc, ages=(300, 600, 1000, 1500))

# ---- ISU (with stress table) ----
cond = pd.read_csv(os.path.join(RES, "isu_conditions.csv"))
cond.columns = ["group", "charge_C", "discharge_C", "mean_DoD_pct"]
cond["DoD"] = cond.mean_DoD_pct/100.0
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
rows += run("ISU", ic, ages=(21, 35, 49, 63), stress_map=S)

T = pd.DataFrame(rows)
T.to_csv(os.path.join(PROTO, "C_validity_ablation.csv"), index=False)
json.dump(T.to_dict("records"), open(os.path.join(PROTO, "C_validity_ablation.json"), "w"), indent=1)
print("\nwrote C_validity_ablation.csv / .json")
