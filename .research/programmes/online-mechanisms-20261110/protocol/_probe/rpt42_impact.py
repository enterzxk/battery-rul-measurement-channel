"""Quantify the RPT-42 NaN break in the UConn cumulative-cycle axis; finish ISU span stats."""
import pickle, numpy as np, os, json
from datetime import datetime
import pandas as pd

BASE = r'E:\桌面\rul\data\external\uconn'
OUT = r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol\_probe'
cc = pickle.load(open(os.path.join(BASE, 'data_cc_1.pkl'), 'rb'))
df = pd.DataFrame({k: v for k, v in cc.items() if isinstance(v, np.ndarray) and v.ndim == 1})
rpt = df.groupby(['cell_id', 'group_id', 'rpt'], as_index=False).agg(
    seg=('num_cycles', 'median'), q=('q_dchg', 'median'), soh=('soh', 'median'))
rpt = rpt.sort_values(['cell_id', 'rpt']).reset_index(drop=True)

print('UConn: cells with NaN segment at rpt==42: %d / %d'
      % (rpt[(rpt.rpt == 42) & rpt.seg.isna()].cell_id.nunique(), rpt.cell_id.nunique()))
print('UConn: cells whose EOL rpt_U > 42 (would need cumsum past the break):')

rows = []
for c, g in rpt.groupby('cell_id'):
    g = g.sort_values('rpt')
    rr = g.rpt.values; s = g.seg.values.astype(float); soh = g.soh.values
    below = np.where(soh < 80.0)[0]
    j = below[0] if len(below) else None
    raw_cum = np.cumsum(s)                      # NaN propagates from rpt 42
    ff = s.copy(); last = 0.0                   # forward-fill variant (repo convention)
    for i in range(len(ff)):
        if not np.isfinite(ff[i]):
            ff[i] = last
        last = ff[i]
    cum_ff = np.cumsum(ff)
    rows.append(dict(cell=int(c), group=int(g.group_id.iloc[0]), rpt_eol=rr[j] if j is not None else np.nan,
                     cum_raw=np.nan, cum_ff=cum_ff[j] if j is not None else np.nan,
                     raw_ok=bool(j is not None and np.isfinite(raw_cum[j - 1]) and np.isfinite(raw_cum[j]))))
r = pd.DataFrame(rows)
print('   EOL at rpt>42: %d cells' % (r.rpt_eol > 42).sum())
print('   cells where RAW cumsum gives a finite EOL bracket: %d / %d' % (r.raw_ok.sum(), len(r)))
print('   cells requiring forward-fill of the rpt-42 gap: %d' % (~r.raw_ok).sum())
print('   their groups: %s' % r.loc[~r.raw_ok].group.value_counts().sort_index().to_dict())
print('   EOL cycles (forward-filled axis): min=%.0f median=%.0f max=%.0f'
      % (r.cum_ff.min(), r.cum_ff.median(), r.cum_ff.max()))
print('   implied imputation size: median segment %.0f cycles -> cumsum shift'
      % rpt[rpt.rpt > 0].seg.median())

# ---------------- ISU span ----------------
def pdt(s):
    for f in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(s, f)
        except Exception:
            continue
    return pd.NaT

isc = pd.read_csv(os.path.join(OUT, 'isu_cells.csv'))
ie = pd.read_csv(os.path.join(OUT, 'isu_eol.csv'))
isc['span_d'] = [(pdt(b) - pdt(a)).days if pdt(b) is not pd.NaT and pdt(a) is not pd.NaT else np.nan
                 for a, b in zip(isc.start_first, isc.start_last)]
st = ie.set_index('cell').loc[isc.cell, 'status'].values
print('\nISU campaign span (days) by EOL status:')
print(pd.DataFrame({'span': isc.span_d.values, 'status': st}).groupby('status').span.describe()
      [['count', 'min', '25%', '50%', '75%', 'max']].to_string())
print('\nISU EOL bracket medians by discharge rate:')
print(ie.groupby('status')[['rpt_U', 'day_L', 'day_U']].median().to_string())
print('\nISU: conditions with any right-censored cell: %s'
      % sorted(ie[ie.status == 'right_censored'].group.unique().tolist()))
r.to_csv(os.path.join(OUT, 'uconn_cycle_axis_status.csv'), index=False)
print('\nwrote uconn_cycle_axis_status.csv')
