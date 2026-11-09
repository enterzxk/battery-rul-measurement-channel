"""UConn: RPT cadence in index / cycle / time units; interval-censored EOL; Ah throughput."""
import pickle, numpy as np, os, json
import pandas as pd

BASE = r'E:\桌面\rul\data\external\uconn'
OUT = r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol\_probe'
cc = pickle.load(open(os.path.join(BASE, 'data_cc_1.pkl'), 'rb'))

df = pd.DataFrame({k: v for k, v in cc.items() if isinstance(v, np.ndarray) and v.ndim == 1})
# collapse to one row per (cell, rpt): scalars are constant within the group (verified)
rpt_df = df.groupby(['cell_id', 'group_id', 'rpt'], as_index=False).agg(
    num_cycles=('num_cycles', 'first'), q_dchg=('q_dchg', 'first'), soh=('soh', 'first'))
rpt_df = rpt_df.sort_values(['cell_id', 'rpt']).reset_index(drop=True)
print('RPT-level rows =', len(rpt_df), ' cells =', rpt_df.cell_id.nunique())
print('rows with NaN num_cycles =', int(rpt_df.num_cycles.isna().sum()),
      ' cells affected =', rpt_df.loc[rpt_df.num_cycles.isna(), 'cell_id'].nunique())

# ---- rpt index contiguity ----
gaps_idx = []
for c, g in rpt_df.groupby('cell_id'):
    r = g.rpt.values
    if r[0] != 0:
        print('  cell %d does not start at rpt 0 (starts %d)' % (c, r[0]))
    gaps_idx.extend(np.diff(r).tolist())
gaps_idx = np.array(gaps_idx)
print('\n(a) RPT-INDEX gaps between consecutive RPTs:')
print('   unique values', dict(zip(*np.unique(gaps_idx, return_counts=True))))

# ---- cycle gaps ----
cyc_gap, all_gap = [], []
first_nc, last_nc = {}, {}
for c, g in rpt_df.groupby('cell_id'):
    g = g.dropna(subset=['num_cycles'])
    nc = g.num_cycles.values
    first_nc[c] = nc[0] if len(nc) else np.nan
    last_nc[c] = nc[-1] if len(nc) else np.nan
    d = np.diff(nc)
    cyc_gap.extend(d.tolist())
cyc_gap = np.array(cyc_gap, dtype=float)
print('\n(b) CYCLE gaps (num_cycles diff) between consecutive RPTs, n=%d' % len(cyc_gap))
print('   min=%.0f p05=%.0f p25=%.0f median=%.0f p75=%.0f p95=%.0f max=%.0f mean=%.1f sd=%.1f'
      % (cyc_gap.min(), np.percentile(cyc_gap, 5), np.percentile(cyc_gap, 25), np.median(cyc_gap),
         np.percentile(cyc_gap, 75), np.percentile(cyc_gap, 95), cyc_gap.max(), cyc_gap.mean(), cyc_gap.std()))
print('   zero-gap pairs (duplicate cycle count): %d (%.1f%%)' % ((cyc_gap == 0).sum(), 100 * (cyc_gap == 0).mean()))
print('   deciles:', np.percentile(cyc_gap, np.arange(0, 101, 10)).round(0).tolist())
print('   coefficient of variation = %.3f' % (cyc_gap.std() / cyc_gap.mean()))
# per-cell irregularity
cvs = []
for c, g in rpt_df.groupby('cell_id'):
    d = np.diff(g.dropna(subset=['num_cycles']).num_cycles.values)
    if len(d) > 1 and d.mean() > 0:
        cvs.append(d.std() / d.mean())
cvs = np.array(cvs)
print('   per-cell CV of cycle-gap: median=%.3f p90=%.3f max=%.3f (n=%d cells)' % (np.median(cvs), np.percentile(cvs, 90), cvs.max(), len(cvs)))
print('\n   num_cycles at first/last RPT: first min=%.0f max=%.0f ; last min=%.0f max=%.0f'
      % (np.nanmin(list(first_nc.values())), np.nanmax(list(first_nc.values())),
         np.nanmin(list(last_nc.values())), np.nanmax(list(last_nc.values()))))

# ---- calendar time ----
print('\n(c) CALENDAR TIME: searching for any timestamp field...')
ts_keys = [k for k in cc.keys() if any(s in k.lower() for s in ('time', 'date', 'start', 'stop', 'stamp'))]
print('   timestamp-like keys in data_cc_1.pkl:', ts_keys if ts_keys else 'NONE')

