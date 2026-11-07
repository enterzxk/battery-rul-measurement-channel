# -*- coding: utf-8 -*-
"""完整复现 docs/e1_final_results.md 的主表（LOGO，单种子，5 个特征集 + bootstrap）。

需要 2-RC 缓存（code/precompute_ecm.py 跑过一次即可）。

    python code/run_e1_reproduce.py
    python code/run_e1_reproduce.py --protocols logo loco --seeds 0 1 2 3
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

from rulkit import cache, data_uconn, features, runner

SETS = ["A_curve", "A_curve+C_desc20", "A_curve+C_desc30", "A_curve+C_ecm", "C_ecm_only"]

# docs/e1_final_results.md（唯一权威数字）
REF = {
    "A_curve": {"logo": 6.587, "loco": 5.069, "dims": 54},
    "A_curve+C_desc20": {"logo": 6.155, "loco": 4.734, "dims": 74},
    "A_curve+C_desc30": {"logo": 6.109, "loco": 4.714, "dims": 82},
    "A_curve+C_ecm": {"logo": 6.020, "loco": 4.591, "dims": 84},
    "C_ecm_only": {"logo": 7.789, "loco": 6.316, "dims": 30},
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0])
    ap.add_argument("--protocols", nargs="+", default=["logo"], choices=["logo", "loco"])
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--force-ecm", action="store_true")
    ap.add_argument("--no-registry", action="store_true")
    args = ap.parse_args(argv)

    t0 = time.time()
    dp = data_uconn.load_pulse(args.data_dir)
    dc = data_uconn.load_cc(args.data_dir)
    rows = features.build_rows(dp, dc)
    print("rows=%d cells=%d groups=%d" % (
        len(rows["y"]), len(np.unique(rows["cells"])), len(np.unique(rows["grp"]))), flush=True)

    desc, ecm, cpath, hit = cache.descriptors(
        REPO_ROOT, dp, rows["rec"], want_ecm=True,
        force=args.force_ecm, verbose=True)
    build_s = round(time.time() - t0, 1)

    X = features.assemble(rows, desc=desc, ecm=ecm, sets=SETS)
    for k, v in X.items():
        print("  %-20s %d dims" % (k, v.shape[1]), flush=True)

    result = runner.run(
        name="e1_reproduce_full_table",
        X_sets=X,
        y=rows["y"], cells=rows["cells"], grp=rows["grp"], rpts=rows["rpts"],
        protocols=tuple(args.protocols), seeds=tuple(args.seeds),
        repo_root=REPO_ROOT,
        registry=not args.no_registry,
        meta={
            "command": "python code/run_e1_reproduce.py " + " ".join(filter(None, [
                "--protocols " + " ".join(args.protocols),
                "--seeds " + " ".join(str(s) for s in args.seeds),
            ])),
            "notes": [
                "完整复现 docs/e1_final_results.md 主表（5 个特征集 + 电芯级配对 bootstrap）。",
                "2-RC 参数来自缓存 code/.cache/（键含数据指纹）；构建耗时 %.1f s。" % build_s,
                "特征构造与 scripts/e1_final.py 的 build() 逐行等价。",
            ],
            "build_seconds": build_s,
            "ecm_cache": os.path.relpath(cpath, REPO_ROOT).replace("\\", "/"),
            "ecm_cache_hit": bool(hit),
            "reference": REF,
        },
    )

    print()
    print("=" * 78)
    print("%-20s %4s %9s %9s %8s" % ("特征集", "维度", "本框架", "权威值", "差"))
    print("-" * 78)
    for name in SETS:
        dim = X[name].shape[1]
        got = result["scores"][name][args.protocols[0]]["mean"]
        ref = REF[name].get(args.protocols[0])
        print("%-20s %4d %9.3f %9s %8s" % (
            name, dim, got,
            "%.3f" % ref if ref is not None else "—",
            "%+.4f" % (got - ref) if ref is not None else "—"))
    print("-" * 78)
    if result.get("deltas"):
        print("配对 bootstrap（vs A_curve，电芯级，5000 次）：")
        for name, d in result["deltas"].items():
            b = d["bootstrap"]
            print("  %-20s Δ=%+.3f  CI=[%+.3f, %+.3f]  改善 %.1f%%" % (
                name, b["delta"], b["ci_low"], b["ci_high"], 100 * b["frac_improved"]))
    print("run_id :", result["run_id"])
    print("out    :", result["out_dir"])
    print("elapsed: %.1f s" % result["elapsed_s"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
