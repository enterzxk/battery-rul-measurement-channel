import pickle, numpy as np, os

base = r'E:\桌面\rul\data\external\uconn'
for name in ['data_cc_1.pkl', 'data_slowpulse_1.pkl']:
    p = os.path.join(base, name)
    with open(p, 'rb') as f:
        d = pickle.load(f)
    print('=' * 78)
    print(name, 'size_MB=%.2f' % (os.path.getsize(p) / 1e6), 'n_keys=', len(d))
    for k, v in d.items():
        if isinstance(v, np.ndarray):
            if v.dtype.kind in 'iuf':
                mn, mx = float(np.nanmin(v)), float(np.nanmax(v))
            else:
                mn = mx = float('nan')
            print('  %-16s shape=%-16s dtype=%-10s min=%-12.4g max=%-12.4g' % (k, str(v.shape), str(v.dtype), mn, mx))
        else:
            print('  %-16s type=%s' % (k, type(v)))
