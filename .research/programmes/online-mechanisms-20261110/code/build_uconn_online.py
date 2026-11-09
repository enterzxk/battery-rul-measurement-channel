# -*- coding: utf-8 -*-
"""Build the canonical online-inspection dataset for question A.

Facts established before writing this (see .research/programmes/online-mechanisms-20261110/protocol/):

1. data_cc_1.pkl stores 6 rows per (cell_id, rpt). The six share identical
   q_dchg / soh / DCIR but carry a 600-point voltage array with a rolling
   offset. It is a storage artefact, NOT six replicates. We dedupe by
   (cell_id, rpt), keeping the first row.

2. `num_cycles` is a SEGMENT LENGTH (cycles accumulated since the previous
   RPT), not a cumulative counter. Confirmed: values are 0, 107, 95, 99, 100...
   and are non-monotone raw but monotone after cumsum. (Matches F-005.)

3. Consequence: the physical lifetime axis is cumsum(num_cycles) within a cell.

Outputs a tidy table: one row per (cell, rpt) with
  cell, cond, rpt, seg_cycles, cum_cycles, soh, q_dchg, dcir_*
plus derived per-cell EOL interval in cumulative cycles.
"""
import os, pickle, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = r"E:\桌面\rul\data\external\uconn\data_cc_1.pkl"
OUT = os.path.join(HERE, "..", "protocol")

d = pickle.load(open(RAW, "rb"))
n = len(d["cell_id"])
df = pd.DataFrame({
    "cell": d["cell_id"], "cond": d["group_id"], "rpt": d["rpt"],
    "seg_cycles": d["num_cycles"], "soh": d["soh"], "q_dchg": d["q_dchg"],
    "dcir_chg_20": d["dcir_chg_20"], "dcir_dchg_20": d["dcir_dchg_20"],
    "dcir_chg_50": d["dcir_chg_50"], "dcir_dchg_50": d["dcir_dchg_50"],
    "dcir_chg_90": d["dcir_chg_90"], "dcir_dchg_90": d["dcir_dchg_90"],
})
print("raw rows: %d  cells: %d  conditions: %d" % (len(df), df.cell.nunique(), df.cond.nunique()))

# --- dedupe the 6x storage artefact ---
df = df.sort_values(["cell", "rpt"]).drop_duplicates(["cell", "rpt"], keep="first").reset_index(drop=True)
print("after dedupe: %d rows  (rows per cell: median %.0f)" % (len(df), df.groupby("cell").size().median()))

# --- cumulative physical axis ---
df = df.sort_values(["cell", "rpt"]).reset_index(drop=True)
df["cum_cycles"] = df.groupby("cell")["seg_cycles"].cumsum()
df["seg_ok"] = np.isfinite(df["seg_cycles"])
print("cells with any non-finite segment length: %d" % df.groupby("cell")["seg_ok"].apply(lambda s: (~s).any()).sum())

# --- inspection cadence in the physical axis ---
gaps = []
for c, g in df.groupby("cell"):
    v = g["cum_cycles"].values
    if len(v) > 1:
        gaps.extend(np.diff(v).tolist())
gaps = np.array(gaps, float)
gaps = gaps[np.isfinite(gaps)]
cad = {
    "n_gaps": int(gaps.size),
    "median": float(np.median(gaps)),
    "q25": float(np.percentile(gaps, 25)),
    "q75": float(np.percentile(gaps, 75)),
    "min": float(gaps.min()), "max": float(gaps.max()),
    "cv": float(gaps.std() / gaps.mean()) if gaps.mean() else None,
}
print("\ninspection cadence in cycles: median %.1f IQR [%.1f, %.1f] cv %.2f max/min %.1f" % (
    cad["median"], cad["q25"], cad["q75"], cad["cv"], cad["max"] / max(cad["min"], 1e-9)))

# --- EOL intervals on the physical axis (80% SOH) ---
rows = []
for c, g in df.groupby("cell"):
    g = g.sort_values("rpt")
    cum = g["cum_cycles"].values.astype(float)
    soh = g["soh"].values.astype(float)
    ok = np.isfinite(cum) & np.isfinite(soh)
    cum, soh = cum[ok], soh[ok]
    if cum.size < 2:
        continue
    below = np.where(soh <= 80.0)[0]
    if below.size == 0:
        rows.append(dict(cell=int(c), cond=int(g.cond.iloc[0]), kind="right_censored",
                         L=float(cum[-1]), U=np.nan, last_soh=float(soh[-1])))
    elif below[0] == 0:
        rows.append(dict(cell=int(c), cond=int(g.cond.iloc[0]), kind="left_of_first",
                         L=np.nan, U=float(cum[0]), last_soh=float(soh[0])))
    else:
        i = below[0]
        rows.append(dict(cell=int(c), cond=int(g.cond.iloc[0]), kind="interval",
                         L=float(cum[i - 1]), U=float(cum[i]), last_soh=float(soh[i])))
eol = pd.DataFrame(rows)
print("\nEOL status counts:\n%s" % eol.kind.value_counts().to_string())
iv = eol[eol.kind == "interval"]
if len(iv):
    w = (iv.U - iv.L).values
    print("interval width (cycles): median %.0f  IQR [%.0f, %.0f]" % (
        np.median(w), np.percentile(w, 25), np.percentile(w, 75)))
    print("relative width (w / U): median %.3f" % np.median(w / iv.U.values))

df.to_csv(os.path.join(OUT, "uconn_online_tidy.csv"), index=False)
eol.to_csv(os.path.join(OUT, "uconn_eol_intervals.csv"), index=False)
json.dump({"cadence_cycles": cad,
           "n_rows_dedup": int(len(df)), "n_cells": int(df.cell.nunique()),
           "n_conditions": int(df.cond.nunique()),
           "eol_status": eol.kind.value_counts().to_dict()},
          open(os.path.join(OUT, "uconn_data_contract.json"), "w"), indent=1)
print("\nwrote uconn_online_tidy.csv / uconn_eol_intervals.csv / uconn_data_contract.json")
