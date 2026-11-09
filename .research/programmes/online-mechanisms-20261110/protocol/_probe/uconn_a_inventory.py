"""UConn REIL: inventory, RPT cadence, physical axes, interval-censored EOL, Ah throughput."""
import pickle, numpy as np, os, json

BASE = r'E:\桌面\rul\data\external\uconn'
OUT = r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol\_probe'
res = {}


def load(name):
    with open(os.path.join(BASE, name), 'rb') as f:
        return pickle.load(f)


cc = load('data_cc_1.pkl')
sp = load('data_slowpulse_1.pkl')

for tag, d in [('cc', cc), ('slowpulse', sp)]:
    cid = d['cell_id']; gid = d['group_id']; rpt = d['rpt']
    nc = d['num_cycles']; soh = d['soh']
    print('=' * 78)
    print(f'[{tag}] rows={len(cid)} cells={len(np.unique(cid))} groups={len(np.unique(gid))}')
    print(f'  cell_id range {cid.min()}..{cid.max()}  group range {gid.min()}..{gid.max()}')
    print(f'  rpt range {rpt.min()}..{rpt.max()}   num_cycles range {nc.min():.0f}..{nc.max():.0f}')
    print(f'  soh range {soh.min():.2f}..{soh.max():.2f}')
    # duplicates on (cell, rpt)?
    key = np.stack([cid, rpt], 1)
    uniq = np.unique(key, axis=0)
    print(f'  unique (cell,rpt) pairs = {len(uniq)}  (rows={len(key)} -> dup rows={len(key)-len(uniq)})')
    # cells per group
    pairs = {}
    for c, g in zip(cid, gid):
        pairs.setdefault(c, set()).add(g)
    multi = {c: g for c, g in pairs.items() if len(g) > 1}
    print(f'  cells with >1 group: {len(multi)}')
    gcount = {}
    for c, g in pairs.items():
        gcount.setdefault(list(g)[0], []).append(c)
    print('  cells per group: ' + ', '.join(f'G{g}:{len(v)}' for g, v in sorted(gcount.items())))
    # RPTs per cell
    nprt = {}
    for c in np.unique(cid):
        nprt[c] = len(np.unique(rpt[cid == c]))
    vals = np.array(list(nprt.values()))
    print(f'  RPTs per cell: min={vals.min()} max={vals.max()} mean={vals.mean():.2f} median={np.median(vals):.0f}')
    print(f'  distribution: ' + str(dict(zip(*np.unique(vals, return_counts=True)))))
    res[tag] = dict(rows=int(len(cid)), cells=int(len(np.unique(cid))), groups=int(len(np.unique(gid))),
                    rpt_min=int(rpt.min()), rpt_max=int(rpt.max()),
                    nc_max=float(nc.max()), soh_min=float(soh.min()),
                    rpt_per_cell=dict(zip([int(x) for x in np.unique(vals)], [int(x) for x in np.unique(vals, return_counts=True)[1]])))

json.dump(res, open(os.path.join(OUT, 'uconn_summary.json'), 'w'), indent=1)
print('\nwrote uconn_summary.json')
