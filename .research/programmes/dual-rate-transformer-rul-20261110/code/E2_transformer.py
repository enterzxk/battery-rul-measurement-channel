# -*- coding: utf-8 -*-
"""E2 · Does a causal sequence model beat a strong tabular learner on the SAME legal inputs?

This is the brief's E2 ("does sequence modelling add value") and it is deliberately
independent of the novelty question: if a Transformer cannot beat LightGBM given
exactly the same legal information, no amount of M3-M5 machinery is worth building.

Legal information (identical for both arms):
    per RPT token:  day, soh, day_gap since previous RPT, cycles accumulated since
                    previous RPT (log1p), cycle-count total (log1p), index
    NOTE: cumulative Ah is EXCLUDED. An audit measured
          Spearman(per-cycle capacity_charge, concurrent C/5 capacity) = 0.995 with
          median(capacity_charge / concurrent capacity) = 0.30 = protocol DoD, so
          per-cycle Ah is a health measurement and is not a legal operating signal.

Arms
    TF        causal Transformer over the RPT-token sequence, last-token readout
    LGBM      LightGBM on the last-token features only (same information, no sequence)
    LGBM_seq  LightGBM on last token + simple sequence summaries (mean/slope of gaps)

All leave-one-condition-out, identical folds, condition-macro MAE, paired bootstrap.

Run remotely.  usage: python E2_transformer.py [cycles|days|ah]
"""
import os
import sys
import json

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import lightgbm as lgb

PROTO = os.environ.get("DLINE_PROTO", "/home/user/dline/prog/protocol")
OUT = os.environ.get("DLINE_OUT", PROTO)
TARGET = sys.argv[1] if len(sys.argv) > 1 else "cycles"
SEED = 0
MAXLEN = 96
DEV = "cuda" if torch.cuda.is_available() else "cpu"

TOK = ["day", "soh", "gap_day", "dcyc", "cumcyc", "idx"]


def build(C):
    """Return (list of per-cell token arrays, query table)."""
    seqs, rows = {}, []
    for cell, g in C.groupby("cell"):
        g = g.sort_values("rpt_idx").reset_index(drop=True)
        j = int(g.eol_rpt.iloc[0])
        if j < 2:
            continue
        day = g.day.values.astype(float)
        soh = g.soh.values.astype(float)
        N = g.cum_cycles.values.astype(float)
        ah = g.cum_ah_ch.values.astype(float)
        gap = np.diff(np.concatenate([[0.0], day]))
        dcyc = np.diff(np.concatenate([[0.0], N]))
        toks = np.stack([day, soh, gap, np.log1p(dcyc), np.log1p(N),
                         np.arange(len(g), dtype=float)], axis=1)
        seqs[cell] = toks[:j]          # only tokens before the crossing
        n_eol = 0.5 * (float(g.N_L.iloc[0]) + float(g.N_U.iloc[0]))
        d_eol = 0.5 * (float(g.L.iloc[0]) + float(g.U.iloc[0]))
        ah_eol = 0.5 * (float(ah[j - 1]) + float(ah[j]))
        for k in range(1, j):
            if TARGET == "cycles":
                rul = n_eol - N[k]
            elif TARGET == "days":
                rul = d_eol - day[k]
            else:
                rul = ah_eol - ah[k]
            if not np.isfinite(rul) or rul <= 0:
                continue
            rows.append(dict(cell=cell, cond=int(g.cond.iloc[0]), rpt_idx=int(k),
                             y=float(np.log(rul)), rul=float(rul),
                             day=day[k], soh=soh[k], gap_day=gap[k],
                             dcyc=float(np.log1p(dcyc[k])),
                             cumcyc=float(np.log1p(N[k])), idx=float(k),
                             dod=float(g.dod_meas.iloc[0])))
    return seqs, pd.DataFrame(rows)


class CausalTF(nn.Module):
    def __init__(self, d_in, d=64, layers=2, heads=4, drop=0.1):
        super().__init__()
        self.proj = nn.Linear(d_in, d)
        self.pos = nn.Parameter(torch.zeros(1, MAXLEN, d))
        nn.init.normal_(self.pos, std=0.02)
        enc = nn.TransformerEncoderLayer(d, heads, 4 * d, dropout=drop,
                                         batch_first=True, norm_first=True)
        self.enc = nn.TransformerEncoder(enc, layers)
        self.norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, 1)

    def forward(self, x, mask):
        B, L, _ = x.shape
        h = self.proj(x) + self.pos[:, :L]
        causal = torch.triu(torch.ones(L, L, device=x.device, dtype=torch.bool), 1)
        h = self.enc(h, mask=causal, src_key_padding_mask=~mask)
        h = self.norm(h)
        last = mask.long().sum(1) - 1
        out = h[torch.arange(B, device=x.device), last]
        return self.head(out).squeeze(-1)


def pad_batch(seqs, cells, ks):
    B = len(cells)
    L = max(int(ks[i]) + 1 for i in range(B))
    L = min(L, MAXLEN)
    x = np.zeros((B, L, len(TOK)), np.float32)
    m = np.zeros((B, L), bool)
    for i, c in enumerate(cells):
        s = seqs[c][:min(int(ks[i]) + 1, L)]
        x[i, :len(s)] = s
        m[i, :len(s)] = True
    return torch.from_numpy(x), torch.from_numpy(m)


