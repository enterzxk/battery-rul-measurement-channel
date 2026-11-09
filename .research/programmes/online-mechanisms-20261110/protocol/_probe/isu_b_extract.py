"""ISU-ILCC: extract per-cell RPT timestamps + capacity from all 251 RPT JSONs; cadence + EOL intervals."""
import json, re, zipfile, os, sys, time
import numpy as np
import pandas as pd

ZP = r'E:\桌面\rul\data\external\isu_raw\RPT_json.zip'
OUT = r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol\_probe'
VALID = r'E:\桌面\rul\data\external\isu_raw\Valid_cells.csv'

CAP = re.compile(r'capacity_discharge_C_5\\?"\s*:\s*\[(.*?)\]', re.S)
SST = re.compile(r'start_stop_time\\?"\s*:\s*\{\\?"start\\?"\s*:\s*\[(.*?)\].*?\\?"stop\\?"\s*:\s*\[(.*?)\]', re.S)
STR = re.compile(r'\\?"([^"\\]+)\\?"')
NUM = re.compile(r'-?\d+\.?\d*(?:[eE][-+]?\d+)?')
# any field that could be a cycle counter
CYC = re.compile(r'\\?"([a-zA-Z_]*(?:cycl|cycle|Cycl)[a-zA-Z_]*)\\?"')

z = zipfile.ZipFile(ZP)
members = [n for n in z.namelist() if n.endswith('.json')]
print('n json members =', len(members))
valid = pd.read_csv(VALID).Cell.tolist()
print('Valid_cells.csv n =', len(valid))

t0 = time.time()
recs, cyc_fields = [], {}
for i, n in enumerate(sorted(members)):
    raw = z.read(n).decode('utf-8', 'replace')
    cell = os.path.basename(n).replace('.json', '')
    grp = int(re.match(r'G(\d+)C', cell).group(1))
    cm = CAP.search(raw)
    cap = [float(x) for x in NUM.findall(cm.group(1))] if cm else []
    sm = SST.search(raw)
    st = STR.findall(sm.group(1)) if sm else []
    sp = STR.findall(sm.group(2)) if sm else []
    for f in set(CYC.findall(raw)):
        cyc_fields[f] = cyc_fields.get(f, 0) + 1
    recs.append(dict(cell=cell, group=grp, n_rpt=len(cap), n_start=len(st), n_stop=len(sp),
                     cap0=cap[0] if cap else np.nan, cap_last=cap[-1] if cap else np.nan,
                     start_first=st[0] if st else None, start_last=st[-1] if st else None,
                     _starts=st, _stops=sp, _cap=cap))
    if (i + 1) % 50 == 0:
        print('  %d/%d  %.1fs' % (i + 1, len(members), time.time() - t0), flush=True)

print('extract %.1fs' % (time.time() - t0))
print('\ncycle-counter-like field names found in ISU JSONs:', cyc_fields if cyc_fields else 'NONE')

df = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith('_')} for r in recs])
print('\ncells=%d  groups=%d' % (len(df), df.group.nunique()))
print('RPTs per cell: ' + str(df.n_rpt.value_counts().to_dict()))
print('start times present: %d / %d cells' % (df.n_start.gt(0).sum(), len(df)))
print('cells in Valid_cells but not zip: %s' % (set(valid) - set(df.cell)))
print('cells in zip but not Valid_cells: %s' % (set(df.cell) - set(valid)))

# per-condition cell counts
pc = df.groupby('group').cell.count()
print('\ncells per condition: n_conditions=%d  counts=%s' % (len(pc), pc.value_counts().to_dict()))
print('condition ids: %s' % sorted(df.group.unique().tolist()))

# ---- cadence in calendar time ----
def parse(ts):
    return np.array([np.datetime64(t.replace(' ', 'T')) for t in ts])

gaps_d, span, per_cell_gap = [], [], []
for r in recs:
    if len(r['_starts']) < 2:
        continue
    t = parse(r['_starts'])
    d = np.diff(t).astype('timedelta64[m]').astype(float) / 1440.0
    gaps_d.extend(d.tolist())
    span.append((t[-1] - t[0]).astype('timedelta64[m]').astype(float) / 1440.0)
    per_cell_gap.append(d)
