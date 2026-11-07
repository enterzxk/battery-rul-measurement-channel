# -*- coding: utf-8 -*-
"""Parse one Bayreuth cell: per-cycle discharge capacity + long-rest relaxation traces."""
import sys, os, zipfile, io, numpy as np, json

def parse_aging(path):
    """Stream the Basytec result file; return (cycles, caps, relaxations)."""
    caps = []          # (cycle_idx, discharge_capacity_Ah)
    rels = []          # (cycle_idx, t_array, v_array)
    seg = None         # current segment
    n_disch = 0
    with open(path, "r", encoding="latin-1") as f:
        for line in f:
            if line.startswith("~"):
                continue
            p = line.rstrip("\n").split(",")
            if len(p) < 13:
                continue
            cmd = p[5]
            try:
                t = float(p[3]); v = float(p[6]); ah = float(p[8])
            except ValueError:
                continue
            if cmd != (seg[0] if seg else None):
                if seg is not None:
                    _close(seg, caps, rels, n_disch)
                    if seg[0] == "Discharge":
                        n_disch += 1
                seg = [cmd, [], [], []]
            seg[1].append(t); seg[2].append(v); seg[3].append(ah)
    if seg is not None:
        _close(seg, caps, rels, n_disch)
    return caps, rels

def _close(seg, caps, rels, n_disch):
    cmd, t, v, ah = seg
    if cmd == "Discharge" and len(ah) > 10:
        cap = float(np.nanmax(ah) - np.nanmin(ah))
        caps.append((n_disch, abs(cap)))
    elif cmd == "Pause" and len(v) > 200:
        dur = t[-1] - t[0]
        if dur >= 0.5:  # long rest only
            rels.append((n_disch, np.array(t) - t[0], np.array(v)))

def main():
    cell = sys.argv[1]
    zdir = r"E:\桌面\rul\data\external\bayreuth"
    exdir = os.path.join(zdir, "_extract")
    d = os.path.join(exdir, cell)
    if not os.path.isdir(d):
        with zipfile.ZipFile(os.path.join(zdir, cell + ".zip")) as z:
            z.extractall(exdir)
    p = os.path.join(d, "M0002_aging.txt")
    caps, rels = parse_aging(p)
    print("cell", cell, "discharge segments", len(caps), "long rests", len(rels))
    if caps:
        c = np.array(caps)
        print("capacity range: %.4f .. %.4f Ah" % (c[:,1].min(), c[:,1].max()))
        print("first 5 caps:", np.round(c[:5,1], 4))
        print("last 5 caps:", np.round(c[-5:,1], 4))
    if rels:
        for i, (cyc, t, v) in enumerate(rels[:3]):
            print("rest %d at cycle %d: %d pts, %.2f h, %.4f -> %.4f V" % (i, cyc, len(t), t[-1], v[0], v[-1]))
    out = os.path.join(exdir, cell + "_parsed.npz")
    np.savez_compressed(out,
                        cap_cycle=np.array([x[0] for x in caps]),
                        cap=np.array([x[1] for x in caps]),
                        rel_cycle=np.array([x[0] for x in rels]),
                        rel_v=np.array([x[2] for x in rels], dtype=object),
                        rel_t=np.array([x[1] for x in rels], dtype=object))
    print("saved", out)

main()
