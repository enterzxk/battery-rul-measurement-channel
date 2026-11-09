"""Reconcile with DATA_CONTRACT.md: NaN position, bracket width over all 64 cells, rows-per-RPT."""
import pickle, numpy as np, os
import pandas as pd

BASE = r'E:\桌面\rul\data\external\uconn'
OUT = r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol\_probe'
cc = pickle.load(open(os.path.join(BASE, 'data_cc_1.pkl'), 'rb'))
sp = pickle.load(open(os.path.join(BASE, 'data_slowpulse_1.pkl'), 'rb'))

# (a) rows per (cell,rpt)
for tag, d in [('cc', cc), ('slowpulse', sp)]:
    k = pd.DataFrame({'c': d['cell_id'], 'r': d['rpt']})
    vc = k.groupby(['c', 'r']).size().value_counts().sort_index()
    print('[%s] rows per (cell,rpt): %s  (mean %.2f)' % (tag, vc.to_dict(), len(k) / k.groupby(['c', 'r']).ngroups))

df = pd.DataFrame({k2: v for k2, v in cc.items() if isinstance(v, np.ndarray) and v.ndim == 1})
rpt = df.groupby(['cell_id', 'group_id', 'rpt'], as_index=False).agg(
    seg=('num_cycles', 'median'), q=('q_dchg', 'median'), soh=('soh', 'median'))
rpt = rpt.sort_values(['cell_id', 'rpt']).reset_index(drop=True)

# (b) EOL with forward-filled axis over ALL 64 cells
THR = 80.0
rows = []
for c, g in rpt.groupby('cell_id'):
    g = g.sort_values('rpt')
    rr = g.rpt.values; s = g.seg.values.astype(float); soh = g.soh.values
    ff = s.copy(); last = 0.0
    for i in range(len(ff)):
        if not np.isfinite(ff[i]):
            ff[i] = last
        last = ff[i]
    cum = np.cumsum(ff)
    b = np.where(soh < THR)[0]
    j = b[0]
    rows.append(dict(cell=int(c), group=int(g.group_id.iloc[0]), n_rpt=len(rr),
                     rpt_L=rr[j - 1], rpt_U=rr[j], L=cum[j - 1], U=cum[j],
                     width=cum[j] - cum[j - 1], soh_L=soh[j - 1], soh_U=soh[j],
                     nan_at42=bool(not np.isfinite(s[rr == 42]).all() if (rr == 42).any() else False),
                     eol_after42=bool(rr[j] > 42), imputed=np.nan))
e = pd.DataFrame(rows)
print('\nEOL over ALL 64 cells (forward-filled axis):')
print('  bracket width: median=%.0f IQR=[%.0f,%.0f] min=%.0f max=%.0f'
      % (e.width.median(), np.percentile(e.width, 25), np.percentile(e.width, 75), e.width.min(), e.width.max()))
print('  relative width (width/U): median=%.3f (%.1f%%)'
      % ((e.width / e.U).median(), 100 * (e.width / e.U).median()))
print('  L: min=%.0f median=%.0f max=%.0f | U: min=%.0f median=%.0f max=%.0f'
      % (e.L.min(), e.L.median(), e.L.max(), e.U.min(), e.U.median(), e.U.max()))
print('\n  cells with NaN at rpt42: %d' % e.nan_at42.sum())
print('  of those, EOL rpt > 42: %d' % (e[e.nan_at42].eol_after42.sum()))
print('  of those, EOL rpt <= 42: %d' % (~e[e.nan_at42].eol_after42).sum())
print('  cells WITHOUT NaN at 42 that have EOL after 42: %d' % ((~e.nan_at42) & e.eol_after42).sum())
print('\n  width by group:')
print(e.groupby('group').agg(n=('cell', 'size'), w_med=('width', 'median'), U_med=('U', 'median')).to_string())
e.to_csv(os.path.join(OUT, 'uconn_eol_all64.csv'), index=False)

# compare to sibling's file
sib = pd.read_csv(r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol\uconn_eol_intervals.csv')
m = e.merge(sib, left_on='cell', right_on='cell', suffixes=('', '_sib'))
print('\n  vs sibling uconn_eol_intervals.csv: cells matched=%d' % len(m))
print('    max |L-L_sib| = %.1f ; max |U-U_sib| = %.1f' % ((m.L - m.L_sib).abs().max(), (m.U - m.U_sib).abs().max()))
print('    sibling width median=%.0f  IQR=[%.0f,%.0f]' % (m.width_sib.median(),
      np.percentile(m.width_sib, 25), np.percentile(m.width_sib, 75)))
