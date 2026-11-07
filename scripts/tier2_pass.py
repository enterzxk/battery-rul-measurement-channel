# -*- coding: utf-8 -*-
"""Tier 2: ECM-parameter trajectory encoder + test-time physics self-supervision.

Protocol: leave-one-condition-out (LOGO). For each held-out group:
  - pre-train (RUL regression + masked reconstruction) on the other groups
  - adapt on the held-out group's *unlabelled* sequences with the reconstruction loss
  - predict
Controls: no adaptation; and a causal variant (adapt only on each cell's first half).
"""
import pickle, numpy as np, json, time, math, warnings
import torch, torch.nn as nn
from scipy.optimize import curve_fit
from sklearn.ensemble import HistGradientBoostingRegressor

warnings.filterwarnings("ignore")
torch.manual_seed(0); np.random.seed(0)
PULSE = r"E:\桌面\rul\data\external\uconn\data_slowpulse_1.pkl"
CC    = r"E:\桌面\rul\data\external\uconn\data_cc_1.pkl"
OUT   = r"C:\Users\Administrator\AppData\Local\Temp\tier2.json"
L     = 16
DEV   = "cpu"

def load(p):
    with open(p, "rb") as f:
        return pickle.load(f, encoding="latin1")

def desc_feats(v, kind):
    v = np.asarray(v, float); v0 = v[0]
    ip = int(np.argmax(v)) if kind == "chg" else int(np.argmin(v))
    return abs(v[ip] - v0), ip

def ecm_fit(v, kind, ip):
    seg = np.asarray(v[ip:], float)
    if seg.size < 15: return (np.nan,) * 5
    x = np.arange(seg.size, dtype=float); y = seg
    c0 = float(y[-1]); a0 = float(y[0] - y[-1])
    p0 = [c0, a0 * .6, 5., a0 * .4, 40.]
    lo = [y.min() - .2, -.6, 1., -.6, 10.]
    hi = [y.max() + .2, .6, 60., .6, 400.]
    try:
        popt, _ = curve_fit(lambda x, c, a1, t1, a2, t2: c + a1*np.exp(-x/t1) + a2*np.exp(-x/t2),
                            x, y, p0=p0, bounds=(lo, hi), maxfev=4000)
        return tuple(float(p) for p in popt)
    except Exception:
        return (np.nan,) * 5

def build():
    dp = load(PULSE)
    cell, rpt, soc, pt, V = dp["cell_id"], dp["rpt"], dp["soc"], dp["pulse_type"], dp["voltage"]
    soh = dp["soh"]
    gmap = {int(c): int(g) for c, g in zip(dp["cell_id"], dp["group_id"])}
    ecm, dv = {}, {}
    for i in range(len(cell)):
        k = (int(cell[i]), int(rpt[i]), int(soc[i]), str(pt[i]))
        d, ip = desc_feats(V[i], k[3]); dv[k] = d; ecm[k] = ecm_fit(V[i], k[3], ip)
    soh_map = {}
    for c, r, s in zip(cell, rpt, soh): soh_map[(int(c), int(r))] = float(s)
    keys = sorted({(k[0], k[1]) for k in ecm})
    E, D, K = [], [], []
    for (c, r) in keys:
        fe, fd, ok = [], [], True
        for s in (20, 50, 90):
            for kk in ("chg", "dchg"):
                q = (c, r, s, kk)
                if q not in ecm: ok = False; break
                fe += list(ecm[q]); fd += [dv[q]]
            if not ok: break
        if not ok: continue
        fd += [np.nanstd([dv[(c, r, s, "chg")] for s in (20, 50, 90)]),
               np.nanstd([dv[(c, r, s, "dchg")] for s in (20, 50, 90)])]
        E.append(fe); D.append(fd); K.append((c, r))
    E = np.array(E); D = np.array(D)
    cells = np.array([k[0] for k in K]); rpts = np.array([k[1] for k in K])
    sh = np.array([soh_map[k] for k in K]); grp = np.array([gmap[c] for c in cells])

    dc = load(CC)
    cc_cell, cc_rpt, ccV = dc["cell_id"], dc["rpt"], dc["voltage"]
    buckets = {}
    for i in range(len(cc_cell)):
        buckets.setdefault((int(cc_cell[i]), int(cc_rpt[i])), []).append(i)
    pfeat = {}
    for k, idxs in buckets.items():
        idxs = sorted(idxs, key=lambda i: float(np.mean(ccV[i])))
        curve = np.concatenate([np.asarray(ccV[i], float) for i in idxs])
        bins = np.array_split(curve, 50)
        pfeat[k] = [b.mean() for b in bins] + [curve.mean(), curve.std(), curve.min(), curve.max()]
    keep = [i for i, k in enumerate(K) if k in pfeat]
    A = np.array([pfeat[K[i]] for i in keep])
    E, D, cells, rpts, sh, grp = E[keep], D[keep], cells[keep], rpts[keep], sh[keep], grp[keep]
    K = [K[i] for i in keep]

    eol = {}
    for c in np.unique(cells):
        m = cells == c; o = np.argsort(rpts[m])
        rr, ss = rpts[m][o], sh[m][o]
        hit = np.where(ss <= 80.0)[0]
        if len(hit): eol[c] = int(rr[hit[0]])
    ok = np.array([c in eol and r <= eol[c] for c, r in zip(cells, rpts)])
    return dict(E=E[ok], D=D[ok], A=A[ok], cells=cells[ok], rpts=rpts[ok],
                grp=grp[ok], eol=eol, soh=sh[ok])

