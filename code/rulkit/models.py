# -*- coding: utf-8 -*-
"""模型工厂。全部实验共用同一套固定超参，保证"只换特征、不换模型"。"""
from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingRegressor

# E1 权威配置（docs/e1_final_results.md）：max_iter=300, learning_rate=0.08
HGB_DEFAULTS = {"max_iter": 300, "learning_rate": 0.08}


def hgb(seed=0, **overrides):
    kwargs = dict(HGB_DEFAULTS)
    kwargs.update(overrides)
    return HistGradientBoostingRegressor(random_state=seed, **kwargs)


def hgb_spec(seed=0, **overrides):
    """可 JSON 化的模型描述，写进 registry。"""
    spec = dict(HGB_DEFAULTS)
    spec.update(overrides)
    spec["random_state"] = seed
    return {"class": "HistGradientBoostingRegressor", "params": spec}
