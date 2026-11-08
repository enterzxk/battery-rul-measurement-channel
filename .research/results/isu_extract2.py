# -*- coding: utf-8 -*-
import json, zipfile, numpy as np, re, time
Z = r"E:\桌面\rul\data\external\isu_raw\RPT_json.zip"
OUT = r"C:\Users\Administrator\AppData\Local\Temp\isu_table.npz"
z = zipfile.ZipFile(Z)
names = sorted(n for n in z.namelist() if n.lower().endswith(".json"))
print("cells:", len(names), flush=True)

def clean(x):
    if not isinstance(x, (list, tuple)): return np.array([], float)
    out = []
    for v in x:
        try: out.append(float(v))
        except Exception: out.append(np.nan)
    return np.array(out, float)

rows, skipped = [], 0
t0 = time.time()
for i, n in enumerate(names):
    cell = n.split("/")[-1].replace(".json", "")
    m = re.match(r"G(\d+)C(\d+)", cell)
    if not m: continue
    grp = int(m.group(1))
    try:
        d = json.loads(json.loads(z.read(n).decode("utf-8")))
        cap2 = clean(d.get("capacity_discharge_C_2"))
        cap5 = clean(d.get("capacity_discharge_C_5"))
        chg2 = clean(d.get("capacity_charge_C_2"))
        chg5 = clean(d.get("capacity_charge_C_5"))
    except Exception:
        skipped += 1; continue
    L = min(len(cap2), len(cap5), len(chg2), len(chg5))
    if L < 4: skipped += 1; continue
    cap2 = cap2[:L]
    if not np.isfinite(cap2).any(): skipped += 1; continue
    ref = np.nanmax(cap2)
    if not np.isfinite(ref) or ref <= 0: skipped += 1; continue
    soh = cap2 / ref
    for r in range(L):
        rows.append((grp, r, cap2[r], cap5[r], chg2[r], chg5[r], soh[r], cell))
    if (i + 1) % 50 == 0:
        print("  %d/%d  %.0fs" % (i + 1, len(names), time.time() - t0), flush=True)

arr = np.array([[r[0], r[1], r[2], r[3], r[4], r[5], r[6]] for r in rows], float)
cells = np.array([r[7] for r in rows])
np.savez(OUT, X=arr, cells=cells)
print("\nrows: %d  cells: %d  groups: %d  skipped: %d" % (
    len(rows), len(np.unique(cells)), len(np.unique(arr[:, 0])), skipped))
print("SOH range %.3f..%.3f" % (np.nanmin(arr[:, 6]), np.nanmax(arr[:, 6])))
print("elapsed %.0fs" % (time.time() - t0))
