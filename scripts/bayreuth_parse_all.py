# -*- coding: utf-8 -*-
"""Batch-parse all Bayreuth cells from their zips (no extraction)."""
import os, zipfile, io, numpy as np, json, time

ZD = r"E:\桌面\rul\data\external\bayreuth"
OUT = r"E:\桌面\rul\data\external\bayreuth\_parsed"
os.makedirs(OUT, exist_ok=True)

def parse_stream(fh):
    caps, rels = [], []
    seg = None; n_disch = 0
    for line in fh:
        if line.startswith("~"): continue
        raw = line.rstrip("\n")
        p = raw.split(",") if "," in raw else raw.split()
        if len(p) < 13: continue
        cmd = p[5]
        try:
            t = float(p[3]); v = float(p[6]); ah = float(p[8])
        except ValueError:
            continue
        if seg is None or cmd != seg[0]:
            if seg is not None:
                _close(seg, caps, rels, n_disch)
                if seg[0] == "Discharge": n_disch += 1
            seg = [cmd, [], [], []]
        seg[1].append(t); seg[2].append(v); seg[3].append(ah)
    if seg is not None: _close(seg, caps, rels, n_disch)
    return caps, rels

def _close(seg, caps, rels, n_disch):
    cmd, t, v, ah = seg
    if cmd == "Discharge" and len(ah) > 10:
        caps.append((n_disch, abs(float(np.nanmax(ah) - np.nanmin(ah)))))
    elif cmd == "Pause" and len(v) > 200 and (t[-1] - t[0]) >= 0.5:
        rels.append((n_disch, np.array(t) - t[0], np.array(v)))

def main():
    zips = sorted(f for f in os.listdir(ZD) if f.endswith(".zip"))
    t0 = time.time()
    summary = []
    for i, zf in enumerate(zips):
        cell = zf[:-4]
        out = os.path.join(OUT, cell + ".npz")
        if os.path.exists(out):
            summary.append(cell); continue
        try:
            with zipfile.ZipFile(os.path.join(ZD, zf)) as z:
                m = [n for n in z.namelist() if n.endswith("_aging.txt")][0]
                with z.open(m) as raw:
                    fh = io.TextIOWrapper(raw, encoding="latin-1")
                    caps, rels = parse_stream(fh)
            np.savez_compressed(out,
                cap_cycle=np.array([c[0] for c in caps], dtype=np.int32),
                cap=np.array([c[1] for c in caps], dtype=np.float32),
                rel_cycle=np.array([r[0] for r in rels], dtype=np.int32),
                rel_v=np.array([r[2] for r in rels], dtype=object),
                rel_t=np.array([r[1] for r in rels], dtype=object))
            summary.append(cell)
            if i % 5 == 0:
                print("parsed %d/%d  %s  caps=%d rests=%d  %.0fs" % (i+1, len(zips), cell, len(caps), len(rels), time.time()-t0), flush=True)
        except Exception as e:
            print("FAIL", cell, e, flush=True)
    print("done", len(summary), "cells in %.0fs" % (time.time()-t0))

main()