# ---- EOL interval censoring ----
THR = 80.0
rows = []
for c, g in rpt_df.groupby('cell_id'):
    g = g.sort_values('rpt')
    soh = g.soh.values; rp = g.rpt.values; nc = g.num_cycles.values
    below = np.where(soh < THR)[0]
    if len(below) == 0:
        status = 'right_censored'
        L = U = np.nan; Lc = Uc = np.nan
    elif below[0] == 0:
        status = 'exact_at_first'  # already below at first RPT -> no upper bracket
        L = U = np.nan; Lc = Uc = np.nan
    else:
        i = below[0]
        status = 'interval'
        L, U = soh[i - 1], soh[i]
        Lc, Uc = nc[i - 1], nc[i]
        if soh[i] == THR:
            status = 'exact_hit'
    rows.append(dict(cell=c, group=int(g.group_id.iloc[0]), n_rpt=len(g),
                     soh_first=soh[0], soh_last=soh[-1], status=status,
                     rpt_L=rp[below[0] - 1] if len(below) and below[0] > 0 else np.nan,
                     rpt_U=rp[below[0]] if len(below) else np.nan,
                     cyc_L=Lc, cyc_U=Uc, soh_L=L, soh_U=U,
                     nc_last=nc[-1]))
eol = pd.DataFrame(rows)
print('\n(4) INTERVAL-CENSORED EOL (threshold SOH < 80%):')
print(eol.status.value_counts().to_string())
print('   width in cycles (U-L): median=%.0f p10=%.0f p90=%.0f max=%.0f'
      % (eol.cyc_U - eol.cyc_L).median(), end='')
print('') if False else None
w = (eol.cyc_U - eol.cyc_L).dropna()
print('   width in cycles (U-L): n=%d median=%.0f p10=%.0f p90=%.0f max=%.0f'
      % (len(w), w.median(), np.percentile(w, 10), np.percentile(w, 90), w.max()))
ws = (eol.soh_L - eol.soh_U).dropna()
print('   width in SOH points: median=%.2f p90=%.2f max=%.2f' % (ws.median(), np.percentile(ws, 90), ws.max()))
print('   cells crossing 80%%: %d / %d (%.1f%%)' % ((eol.status != 'right_censored').sum(), len(eol),
                                                     100 * (eol.status != 'right_censored').mean()))
print('   cells whose soh_last >= 80: %d' % (eol.soh_last >= 80).sum())

# ---- Ah throughput ----
print('\n(5) Ah THROUGHPUT:')
tot = {}
for c, g in rpt_df.groupby('cell_id'):
    g = g.sort_values('rpt').dropna(subset=['num_cycles'])
    if len(g) < 2:
        continue
    dnc = np.diff(g.num_cycles.values)
    q = g.q_dchg.values
    # left-endpoint rectangle: charge per cycle ~ q at the preceding RPT
    ah = float(np.sum(q[:-1] * dnc))
    tot[c] = ah
print('   trapezoid/left-rect over measured q_dchg x measured dnum_cycles:')
print('   cells=%d  Ah range %.1f .. %.1f  median %.1f' % (len(tot), min(tot.values()), max(tot.values()),
                                                            np.median(list(tot.values()))))
print('   NOTE: this is an APPROXIMATION. It uses the RPT-measured discharge capacity as a')
print('   stand-in for per-cycle throughput in the intervening cycles. True per-cycle Ah is MISSING.')

eol.to_csv(os.path.join(OUT, 'uconn_eol.csv'), index=False)
json.dump(dict(cyc_gap_pcts={str(p): float(np.percentile(cyc_gap, p)) for p in [0, 5, 25, 50, 75, 95, 100]},
               cyc_gap_cv=float(cyc_gap.std() / cyc_gap.mean()),
               percell_cv_median=float(np.median(cvs)),
               n_rpt=len(rpt_df), n_cells=int(rpt_df.cell_id.nunique()),
               eol_counts=eol.status.value_counts().to_dict(),
               ah_median=float(np.median(list(tot.values()))),
               ah_min=float(min(tot.values())), ah_max=float(max(tot.values()))),
          open(os.path.join(OUT, 'uconn_cadence.json'), 'w'), indent=1)
print('\nwrote uconn_eol.csv, uconn_cadence.json')
