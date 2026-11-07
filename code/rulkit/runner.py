# -*- coding: utf-8 -*-
"""统一执行器：一次实验 = 一个 run 目录 + 一条 registry 记录。

落盘结构（code/results/<run_id>/）
  result.json     配置 / 环境 / 指标 / 折诊断 / 耗时
  preds.npz       全量预测矩阵（行表 + 每个 特征集×协议×种子 的预测）
  preds.csv       宽表（seed 最小的一次），供人工核对与画图
  fold_log.json   逐折训练/测试规模与 MAE
"""
from __future__ import annotations

import json
import os
import time

import numpy as np

from . import env as env_mod
from . import metrics as metrics_mod
from . import models as models_mod
from . import registry as registry_mod
from . import splits as splits_mod

RESULTS_SUBDIR = os.path.join("code", "results")


def _slug(text):
    keep = []
    for ch in text:
        if ch.isalnum() or ch in "-_.":
            keep.append(ch)
        elif ch in " /+":
            keep.append("_")
    return "".join(keep)[:60] or "run"


def new_run_dir(name, repo_root, root=None):
    root = root or os.path.join(repo_root, RESULTS_SUBDIR)
    run_id = time.strftime("%Y%m%d-%H%M%S") + "_" + _slug(name)
    out = os.path.join(root, run_id)
    os.makedirs(out, exist_ok=False)
    return run_id, out


def predict_cv(X, y, cells, grp, protocol, seed, model_factory=None,
               min_train=100):
    """按协议逐折训练/预测，返回 (pred, fold_log)。"""
    factory = model_factory or (lambda s: models_mod.hgb(seed=s))
    folds = splits_mod.make_folds(protocol, cells, grp, min_train=min_train)
    pred = np.full(len(y), np.nan)
    log = []
    for fold in folds:
        if fold["skipped"] is not None:
            log.append({
                "fold": fold["fold_key"], "skipped": fold["skipped"],
                "n_train": fold["n_train"], "n_test": fold["n_test"], "mae": None,
            })
            continue
        tr, te = fold["train"], fold["test"]
        model = factory(seed)
        model.fit(X[tr], y[tr])
        p = model.predict(X[te])
        pred[te] = p
        log.append({
            "fold": fold["fold_key"], "skipped": None,
            "n_train": fold["n_train"], "n_test": fold["n_test"],
            "mae": float(np.mean(np.abs(y[te] - p))),
        })
    return pred, log


def evaluate(y, pred, cells, protocols, seeds):
    """把预测矩阵汇总成指标表。"""
    out = {}
    for protocol in protocols:
        per_seed = {}
        for seed in seeds:
            m = ~np.isnan(pred[protocol][seed])
            if m.sum() == 0:
                continue
            per_seed[int(seed)] = {
                "cell_macro_mae": metrics_mod.cell_macro_mae(
                    y[m], pred[protocol][seed][m], cells[m]),
                "row_mae": metrics_mod.row_mae(y[m], pred[protocol][seed][m]),
                "n_eval_rows": int(m.sum()),
                "n_eval_cells": int(len(np.unique(cells[m]))),
            }
        vals = [v["cell_macro_mae"] for v in per_seed.values()]
        out[protocol] = {
            "per_seed": per_seed,
            "mean": float(np.mean(vals)) if vals else None,
            "std": float(np.std(vals)) if vals else None,
            "n_seeds": len(vals),
        }
    return out


