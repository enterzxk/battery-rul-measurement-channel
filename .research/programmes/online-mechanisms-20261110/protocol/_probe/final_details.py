"""Final detail pass: UConn segment stats w/o NaN, missing-RPT location, ISU censoring structure."""
import pickle, numpy as np, os, json
import pandas as pd

BASE = r'E:\桌面\rul\data\external\uconn'
OUT = r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol\_probe'
cc = pickle.load(open(os.path.join(BASE, 'data_cc_1.pkl'), 'rb'))
df = pd.DataFrame({k: v for k, v in cc.items() if isinstance(v, np.ndarray) and v.ndim == 1})
rpt = df.groupby(['cell_id', 'group_id', 'rpt'], as_index=False).agg(
    seg=('num_cycles', 'median'), q=('q_dchg', 'median'), soh=('soh', 'median'))
rpt = rpt.sort_values(['cell_id', 'rpt']).reset_index(drop=True)

# where are the NaNs?
nan_rows = rpt[rpt.seg.isna()]
print('UConn NaN-segment rows: %d across %d cells' % (len(nan_rows), nan_rows.cell_id.nunique()))
print('  their rpt index: %s' % dict(zip(*[x.tolist() for x in np.unique(nan_rows.rpt, return_counts=True)])))
print('  their rpt position from end (0=last): %s' % dict(zip(*[x.tolist() for x in np.unique(
    [len(rpt[rpt.cell_id == c]) - 1 - int(r) for c, r in zip(nan_rows.cell_id, nan_rows.rpt)], return_counts=True)])))

# missing RPT (index gap of 2)
for c, g in rpt.groupby('cell_id'):
    d = np.diff(g.rpt.values)
    if np.any(d > 1):
        print('  cell %d has RPT index jump at %s' % (c, g.rpt.values[np.where(d > 1)[0]]))

segs = rpt[rpt.seg.notna() & (rpt.rpt > 0)].seg.values.astype(float)
print('\nUConn segment length (cycles between consecutive RPTs), n=%d' % len(segs))
print('  min=%.0f p05=%.0f p25=%.0f median=%.0f p75=%.0f p95=%.0f max=%.0f mean=%.1f sd=%.1f'
      % (segs.min(), *np.percentile(segs, [5, 25, 50, 75, 95]), segs.max(), segs.mean(), segs.std()))
print('  CV = %.3f' % (segs.std() / segs.mean()))
print('  deciles:', np.percentile(segs, np.arange(0, 101, 10)).round(0).tolist())
print('  fraction within +/-20%% of median: %.1f%%' % (100 * np.mean(np.abs(segs / np.median(segs) - 1) <= 0.2)))

cumtot = []
for c, g in rpt.groupby('cell_id'):
    cumtot.append(np.nansum(g.sort_values('rpt').seg.values))
cumtot = np.array(cumtot)
print('  cumulative cycles per cell: min=%.0f p25=%.0f median=%.0f p75=%.0f max=%.0f'
      % (cumtot.min(), *np.percentile(cumtot, [25, 50, 75]), cumtot.max()))

# per-group
print('\nUConn per-condition: cells, RPTs, EOL cycles')
eol = pd.read_csv(os.path.join(OUT, 'uconn_eol2.csv'))
m = rpt.groupby('cell_id').agg(group=('group_id', 'first'), n_rpt=('rpt', 'size'))
eol = eol.merge(m, left_on='cell', right_index=True)
agg = eol.groupby('group').agg(n_cells=('cell', 'size'), rpt_med=('n_rpt', 'median'),
                               eol_cyc_med=('cyc_U', 'median'))
print(agg.to_string())

# ---------------- ISU ----------------
isc = pd.read_csv(os.path.join(OUT, 'isu_cells.csv'))
ie = pd.read_csv(os.path.join(OUT, 'isu_eol.csv'))
print('\n' + '=' * 70)
print('ISU: n_cells=%d n_cond=%d' % (len(isc), isc.group.nunique()))
print('n_rpt distribution: %s' % isc.n_rpt.value_counts().sort_index().to_dict())
five = isc[isc.n_rpt == 5]
print('cells with exactly 5 RPTs: %d ; of these right_censored: %d'
      % (len(five), (ie.set_index('cell').loc[five.cell, 'status'] == 'right_censored').sum()))
print('right-censored cells by condition: %s'
      % ie[ie.status == 'right_censored'].group.value_counts().sort_index().to_dict())
print('conditions with 0 right-censored: %d / %d'
      % (ie.group.nunique() - ie[ie.status == 'right_censored'].group.nunique(), ie.group.nunique()))
print('campaign span by censoring:')
span = isc.copy(); span['span'] = pd.to_datetime(span.start_last) - pd.to_datetime(span.start_first)
span['span_d'] = span.span.dt.days
print(span.groupby(ie.set_index('cell').loc[span.cell, 'status'].values).span_d.describe()[['count', '25%', '50%', '75%', 'max']].to_string())
print('\nISU EOL day bracket by discharge rate:')
print(ie.groupby('status')[['rpt_U', 'day_L', 'day_U']].median().to_string())
