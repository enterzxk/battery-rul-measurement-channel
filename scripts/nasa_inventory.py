# -*- coding: utf-8 -*-
"""Inventory every cell in the NASA PCoE battery archive (nested zips)."""
import io, os, sys, zipfile, json
import numpy as np
import scipy.io as sio

ROOT = r"E:\桌面\rul\data\external\nasa_pcoe"
OUT = r"E:\桌面\rul\rul_v4_20261107\docs\nasa_inventory.json"

def walk_zip(path, prefix=""):
    """Yield (member_name, bytes_loader) for every .mat inside nested zips."""
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            name = info.filename
            if name.endswith("/"):
                continue
            if name.lower().endswith(".zip"):
                with z.open(info) as fh:
                    nested = fh.read()
                yield from walk_zip(io.BytesIO(nested), prefix + name + "::")
            elif name.lower().endswith(".mat"):
                with z.open(info) as fh:
                    yield (prefix + name, fh.read())

def summarize(raw, name):
    try:
        m = sio.loadmat(io.BytesIO(raw), squeeze_me=False, struct_as_record=False)
    except NotImplementedError:
        return {"file": name, "error": "v7.3 hdf5"}
    keys = [k for k in m if not k.startswith("__")]
    if not keys:
        return {"file": name, "error": "no var"}
    b = m[keys[0]][0, 0]
    cyc = b.cycle
    counts = {}
    eis_pts = []
    for c in cyc.ravel():
        t = str(c.type[0])
        counts[t] = counts.get(t, 0) + 1
        if t == "impedance":
            try:
                eis_pts.append(int(np.shape(c.data[0, 0].Battery_impedance)[0]))
            except Exception:
                eis_pts.append(0)
    return {
        "file": name,
        "var": keys[0],
        "charge": counts.get("charge", 0),
        "discharge": counts.get("discharge", 0),
        "impedance": counts.get("impedance", 0),
        "eis_freq_median": int(np.median(eis_pts)) if eis_pts else 0,
    }

rows = []
outer = os.path.join(ROOT, "NASA_5_Battery_Data_Set.zip")
for name, raw in walk_zip(outer):
    r = summarize(raw, name)
    rows.append(r)
    print(json.dumps(r, ensure_ascii=False), flush=True)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
print("TOTAL_CELLS", len(rows))
