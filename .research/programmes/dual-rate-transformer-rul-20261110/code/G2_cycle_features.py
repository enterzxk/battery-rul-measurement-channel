# -*- coding: utf-8 -*-
"""G2 · Extract LEGAL per-cycle operating features (no capacity information).

Why this exists: Gate 1's E1-A only added two cumulative SCALARS (cycle count and
cumulative Ah). That does not test the brief's H1, which is about per-cycle
OPERATING information. The brief's own arms E1-B (legal per-cycle features) and
E1-C (sequence representation) are the ones that actually test it, and the brief
permits exactly one mechanism-justified correction.

What counts as legal: the archive records, per cycle, the start and stop times of
the charge and discharge steps. Durations and rests derived from those timestamps
carry no capacity information. They are standard BMS-visible signals.

What is EXCLUDED here on purpose: capacity_charge / capacity_discharge. Those are
measured delivered capacity ~ DoD x cell capacity, so they are health
measurements, not free operating signals. They are kept in the separate CAPACITY
arm and never enter these features.

Per (cell, RPT interval k) this writes:
    n_cyc        cycles in the interval
    ch_dur_med   median charge-step duration (h)
    dis_dur_med  median discharge-step duration (h)
    cyc_dur_med  median cycle duration, charge start to discharge stop (h)
    rest_med     median rest between discharge stop and next charge start (h)
    cyc_dur_trend  OLS slope of cycle duration over cycle index within the interval
    cyc_dur_first / cyc_dur_last   first and last cycle duration in the interval

Run remotely (reads the 10.2 GB archive once).
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
ZIP = "/home/user/dline/data/Cycling_json.zip"
RAW_RPT = "/home/user/dline/data/RPT_json.zip"
NPROC = int(os.environ.get("G2_NPROC", "6"))


def to_ns(x):
    if isinstance(x, str):
        s = x.strip()
        if s in ("", "[]", "nan", "None"):
            return None
        try:
            return int(pd.Timestamp(s).value)
        except Exception:
            return None
    return None


def parse_cell(args):
    cell, release = args
    try:
        z = zipfile.ZipFile(ZIP)
        raw = z.read("%s/%s.json" % (release, cell))
        z.close()
        d = json.loads(json.loads(raw.decode("utf-8")))
    except Exception as e:
        return cell, None, str(e)

    tsc = d.get("time_series_charge") or {}
    tsd = d.get("time_series_discharge") or {}
    cs = [to_ns(x) for x in (tsc.get("start") or [])]
    ce = [to_ns(x) for x in (tsc.get("stop") or [])]
    ds = [to_ns(x) for x in (tsd.get("start") or [])]
    de = [to_ns(x) for x in (tsd.get("stop") or [])]
    n = min(len(cs), len(ce), len(ds), len(de))
    if n < 2:
        return cell, None, "too few cycles"

    H = 3600e9
    ch_dur, dis_dur, cyc_dur, rest = [], [], [], []
    for i in range(n):
        if cs[i] is None or ce[i] is None or ds[i] is None or de[i] is None:
            ch_dur.append(np.nan); dis_dur.append(np.nan)
            cyc_dur.append(np.nan); rest.append(np.nan)
            continue
        ch_dur.append((ce[i] - cs[i]) / H)
        dis_dur.append((de[i] - ds[i]) / H)
        cyc_dur.append((de[i] - cs[i]) / H)
        if i > 0 and de[i - 1] is not None:
            rest.append((cs[i] - de[i - 1]) / H)
        else:
            rest.append(np.nan)
    return cell, dict(cyc_start=np.array([x if x is not None else -1 for x in cs], dtype="int64"),
                      ch_dur=np.array(ch_dur, float),
                      dis_dur=np.array(dis_dur, float),
                      cyc_dur=np.array(cyc_dur, float),
                      rest=np.array(rest, float)), ""


def load_rpt_times():
    z = zipfile.ZipFile(RAW_RPT)
    out = {}
    for n in sorted(x for x in z.namelist() if x.lower().endswith(".json")):
        name = n.split("/")[-1].replace(".json", "")
        if not re.match(r"G\d+C\d+$", name):
            continue
        try:
            dd = json.loads(json.loads(z.read(n).decode("utf-8")))
        except Exception:
            continue
        ts = (dd.get("start_stop_time") or {}).get("start") or []
        t = [to_ns(x) for x in ts]
        t = [x for x in t if x is not None]
        if len(t) >= 3:
            out[name] = np.array(t, dtype="int64")
    return out


def main():
    z = zipfile.ZipFile(ZIP)
    items = []
    for n in z.namelist():
        if not n.lower().endswith(".json"):
            continue
        parts = n.split("/")
        cell = parts[-1].replace(".json", "")
        if re.match(r"G\d+C\d+$", cell):
            items.append((cell, "/".join(parts[:-1])))
    z.close()
    print("cycling entries: %d" % len(items), flush=True)

    from multiprocessing import Pool
    per = {}
    errs = 0
    with Pool(NPROC) as p:
        for i, (cell, payload, err) in enumerate(p.imap_unordered(parse_cell, items, chunksize=1)):
            if payload is None:
                errs += 1
                continue
            per[cell] = payload
            if (i + 1) % 40 == 0:
                print("  parsed %d/%d" % (i + 1, len(items)), flush=True)
    print("parsed %d cells, %d errors" % (len(per), errs))

    rpt = load_rpt_times()
    print("RPT cells with >=3 timestamps: %d" % len(rpt))

    rows = []
    for cell, d in per.items():
        if cell not in rpt:
            continue
        rt = rpt[cell]
        cs = d["cyc_start"]
        for k in range(1, len(rt)):
            lo, hi = rt[k - 1], rt[k]
            m = (cs >= lo) & (cs < hi)
            if m.sum() < 2:
                continue
            cd = d["cyc_dur"][m]
            ok = np.isfinite(cd)
            if ok.sum() < 2:
                continue
            idx = np.arange(ok.sum())
            slope = float(np.polyfit(idx, cd[ok], 1)[0]) if ok.sum() >= 3 else np.nan
            rows.append(dict(
                cell=cell, rpt_idx=int(k),
                n_cyc=int(m.sum()),
                ch_dur_med=float(np.nanmedian(d["ch_dur"][m])),
                dis_dur_med=float(np.nanmedian(d["dis_dur"][m])),
                cyc_dur_med=float(np.nanmedian(cd[ok])),
                rest_med=float(np.nanmedian(d["rest"][m])),
                cyc_dur_trend=slope,
                cyc_dur_first=float(cd[ok][0]),
                cyc_dur_last=float(cd[ok][-1])))
    F = pd.DataFrame(rows)
    print("interval feature rows: %d | cells %d" % (len(F), F.cell.nunique()))
    print(F[["n_cyc", "ch_dur_med", "dis_dur_med", "cyc_dur_med", "rest_med"]].describe().to_string())
    F.to_csv(os.path.join(PROTO, "G2_cycle_features.csv"), index=False)
    json.dump(dict(n_cells=int(F.cell.nunique()), n_rows=int(len(F)), errors=int(errs)),
              open(os.path.join(PROTO, "G2_cycle_features.json"), "w"), indent=1)
    print("\nwrote G2_cycle_features.csv")


if __name__ == "__main__":
    main()
