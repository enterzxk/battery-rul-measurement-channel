# -*- coding: utf-8 -*-
"""NASA PCoE, v2: prefix features matched to the UConn design.

prefix : 50-bin discharge voltage curve + mean/std/min/max  (54 dims, same as UConn)
eis    : 48-point complex spectrum -> 12 real + 12 imag decimated + 6 derived shape stats
align  : each discharge cycle uses the most recent impedance measurement *before* it (causal)
"""
import io, os, zipfile, json, warnings, numpy as np
import scipy.io as sio
from sklearn.ensemble import HistGradientBoostingRegressor
warnings.filterwarnings("ignore")
ROOT = r"E:\桌面\rul\data\external\nasa_pcoe\NASA_5_Battery_Data_Set.zip"
OUT = r"C:\Users\Administrator\AppData\Local\Temp\nasa_v2.json"
CACHE = r"C:\Users\Administrator\AppData\Local\Temp\nasa_v2.npz"

def iter_mats():
    with zipfile.ZipFile(ROOT) as z:
        for info in z.infolist():
            if not info.filename.lower().endswith(".zip"): continue
            with z.open(info) as fh: buf = fh.read()
            with zipfile.ZipFile(io.BytesIO(buf)) as z2:
                for i2 in z2.infolist():
                    if i2.filename.lower().endswith(".mat"):
                        with z2.open(i2) as fh:
                            yield os.path.basename(i2.filename).replace(".mat", ""), fh.read()

def parse_cell(raw):
    m = sio.loadmat(io.BytesIO(raw), squeeze_me=False, struct_as_record=False)
    keys = [k for k in m if not k.startswith("__")]
    if not keys: return None
    b = m[keys[0]][0, 0]
    disch, eis = [], []
    for c in b.cycle.ravel():
        t = str(c.type[0])
        try: d = c.data[0, 0]
        except Exception: continue
        if t == "discharge":
            try:
                v = np.ravel(d.Voltage_measured).astype(float)
                cap = float(np.ravel(d.Capacity)[0])
                disch.append((v, cap))
            except Exception: pass
        elif t == "impedance":
            try:
                zc = np.ravel(d.Battery_impedance).astype(complex)
                if zc.size >= 20: eis.append(zc)
            except Exception: pass
    return disch, eis

def eis_feats(zc):
    n = zc.size
    idx = np.linspace(0, n - 1, 12).astype(int)
    re = np.real(zc)[idx]; im = -np.imag(zc)[idx]
    mag = np.abs(zc)
    return list(re) + list(im) + [
        float(np.max(-np.imag(zc))), float(np.argmax(-np.imag(zc))),
        float(np.real(zc)[0]), float(np.real(zc)[-1]),
        float(np.log10(mag.min() + 1e-9)), float(np.log10(mag.max() + 1e-9)),
    ]

def main():
    if os.path.exists(CACHE):
        z = np.load(CACHE, allow_pickle=True)
        A, C, y, cells = z["A"], z["C"], z["y"], z["cells"]
    else:
        rowsA, rowsC, ys, cs = [], [], [], []
        n_cells = 0
        for name, raw in iter_mats():
            p = parse_cell(raw)
            if p is None: continue
            disch, eis = p
            if len(disch) < 30 or len(eis) < 5: continue
            caps = np.array([c for _, c in disch], float)
            if not np.isfinite(caps[0]) or caps[0] <= 0: continue
            nom = caps[0]
            hit = np.where(caps <= 0.8 * nom)[0]
            if len(hit) == 0 or hit[0] < 20: continue
            eol = int(hit[0]); n_cells += 1
            for i in range(eol + 1):
                v, cap = disch[i]
                if v.size < 50 or not np.isfinite(cap): continue
                bins = np.array_split(v, 50)
                pref = [b.mean() for b in bins] + [v.mean(), v.std(), v.min(), v.max()]
                # most recent impedance strictly before this discharge
                j = min(len(eis) - 1, int(np.floor(i / max(1, len(disch)) * len(eis))))
                j = max(0, min(j, len(eis) - 1))
                rowsA.append(pref); rowsC.append(eis_feats(eis[j]))
                ys.append(eol - i); cs.append(name)
        A = np.array(rowsA); C = np.array(rowsC); y = np.array(ys, float); cells = np.array(cs)
        np.savez(CACHE, A=A, C=C, y=y, cells=cells)
        print("cells", n_cells, "rows", len(y), flush=True)

    def cm(y, p, c):
        return float(np.mean([np.mean(np.abs(y[c == k] - p[c == k])) for k in np.unique(c)]))

    res = {"n_rows": int(len(y)), "n_cells": int(len(np.unique(cells))),
           "dims": {"prefix": int(A.shape[1]), "eis": int(C.shape[1])}, "sets": {}}
    for nm, X in {"A_prefix": A, "C_eis": C, "A+C": np.hstack([A, C])}.items():
        pred = np.full(len(y), np.nan)
        for c in np.unique(cells):
            te = cells == c; tr = ~te
            if tr.sum() < 100: continue
            m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
            m.fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
        ok = ~np.isnan(pred)
        res["sets"][nm] = round(cm(y[ok], pred[ok], cells[ok]), 3)
        print(nm, res["sets"][nm], flush=True)
    with open(OUT, "w", encoding="utf-8") as f: json.dump(res, f, ensure_ascii=False, indent=1)
    print("done")

main()
