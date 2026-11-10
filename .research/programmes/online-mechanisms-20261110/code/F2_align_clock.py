# -*- coding: utf-8 -*-
"""F2 · Align the measured cycling clock to the RPT observations, and audit it.

Uses the compact arrays cached by F1 (`_cycle_ts` as int64 epoch-ns,
`_cum_ah_ch`, `_cum_ah_dis`), so the 10.2 GB archive is parsed exactly once.

Alignment uses ABSOLUTE datetimes on both sides, never the relative day axes,
because the RPT campaign and the cycling campaign need not share a t0.

For each (cell, RPT index) it records the measured exposure accumulated BEFORE
that RPT:
    cum_cycles   number of completed cycles strictly before the RPT start
    cum_ah_ch    cumulative measured charge throughput (Ah)
    cum_ah_dis   cumulative measured discharge throughput (Ah)
    day          calendar day from the cell's first RPT (the axis used in D/E)

Audit checks the data gate asks for:
  A1 RPT count per cell vs cycling record presence
  A2 RPTs that precede the first cycling record
  A3 cycles-per-day, per cell and per condition (is the clock a rescaling?)
  A4 gaps between consecutive cycle timestamps
  A5 duplicate cycle timestamps
  A6 cross-condition spread of cum_cycles at a FIXED calendar day
  A7 measured Ah per cycle vs the 0.250 Ah rated capacity

Run remotely.
"""
import os
import json
import pickle
import re
import zipfile

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO
RAW_RPT = C.RAW_ISU


def load_rpt_absolute():
    """Same admission filter as D_common.load_isu, but keep absolute datetimes."""
    z = zipfile.ZipFile(RAW_RPT)
    cells = {}
    for n in sorted(x for x in z.namelist() if x.lower().endswith(".json")):
        name = n.split("/")[-1].replace(".json", "")
        if not re.match(r"G(\d+)C(\d+)", name):
            continue
        try:
            dd = json.loads(json.loads(z.read(n).decode("utf-8")))
        except Exception:
            continue
        cap = dd.get("capacity_discharge_C_5") or dd.get("capacity_discharge_C_2")
        ts = (dd.get("start_stop_time") or {}).get("start") or []
        if not isinstance(cap, list) or len(cap) < 4:
            continue
        v = []
        for x in cap:
            try:
                v.append(float(x))
            except Exception:
                v.append(np.nan)
        v = np.array(v, float)
        L = min(len(v), len(ts)) if ts else 0
        if L < 4:
            continue
        t = [pd.to_datetime(x, errors="coerce") for x in ts[:L]]
        if not all(pd.notna(x) for x in t):
            continue
        ref = np.nanmax(v[:L])
        if not np.isfinite(ref) or ref <= 0:
            continue
        soh = v[:L] / ref
        b = np.where(soh <= C.EOL_SOH)[0]
        if b.size == 0:
            continue
        k = int(b[0])
        if k == 0:
            continue
        cells[name] = dict(cond=int(re.match(r"G(\d+)", name).group(1)),
                           t=np.array([x.value for x in t], dtype="int64"),
                           soh=soh,
                           L=float((t[k - 1] - t[0]).total_seconds() / 86400.0),
                           U=float((t[k] - t[0]).total_seconds() / 86400.0))
    return cells


