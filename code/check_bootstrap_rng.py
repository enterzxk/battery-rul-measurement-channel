# -*- coding: utf-8 -*-
"""复现性诊断：为什么本框架的 bootstrap CI 与 docs/e1_final_results.md 有 0.00x 差异。

假设：scripts/e1_final.py 在循环**外面**只建了一个 rng = default_rng(0)，
三个对比依次消耗同一条随机流；本框架每个对比各自新建 default_rng(0)，
于是第一个对比完全一致、后两个的 resample 下标不同。

本脚本用同一份分电芯误差，分别用"共享随机流"和"独立随机流"重算 CI，验证假设。
只读 result.json，不写任何结果文件。
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

CODE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CODE_DIR)

RUN = os.path.join(
    REPO_ROOT, "code", "results", "20261107-203233_e1_reproduce_full_table", "result.json")
DOC = {
    "A_curve+C_desc20": {"delta": -0.432, "ci": [-0.710, -0.144], "frac": 0.641},
    "A_curve+C_desc30": {"delta": -0.479, "ci": [-0.811, -0.141], "frac": 0.625},
    "A_curve+C_ecm": {"delta": -0.568, "ci": [-0.999, -0.133], "frac": 0.625},
}
ORDER = ["A_curve+C_desc20", "A_curve+C_desc30", "A_curve+C_ecm"]


def boot(diffs, rng, n_boot=5000):
    return np.array([np.mean(rng.choice(diffs, len(diffs), replace=True))
                     for _ in range(n_boot)])


def main():
    with open(RUN, "r", encoding="utf-8") as fh:
        res = json.load(fh)
    per_cell = res["per_cell_mae"]
    base = per_cell["A_curve"]
    keys = sorted(base, key=lambda k: int(k))
    print("%-20s %10s %22s %8s" % ("对比", "Δ", "95% CI", "改善比例"))
    print("-" * 66)

    # 假设 A：共享随机流（e1_final.py 的做法）
    rng_shared = np.random.default_rng(0)
    shared = {}
    for name in ORDER:
        other = per_cell[name]
        diffs = np.array([other[k] - base[k] for k in keys], float)
        bs = boot(diffs, rng_shared)
        shared[name] = (diffs.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5))
    print("[A] 共享随机流 rng=default_rng(0)，三个对比依次消耗")
    for name in ORDER:
        d, lo, hi = shared[name]
        print("%-20s %+10.3f   [%+.3f, %+.3f]   doc[%+.3f, %+.3f]" % (
            name, d, lo, hi, DOC[name]["ci"][0], DOC[name]["ci"][1]))

    # 假设 B：每个对比独立 default_rng(0)（本框架 runner 的做法）
    print()
    print("[B] 每个对比独立 default_rng(0)")
    for name in ORDER:
        other = per_cell[name]
        diffs = np.array([other[k] - base[k] for k in keys], float)
        bs = boot(diffs, np.random.default_rng(0))
        print("%-20s %+10.3f   [%+.3f, %+.3f]" % (
            name, diffs.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
