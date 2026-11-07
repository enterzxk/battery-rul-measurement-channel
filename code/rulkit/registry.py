# -*- coding: utf-8 -*-
"""追加写入 EXPERIMENT_REGISTRY.md —— 只追加，绝不覆盖已有内容。"""
from __future__ import annotations

import os

HEADER = """# EXPERIMENT REGISTRY

> 由 Implementation & Experiment Engineer (A4) 维护。
> **规则**：任何实验都必须先在此登记；只追加、不覆盖；配置 / 种子 / 结果路径三者缺一不可。

## 如何复现

每条记录给出 run_id、命令、配置、种子、耗时、指标、结果目录
（`code/results/<run_id>/` 含 `result.json` / `preds.npz` / `preds.csv` / `fold_log.json`）。

## 记录索引

| # | run_id | 名称 | 主指标 | 耗时 |
|---|---|---|---|---|
"""


def default_path(repo_root):
    return os.path.join(repo_root, "docs", "autonomous_research", "EXPERIMENT_REGISTRY.md")


def ensure_file(path):
    """只在文件不存在时创建（含表头）。绝不覆盖。"""
    if os.path.exists(path):
        return False
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(HEADER)
    return True


def render_entry(result):
    """把 result.json 渲染成一段 markdown（追加到文件末尾）。"""
    r = result
    cfg = r["config"]
    lines = []
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## %s" % r["run_id"])
    lines.append("")
    lines.append("| 项 | 值 |")
    lines.append("|---|---|")
    lines.append("| 名称 | %s |" % r["name"])
    lines.append("| 时间 | %s |" % r["created_local"])
    lines.append("| 命令 | `%s` |" % r.get("meta", {}).get("command", "n/a"))
    lines.append("| 结果目录 | `%s` |" % os.path.relpath(
        r["out_dir"], r["repo_root"]).replace("\\", "/"))
    lines.append("| 行数 / 电芯 / 工况组 | %d / %d / %d |" % (
        r["data"]["n_rows"], r["data"]["n_cells"], r["data"]["n_groups"]))
    lines.append("| 标签范围 (min/mean/max) | %.1f / %.2f / %.1f |" % (
        r["data"]["y_min"], r["data"]["y_mean"], r["data"]["y_max"]))
    lines.append("| 协议 | %s |" % ", ".join(cfg["protocols"]))
    lines.append("| 种子 | %s |" % cfg["seeds"])
    lines.append("| 模型 | %s(%s) |" % (
        cfg["model"]["class"],
        ", ".join("%s=%s" % (k, v) for k, v in cfg["model"]["params"].items())))
    lines.append("| min_train | %d |" % cfg["min_train"])
    lines.append("| 耗时 | %.1f s |" % r["elapsed_s"])
    lines.append("")
    lines.append("### 特征集与指标（cell-macro MAE，越低越好）")
    lines.append("")
    header = ["特征集", "维度"] + ["%s (mean±std)" % p.upper() for p in cfg["protocols"]]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] + ["---:"] * (len(header) - 1)) + "|")
    for set_name, dim in cfg["feature_sets"].items():
        cells = [set_name, str(dim)]
        for p in cfg["protocols"]:
            s = r["scores"].get(set_name, {}).get(p)
            if not s or s["mean"] is None:
                cells.append("—")
            elif s["n_seeds"] > 1:
                cells.append("%.3f ± %.3f" % (s["mean"], s["std"]))
            else:
                cells.append("%.3f" % s["mean"])
        lines.append("| " + " | ".join(cells) + " |")
    if r.get("deltas"):
        lines.append("")
        lines.append("### 配对 bootstrap（电芯级，5000 次重采样，seed=0）")
        lines.append("")
        lines.append("| 对比 | Δ | 95% CI | 改善电芯比例 |")
        lines.append("|---|---:|---|---:|")
        for name, d in r["deltas"].items():
            b = d["bootstrap"]
            lines.append("| %s vs %s | %+.3f | [%+.3f, %+.3f] | %.1f%% |" % (
                name, d["vs"], b["delta"], b["ci_low"], b["ci_high"],
                100.0 * b["frac_improved"]))
    splits = r.get("splits", {})
    if splits:
        lines.append("")
        lines.append("### 折结构")
        lines.append("")
        for p, d in splits.items():
            lines.append("- %s：%d 折，使用 %d 折，跳过 %d 折（%s），min_train=%d" % (
                p.upper(), d["n_folds"], d["n_folds_used"], d["n_skipped"],
                d["skipped"] or "无", d["min_train"]))
    env = r["env"]
    lines.append("")
    lines.append("### 运行环境")
    lines.append("")
    lines.append("| 项 | 值 |")
    lines.append("|---|---|")
    lines.append("| OS | %s |" % env["platform"])
    lines.append("| Python | %s |" % env["python_version"])
    lines.append("| CPU 逻辑核 | %s |" % env["cpu_logical"])
    lines.append("| 包版本 | %s |" % ", ".join(
        "%s %s" % (k, v) for k, v in env["packages"].items() if v != "MISSING"))
    lines.append("| git | %s @ %s |" % (env["git"]["branch"], env["git"]["commit"]))
    notes = r.get("meta", {}).get("notes")
    if notes:
        lines.append("")
        lines.append("### 备注")
        lines.append("")
        for note in notes:
            lines.append("- %s" % note)
    return "\n".join(lines) + "\n"


def append_entry(path, text):
    """追加一段记录；保证与上文之间至少有一个空行。"""
    with open(path, "r", encoding="utf-8") as fh:
        existing = fh.read()
    if existing and not existing.endswith("\n"):
        text = "\n" + text
    elif existing and not existing.endswith("\n\n"):
        text = "\n" + text
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text)
