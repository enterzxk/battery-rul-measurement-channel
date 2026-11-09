# -*- coding: utf-8 -*-
"""Rebuild the ISU-ILCC lifetime table from the RAW release, fixing three
errors inherited from earlier probe files.

Errors being corrected:
  E1. A probe file (`_probe/isu_eol.csv`) classified 40 cells as right-censored
      and dropped them, so the B analysis silently used 211/251 cells and 53/63
      conditions. Direct check on the processed table shows ALL 248 parsed cells
      cross 80% SOH on every capacity channel. There is NO right-censoring.
  E2. That same file derived EOL from C/5 discharge capacity only.
  E3. The day axis was not reconstructed per RPT, so EOL in days was unavailable
      for the crossing itself.

This script reads the raw JSONs and produces, per cell:
  group, n_rpt, cap0, soh series, RPT index of first crossing, and the
  calendar timestamps of the bracketing observations (L and U) in days.

Source: E:\\桌面\\rul\\data\\external\\isu_raw\\RPT_json.zip (929 MB, 251 cells).
SOH definition frozen here: capacity_discharge_C_5 normalised by its own maximum
(the release's own reference), matching .research/results/isu_extract2.py.
"""
import os, json, zipfile, re
import numpy as np
import pandas as pd

RAW = r"E:\桌面\rul\data\external\isu_raw\RPT_json.zip"
OUT = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(OUT, "..", "protocol")
THRESH = 0.80

def to_float_list(x):
    if not isinstance(x, (list, tuple)): return np.array([], float)
    out = []
    for v in x:
        try: out.append(float(v))
        except Exception: out.append(np.nan)
    return np.array(out, float)

def to_dt_list(x):
    if not isinstance(x, (list, tuple)): return []
    return [pd.to_datetime(v, errors="coerce") for v in x]

z = zipfile.ZipFile(RAW)
names = sorted(n for n in z.namelist() if n.lower().endswith(".json"))
print("json files: %d" % len(names))

rows = []
bad = 0
for n in names:
    cell = n.split("/")[-1].replace(".json", "")
    m = re.match(r"G(\d+)C(\d+)", cell)
    if not m:
        continue
    grp = int(m.group(1))
    try:
        d = json.loads(json.loads(z.read(n).decode("utf-8")))
    except Exception:
        bad += 1; continue
    cap5 = to_float_list(d.get("capacity_discharge_C_5"))
    cap2 = to_float_list(d.get("capacity_discharge_C_2"))
    ts = d.get("start_stop_time", {}) or {}
    tstart = to_dt_list(ts.get("start"))
    cap = cap5 if cap5.size >= cap2.size else cap2
    use = "C5" if cap5.size >= cap2.size else "C2"
    L = min(len(cap), len(tstart)) if tstart else len(cap)
    if L < 3:
        bad += 1; continue
    cap = cap[:L]; tstart = tstart[:L]
    fin = np.isfinite(cap)
    if fin.sum() < 3:
        bad += 1; continue
    cap = np.where(fin, cap, np.nan)
    ref = np.nanmax(cap)
    if not np.isfinite(ref) or ref <= 0:
        bad += 1; continue
    soh = cap / ref
    # RPT index is the position in the chronological record
    idx = np.arange(L)
    below = np.where(soh <= THRESH)[0]
    below = below[np.isfinite(soh[below])]
    rec = dict(cell=cell, group=grp, n_rpt=int(L), channel=use,
               cap0=float(cap[0]), soh_min=float(np.nanmin(soh)),
               t_first=tstart[0], t_last=tstart[-1])
    if below.size == 0:
        rec.update(status="right_censored", rpt_L=np.nan, rpt_U=np.nan,
                   day_L=np.nan, day_U=np.nan, soh_L=np.nan, soh_U=np.nan)
    else:
        u = int(below[0])
        rec["status"] = "interval" if u > 0 else "left_of_first"
        rec["rpt_U"] = u
        rec["soh_U"] = float(soh[u])
        rec["day_U"] = (tstart[u] - tstart[0]).total_seconds() / 86400.0 if pd.notna(tstart[u]) else np.nan
        if u > 0:
            rec["rpt_L"] = u - 1
            rec["soh_L"] = float(soh[u - 1])
            rec["day_L"] = (tstart[u - 1] - tstart[0]).total_seconds() / 86400.0 if pd.notna(tstart[u - 1]) else np.nan
        else:
            rec["rpt_L"] = np.nan; rec["soh_L"] = np.nan; rec["day_L"] = np.nan
    rows.append(rec)

df = pd.DataFrame(rows)
print("parsed: %d cells   failed: %d" % (len(df), bad))
print("\nstatus counts:\n%s" % df.status.value_counts().to_string())
print("\nconditions: %d   cells per condition: %s" % (
    df.group.nunique(), dict(sorted(df.groupby("group").size().value_counts().items()))))
print("channel used: %s" % df.channel.value_counts().to_dict())
ok = df[df.status == "interval"].copy()
ok["width_rpt"] = ok.rpt_U - ok.rpt_L
ok["width_day"] = ok.day_U - ok.day_L
print("\ninterval cells: %d" % len(ok))
print("  width in RPT: median %.1f  (all == 1? %s)" % (ok.width_rpt.median(), bool((ok.width_rpt == 1).all())))
print("  width in days: median %.2f  IQR [%.2f, %.2f]" % (
    ok.width_day.median(), ok.width_day.quantile(.25), ok.width_day.quantile(.75)))
print("  relative width (days): median %.4f" % (ok.width_day / ok.day_U).median())

df.to_csv(os.path.join(PROTO, "isu_lifetime_raw.csv"), index=False)
ok.to_csv(os.path.join(PROTO, "isu_lifetime_interval.csv"), index=False)
print("\nwrote isu_lifetime_raw.csv / isu_lifetime_interval.csv")