def main():
    with open(os.path.join(OUT, "F1_cycling_arrays.pkl"), "rb") as f:
        cyc = pickle.load(f)
    with open(os.path.join(OUT, "F1_cycling_cells.csv"), "rb") as f:
        F1 = pd.read_csv(f)
    rpt = load_rpt_absolute()
    stress = C.load_stress()
    print("RPT cells: %d | cycling cells: %d" % (len(rpt), len(cyc)))

    rows, audit = [], []
    for cell, info in sorted(cyc.items()):
        if cell not in rpt:
            continue
        ts = np.asarray(info.get("_cycle_ts", []), dtype="int64")
        if ts.size < 2:
            audit.append(dict(cell=cell, error="too few cycle timestamps"))
            continue
        days = (ts - ts[0]) / 86400e9
        cum_ch = np.asarray(info.get("_cum_ah_ch", []), float)
        cum_dis = np.asarray(info.get("_cum_ah_dis", []), float)
        gaps = np.diff(days)

        # per-cycle Ah medians straight from the increments
        inc_ch = np.diff(np.concatenate([[0.0], cum_ch])) if cum_ch.size else np.array([])
        inc_dis = np.diff(np.concatenate([[0.0], cum_dis])) if cum_dis.size else np.array([])

        audit.append(dict(
            cell=cell, cond=rpt[cell]["cond"], error="",
            n_cycles=int(ts.size), span_days=float(days[-1]),
            cycles_per_day=float(ts.size / days[-1]) if days[-1] > 0 else np.nan,
            gap_med_days=float(np.median(gaps)) if gaps.size else np.nan,
            gap_max_days=float(gaps.max()) if gaps.size else np.nan,
            n_dup_ts=int((gaps == 0).sum()), n_neg_ts=int((gaps < 0).sum()),
            med_ah_ch=float(np.median(inc_ch[inc_ch > 0])) if (inc_ch > 0).any() else np.nan,
            med_ah_dis=float(np.median(inc_dis[inc_dis > 0])) if (inc_dis > 0).any() else np.nan,
            sum_ah_ch=float(cum_ch[-1]) if cum_ch.size else np.nan,
            sum_ah_dis=float(cum_dis[-1]) if cum_dis.size else np.nan))

        t_rpt = rpt[cell]["t"]
        for k, tk in enumerate(t_rpt):
            j = int(np.searchsorted(ts, tk, side="left"))
            rows.append(dict(
                cell=cell, cond=rpt[cell]["cond"], rpt_idx=k,
                day=float((tk - t_rpt[0]) / 86400e9),
                soh=float(rpt[cell]["soh"][k]),
                cum_cycles=int(j),
                cum_ah_ch=float(cum_ch[j - 1]) if (j > 0 and cum_ch.size >= j) else 0.0,
                cum_ah_dis=float(cum_dis[j - 1]) if (j > 0 and cum_dis.size >= j) else 0.0,
                cyc_day_at_rpt=float(days[j - 1]) if j > 0 else np.nan,
                L=rpt[cell]["L"], U=rpt[cell]["U"]))

    A = pd.DataFrame(audit)
    R = pd.DataFrame(rows)
    A.to_csv(os.path.join(OUT, "F2_cell_audit.csv"), index=False)
    R.to_csv(os.path.join(OUT, "F2_rpt_alignment.csv"), index=False)

    print("\n=== A1/A2 alignment ===")
    print("cells with cycling+RT paired: %d | RPT rows: %d" % (len(A), len(R)))
    print("RPTs with zero preceding cycles: %d (%.2f%%)" % (
        int((R.cum_cycles == 0).sum()), 100 * (R.cum_cycles == 0).mean()))

    print("\n=== A3 cycles per day ===")
    print(A.cycles_per_day.describe().to_string())

    print("\n=== A4/A5 gaps and duplicates ===")
    print("  cells with duplicated cycle timestamps: %d" % int((A.n_dup_ts > 0).sum()))
    print("  cells with non-monotone timestamps    : %d" % int((A.n_neg_ts > 0).sum()))
    print("  median gap (days) across cells        : %.4f" % A.gap_med_days.median())
    print("  max gap (days) p95                    : %.3f" % A.gap_max_days.quantile(.95))

    print("\n=== A6 cross-condition spread of cum_cycles at a FIXED calendar day ===")
    cond_of = A.set_index("cell").cond
    for day in (21, 35, 49, 63):
        sub = R[R.day <= day].groupby("cell").cum_cycles.max()
        med = sub.groupby(cond_of.reindex(sub.index)).median()
        print("  day<=%-3d  cum_cycles across conditions: min %6.0f  median %6.0f  max %6.0f  ratio %.2fx" % (
            day, med.min(), med.median(), med.max(), med.max() / max(med.min(), 1)))

    print("\n=== A7 measured Ah per cycle vs rated 0.250 Ah ===")
    print("  median measured charge Ah per cycle   : %.4f" % A.med_ah_ch.median())
    print("  median measured discharge Ah per cycle: %.4f" % A.med_ah_dis.median())
    print("  -> partial-DoD conditions must fall below the rated capacity")

    print("\n=== cross-check: measured cum_cycles vs nominal 24/(1/Cc+1/Cd) * day ===")
    if len(R):
        r = R.dropna(subset=["cum_cycles"])
        r = r[r.day > 0]
        if len(r):
            nom = r.cond.map(lambda g: 24.0 / (1.0 / stress.loc[g, "charge_C"]
                                               + 1.0 / stress.loc[g, "discharge_C"])) * r.day
            ok = np.isfinite(nom) & (nom > 0) & (r.cum_cycles > 0)
            if ok.any():
                ratio = (r.cum_cycles[ok] / nom[ok])
                print("  measured / nominal cycles: median %.3f  IQR [%.3f, %.3f]" % (
                    ratio.median(), ratio.quantile(.25), ratio.quantile(.75)))
                print("  (1.0 would mean the nominal formula is exact; deviation is real)")
    print("\nwrote F2_cell_audit.csv / F2_rpt_alignment.csv")


if __name__ == "__main__":
    main()
