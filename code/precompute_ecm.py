# -*- coding: utf-8 -*-
"""预计算并缓存波形描述子 + 两节 RC 参数（约 30 分钟单核，只需跑一次）。

    python code/precompute_ecm.py            # 有缓存则直接跳过
    python code/precompute_ecm.py --force    # 强制重算

产物：`code/.cache/desc_<hash>.npz`
后续任何实验调用 rulkit.cache.descriptors(..., want_ecm=True) 都会命中缓存。
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

from rulkit import cache, data_uconn, features


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args(argv)

    t0 = time.time()
    dp = data_uconn.load_pulse(args.data_dir)
    rec = features.pulse_record_index(dp)
    print("records = %d" % len(rec), flush=True)
    desc, ecm, path, hit = cache.descriptors(
        REPO_ROOT, dp, rec, want_ecm=True, force=args.force, verbose=True)
    print("desc=%d ecm=%d from_cache=%s path=%s" % (len(desc), len(ecm), hit, path))
    print("elapsed %.1f s" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
