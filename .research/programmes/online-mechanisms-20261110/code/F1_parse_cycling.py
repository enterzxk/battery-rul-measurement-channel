# -*- coding: utf-8 -*-
"""F1 · Parse the official ISU-ILCC Cycling_json.zip into a measured physical clock.

Source of truth for the schema (all verified from the official release, v2,
published 2023-12-21, DOI 10.25380/iastate.22582234.v2):

  README_V2.0.pdf §4.3 "Structure of cycling data":
      capacity_discharge  -> Python list, one entry per CYCLE, Ah
      capacity_charge     -> Python list, one entry per CYCLE, Ah
      QV_discharge/charge -> per-cycle Q, V, E, I, t
      start_stop_time     -> start/stop per WEEK of cycling
      time_series_discharge / time_series_charge -> start/stop per CYCLE

  process_data.py convert_cycling_to_dict() confirms the double-encoded JSON
  (json.loads(json.load(file))) and that start_stop_time / time_series entries
  may be the literal string '[]' when absent.

What this produces, per cell:
  * n_cycles        = number of measured cycles (from capacity_charge length,
                      cross-checked against time_series_charge length)
  * cum_ah_charge   = cumulative MEASURED charge throughput (Ah), from the cycler
  * cum_ah_discharge= cumulative MEASURED discharge throughput (Ah)
  * calendar span   = from the per-cycle timestamps

and, per (cell, RPT index), the value of each clock at that observation:
  day, cum_cycles, cum_ah_charge, cum_ah_discharge

Nothing here is inferred from nominal C-rates. If a quantity is unavailable for a
cell it is left NaN and counted, never fabricated.

Run remotely (reads the 10.2 GB archive). Writes a compact pickle + CSVs.
"""
import os
import io
import json
import re
import sys
import zipfile
import pickle
from datetime import datetime

import numpy as np
import pandas as pd

OUT = os.environ.get("DLINE_PROTO", ".")
ZIP = "/home/user/dline/data/Cycling_json.zip"
NPROC = int(os.environ.get("F1_NPROC", "12"))


def to_float(x):
    """Per-cycle capacity entry -> float, or NaN. Never invents a value."""
    if x is None:
        return np.nan
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        if s in ("", "[]", "nan", "None"):
            return np.nan
        try:
            return float(s)
        except Exception:
            return np.nan
    if isinstance(x, (list, tuple, np.ndarray)):
        vals = [to_float(v) for v in x]
        vals = [v for v in vals if np.isfinite(v)]
        return float(np.sum(vals)) if vals else np.nan
    return np.nan


def to_dt(x):
    if isinstance(x, str):
        s = x.strip()
        if s in ("", "[]", "nan", "None"):
            return None
        try:
            return np.datetime64(pd.to_datetime(s))
        except Exception:
            return None
    return None