def run(name, X_sets, y, cells, grp, rpts, protocols=("logo",), seeds=(0,),
        model_factory=None, repo_root=None, root=None, min_train=100,
        meta=None, registry=True, write_csv=True, extra_metrics=None):
    """执行一组特征集 × 协议 × 种子，落盘并登记。"""
    repo_root = repo_root or os.getcwd()
    t0 = time.time()
    y = np.asarray(y, float)
    cells = np.asarray(cells)
    grp = np.asarray(grp)
    rpts = np.asarray(rpts)

    run_id, out_dir = new_run_dir(name, repo_root, root=root)
    env_info = env_mod.snapshot(repo_root)

    pred = {}
    fold_logs = {}
    timings = {}
    for set_name in X_sets:
        X = X_sets[set_name]
        pred[set_name] = {}
        for protocol in protocols:
            pred[set_name][protocol] = {}
            for seed in seeds:
                t1 = time.time()
                p, log = predict_cv(X, y, cells, grp, protocol, int(seed),
                                    model_factory=model_factory, min_train=min_train)
                pred[set_name][protocol][int(seed)] = p
                timings["%s|%s|s%d" % (set_name, protocol, int(seed))] = round(time.time() - t1, 2)
                if protocol == protocols[0] and int(seed) == int(min(seeds)):
                    fold_logs[set_name] = {"protocol": protocol, "seed": int(seed), "folds": log}
        print("[%s] done %s (%.1fs)" % (run_id, set_name, time.time() - t0), flush=True)

    scores = {
        set_name: evaluate(y, pred[set_name], cells, protocols, seeds)
        for set_name in X_sets
    }

    base_seed = int(min(seeds))
    primary = protocols[0]
    per_cell = {}
    for set_name in X_sets:
        p = pred[set_name][primary][base_seed]
        m = ~np.isnan(p)
        per_cell[set_name] = metrics_mod.per_cell_mae(y[m], p[m], cells[m])

    deltas = {}
    if len(X_sets) > 1:
        base_name = next(iter(X_sets))
        base = per_cell[base_name]
        keys = sorted(base)
        for set_name in X_sets:
            if set_name == base_name:
                continue
            other = per_cell[set_name]
            diffs = np.array([other[c] - base[c] for c in keys], float)
            deltas[set_name] = {
                "vs": base_name,
                "protocol": primary,
                "seed": base_seed,
                "bootstrap": metrics_mod.paired_bootstrap(diffs, n_boot=5000, seed=0),
            }

    npz = {
        "row_y": y, "row_cells": cells, "row_rpts": rpts, "row_grp": grp,
    }
    for set_name in X_sets:
        for protocol in protocols:
            for seed in seeds:
                npz["pred__%s__%s__s%d" % (set_name, protocol, int(seed))] = (
                    pred[set_name][protocol][int(seed)])
    np.savez_compressed(os.path.join(out_dir, "preds.npz"), **npz)

    if write_csv:
        cols = ["row_idx", "cell_id", "rpt", "group_id", "y_true"]
        header_preds = []
        for set_name in X_sets:
            for protocol in protocols:
                if base_seed in pred[set_name][protocol]:
                    header_preds.append((set_name, protocol,
                                         pred[set_name][protocol][base_seed]))
        cols += ["pred_%s_%s" % (s, p) for s, p, _ in header_preds]
        lines = [",".join(cols)]
        for i in range(len(y)):
            row = [str(i), str(int(cells[i])), str(int(rpts[i])), str(int(grp[i])),
                   "%.6f" % y[i]]
            for _, _, pv in header_preds:
                v = pv[i]
                row.append("" if np.isnan(v) else "%.6f" % v)
            lines.append(",".join(row))
        with open(os.path.join(out_dir, "preds.csv"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    result = {
        "run_id": run_id,
        "name": name,
        "created_local": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "repo_root": repo_root,
        "out_dir": out_dir,
        "env": env_info,
        "data": {
            "n_rows": int(len(y)),
            "n_cells": int(len(np.unique(cells))),
            "n_groups": int(len(np.unique(grp))),
            "y_min": float(y.min()), "y_max": float(y.max()),
            "y_mean": float(y.mean()),
        },
        "config": {
            "feature_sets": {k: int(v.shape[1]) for k, v in X_sets.items()},
            "protocols": list(protocols),
            "seeds": [int(s) for s in seeds],
            "min_train": int(min_train),
            "model": models_mod.hgb_spec(seed=base_seed),
        },
        "splits": {
            p: splits_mod.describe(p, cells, grp, min_train=min_train)
            for p in protocols
        },
        "scores": scores,
        "per_cell_mae": {k: {str(c): round(v, 4) for c, v in d.items()}
                         for k, d in per_cell.items()},
        "deltas": deltas,
        "fold_logs": fold_logs,
        "timings_s": timings,
        "elapsed_s": round(time.time() - t0, 2),
        "meta": meta or {},
    }
    if extra_metrics:
        result["extra"] = extra_metrics
    with open(os.path.join(out_dir, "result.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "fold_log.json"), "w", encoding="utf-8") as fh:
        json.dump(fold_logs, fh, ensure_ascii=False, indent=1)

    if registry:
        path = registry_mod.default_path(repo_root)
        registry_mod.ensure_file(path)
        registry_mod.append_entry(path, registry_mod.render_entry(result))
    return result
