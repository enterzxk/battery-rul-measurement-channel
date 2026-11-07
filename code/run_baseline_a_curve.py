# -*- coding: utf-8 -*-
"""E1 基线复现：A_curve + LOGO + 单种子（目标值 6.587）。

用法
----
    python code/run_baseline_a_curve.py                 # 默认 LOGO / seed 0，登记
    python code/run_baseline_a_curve.py --seeds 0 1 2 3 # 多种子
    python code/run_baseline_a_curve.py --no-registry   # 只跑不登记（仅调试用）

参考值来自 docs/e1_final_results.md（唯一权威数字）：
    A_curve  LOGO 6.587 / LOCO 5.069，54 维，2,813 行，64 电芯，11 工况组
"""
from __future__ import annotations

import argparse
import os
import sys
import time

CODE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CODE_DIR)
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

import numpy as np

from rulkit import data_uconn, features, runner

REFERENCE = {
    "A_curve": {"logo": 6.587, "loco": 5.069, "dims": 54},
}


def main(argv=None):
    ap = argparse.ArgumentParser(description="A_curve 基线复现")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0])
    ap.add_argument("--protocols", nargs="+", default=["logo"],
                    choices=["logo", "loco"])
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--no-registry", action="store_true")
    ap.add_argument("--name", default=None)
    args = ap.parse_args(argv)

    t0 = time.time()
    print("[1/3] 读取原始 pickle ...", flush=True)
    dp = data_uconn.load_pulse(args.data_dir)
    dc = data_uconn.load_cc(args.data_dir)
    print("      pulse records=%d  cc records=%d" % (len(dp["cell_id"]), len(dc["cell_id"])), flush=True)

    print("[2/3] 构造行表 + A_curve ...", flush=True)
    rows = features.build_rows(dp, dc)
    print("      rows=%d cells=%d groups=%d dims=%d" % (
        len(rows["y"]), len(np.unique(rows["cells"])),
        len(np.unique(rows["grp"])), rows["A"].shape[1]), flush=True)
    print("      dropped: pulse_incomplete=%d cc_missing=%d after_eol=%d" % (
        rows["n_dropped_missing_pulse"], rows["n_dropped_missing_cc"],
        rows["n_dropped_after_eol"]), flush=True)
    build_s = round(time.time() - t0, 1)

    X = {"A_curve": rows["A"]}
    name = args.name or "baseline_A_curve"
    notes = [
        "复现 docs/e1_final_results.md 的 A_curve 基线（LOGO 6.587 / LOCO 5.069）。",
        "特征构造与 scripts/e1_final.py 的 build() 逐行等价，未做任何超参改动。",
        "耗时拆分：数据加载+特征构造 %.1f s；其余为训练与落盘。" % build_s,
    ]

    print("[3/3] 训练 / 评估 ...", flush=True)
    result = runner.run(
        name=name,
        X_sets=X,
        y=rows["y"],
        cells=rows["cells"],
        grp=rows["grp"],
        rpts=rows["rpts"],
        protocols=tuple(args.protocols),
        seeds=tuple(args.seeds),
        repo_root=REPO_ROOT,
        meta={
            "command": "python code/run_baseline_a_curve.py " + " ".join(
                filter(None, [
                    "--seeds " + " ".join(str(s) for s in args.seeds),
                    "--protocols " + " ".join(args.protocols),
                ])).strip(),
            "notes": notes,
            "build_seconds": build_s,
            "reference": REFERENCE,
            "data_fingerprint": data_uconn.fingerprint(args.data_dir),
        },
    )

    print()
    print("run_id :", result["run_id"])
    print("out    :", result["out_dir"])
    print("elapsed: %.1f s" % result["elapsed_s"])
    for protocol in args.protocols:
        got = result["scores"]["A_curve"][protocol]["mean"]
        ref = REFERENCE["A_curve"].get(protocol)
        if ref is None:
            print("  %-4s = %.3f  (无参考值)" % (protocol.upper(), got))
        else:
            print("  %-4s = %.3f   reference %.3f   diff %+.4f" % (
                protocol.upper(), got, ref, got - ref))
    return 0


if __name__ == "__main__":
    sys.exit(main())
