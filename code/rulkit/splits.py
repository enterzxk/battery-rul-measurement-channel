# -*- coding: utf-8 -*-
"""统一划分：LOGO（留一工况组）/ LOCO（留一电芯）。

与 scripts/e1_final.py 的 predict() 语义完全一致：
  - 折键：LOGO 用 group_id，LOCO 用 cell_id
  - 训练集过小（< min_train）或测试集为空的折被跳过，该折预测保持 NaN
  - 指标只在非 NaN 行上计算
"""
from __future__ import annotations

import numpy as np

PROTOCOLS = ("logo", "loco")


def fold_keys(protocol, cells, grp):
    if protocol == "logo":
        return np.unique(grp)
    if protocol == "loco":
        return np.unique(cells)
    raise ValueError("unknown protocol: %r" % (protocol,))


def make_folds(protocol, cells, grp, min_train=100):
    """返回 [{fold_key, train_mask, test_mask, skipped, reason}]，顺序与 e1_final.py 一致。"""
    cells = np.asarray(cells)
    grp = np.asarray(grp)
    out = []
    for key in fold_keys(protocol, cells, grp):
        if protocol == "logo":
            te = grp == key
        else:
            te = cells == key
        tr = ~te
        skipped = None
        if tr.sum() < min_train:
            skipped = "train<%d" % min_train
        elif te.sum() == 0:
            skipped = "empty_test"
        out.append(
            {
                "fold_key": int(key),
                "train": tr,
                "test": te,
                "n_train": int(tr.sum()),
                "n_test": int(te.sum()),
                "skipped": skipped,
            }
        )
    return out


def describe(protocol, cells, grp, min_train=100):
    folds = make_folds(protocol, cells, grp, min_train=min_train)
    used = [f for f in folds if f["skipped"] is None]
    return {
        "protocol": protocol,
        "n_folds": len(folds),
        "n_folds_used": len(used),
        "n_skipped": len(folds) - len(used),
        "skipped": [(f["fold_key"], f["skipped"]) for f in folds if f["skipped"]],
        "test_sizes": [f["n_test"] for f in folds],
        "min_train": min_train,
    }
