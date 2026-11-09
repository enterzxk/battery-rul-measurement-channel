"""What are the UConn voltage matrices? + verify ISU/UConn condition-table mapping."""
import pickle, numpy as np, os
import pandas as pd

BASE = r'E:\桌面\rul\data\external\uconn'
OUT = r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol\_probe'

cc = pickle.load(open(os.path.join(BASE, 'data_cc_1.pkl'), 'rb'))
sp = pickle.load(open(os.path.join(BASE, 'data_slowpulse_1.pkl'), 'rb'))

V = cc['voltage']
print('UConn cc voltage matrix: shape %s' % (V.shape,))
print('  global min=%.4f max=%.4f  (span %.1f mV)' % (V.min(), V.max(), 1000 * (V.max() - V.min())))
spread = V.max(1) - V.min(1)
print('  per-record span (mV): median=%.1f p95=%.1f max=%.1f'
      % (1000 * np.median(spread), 1000 * np.percentile(spread, 95), 1000 * spread.max()))
print('  -> a full Li-ion discharge spans ~1000+ mV; these records span tens of mV')
meanv = V.mean(1)
print('  per-record mean voltage: min=%.4f max=%.4f' % (meanv.min(), meanv.max()))
h, edges = np.histogram(meanv, bins=20)
print('  histogram of per-record mean V:')
for i in range(len(h)):
    if h[i]:
        print('    %.4f-%.4f : %d' % (edges[i], edges[i + 1], h[i]))

Vs = sp['voltage']
print('\nUConn slowpulse voltage: shape %s  global %.3f..%.3f' % (Vs.shape, Vs.min(), Vs.max()))
print('  pulse_type values: %s' % dict(zip(*np.unique(sp['pulse_type'], return_counts=True))))
print('  soc values: %s' % dict(zip(*np.unique(sp['soc'], return_counts=True))))
# confirm 6 records per (cell,rpt)
k = pd.DataFrame({'c': sp['cell_id'], 'r': sp['rpt'], 's': sp['soc'], 'p': sp['pulse_type']})
print('  records per (cell,rpt): %s' % k.groupby(['c', 'r']).size().value_counts().to_dict())
print('  distinct (soc,pulse) combos: %d' % k.groupby(['s', 'p']).ngroups)

# ---- condition mapping ----
print('\n' + '=' * 70)
cond = pd.read_csv(r'E:\桌面\rul\rul_v4_20261107\.research\results\isu_conditions.csv')
isc = pd.read_csv(os.path.join(OUT, 'isu_cells.csv'))
print('isu_conditions.csv groups: %d  (ids %d..%d)' % (len(cond), cond.group.min(), cond.group.max()))
print('ISU cells groups: %d  (ids %s..%s)' % (isc.group.nunique(), isc.group.min(), isc.group.max()))
print('group sets identical: %s' % (set(cond.group) == set(isc.group)))
print('missing from table: %s ; extra in table: %s'
      % (sorted(set(isc.group) - set(cond.group)), sorted(set(cond.group) - set(isc.group))))
cc2 = isc.groupby('group').cell.count()
print('per-condition cells: %s' % cc2.value_counts().to_dict())
print('condition with 3 cells: %s' % cc2[cc2 == 3].index.tolist())
print('\nUConn per-condition cells (from group_id):')
print(pd.Series(cc['group_id']).value_counts().sort_index().to_string())
