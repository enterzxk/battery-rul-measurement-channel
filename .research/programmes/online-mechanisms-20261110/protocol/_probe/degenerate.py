"""Identify cells whose EOL crossing lands exactly at rpt 42, and the one non-matching cell."""
import pickle, numpy as np, os
import pandas as pd

BASE = r'E:\桌面\rul\data\external\uconn'
PROT = r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol'
sp = pickle.load(open(os.path.join(BASE, 'data_slowpulse_1.pkl'), 'rb'))
sib = pd.read_csv(os.path.join(PROT, 'uconn_eol_intervals.csv'))
df = pd.DataFrame({k: v for k, v in sp.items() if isinstance(v, np.ndarray) and v.ndim == 1})
r = df.groupby(['cell_id', 'rpt'], as_index=False).agg(seg=('num_cycles', 'median'), soh=('soh', 'median'))

rows = []
for c, g in r.groupby('cell_id'):
    g = g.sort_values('rpt')
    rr = g.rpt.values; s = g.seg.values.astype(float); soh = g.soh.values
    j = np.where(soh < 80.0)[0][0]
    rows.append(dict(cell=int(c), rpt_L=rr[j - 1], rpt_U=rr[j], seg42=s[rr == 42][0] if (rr == 42).any() else np.nan))
t = pd.DataFrame(rows)
print('cells with rpt_U == 42 (crossing lands on the gapped RPT): %d' % (t.rpt_U == 42).sum())
print(t[t.rpt_U == 42].to_string())
print('\ncells with rpt_L == 42: %d' % (t.rpt_L == 42).sum())
print('cells with rpt_U == 43: %d' % (t.rpt_U == 43).sum())
print('\ndistribution of rpt_U among the 32 gapped cells:')
print(t[t.seg42.isna()].rpt_U.value_counts().sort_index().to_string())

# the one non-matching cell under fill=zero
e = {}
for c, g in r.groupby('cell_id'):
    g = g.sort_values('rpt')
    rr = g.rpt.values; s = g.seg.values.astype(float); soh = g.soh.values
    v = s.copy(); last = 0.0
    for i in range(len(v)):
        if not np.isfinite(v[i]):
            v[i] = 0.0
        last = v[i]
    cum = np.cumsum(v)
    j = np.where(soh < 80.0)[0][0]
    e[int(c)] = (cum[j - 1], cum[j], rr[j - 1], rr[j])
bad = [(c, e[c], sib.set_index('cell').loc[c, ['L', 'U']].tolist())
       for c in sib.cell if abs(e[c][1] - sib.set_index('cell').loc[c, 'U']) > 0.5]
print('\nnon-matching cell(s) under fill=0:')
for c, mine, s_ in bad:
    print('  cell %d: mine L=%.0f U=%.0f (rpt_L=%d rpt_U=%d) | sib L=%.0f U=%.0f' % (c, mine[0], mine[1], mine[2], mine[3], s_[0], s_[1]))
    g = r[r.cell_id == c].sort_values('rpt')
    print('   seg around 40-45:', g[(g.rpt >= 40) & (g.rpt <= 45)][['rpt', 'seg', 'soh']].to_dict('records'))
