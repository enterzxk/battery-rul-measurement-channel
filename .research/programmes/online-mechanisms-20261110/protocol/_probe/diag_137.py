"""Diagnose the 137-cycle L/U discrepancy vs uconn_eol_intervals.csv."""
import pickle, numpy as np, os
import pandas as pd

BASE = r'E:\桌面\rul\data\external\uconn'
PROT = r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol'
cc = pickle.load(open(os.path.join(BASE, 'data_cc_1.pkl'), 'rb'))
sp = pickle.load(open(os.path.join(BASE, 'data_slowpulse_1.pkl'), 'rb'))
sib = pd.read_csv(os.path.join(PROT, 'uconn_eol_intervals.csv'))

def build_eol(d, label, agg='median'):
    df = pd.DataFrame({k: v for k, v in d.items() if isinstance(v, np.ndarray) and v.ndim == 1})
    r = df.groupby(['cell_id', 'group_id', 'rpt'], as_index=False).agg(
        seg=('num_cycles', agg), soh=('soh', agg))
    out = {}
    for c, g in r.groupby('cell_id'):
        g = g.sort_values('rpt')
        rr = g.rpt.values; s = g.seg.values.astype(float); soh = g.soh.values
        ff = s.copy(); last = 0.0
        for i in range(len(ff)):
            if not np.isfinite(ff[i]):
                ff[i] = last
            last = ff[i]
        cum = np.cumsum(ff)
        b = np.where(soh < 80.0)[0]
        j = b[0]
        out[int(c)] = (cum[j - 1], cum[j], rr[j - 1], rr[j])
    return out

for lbl, d in [('cc', cc), ('slowpulse', sp)]:
    for agg in ['median', 'first']:
        e = build_eol(d, lbl, agg)
        L = np.array([e[c][0] for c in sib.cell]); U = np.array([e[c][1] for c in sib.cell])
        dL = np.abs(L - sib.L.values); dU = np.abs(U - sib.U.values)
        bad = np.where((dL > 0.5) | (dU > 0.5))[0]
        print('%-10s agg=%-6s  n_mismatch=%2d  max|dL|=%.0f max|dU|=%.0f  cells=%s'
              % (lbl, agg, len(bad), dL.max(), dU.max(), sib.cell.values[bad].tolist()))

# inspect the offending cell with cc/median
e = build_eol(cc, 'cc', 'median')
L = np.array([e[c][0] for c in sib.cell]); U = np.array([e[c][1] for c in sib.cell])
bad = np.where(np.abs(U - sib.U.values) > 0.5)[0]
print('\noffending cells:', sib.cell.values[bad].tolist())
for bi in bad:
    c = int(sib.cell.values[bi])
    print('\ncell %d  mine L=%.0f U=%.0f (rpt_L=%d rpt_U=%d) | sib L=%.0f U=%.0f'
          % (c, L[bi], U[bi], e[c][2], e[c][3], sib.L.values[bi], sib.U.values[bi]))
    df = pd.DataFrame({k: v for k, v in cc.items() if isinstance(v, np.ndarray) and v.ndim == 1})
    g = df[df.cell_id == c].groupby('rpt').agg(seg=('num_cycles', 'median'), soh=('soh', 'median'),
                                               n=('num_cycles', 'size'))
    seg_all = df[df.cell_id == c].groupby('rpt').num_cycles.apply(lambda x: x.tolist())
    print(g.loc[[i for i in range(38, 48) if i in g.index]].to_string())
    print(' raw num_cycles per rpt 40-45:', {i: seg_all[i] for i in range(40, 46) if i in seg_all.index})