gaps_d = np.array(gaps_d)
print('\n(c) CALENDAR-TIME cadence between consecutive RPTs (days), n=%d' % len(gaps_d))
print('   min=%.2f p05=%.2f p25=%.2f median=%.2f p75=%.2f p95=%.2f max=%.2f mean=%.2f sd=%.2f'
      % (gaps_d.min(), *np.percentile(gaps_d, [5, 25, 50, 75, 95]), gaps_d.max(), gaps_d.mean(), gaps_d.std()))
print('   CV = %.3f' % (gaps_d.std() / gaps_d.mean()))
print('   deciles:', np.percentile(gaps_d, np.arange(0, 101, 10)).round(2).tolist())
print('   cell campaign span (days): min=%.1f median=%.1f max=%.1f' % (min(span), np.median(span), max(span)))

# ---- EOL interval in calendar time ----
THR = 0.80
rows = []
for r in recs:
    cap = np.array(r['_cap'], float)
    if cap.size < 2:
        continue
    q0 = cap[0]
    soh = cap / q0
    below = np.where(soh < THR)[0]
    t = parse(r['_starts']) if len(r['_starts']) == cap.size else None
    if len(below) == 0:
        status = 'right_censored'; L = U = np.nan; tL = tU = np.nan
    elif below[0] == 0:
        status = 'below_at_first'; L = U = np.nan; tL = tU = np.nan
    else:
        j = below[0]
        status = 'exact_hit' if soh[j] == THR else 'interval'
        L, U = soh[j - 1], soh[j]
        tL = (t[j - 1] - t[0]).astype('timedelta64[m]').astype(float) / 1440.0 if t is not None else np.nan
        tU = (t[j] - t[0]).astype('timedelta64[m]').astype(float) / 1440.0 if t is not None else np.nan
    rows.append(dict(cell=r['cell'], group=r['group'], n_rpt=cap.size, cap0=q0,
                     soh_last=soh[-1], status=status, soh_L=L, soh_U=U,
                     rpt_L=below[0] - 1 if len(below) and below[0] > 0 else np.nan,
                     rpt_U=below[0] if len(below) else np.nan,
                     day_L=tL, day_U=tU,
                     span_day=span[len([x for x in rows])] if False else np.nan))
eol = pd.DataFrame(rows)
print('\n(4) ISU interval-censored EOL (threshold SOH < 80%% of RPT-0 discharge capacity):')
print(eol.status.value_counts().to_string())
print('   soh_last: min=%.3f median=%.3f max=%.3f ; cells with soh_last>=0.8: %d'
      % (eol.soh_last.min(), eol.soh_last.median(), eol.soh_last.max(), (eol.soh_last >= 0.8).sum()))
w = (eol.rpt_U - eol.rpt_L).dropna()
print('   interval width in RPT index: median=%.0f max=%.0f (always 1 by construction if contiguous)' % (w.median(), w.max()))
wd = (eol.day_U - eol.day_L).dropna()
print('   interval width in DAYS: n=%d median=%.1f p10=%.1f p90=%.1f max=%.1f'
      % (len(wd), wd.median(), np.percentile(wd, 10), np.percentile(wd, 90), wd.max()))
print('   EOL day (midpoint) median=%.1f' % ((eol.day_L + eol.day_U).median() / 2))

df.to_csv(os.path.join(OUT, 'isu_cells.csv'), index=False)
eol.to_csv(os.path.join(OUT, 'isu_eol.csv'), index=False)
json.dump(dict(n_cells=len(df), n_groups=int(df.group.nunique()),
               rpt_per_cell=df.n_rpt.value_counts().to_dict(),
               gap_median=float(np.median(gaps_d)), gap_cv=float(gaps_d.std() / gaps_d.mean()),
               gap_min=float(gaps_d.min()), gap_max=float(gaps_d.max()),
               eol_counts=eol.status.value_counts().to_dict(),
               day_width_median=float(wd.median()),
               span_median=float(np.median(span))),
          open(os.path.join(OUT, 'isu_summary.json'), 'w'), indent=1)
print('\nwrote isu_cells.csv, isu_eol.csv, isu_summary.json')
