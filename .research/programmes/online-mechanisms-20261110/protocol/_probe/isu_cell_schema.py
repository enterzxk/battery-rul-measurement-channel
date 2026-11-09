import json, os, zipfile

p = r'E:\桌面\rul\data\external\isu_raw\one\G30C1.json'
print('size_MB=%.2f' % (os.path.getsize(p) / 1e6))
raw = open(p, 'r', encoding='utf-8', errors='replace').read()
print('first 400 chars:', repr(raw[:400]))
d = json.loads(raw)
print('after 1st load type', type(d))
if isinstance(d, str):
    d = json.loads(d)
    print('after 2nd load type', type(d))
if isinstance(d, dict):
    for k, v in d.items():
        print('  KEY', k, type(v), (len(v) if hasattr(v, '__len__') else ''))
        if isinstance(v, dict):
            for k2, v2 in list(v.items())[:8]:
                print('      ', k2, type(v2), (len(v2) if hasattr(v2, '__len__') else ''))
        if isinstance(v, list) and v:
            print('       elem0 type', type(v[0]), repr(v[0])[:300])
