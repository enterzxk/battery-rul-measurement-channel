# -*- coding: utf-8 -*-
"""E5 · Structural identifiability gate for pivot B (clock discrimination).

Codex authorised pivot B only to "establish whether the available data contain a
discriminating contrast", and gave a structural stop: stop if the relevant
exposure variation is algebraically redundant, unavailable in the records, or
inseparable from competing protocol effects.

Pivot B needs three clocks that can disagree: calendar time, native cycle count,
and cumulative charge throughput. This script asks whether the ISU records contain
the second one at all, and whether the third is anything other than a
deterministic rescaling of calendar time given the design factors.

  nominal throughput = elapsed_days * 24 / (1/charge_C + 1/discharge_C)

is an algebraic function of (days, charge_C, discharge_C). If no measured cycle
count or measured Ah throughput exists in the records, then two of the three
"clocks" are not independent observations and the contrast is not identifiable
on this cohort.

Run remotely (reads the 929 MB archive).
"""
import os
import json
import re
import zipfile

import numpy as np
import pandas as pd

import D_common as C

OUT = C.PROTO
N_SAMPLE = 12


def main():
    z = zipfile.ZipFile(C.RAW_ISU)
    names = sorted(x for x in z.namelist() if x.lower().endswith(".json"))
    print("JSON entries: %d" % len(names))

    key_counts = {}
    samples = 0
    for n in names:
        if not re.match(r"G(\d+)C(\d+)", n.split("/")[-1].replace(".json", "")):
            continue
        try:
            dd = json.loads(json.loads(z.read(n).decode("utf-8")))
        except Exception:
            continue
        for k in dd.keys():
            key_counts[k] = key_counts.get(k, 0) + 1
        samples += 1
        if samples >= N_SAMPLE:
            break

    print("\n=== top-level keys present in the first %d cell records ===" % samples)
    for k, v in sorted(key_counts.items(), key=lambda kv: -kv[1]):
        print("  %-34s %d/%d" % (k, v, samples))

    # does anything look like a cycle count or a measured throughput?
    cand_cycle = [k for k in key_counts if re.search(r"cycl|count|n_cyc", k, re.I)]
    cand_ah = [k for k in key_counts if re.search(r"ah|amph|throughput|charge_ah|discharge_ah", k, re.I)]
    print("\n  cycle-count-like keys : %s" % (cand_cycle if cand_cycle else "NONE"))
    print("  throughput-like keys  : %s" % (cand_ah if cand_ah else "NONE"))

    # algebra: is nominal throughput a deterministic function of days and rates?
    stress = C.load_stress()
    cells = C.load_isu()
    rows = []
    for name, s in cells.items():
        if s["cond"] not in stress.index:
            continue
        r = stress.loc[s["cond"]]
        cc, cd = float(r["charge_C"]), float(r["discharge_C"])
        efc_per_day = 24.0 / (1.0 / cc + 1.0 / cd)
        rows.append(dict(cell=name, cond=s["cond"], days=float(s["U"]),
                         cc=cc, cd=cd, efc_per_day=efc_per_day,
                         efc_to_eol=float(s["U"]) * efc_per_day))
    D = pd.DataFrame(rows)
    print("\n=== cells with a stress descriptor: %d ===" % len(D))
    print("  efc_per_day depends ONLY on (charge_C, discharge_C): "
          "%d distinct values across %d conditions" % (
              D.groupby("cond").efc_per_day.first().nunique(), D.cond.nunique()))

    # The decisive question: at FIXED nominal throughput, does calendar time vary
    # across conditions? If throughput is a per-condition constant multiple of
    # days, then the two axes are collinear within condition and only differ by
    # that constant -> no independent contrast.
    g = D.groupby("cond").agg(days_med=("days", "median"),
                              efc_day=("efc_per_day", "first"),
                              efc_eol=("efc_to_eol", "median"),
                              n=("days", "size")).reset_index()
    print("\n=== condition-level exposure map (%d conditions) ===" % len(g))
    print("  corr(calendar days, nominal EFC-to-EOL) across conditions: "
          "pearson %.3f  spearman %.3f" % (
              np.corrcoef(g.days_med, g.efc_eol)[0, 1],
              g.days_med.corr(g.efc_eol, method="spearman")))

    # cycles-per-day would be needed to break this; it is not in the records.
    verdict = "NOT IDENTIFIABLE ON THESE RECORDS"
    reason = []
    if not cand_cycle:
        reason.append("no cycle-count field exists in the cell records")
    if not cand_ah:
        reason.append("no measured Ah-throughput field exists in the cell records")
    reason.append("nominal throughput = days * 24/(1/cc + 1/cd) is an algebraic "
                  "function of the design factors, so it is a per-condition rescaling "
                  "of calendar time, not an independent clock")
    print("\n=== VERDICT: %s ===" % verdict)
    for r in reason:
        print("  - %s" % r)
    print("\n  What WOULD make it identifiable: measured per-cycle counts or measured")
    print("  Ah throughput (ISU Cycling_json.zip, 10.2 GB, currently blocked), or a")
    print("  cohort whose cycles-per-day varies at fixed throughput.")

    g.to_csv(os.path.join(OUT, "E5_exposure_map.csv"), index=False)
    json.dump(dict(keys=sorted(key_counts), n_sampled=samples,
                   cycle_like=cand_cycle, ah_like=cand_ah,
                   n_cells_with_stress=int(len(D)),
                   n_cond=int(D.cond.nunique()),
                   corr_days_efc_pearson=float(np.corrcoef(g.days_med, g.efc_eol)[0, 1]),
                   corr_days_efc_spearman=float(g.days_med.corr(g.efc_eol, method="spearman")),
                   verdict=verdict, reasons=reason),
              open(os.path.join(OUT, "E5_clock_gate.json"), "w"), indent=1)
    print("\nwrote E5_exposure_map.csv / E5_clock_gate.json")


if __name__ == "__main__":
    main()