def parse_one(args):
    name, release = args
    try:
        z = zipfile.ZipFile(ZIP)
        raw = z.read("%s/%s.json" % (release, name))
        z.close()
        d = json.loads(json.loads(raw.decode("utf-8")))
    except Exception as e:
        return dict(cell=name, release=release, error="%s: %s" % (type(e).__name__, e))

    rec = dict(cell=name, release=release, error="")
    cap_ch = d.get("capacity_charge") or []
    cap_dis = d.get("capacity_discharge") or []
    tsc = (d.get("time_series_charge") or {}).get("start") or []
    tsd = (d.get("time_series_discharge") or {}).get("start") or []
    sst = d.get("start_stop_time") or {}

    ch = np.array([to_float(x) for x in cap_ch], float) if len(cap_ch) else np.array([])
    dis = np.array([to_float(x) for x in cap_dis], float) if len(cap_dis) else np.array([])

    rec["n_cap_charge"] = int(len(ch))
    rec["n_cap_discharge"] = int(len(dis))
    rec["n_ts_charge"] = int(len(tsc))
    rec["n_ts_discharge"] = int(len(tsd))
    rec["n_weeks"] = int(len(sst.get("start") or []))

    rec["n_nan_charge"] = int(np.isnan(ch).sum()) if len(ch) else 0
    rec["n_nan_discharge"] = int(np.isnan(dis).sum()) if len(dis) else 0

    # measured cumulative throughput
    rec["sum_ah_charge"] = float(np.nansum(ch)) if len(ch) else np.nan
    rec["sum_ah_discharge"] = float(np.nansum(dis)) if len(dis) else np.nan
    rec["med_ah_charge"] = float(np.nanmedian(ch)) if len(ch) and np.isfinite(ch).any() else np.nan
    rec["med_ah_discharge"] = float(np.nanmedian(dis)) if len(dis) and np.isfinite(dis).any() else np.nan

    # per-cycle timestamps -> calendar clock
    ct = [to_dt(x) for x in tsc]
    ct = [x for x in ct if x is not None]
    if ct:
        t0 = ct[0]
        days = np.array([(x - t0) / np.timedelta64(1, "D") for x in ct], float)
        rec["first_cycle_dt"] = str(t0)
        rec["last_cycle_dt"] = str(ct[-1])
        rec["cycle_span_days"] = float(days[-1]) if len(days) else np.nan
        rec["cycle_days_nonmonotone"] = int((np.diff(days) < -1e-9).sum()) if len(days) > 1 else 0
        rec["_cycle_days"] = days
        # absolute per-cycle timestamps as int64 ns, so downstream steps never
        # need to re-parse the 10.2 GB archive
        rec["_cycle_ts"] = np.array(
            [x.astype("datetime64[ns]").astype("int64") for x in ct], dtype="int64")
    else:
        rec["first_cycle_dt"] = ""
        rec["last_cycle_dt"] = ""
        rec["cycle_span_days"] = np.nan
        rec["cycle_days_nonmonotone"] = -1
        rec["_cycle_days"] = np.array([])
        rec["_cycle_ts"] = np.array([], dtype="int64")

    # cumulative measured throughput aligned to the per-cycle index
    if len(ch) and np.isfinite(ch).any():
        rec["_cum_ah_ch"] = np.nancumsum(np.where(np.isfinite(ch), ch, 0.0))
    else:
        rec["_cum_ah_ch"] = np.array([])
    if len(dis) and np.isfinite(dis).any():
        rec["_cum_ah_dis"] = np.nancumsum(np.where(np.isfinite(dis), dis, 0.0))
    else:
        rec["_cum_ah_dis"] = np.array([])

    # week-level span, as an independent cross-check
    wk = [to_dt(x) for x in (sst.get("start") or [])]
    wk = [x for x in wk if x is not None]
    rec["week_span_days"] = float((wk[-1] - wk[0]) / np.timedelta64(1, "D")) if len(wk) > 1 else np.nan
    rec["n_weeks_parsed"] = int(len(wk))
    return rec


def main():
    z = zipfile.ZipFile(ZIP)
    names = [n for n in z.namelist() if n.lower().endswith(".json")]
    z.close()
    items = []
    for n in names:
        parts = n.split("/")
        if len(parts) < 2:
            continue
        rel = "/".join(parts[:-1])
        cell = parts[-1].replace(".json", "")
        if not re.match(r"G\d+C\d+$", cell):
            continue
        items.append((cell, rel))
    print("cycling entries: %d  (releases: %s)" % (
        len(items), sorted({r for _, r in items})), flush=True)

    from multiprocessing import Pool
    with Pool(NPROC) as p:
        recs = []
        for i, r in enumerate(p.imap_unordered(parse_one, items, chunksize=1)):
            recs.append(r)
            if (i + 1) % 25 == 0:
                print("  parsed %d/%d" % (i + 1, len(items)), flush=True)
    D = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in recs])
    D = D.sort_values("cell").reset_index(drop=True)

    print("\n=== parse summary ===")
    print("cells: %d | parse errors: %d" % (len(D), int((D.error != "").sum())))
    if (D.error != "").any():
        print(D[D.error != ""][["cell", "release", "error"]].head(10).to_string(index=False))
    for c in ["n_cap_charge", "n_cap_discharge", "n_ts_charge", "n_weeks",
              "cycle_span_days", "sum_ah_charge", "sum_ah_discharge"]:
        s = pd.to_numeric(D[c], errors="coerce")
        print("  %-18s min %10.3f  med %10.3f  max %10.3f  nan %d" % (
            c, s.min(), s.median(), s.max(), int(s.isna().sum())))
    print("  cycle_days_nonmonotone>0: %d cells" % int((D.cycle_days_nonmonotone > 0).sum()))
    print("  release counts: %s" % D.release.value_counts().to_dict())

    D.to_csv(os.path.join(OUT, "F1_cycling_cells.csv"), index=False)
    keep = {r["cell"]: {k: v for k, v in r.items() if k.startswith("_")} | {
        "release": r["release"], "error": r["error"]} for r in recs}
    with open(os.path.join(OUT, "F1_cycling_arrays.pkl"), "wb") as f:
        pickle.dump(keep, f, protocol=4)
    print("\nwrote F1_cycling_cells.csv and F1_cycling_arrays.pkl")


if __name__ == "__main__":
    main()
