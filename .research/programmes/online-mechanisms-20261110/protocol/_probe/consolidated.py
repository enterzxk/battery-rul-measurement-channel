"""Consolidated, corrected cadence + EOL for UConn (cumulative-cycle axis) and robustness for ISU."""
import pickle, numpy as np, os, json
import pandas as pd

BASE = r'E:\桌面\rul\data\external\uconn'
OUT = r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol\_probe'
cc = pickle.load(open(os.path.join(BASE, 'data_cc_1.pkl'), 'rb'))
df = pd.DataFrame({k: v for k, v in cc.items() if isinstance(v, np.ndarray) and v.ndim == 1})
rpt = df.groupby(['cell_id', 'group_id', 'rpt'], as_index=False).agg(
    seg=('num_cycles', 'median'), q=('q_dchg', 'median'), soh=('soh', 'median'))
rpt = rpt.sort_values(['cell_id', 'rpt']).reset_index(drop=True)
print('UConn RPT-level rows=%d cells=%d groups=%d' % (len(rpt), rpt.cell_id.nunique(), rpt.group_id.nunique()))

# ---------- (a) RPT index gap ----------
idx_gaps = np.concatenate([np.diff(g.rpt.values) for _, g in rpt.groupby('cell_id')])
print('\n(a) RPT-INDEX gap: %s' % dict(zip(*[x.tolist() for x in np.unique(idx_gaps, return_counts=True)])))

# ---------- (b) cumulative-cycle gap = segment length ----------
segs, cumtot, cvlist, cum_at_rpt = [], [], [], {}
for c, g in rpt.groupby('cell_id'):
    g = g.sort_values('rpt')
    s = g.seg.values.astype(float)
    cum = np.cumsum(s)
    cum_at_rpt[c] = (g.rpt.values, cum, g.soh.values)
    segs.extend(s[1:].tolist())            # exclude rpt0 (always 0)
    cumtot.append(cum[-1])
    if len(s) > 2 and np.nanmean(s[1:]) > 0:
        cvlist.append(np.nanstd(s[1:]) / np.nanmean(s[1:]))
segs = np.array(segs)
cumtot = np.array(cumtot); cvlist = np.array(cvlist)
print('\n(b) CUMULATIVE-CYCLE gap between consecutive RPTs (= segment length), n=%d' % len(segs))
print('   min=%.0f p05=%.0f p25=%.0f median=%.0f p75=%.0f p95=%.0f max=%.0f mean=%.1f sd=%.1f'
      % (segs.min(), *np.percentile(segs, [5, 25, 50, 75, 95]), segs.max(), segs.mean(), segs.std()))
print('   CV across all gaps = %.3f ; per-cell CV median=%.3f p90=%.3f max=%.3f'
      % (segs.std() / segs.mean(), np.median(cvlist), np.percentile(cvlist, 90), cvlist.max()))
print('   deciles:', np.percentile(segs, np.arange(0, 101, 10)).round(0).tolist())
print('   total cumulative cycles per cell: min=%.0f median=%.0f max=%.0f'
      % (cumtot.min(), np.median(cumtot), cumtot.max()))
print('   NaN segments: %d' % int(np.isnan(segs).sum()))

# ---------- (c) calendar time ----------
print('\n(c) CALENDAR TIME in UConn pickles: NONE (no time/date/start/stop key in either pickle)')

# ---------- EOL intervals ----------
THR = 80.0
rows = []
for c, (rr, cum, soh) in cum_at_rpt.items():
    below = np.where(soh < THR)[0]
    if len(below) == 0:
        st = 'right_censored'; a = dict(rpt_L=np.nan, rpt_U=np.nan, cyc_L=np.nan, cyc_U=np.nan, soh_L=np.nan, soh_U=np.nan)
    elif below[0] == 0:
        st = 'below_at_first'; a = dict(rpt_L=np.nan, rpt_U=np.nan, cyc_L=np.nan, cyc_U=np.nan, soh_L=np.nan, soh_U=np.nan)
    else:
        j = below[0]
        st = 'exact_hit' if soh[j] == THR else 'interval'
        a = dict(rpt_L=rr[j - 1], rpt_U=rr[j], cyc_L=cum[j - 1], cyc_U=cum[j], soh_L=soh[j - 1], soh_U=soh[j])
    rows.append(dict(cell=int(c), status=st, soh_last=soh[-1], cyc_last=cum[-1], **a))
