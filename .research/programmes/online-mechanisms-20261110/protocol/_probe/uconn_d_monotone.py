import pickle, numpy as np, os
import pandas as pd

BASE = r'E:\桌面\rul\data\external\uconn'
cc = pickle.load(open(os.path.join(BASE, 'data_cc_1.pkl'), 'rb'))
df = pd.DataFrame({k: v for k, v in cc.items() if isinstance(v, np.ndarray) and v.ndim == 1})
rpt_df = df.groupby(['cell_id', 'group_id', 'rpt'], as_index=False).agg(
    num_cycles=('num_cycles', 'first'), q_dchg=('q_dchg', 'first'), soh=('soh', 'first'))
rpt_df = rpt_df.sort_values(['cell_id', 'rpt']).reset_index(drop=True)

for c in [2, 3, 4]:
    g = rpt_df[rpt_df.cell_id == c].sort_values('rpt')
    print('=' * 70)
    print('cell', c, 'group', g.group_id.iloc[0], 'n_rpt', len(g))
    print(g[['rpt', 'num_cycles', 'q_dchg', 'soh']].to_string(index=False))

# how many cells are non-monotone in num_cycles vs rpt?
bad = 0
for c, g in rpt_df.groupby('cell_id'):
    nc = g.sort_values('rpt').num_cycles.dropna().values
    if len(nc) > 1 and np.any(np.diff(nc) < 0):
        bad += 1
print('\ncells with any negative dnum_cycles: %d / %d' % (bad, rpt_df.cell_id.nunique()))

# is num_cycles maybe a per-rpt label that resets? check monotone after sorting by rpt
# check correlation of num_cycles with rpt
print('\nSpearman(num_cycles, rpt) per cell (first 12):')
for c, g in list(rpt_df.groupby('cell_id'))[:12]:
    gg = g.dropna(subset=['num_cycles'])
    if len(gg) > 2:
        from scipy.stats import spearmanr
        r = spearmanr(gg.rpt, gg.num_cycles).correlation
        print('   cell %2d  rho=%+.3f  nc[0]=%.0f nc[-1]=%.0f' % (c, r, gg.num_cycles.iloc[0], gg.num_cycles.iloc[-1]))
