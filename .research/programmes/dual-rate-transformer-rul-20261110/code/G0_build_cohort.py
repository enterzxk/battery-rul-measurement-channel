# -*- coding: utf-8 -*-
"""G0 · Corrected cohort construction (fixes two protocol bugs found by audit).

BUG 1 (loader): for every cell in conditions 20-29, RPT record index 5 is the
literal string '[]' in start[5]/stop[5] and capacity_discharge_C_5[5] is
non-numeric. D_common.load_isu used `if not all(pd.notna(x) for x in t): continue`,
which dropped the ENTIRE CELL for one empty record. Because the defect is shared
across a block of conditions, ten whole conditions vanished from every derived
table (that is why Stage D/E/F reported 53 conditions, not 63).
FIX: drop the offending RECORD, keep the CELL. Recovers 40 cells / 10 conditions.

BUG 2 (condition table): results/isu_conditions.csv `mean_DoD_pct` is not
reproducible from the measured throughput for 21 of 53 conditions
(measured/tabulated ratio 0.068-0.559). The archive measurement is self-consistent
(charge and discharge agree), so the TABLE is the suspect quantity.
FIX: re-derive DoD from measurements. Per the audit, median(capacity_charge /
concurrent capacity) equals the protocol DoD, so a measured DoD is
    DoD_meas = median(per-cycle capacity_charge) / (first-RPT C/5 capacity)
and is reported per cell and per condition alongside the tabulated value.

ALSO: SOH is normalised against the FIRST RPT explicitly (not max over all RPTs),
removing a post-hoc dependency; the audit measured the impact as tiny but it
should still be removed.

Output: protocol/G0_cohort.csv  (per cell x RPT: soh, day, cum_cycles, cum_ah,
L/U in all three clocks, DoD_meas, and the tabulated DoD for comparison)
        protocol/G0_conditions.csv
Run remotely.
"""
import os
import json
import pickle
import re
import zipfile

import numpy as np
import pandas as pd

PROTO = os.environ.get("DLINE_PROTO", "/home/user/dline/prog/protocol")
RES = os.environ.get("DLINE_RES", "/home/user/dline/prog/results")
RAW_RPT = "/home/user/dline/data/RPT_json.zip"
THRESH = 0.80


def load_rpt_fixed():
    """Parse RPT records, dropping BAD RECORDS but keeping the cell."""
    z = zipfile.ZipFile(RAW_RPT)
    out, dropped = {}, {}
    for n in sorted(x for x in z.namelist() if x.lower().endswith(".json")):
        cell = n.split("/")[-1].replace(".json", "")
        if not re.match(r"G\d+C\d+$", cell):
            continue
        try:
            dd = json.loads(json.loads(z.read(n).decode("utf-8")))
        except Exception:
            continue
        cap = dd.get("capacity_discharge_C_5")
        if cap is None:
            cap = dd.get("capacity_discharge_C_2")
        ts = (dd.get("start_stop_time") or {}).get("start") or []
        if not isinstance(cap, list) or not isinstance(ts, list):
            continue
        nrec = min(len(cap), len(ts))
        keep_t, keep_c = [], []
        for i in range(nrec):
            t = pd.to_datetime(ts[i], errors="coerce")
            try:
                c = float(cap[i])
            except Exception:
                c = np.nan
            if pd.isna(t) or not np.isfinite(c) or c <= 0:
                continue
            keep_t.append(t)
            keep_c.append(c)
        dropped[cell] = nrec - len(keep_t)
        if len(keep_c) >= 3:
            out[cell] = dict(t=np.array([x.value for x in keep_t], dtype="int64"),
                             cap=np.array(keep_c, float),
                             cond=int(re.match(r"G(\d+)", cell).group(1)))
    return out, dropped


