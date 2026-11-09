"""Validate regex extraction of start_stop_time / capacity from ISU double-encoded JSON."""
import json, re, time, os

p = r'E:\桌面\rul\data\external\isu_raw\one\G30C1.json'
t0 = time.time()
raw = open(p, 'r', encoding='utf-8', errors='replace').read()
print('read %.2fs len=%d' % (time.time() - t0, len(raw)))

t0 = time.time()
d = json.loads(json.loads(raw))
print('full json parse %.2fs' % (time.time() - t0))
print('start_stop_time:', json.dumps(d['start_stop_time'])[:400])
print('n capacity_discharge_C_5:', len(d['capacity_discharge_C_5']))
print('capacity_discharge_C_5:', [round(x, 4) for x in d['capacity_discharge_C_5']])
print('capacity keys:', [k for k in d if k.startswith('capacity')])
print('n RPT in start_stop_time:', len(d['start_stop_time']['start']))

# ---- regex attempt ----
t0 = time.time()
m = re.search(r'start_stop_time\\?"\s*:\s*\{\\?"start\\?"\s*:\s*\[(.*?)\]', raw, re.S)
print('\nregex %.3fs found=%s' % (time.time() - t0, bool(m)))
if m:
    starts = re.findall(r'\\?"([^"\\]+)\\?"', m.group(1))
    print('n starts', len(starts), starts[:3])

m2 = re.search(r'capacity_discharge_C_5\\?"\s*:\s*\[(.*?)\]', raw, re.S)
print('cap regex found=%s' % bool(m2))
if m2:
    vals = re.findall(r'-?\d+\.?\d*(?:[eE][-+]?\d+)?', m2.group(1))
    print('n vals', len(vals), vals[:5])
