# -*- coding: utf-8 -*-
"""Question C: inspection thinning on UConn (rich RPT schedule, cycle axis).

ISU was tried first and rejected: its cells have a median of 20 reference tests,
so thinning by 6 leaves almost nothing and no fixed population survives every
level. UConn has 22-77 tests per cell, which supports a real thinning curve.

Design (fixed population, fixed queries):
  1. A cell is eligible only if, at EVERY thinning factor in the grid, it still
     contributes >= MIN_OBS inspections by the earliest query fraction.
     The eligible set is computed once and used at every level.
  2. At thinning factor k we keep every k-th reference test (plus the first and
     the crossing observation). Nothing else changes.
  3. For each cell and life fraction we predict the end-of-life cycle from the
     visible thinned history; leave-one-condition-out; condition-macro scoring.
  4. Report both absolute error and whether the CONDITION RANKING survives.

This is a controlled manipulation of the inspection budget: same cells, same
targets, same model, only the number of allowed inspections changes.
"""
import os, json
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "protocol")

df = pd.read_csv(os.path.join(PROTO, "uconn_online_tidy.csv"))
df = df[np.isfinite(df.cum_cycles)].copy()
eol = pd.read_csv(os.path.join(PROTO, "uconn_eol_intervals.csv"))
eol = eol[eol.kind == "interval"].set_index("cell")
print("cells with finite cycle axis: %d | interval EOL: %d" % (df.cell.nunique(), len(eol)))

KS = (1, 2, 3, 4)
FRACS = (0.5, 0.75)
MIN_OBS = 2

cells = {}
for c, g in df.groupby("cell"):
    if c not in eol.index: continue
    g = g.sort_values("cum_cycles")
    cells[c] = dict(cond=int(g.cond.iloc[0]), cum=g.cum_cycles.values.astype(float),
                    soh=g.soh.values.astype(float), d20c=g.dcir_chg_20.values.astype(float),
                    d20d=g.dcir_dchg_20.values.astype(float),
                    L=float(eol.loc[c, "L"]), U=float(eol.loc[c, "U"]))

def thinned(n, stop, k):
    idx = [i for i in range(0, stop + 1, k)]
    if stop not in idx: idx.append(stop)
    return idx

# ---- fix the population once ----
elig = []
for c, s in cells.items():
    if not (s["U"] > s["L"]): continue
    stop = int(np.searchsorted(s["cum"], s["L"]))
    stop = min(max(stop, 1), len(s["cum"]) - 1)
    ok = True
    for k in KS:
        idx = thinned(len(s["cum"]), stop, k)
        cum = s["cum"][idx]
        t = cum[0] + FRACS[0] * (s["L"] - cum[0])
        if (cum <= t).sum() < MIN_OBS: ok = False; break
    if ok: elig.append(c)
print("eligible for every k in %s: %d cells | conditions %d" % (
    list(KS), len(elig), len(set(cells[c]["cond"] for c in elig))))

FEATS = ["n_obs", "t", "soh_last", "slope", "span", "soh0", "d20c", "d20d"]

def build(k):
    out = []
    for c in elig:
        s = cells[c]
        stop = int(np.searchsorted(s["cum"], s["L"])); stop = min(max(stop, 1), len(s["cum"]) - 1)
        idx = thinned(len(s["cum"]), stop, k)
        cum, soh = s["cum"][idx], s["soh"][idx]
        for f in FRACS:
            t = cum[0] + f * (s["L"] - cum[0])
            vis = cum <= t
            if vis.sum() < MIN_OBS: continue
            cv, sv = cum[vis], soh[vis]
            out.append(dict(cell=c, cond=s["cond"], frac=f, n_obs=int(vis.sum()), t=float(cv[-1]),
                            soh_last=float(sv[-1]), slope=float((sv[-1]-sv[0])/max(cv[-1]-cv[0],1e-9)),
                            span=float(cv[-1]-cv[0]), soh0=float(sv[0]),
                            d20c=float(s["d20c"][idx][vis][-1]), d20d=float(s["d20d"][idx][vis][-1]),
                            L=s["L"], U=s["U"]))
    return pd.DataFrame(out)

def run(k):
    Q = build(k)
    Q["y"] = np.log(Q.U)
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
    pr = pd.DataFrame({"g": Q.cond.values[ok], "p": pred[ok], "y": Q.y.values[ok]}).groupby("g").median()
    rho = stats.spearmanr(pr.p, pr.y).statistic if len(pr) > 3 else np.nan
    return dict(k=k, n_cells=int(Q[ok].cell.nunique()), n_cond=int(cm.size), n_q=int(ok.sum()),
                mean_nobs=float(Q.n_obs.mean()), cond_macro=float(cm.mean()), rho=float(rho),
                cm=cm)

rows = [run(k) for k in KS]
for r in rows:
    print("k=%-2d  cells %2d  conds %2d  queries %3d  mean n_obs %5.1f  cond-macro |log err| %.4f  rank rho %+.3f" % (
        r["k"], r["n_cells"], r["n_cond"], r["n_q"], r["mean_nobs"], r["cond_macro"], r["rho"]), flush=True)

T = pd.DataFrame([{k: v for k, v in r.items() if k != "cm"} for r in rows])
base = T.cond_macro.iloc[0]
T["rel_vs_full"] = T.cond_macro / base - 1
print("\n=== fixed population (%d cells), relative to full inspection ===" % rows[0]["n_cells"])
print(T[["k", "mean_nobs", "cond_macro", "rel_vs_full", "rho"]].to_string(index=False, float_format=lambda x: "%.4f" % x))

# paired test of the most aggressive level vs full
a = rows[0]["cm"]; b = rows[-1]["cm"]
common = a.index.intersection(b.index)
if len(common) >= 6:
    w = stats.wilcoxon(a.loc[common].values, b.loc[common].values)
    print("\nk=%d vs k=1 on %d common conditions: median delta %+.4f  Wilcoxon p=%.4g" % (
        rows[-1]["k"], len(common), float(np.median(b.loc[common]-a.loc[common])), w.pvalue))

T.to_csv(os.path.join(PROTO, "C_thinning_uconn.csv"), index=False)
json.dump(T.to_dict("records"), open(os.path.join(PROTO, "C_thinning_uconn.json"), "w"), indent=1)
print("\nwrote C_thinning_uconn.csv / .json")
