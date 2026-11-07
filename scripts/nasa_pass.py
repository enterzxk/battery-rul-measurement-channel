# -*- coding: utf-8 -*-
"""NASA PCoE: does EIS add over the discharge-capacity prefix? (cross-modal confirmation)"""
import io, os, zipfile, json, warnings, numpy as np
import scipy.io as sio
from sklearn.ensemble import HistGradientBoostingRegressor
warnings.filterwarnings("ignore")
ROOT = r"E:\桌面\rul\data\external\nasa_pcoe\NASA_5_Battery_Data_Set.zip"
OUT = r"C:\Users\Administrator\AppData\Local\Temp\nasa_run.json"

def iter_mats():
    with zipfile.ZipFile(ROOT) as z:
        for info in z.infolist():
            n = info.filename
            if n.lower().endswith(".zip"):
                with z.open(info) as fh: buf = fh.read()
                with zipfile.ZipFile(io.BytesIO(buf)) as z2:
                    for i2 in z2.infolist():
                        if i2.filename.lower().endswith(".mat"):
                            with z2.open(i2) as fh:
                                yield os.path.basename(i2.filename), fh.read()

def parse(raw):
    m = sio.loadmat(io.BytesIO(raw), squeeze_me=False, struct_as_record=False)
    keys = [k for k in m if not k.startswith("__")]
    if not keys: return None
    b = m[keys[0]][0, 0]
    cyc = b.cycle
    cap, re_, rct = [], [], []
    for c in cyc.ravel():
        t = str(c.type[0])
        try:
            d = c.data[0, 0]
        except Exception:
            continue
        if t == "discharge":
            try:
                cap.append(float(np.ravel(d.Capacity)[0]))
            except Exception:
                cap.append(np.nan)
        elif t == "impedance":
            try:
                re_.append(float(np.ravel(d.Re)[0])); rct.append(float(np.ravel(d.Rct)[0]))
            except Exception:
                re_.append(np.nan); rct.append(np.nan)
    return cap, re_, rct

def main():
    rows = []
    for name, raw in iter_mats():
        p = parse(raw)
        if p is None: continue
        cap, re_, rct = p
        cap = np.array(cap); re_ = np.array(re_); rct = np.array(rct)
        if len(cap) < 20: continue
        # interpolate EIS onto the discharge-cycle grid (EIS sampled more/less often)
        n = len(cap)
        idx_re = np.interp(np.arange(n), np.linspace(0, n - 1, len(re_)), re_) if len(re_) > 1 else np.full(n, np.nan)
        idx_rct = np.interp(np.arange(n), np.linspace(0, n - 1, len(rct)), rct) if len(rct) > 1 else np.full(n, np.nan)
        rows.append(dict(cell=name.replace(".mat", ""), cap=cap, re=idx_re, rct=idx_rct))
    print("cells parsed", len(rows), flush=True)

    feats, ys, cells, groups = [], [], [], []
    for r in rows:
        cap = r["cap"]; n = len(cap)
        if not np.isfinite(cap[0]) or cap[0] <= 0: continue
        nom = cap[0]
        eol = None
        for i in range(n):
            if np.isfinite(cap[i]) and cap[i] <= 0.8 * nom:
                eol = i; break
        if eol is None or eol < 10: continue
        for i in range(eol + 1):
            if not np.isfinite(cap[i]): continue
            hist = cap[:i+1]
            A = [hist.mean(), hist.std(), hist[-1], (hist[-1]-hist[0])/max(1, i),
                 np.polyfit(np.arange(len(hist)), hist, 1)[0] if len(hist) > 2 else 0.0]
            C = [r["re"][i], r["rct"][i]]
            if not np.isfinite(C[0]) or not np.isfinite(C[1]): continue
            hre = r["re"][:i+1]; hrct = r["rct"][:i+1]
            C += [np.nanmean(hre), np.nanstd(hre), np.nanmean(hrct), np.nanstd(hrct)]
            feats.append((A, C)); ys.append(eol - i); cells.append(r["cell"])
    print("rows", len(feats), flush=True)
    A = np.array([f[0] for f in feats]); C = np.array([f[1] for f in feats])
    y = np.array(ys, float); cells = np.array(cells)

    def cm(y, p, c):
        return float(np.mean([np.mean(np.abs(y[c == k] - p[c == k])) for k in np.unique(c)]))

    res = {"n_rows": int(len(y)), "n_cells": int(len(np.unique(cells))), "sets": {}}
    # leave-one-cell-out (NASA has no meaningful condition groups in this extraction)
    for nm, X in {"A_prefix": A, "C_eis": C, "A+C": np.hstack([A, C])}.items():
        pred = np.full(len(y), np.nan)
        for c in np.unique(cells):
            te = cells == c; tr = ~te
            if tr.sum() < 50: continue
            m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, random_state=0)
            m.fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
        ok = ~np.isnan(pred)
        res["sets"][nm] = round(cm(y[ok], pred[ok], cells[ok]), 3)
        print(nm, res["sets"][nm], flush=True)
    with open(OUT, "w", encoding="utf-8") as f: json.dump(res, f, ensure_ascii=False, indent=1)
    print("done")

main()