def main():
    with open(os.path.join(PROTO, "F1_cycling_arrays.pkl"), "rb") as f:
        cyc = pickle.load(f)
    rpt, dropped = load_rpt_fixed()
    print("RPT cells kept: %d (of 251) | total bad records dropped: %d" % (
        len(rpt), sum(dropped.values())))
    print("cells that lost >=1 record: %d" % sum(1 for v in dropped.values() if v > 0))
    print("  worst: %s" % sorted(((v, k) for k, v in dropped.items()), reverse=True)[:5])

    tab = pd.read_csv(os.path.join(RES, "isu_conditions.csv"))
    tab.columns = ["cond", "charge_C", "discharge_C", "mean_DoD_pct"]

    rows, cellinfo = [], []
    for cell, r in rpt.items():
        if cell not in cyc:
            continue
        ts = np.asarray(cyc[cell].get("_cycle_ts", []), dtype="int64")
        if ts.size < 2:
            continue
        cum_ch = np.asarray(cyc[cell].get("_cum_ah_ch", []), float)
        cum_dis = np.asarray(cyc[cell].get("_cum_ah_dis", []), float)

        cap = r["cap"]
        q0 = float(cap[0])                      # FIRST-RPT reference, explicit
        soh = cap / q0
        below = np.where(soh <= THRESH)[0]
        if below.size == 0:
            cellinfo.append(dict(cell=cell, cond=r["cond"], crossed=0))
            continue
        j = int(below[0])
        if j == 0:
            cellinfo.append(dict(cell=cell, cond=r["cond"], crossed=0))
            continue

        # measured DoD: median per-cycle charge Ah / first-RPT C/5 capacity
        inc = np.diff(np.concatenate([[0.0], cum_ch])) if cum_ch.size else np.array([])
        pos = inc[inc > 0]
        dod_meas = float(np.median(pos) / q0) if pos.size else np.nan

        days = (r["t"] - r["t"][0]) / 86400e9
        Ncum = np.array([int(np.searchsorted(ts, tk, side="left")) for tk in r["t"]])
        Ah = np.array([float(cum_ch[k - 1]) if (k > 0 and cum_ch.size >= k) else 0.0
                       for k in Ncum])
        Ahd = np.array([float(cum_dis[k - 1]) if (k > 0 and cum_dis.size >= k) else 0.0
                        for k in Ncum])

        cellinfo.append(dict(cell=cell, cond=r["cond"], crossed=1, eol_rpt=j,
                             q0=q0, dod_meas=dod_meas, n_rpt=len(cap),
                             n_cycles_end=int(Ncum[-1])))
        for k in range(len(cap)):
            rows.append(dict(cell=cell, cond=r["cond"], rpt_idx=k,
                             day=float(days[k]), soh=float(soh[k]),
                             cum_cycles=int(Ncum[k]), cum_ah_ch=float(Ah[k]),
                             cum_ah_dis=float(Ahd[k]), q0=q0, dod_meas=dod_meas,
                             L=float(days[j - 1]), U=float(days[j]),
                             N_L=int(Ncum[j - 1]), N_U=int(Ncum[j]),
                             eol_rpt=j))
    D = pd.DataFrame(rows)
    C = pd.DataFrame(cellinfo)
    C.to_csv(os.path.join(PROTO, "G0_cells.csv"), index=False)

    print("\n=== corrected cohort ===")
    print("cells with >=3 usable RPTs: %d | cells with an observed crossing: %d" % (
        len(C), int(C.crossed.sum())))
    print("conditions represented: %d" % D.cond.nunique())
    per = D.groupby("cond").cell.nunique()
    print("cells per condition: min %d median %.0f max %d" % (per.min(), per.median(), per.max()))
    for thr in (1, 2, 3, 4):
        print("  LOCO usable with >=%d cells/condition: %d" % (thr, int((per >= thr).sum())))

    # DoD reconciliation
    M = C[C.crossed == 1].groupby("cond").dod_meas.median().rename("dod_meas_med").reset_index()
    M = M.merge(tab, on="cond", how="left")
    M["tab_dod"] = M.mean_DoD_pct / 100.0
    M["ratio"] = M.dod_meas_med / M.tab_dod
    print("\n=== DoD reconciliation (measured vs tabulated) ===")
    print("  ratio measured/tabulated: median %.3f  IQR [%.3f, %.3f]" % (
        M.ratio.median(), M.ratio.quantile(.25), M.ratio.quantile(.75)))
    print("  conditions outside [0.6, 1.6]: %d of %d" % (
        int(((M.ratio < 0.6) | (M.ratio > 1.6)).sum()), len(M)))
    M.to_csv(os.path.join(PROTO, "G0_conditions.csv"), index=False)

    D.to_csv(os.path.join(PROTO, "G0_cohort.csv"), index=False)
    json.dump(dict(n_cells=int(len(C)), n_crossed=int(C.crossed.sum()),
                   n_cond=int(D.cond.nunique()),
                   cells_per_cond={int(k): int(v) for k, v in per.items()},
                   bad_records_dropped=int(sum(dropped.values())),
                   dod_ratio_median=float(M.ratio.median()),
                   dod_outside=int(((M.ratio < 0.6) | (M.ratio > 1.6)).sum())),
              open(os.path.join(PROTO, "G0_cohort.json"), "w"), indent=1, default=float)
    print("\nwrote G0_cohort.csv / G0_cells.csv / G0_conditions.csv")


if __name__ == "__main__":
    main()
