import pickle, numpy as np, os
import pandas as pd

BASE = r'E:\桌面\rul\data\external\uconn'
cc = pickle.load(open(os.path.join(BASE, 'data_cc_1.pkl'), 'rb'))
sp = pickle.load(open(os.path.join(BASE, 'data_slowpulse_1.pkl'), 'rb'))

for tag, d in [('cc', cc), ('slowpulse', sp)]:
    print('=' * 78)
    print('[%s] NaN counts per field:' % tag)
    for k, v in d.items():
        if isinstance(v, np.ndarray) and v.dtype.kind in 'iuf':
            n = int(np.isnan(v).sum()) if v.dtype.kind == 'f' else 0
            print('   %-16s NaN=%d / %d' % (k, n, len(v)))
        elif isinstance(v, np.ndarray) and v.ndim == 2:
            print('   %-16s NaN=%d / %d' % (k, int(np.isnan(v).sum()), v.size))

df = pd.DataFrame({k: v for k, v in cc.items() if isinstance(v, np.ndarray) and v.ndim == 1})
print('\n[cc] rows=%d' % len(df))
sub = df[df.cell_id == 2].sort_values('rpt')
print('\n[cc] cell 2, all rows (grain check):')
print(sub[['rpt', 'num_cycles', 'q_dchg', 'soh', 'dcir_chg_20', 'dcir_chg_50', 'dcir_chg_90']].head(12).to_string())

g = sub.groupby('rpt').size()
print('\n[cc] cell2 rows per rpt: value_counts', g.value_counts().to_dict())

# within one (cell,rpt), what varies?
one = sub[sub.rpt == 1]
print('\n[cc] cell2 rpt1 rows:')
print(one[['num_cycles', 'q_dchg', 'soh', 'dcir_chg_20', 'dcir_chg_50', 'dcir_chg_90']].to_string())
print('voltage rows identical?', np.allclose(cc['voltage'][one.index[0]], cc['voltage'][one.index[1]]) if len(one) > 1 else 'n/a')
