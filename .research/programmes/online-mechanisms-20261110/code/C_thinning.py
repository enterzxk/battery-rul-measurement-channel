# -*- coding: utf-8 -*-
"""Question C, v2: inspection thinning on a FIXED evaluation population.

v1 was invalid: as the thinning factor grew, cells with few RPTs dropped out, so
the evaluated population changed with k. The apparent "error falls with thinner
inspection" was a population artefact, not a result.

v2 fixes the population first:
  * a cell is eligible only if, at EVERY thinning factor in the grid, it still
    contributes at least MIN_OBS observations at the earliest life fraction;
  * the same eligible cells, the same life fractions and the same scoring are
    used at every k.

Then the only thing that changes across the curve is how many inspections the
model is allowed to see.
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

def load_series():
    z = zipfile.ZipFile(RAW)
    out = []
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
        day = np.array([(x - t[0]).total_seconds() / 86400.0 for x in t])
        out.append(dict(cell=cell, group=g, soh=soh, day=day))
    return out

SER = load_series()
print("cells with full timestamps: %d" % len(SER))

def eol_of(soh, day):
    b = np.where(soh <= 0.80)[0]; b = b[np.isfinite(soh[b])]
    if b.size == 0: return None
    u = int(b[0])
    return None if u == 0 else (day[u - 1], day[u])

KS = (1, 2, 3, 4, 6)
FRACS = (0.25, 0.5, 0.75)
MIN_OBS = 3

def thinned_idx(soh, k):
    below = np.where(soh <= 0.80)[0]
    stop = int(below[0]) if below.size else len(soh) - 1
    idx = [i for i in range(0, len(soh), k) if i <= stop]
    if stop not in idx: idx.append(stop)
    return idx

# ---- fix the population FIRST ----
elig = []
for s in SER:
    e = eol_of(s["soh"], s["day"])
    if e is None or not (e[1] > e[0]): continue
    L, U = e
    ok = True
    for k in KS:
        idx = thinned_idx(s["soh"], k)
        d = s["day"][idx]
        t = d[0] + FRACS[0] * (L - d[0])
        if (d <= t).sum() < MIN_OBS: ok = False; break
    if ok: elig.append(s)
print("eligible for EVERY k in %s at frac=%s with >=%d obs: %d cells" % (list(KS), FRACS[0], MIN_OBS, len(elig)))
print("conditions covered: %d" % len(set(s["group"] for s in elig)))

cond = pd.read_csv(os.path.join(RES, "isu_conditions.csv"))
cond.columns = ["group", "charge_C", "discharge_C", "mean_DoD_pct"]
cond["DoD"] = cond.mean_DoD_pct / 100.0
CMAP = cond.set_index("group")

def build(k):
    out = []
    for s in elig:
        soh, day, g, cell = s["soh"], s["day"], s["group"], s["cell"]
        L, U = eol_of(soh, day)
        idx = thinned_idx(soh, k)
        sv, dv = soh[idx], day[idx]
        for f in FRACS:
            t = dv[0] + f * (L - dv[0])
            vis = dv <= t
            if vis.sum() < MIN_OBS: continue
            a, b = sv[vis], dv[vis]
            out.append(dict(cell=cell, group=g, frac=f, n_obs=int(vis.sum()),
                            t=float(b[-1]), soh_last=float(a[-1]),
                            slope=float((a[-1] - a[0]) / max(b[-1] - b[0], 1e-9)),
                            span=float(b[-1] - b[0]), soh0=float(a[0]), L=L, U=U))
    return pd.DataFrame(out)

FEATS = ["n_obs", "t", "soh_last", "slope", "span", "soh0"]

def run(k):
    Q = build(k)
    Q = Q[Q.group.isin(CMAP.index)].copy()
    Q["y"] = np.log(Q.U)
    pred = np.full(len(Q), np.nan)
    for held in sorted(Q.group.unique()):
        te = Q.group == held; tr = ~te
        if tr.sum() < 60 or te.sum() == 0: continue
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
        m.fit(Q.loc[tr, FEATS].values, Q.loc[tr, "y"].values)
        pred[te.values] = m.predict(Q.loc[te, FEATS].values)
    ok = np.isfinite(pred)
    e = np.abs(pred[ok] - Q.y.values[ok])
    cm = pd.DataFrame({"e": e, "g": Q.group.values[ok]}).groupby("g").e.mean()
    pr = pd.DataFrame({"g": Q.group.values[ok], "p": pred[ok], "y": Q.y.values[ok]}).groupby("g").median()
    rho = stats.spearmanr(pr.p, pr.y).statistic if len(pr) > 3 else np.nan
    return dict(k=k, n_queries=int(ok.sum()), n_cond=int(cm.size), n_cells=int(Q[ok].cell.nunique()),
                mean_nobs=float(Q.n_obs.mean()), cond_macro=float(cm.mean()), rho=float(rho))

rows = [run(k) for k in KS]
for r in rows:
    print("k=%-2d  cells %2d  conds %2d  queries %4d  mean n_obs %4.1f  cond-macro %.4f  rank rho %+.3f" % (
        r["k"], r["n_cells"], r["n_cond"], r["n_queries"], r["mean_nobs"], r["cond_macro"], r["rho"]), flush=True)

T = pd.DataFrame(rows)
base = T.cond_macro.iloc[0]
T["rel_vs_full"] = T.cond_macro / base - 1
print("\n=== on a FIXED population (%d cells), relative to full inspection ===" % rows[0]["n_cells"])
print(T[["k", "mean_nobs", "cond_macro", "rel_vs_full", "rho"]].to_string(index=False, float_format=lambda x: "%.4f" % x))
T.to_csv(os.path.join(PROTO, "C_thinning_curve.csv"), index=False)
json.dump(T.to_dict("records"), open(os.path.join(PROTO, "C_thinning.json"), "w"), indent=1)
print("\nwrote C_thinning_curve.csv / C_thinning.json")
