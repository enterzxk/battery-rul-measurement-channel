# -*- coding: utf-8 -*-
"""统一指标。主指标 = 电芯宏平均 MAE（cell-macro MAE），与 e1_final.py 的 cm() 同定义。"""
from __future__ import annotations

import numpy as np


def cell_macro_mae(y, pred, cells):
    """先对每个电芯内部求平均绝对误差，再对电芯取平均（每个电芯等权）。"""
    y = np.asarray(y, float)
    pred = np.asarray(pred, float)
    cells = np.asarray(cells)
    vals = [
        float(np.mean(np.abs(y[cells == c] - pred[cells == c])))
        for c in np.unique(cells)
    ]
    return float(np.mean(vals))


def per_cell_mae(y, pred, cells):
    y = np.asarray(y, float)
    pred = np.asarray(pred, float)
    cells = np.asarray(cells)
    return {
        int(c): float(np.mean(np.abs(y[cells == c] - pred[cells == c])))
        for c in np.unique(cells)
    }


def row_mae(y, pred):
    return float(np.mean(np.abs(np.asarray(y, float) - np.asarray(pred, float))))


def paired_bootstrap(diffs, n_boot=5000, seed=0):
    """电芯级配对重采样：diffs = 每个电芯的 (候选 - 基线) MAE。"""
    diffs = np.asarray(diffs, float)
    rng = np.random.default_rng(seed)
    bs = np.array(
        [np.mean(rng.choice(diffs, len(diffs), replace=True)) for _ in range(n_boot)]
    )
    return {
        "delta": float(diffs.mean()),
        "ci_low": float(np.percentile(bs, 2.5)),
        "ci_high": float(np.percentile(bs, 97.5)),
        "frac_improved": float((diffs < 0).mean()),
        "n_cells": int(len(diffs)),
        "n_boot": int(n_boot),
        "seed": int(seed),
    }
