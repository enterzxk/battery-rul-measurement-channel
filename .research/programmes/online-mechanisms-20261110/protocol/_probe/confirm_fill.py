"""Confirm: uconn_eol_intervals.csv == fill(0) variant; v2_main.py == forward-fill variant."""
import pickle, numpy as np, os
import pandas as pd

BASE = r'E:\桌面\rul\data\external\uconn'
PROT = r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol'
sp = pickle.load(open(os.path.join(BASE, 'data_slowpulse_1.pkl'), 'rb'))
sib = pd.read_csv(os.path.join(PROT, 'uconn_eol_intervals.csv'))

df = pd.DataFrame({k: v for k, v in sp.items() if isinstance(v, np.ndarray) and v.ndim == 1})
r = df.groupby(['cell_id', 'rpt'], as_index=False).agg(seg=('num_cycles', 'median'), soh=('soh', 'median'))


def eol(fill):
    out = {}
    for c, g in r.groupby('cell_id'):
        g = g.sort_values('rpt')
        rr = g.rpt.values; s = g.seg.values.astype(float); soh = g.soh.values
        v = s.copy()
        last = 0.0
        for i in range(len(v)):
            if not np.isfinite(v[i]):
                v[i] = last if fill == 'prev' else (np.nanmedian(s[np.isfinite(s)]) if fill == 'median' else 0.0)
            last = v[i]
        cum = np.cumsum(v)
        j = np.where(soh < 80.0)[0][0]
        out[int(c)] = (cum[j - 1], cum[j], rr[j - 1], rr[j], s[rr == 42])
    return out


res = {}
for fill in ['prev', 'zero', 'median']:
    e = eol(fill)
    L = np.array([e[c][0] for c in sib.cell]); U = np.array([e[c][1] for c in sib.cell])
    d = np.abs(U - sib.U.values)
    res[fill] = d
    print('fill=%-7s  vs sibling: n_exact=%d  max|dU|=%.0f  mean|dU|=%.2f'
          % (fill, (d < 0.5).sum(), d.max(), d.mean()))

e_prev, e_zero = eol('prev'), eol('zero')
print('\nspread of absolute EOL (U) between fill=prev and fill=zero, over 64 cells:')
diffs = [abs(e_prev[c][1] - e_zero[c][1]) for c in sib.cell]
nz = [d for d in diffs if d > 0]
print('  cells affected=%d  median shift=%.0f  min=%.0f  max=%.0f  (as %% of U: median %.2f%%)'
      % (len(nz), np.median(nz), min(nz), max(nz), 100 * np.median(nz) / sib.U.median()))
print('  width (U-L) invariant? max |width_prev - width_zero| = %.0f'
      % max(abs((e_prev[c][1] - e_prev[c][0]) - (e_zero[c][1] - e_zero[c][0])) for c in sib.cell))
print('\n  NaN segment value at rpt42 for affected cells: %s'
      % [e_prev[c][4] for c in list(sib.cell)[:5]])