def make_sequences(E, cells, rpts, L):
    """Per-row index list into E forming the last-L window of that cell."""
    idx = []
    order = {}
    for i, c in enumerate(cells):
        order.setdefault(c, []).append(i)
    pos = {}
    for c, ids in order.items():
        ids = sorted(ids, key=lambda i: rpts[i])
        for j, i in enumerate(ids): pos[i] = j
    for i in range(len(cells)):
        c = cells[i]; j = pos[i]
        ids = sorted(order[c], key=lambda k: rpts[k])
        lo = max(0, j - L + 1)
        win = ids[lo:j + 1]
        pad = [win[0]] * (L - len(win))
        idx.append(pad + win)
    return np.array(idx)

class Net(nn.Module):
    def __init__(self, d_in, d_static, h=32):
        super().__init__()
        self.gru = nn.GRU(d_in, h, batch_first=True)
        self.rec = nn.Linear(h, d_in)
        self.head = nn.Sequential(nn.Linear(h + d_static, 64), nn.ReLU(), nn.Linear(64, 1))
    def forward(self, x, s, mask=None):
        h, _ = self.gru(x)
        z = h[:, -1]
        out = self.head(torch.cat([z, s], 1)).squeeze(1)
        rec = self.rec(h)
        return out, rec

def standardize(train, *others):
    mu = train.mean(0); sd = train.std(0) + 1e-8
    return [(o - mu) / sd for o in (train, *others)], (mu, sd)

def run_fold(Xs, Xst, y, seqidx, tr, te, adapt_idx=None, epochs=150, adapt_steps=60, lr=3e-3):
    dev = DEV
    net = Net(Xs.shape[2], Xst.shape[1]).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    xa = torch.tensor(Xs[tr], dtype=torch.float32)
    sa = torch.tensor(Xst[tr], dtype=torch.float32)
    ya = torch.tensor(y[tr], dtype=torch.float32)
    n = len(tr)
    for ep in range(epochs):
        perm = np.random.permutation(n)
        for b in range(0, n, 128):
            bi = perm[b:b + 128]
            xb, sb, yb = xa[bi], sa[bi], ya[bi]
            m = torch.rand(xb.shape[0], xb.shape[1]) < 0.2
            xin = xb.clone(); xin[m] = 0.0
            pred, rec = net(xin, sb)
            loss = nn.functional.mse_loss(pred, yb) + 0.5 * nn.functional.mse_loss(rec[m], xb[m])
            opt.zero_grad(); loss.backward(); opt.step()
    if adapt_idx is not None and len(adapt_idx) > 0:
        xad = torch.tensor(Xs[adapt_idx], dtype=torch.float32)
        sad = torch.tensor(Xst[adapt_idx], dtype=torch.float32)
        for _ in range(adapt_steps):
            m = torch.rand(xad.shape[0], xad.shape[1]) < 0.3
            xin = xad.clone(); xin[m] = 0.0
            _, rec = net(xin, sad)
            loss = nn.functional.mse_loss(rec[m], xad[m])
            opt.zero_grad(); loss.backward(); opt.step()
    net.eval()
    with torch.no_grad():
        pred, _ = net(torch.tensor(Xs[te], dtype=torch.float32), torch.tensor(Xst[te], dtype=torch.float32))
    return pred.numpy()

def cell_macro(y, p, cells):
    return float(np.mean([np.mean(np.abs(y[cells == c] - p[cells == c])) for c in np.unique(cells)]))

def main():
    d = build()
    E, D, A = d["E"], d["D"], d["A"]
    cells, rpts, grp = d["cells"], d["rpts"], d["grp"]
    y = np.array([d["eol"][c] - r for c, r in zip(cells, rpts)], float)
    seq = make_sequences(E, cells, rpts, L)

    # normalise ECM params (per-dim) using global stats; static features too
    Emu, Esd = E.mean(0), E.std(0) + 1e-8
    Es = (E - Emu) / Esd
    Amu, Asd = A.mean(0), A.std(0) + 1e-8
    As = (A - Amu) / Asd
    Xs = Es[seq]                       # (N, L, d)

    res = {"n": int(len(y)), "n_cells": int(len(np.unique(cells))), "groups": {}}
    preds = {"no_adapt": np.full(len(y), np.nan), "adapt": np.full(len(y), np.nan),
             "adapt_causal": np.full(len(y), np.nan)}
    t0 = time.time()
    for g in np.unique(grp):
        te = np.where(grp == g)[0]
        tr = np.where(grp != g)[0]
        if len(tr) < 100: continue
        # transductive adaptation: all held-out rows
        p1 = run_fold(Xs, As, y, seq, tr, te, adapt_idx=None)
        p2 = run_fold(Xs, As, y, seq, tr, te, adapt_idx=te)
        # causal adaptation: only the first half of each cell's trajectory in the held-out group
        first = []
        for c in np.unique(cells[te]):
            ids = te[cells[te] == c]
            ids = ids[np.argsort(rpts[ids])]
            first += list(ids[:max(1, len(ids) // 2)])
        p3 = run_fold(Xs, As, y, seq, tr, te, adapt_idx=np.array(first))
        preds["no_adapt"][te] = p1; preds["adapt"][te] = p2; preds["adapt_causal"][te] = p3
        res["groups"][int(g)] = dict(n=int(len(te)),
                                     no_adapt=round(cell_macro(y[te], p1, cells[te]), 3),
                                     adapt=round(cell_macro(y[te], p2, cells[te]), 3),
                                     adapt_causal=round(cell_macro(y[te], p3, cells[te]), 3))
        print("group", int(g), res["groups"][int(g)], flush=True)

    for k in preds:
        m = ~np.isnan(preds[k])
        res[k] = round(cell_macro(y[m], preds[k][m], cells[m]), 3)
    res["sec"] = round(time.time() - t0, 1)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ["no_adapt", "adapt", "adapt_causal", "sec"]}, indent=1))

main()