eol = pd.DataFrame(rows)
print('\n(4) UCONN interval-censored EOL (SOH<80):')
print(eol.status.value_counts().to_string())
print('   soh_last: min=%.2f median=%.2f max=%.2f' % (eol.soh_last.min(), eol.soh_last.median(), eol.soh_last.max()))
wc = (eol.cyc_U - eol.cyc_L).dropna()
ws = (eol.soh_L - eol.soh_U).dropna()
print('   bracket width: cycles median=%.0f p90=%.0f max=%.0f | SOH pts median=%.2f p90=%.2f max=%.2f'
      % (wc.median(), np.percentile(wc, 90), wc.max(), ws.median(), np.percentile(ws, 90), ws.max()))
print('   EOL location in cycles: min=%.0f median=%.0f max=%.0f' % (eol.cyc_U.min(), eol.cyc_U.median(), eol.cyc_U.max()))

# ---------- Ah throughput ----------
ahs = []
for c, g in rpt.groupby('cell_id'):
    g = g.sort_values('rpt')
    s = g.seg.values.astype(float); q = g.q.values.astype(float)
    m = np.isfinite(s) & np.isfinite(q)
    s, q = s[m], q[m]
    ahs.append(float(np.sum(q[1:] * s[1:])))
ahs = np.array(ahs)
print('\n(5) UCONN Ah throughput (DERIVED: sum over RPT intervals of q_dchg x segment cycles)')
print('   Ah per cell: min=%.1f median=%.1f max=%.1f' % (ahs.min(), np.median(ahs), ahs.max()))

eol.to_csv(os.path.join(OUT, 'uconn_eol2.csv'), index=False)
json.dump(dict(rows=len(rpt), cells=int(rpt.cell_id.nunique()),
               seg_pcts={str(p): float(np.percentile(segs, p)) for p in [0, 5, 25, 50, 75, 95, 100]},
               seg_cv=float(segs.std() / segs.mean()), percell_cv_median=float(np.median(cvlist)),
               cum_total_median=float(np.median(cumtot)),
               eol=eol.status.value_counts().to_dict(),
               bracket_cyc_median=float(wc.median()),
               ah_min=float(ahs.min()), ah_median=float(np.median(ahs)), ah_max=float(ahs.max())),
          open(os.path.join(OUT, 'uconn_final.json'), 'w'), indent=1)

# ---------- ISU robustness: C/2 vs C/5, first vs max normalization ----------
print('\n' + '=' * 70)
print('ISU robustness of EOL counts to SOH definition')
import re, zipfile
ZP = r'E:\桌面\rul\data\external\isu_raw\RPT_json.zip'
z = zipfile.ZipFile(ZP)
members = sorted([n for n in z.namelist() if n.endswith('.json')])
CAP2 = re.compile(r'capacity_discharge_C_2\\?"\s*:\s*\[(.*?)\]', re.S)
CAP5 = re.compile(r'capacity_discharge_C_5\\?"\s*:\s*\[(.*?)\]', re.S)
NUM = re.compile(r'-?\d+\.?\d*(?:[eE][-+]?\d+)?')
caps = {}
for n in members:
    raw = z.read(n).decode('utf-8', 'replace')
    cell = os.path.basename(n).replace('.json', '')
    c2 = [float(x) for x in NUM.findall(CAP2.search(raw).group(1))]
    c5 = [float(x) for x in NUM.findall(CAP5.search(raw).group(1))]
    caps[cell] = (np.array(c2), np.array(c5))
for which in ['C_2', 'C_5']:
    for norm in ['first', 'max']:
        cnt = {'interval': 0, 'right_censored': 0, 'exact_hit': 0, 'below_at_first': 0}
        for cell, (c2, c5) in caps.items():
            cap = c2 if which == 'C_2' else c5
            if cap.size < 2:
                continue
            ref = cap[0] if norm == 'first' else np.nanmax(cap)
            soh = cap / ref
            b = np.where(soh < 0.80)[0]
            if len(b) == 0: cnt['right_censored'] += 1
            elif b[0] == 0: cnt['below_at_first'] += 1
            elif soh[b[0]] == 0.80: cnt['exact_hit'] += 1
            else: cnt['interval'] += 1
        print('   %s / norm=%s -> %s' % (which, norm, cnt))