def train_tf(seqs, tr, epochs=60, lr=1e-3):
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    model = CausalTF(len(TOK)).to(DEV)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    cells = tr.cell.values
    ks = tr.rpt_idx.values
    y = torch.tensor(tr.y.values, dtype=torch.float32, device=DEV)
    n = len(tr)
    for ep in range(epochs):
        model.train()
        perm = np.random.permutation(n)
        for b in range(0, n, 128):
            idx = perm[b:b + 128]
            x, m = pad_batch(seqs, cells[idx], ks[idx])
            x, m = x.to(DEV), m.to(DEV)
            pred = model(x, m)
            loss = nn.functional.l1_loss(pred, y[idx])
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
    model.eval()
    return model


@torch.no_grad()
def predict_tf(model, seqs, te):
    model.eval()
    out = np.zeros(len(te), np.float32)
    cells, ks = te.cell.values, te.rpt_idx.values
    for b in range(0, len(te), 256):
        idx = np.arange(b, min(b + 256, len(te)))
        x, m = pad_batch(seqs, [cells[i] for i in idx], [ks[i] for i in idx])
        out[idx] = model(x.to(DEV), m.to(DEV)).cpu().numpy()
    return out


def cm_mae(pred, true, cond):
    return pd.DataFrame({"e": np.abs(pred - true), "cond": cond}).groupby("cond").e.mean()


def paired_gain(a, b, n_boot=4000, seed=0):
    idx = a.index.intersection(b.index)
    x, y = a.loc[idx].values, b.loc[idx].values
    n = len(idx)
    g = 100.0 * (y.mean() / x.mean() - 1.0)
    rng = np.random.default_rng(seed)
    bs = np.array([100.0 * (y[k].mean() / x[k].mean() - 1.0)
                   for k in (rng.integers(0, n, n) for _ in range(n_boot))])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return float(g), float(lo), float(hi)


def main():
    C = pd.read_csv(os.path.join(PROTO, "G0_cohort.csv"))
    seqs, Q = build(C)
    conds = sorted(Q.cond.unique())
    print("=== E2 · sequence vs tabular on identical LEGAL inputs ===")
    print("target=%s | device=%s | rows %d | cells %d | conditions %d" % (
        TARGET, DEV, len(Q), Q.cell.nunique(), len(conds)))

    LGB = ["day", "soh", "gap_day", "dcyc", "cumcyc", "idx", "dod"]
    LGB_SEQ = LGB + ["n_tok"]
    Q["n_tok"] = Q.rpt_idx + 1

    p_tf = np.full(len(Q), np.nan)
    p_lg = np.full(len(Q), np.nan)
    p_ls = np.full(len(Q), np.nan)
    for ci, held in enumerate(conds):
        te = (Q.cond == held).values
        tr = ~te
        if tr.sum() < 300 or te.sum() == 0:
            continue
        m = train_tf(seqs, Q[tr])
        p_tf[te] = predict_tf(m, seqs, Q[te])
        for feats, dst in ((LGB, p_lg), (LGB_SEQ, p_ls)):
            g = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.05, num_leaves=15,
                                  min_child_samples=20, subsample=0.9,
                                  colsample_bytree=0.9, random_state=SEED,
                                  verbose=-1, n_jobs=4)
            g.fit(Q.loc[tr, feats].values, Q.loc[tr, "y"].values)
            dst[te] = g.predict(Q.loc[te, feats].values)
        if ci % 15 == 0:
            print("  fold %d/%d cond=%s" % (ci + 1, len(conds), held), flush=True)

    ok = np.isfinite(p_tf) & np.isfinite(p_lg) & np.isfinite(p_ls)
    true_v = Q.rul.values[ok]
    cond = Q.cond.values[ok]
    res = {}
    print("\n  %-10s %-12s %-10s %s" % ("arm", "condMAE", "med|log|", "vs LGBM"))
    for name, p in [("LGBM", p_lg), ("LGBM_seq", p_ls), ("TF", p_tf)]:
        pc = np.clip(np.expm1(p[ok]), 1e-6, None)
        cm = cm_mae(pc, true_v, cond)
        ml = float(np.median(np.abs(np.log(pc / true_v))))
        res[name] = cm
        print("  %-10s %-12.4g %-10.3f" % (name, cm.mean(), ml), end="")
        if name != "LGBM":
            g, lo, hi = paired_gain(res["LGBM"], cm)
            print("  %+6.1f%% [%+6.1f,%+6.1f]" % (g, lo, hi))
        else:
            print("  -")

    out = dict(target=TARGET, n_rows=int(len(Q)), n_cond=int(len(conds)),
               cond_macro_mae={k: float(v.mean()) for k, v in res.items()})
    for name in ["LGBM_seq", "TF"]:
        g, lo, hi = paired_gain(res["LGBM"], res[name])
        out[name] = dict(gain=g, lo=lo, hi=hi)
    json.dump(out, open(os.path.join(OUT, "E2_%s.json" % TARGET), "w"), indent=1, default=float)
    print("\nwrote E2_%s.json" % TARGET)


if __name__ == "__main__":
    main()
