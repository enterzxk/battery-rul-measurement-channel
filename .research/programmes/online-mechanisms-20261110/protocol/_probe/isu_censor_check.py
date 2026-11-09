"""Are ISU's 40 '5-RPT / 25-day' cells genuinely right-censored, or a scale artifact?"""
import re, zipfile, os
import numpy as np
import pandas as pd

ZP = r'E:\桌面\rul\data\external\isu_raw\RPT_json.zip'
OUT = r'E:\桌面\rul\rul_v4_20261107\.research\programmes\online-mechanisms-20261110\protocol\_probe'
z = zipfile.ZipFile(ZP)
CAP5 = re.compile(r'capacity_discharge_C_5\\?"\s*:\s*\[(.*?)\]', re.S)
CAP2 = re.compile(r'capacity_discharge_C_2\\?"\s*:\s*\[(.*?)\]', re.S)
NUM = re.compile(r'-?\d+\.?\d*(?:[eE][-+]?\d+)?')

ie = pd.read_csv(os.path.join(OUT, 'isu_eol.csv'))
cens = set(ie[ie.status == 'right_censored'].cell)
print('right-censored cells: %d' % len(cens))

show = sorted(cens)[:4] + [c for c in sorted(ie[ie.status == 'interval'].cell)[:3]]
for cell in show:
    n = [x for x in z.namelist() if x.endswith('/' + cell + '.json')][0]
    raw = z.read(n).decode('utf-8', 'replace')
    c5 = np.array([float(x) for x in NUM.findall(CAP5.search(raw).group(1))])
    c2 = np.array([float(x) for x in NUM.findall(CAP2.search(raw).group(1))])
    print('\n%s  status=%s  n_c5=%d n_c2=%d' % (cell, ie.set_index('cell').loc[cell, 'status'], len(c5), len(c2)))
    print('  C/5 cap:', np.round(c5, 4).tolist())
    print('  C/5 soh vs first:', np.round(c5 / c5[0], 3).tolist())
    print('  C/2 cap:', np.round(c2, 4).tolist())

# distribution of cap0 for censored vs interval
rows = []
for cell in ie.cell:
    n = [x for x in z.namelist() if x.endswith('/' + cell + '.json')][0]
    raw = z.read(n).decode('utf-8', 'replace')
    c5 = np.array([float(x) for x in NUM.findall(CAP5.search(raw).group(1))])
    c2 = np.array([float(x) for x in NUM.findall(CAP2.search(raw).group(1))])
    rows.append(dict(cell=cell, n5=len(c5), n2=len(c2), cap0_5=c5[0], capmin_5=c5.min(), capmax_5=c5.max(),
                     ratio_min=c5.min() / c5.max(), cap0_2=c2[0] if len(c2) else np.nan))
t = pd.DataFrame(rows).merge(ie[['cell', 'status']], on='cell')
print('\n=== cap0 and range by status ===')
print(t.groupby('status')[['n5', 'cap0_5', 'ratio_min']].describe().T.to_string())
print('\n=== n5 vs n2 mismatch cells: %d ===' % (t.n5 != t.n2).sum())
print(t[t.n5 != t.n2].head(10).to_string())
print('\n=== censored cells: is cap monotone decreasing? ===')
for cell in sorted(cens)[:8]:
    n = [x for x in z.namelist() if x.endswith('/' + cell + '.json')][0]
    raw = z.read(n).decode('utf-8', 'replace')
    c5 = np.array([float(x) for x in NUM.findall(CAP5.search(raw).group(1))])
    print('  %s  cap=%s  d=%s' % (cell, np.round(c5, 4).tolist(), np.round(np.diff(c5), 4).tolist()))
