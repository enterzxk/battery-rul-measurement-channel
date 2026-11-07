# -*- coding: utf-8 -*-
"""特征缓存。

昂贵的部分（波形描述子 + 两节 RC 拟合，约 30 分钟单核）只算一次，
缓存键包含数据文件指纹（大小 + mtime）与代码版本，数据一变自动失效。

缓存目录：`code/.cache/`（*.npz 已被 .gitignore 忽略，属本地产物）
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np

from . import data_uconn, features

CACHE_SUBDIR = os.path.join("code", ".cache")
CACHE_VERSION = "v1"


def _hash(payload):
    return hashlib.sha1(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:12]


def cache_key(kind, want_ecm=False, extra=""):
    return _hash({
        "fingerprint": data_uconn.fingerprint(),
        "kind": kind,
        "want_ecm": bool(want_ecm),
        "version": CACHE_VERSION,
        "extra": extra,
    })


def _enc(k):
    return "%d|%d|%d|%s" % (k[0], k[1], k[2], k[3])


def _dec(s):
    a, b, c, d = s.split("|")
    return (int(a), int(b), int(c), d)


def _cache_dir(repo_root):
    d = os.path.join(repo_root, CACHE_SUBDIR)
    os.makedirs(d, exist_ok=True)
    return d


def descriptors(repo_root, dp, rec, want_ecm=False, force=False, verbose=False):
    """返回 (desc, ecm, cache_path, from_cache)。

    desc: {(cell,rpt,soc,type): (dv, tau, resid, slope, area)}
    ecm : {(cell,rpt,soc,type): (c, a1, t1, a2, t2)} 或 {} （want_ecm=False）
    """
    d = _cache_dir(repo_root)
    path = os.path.join(d, "desc_%s.npz" % cache_key("desc", want_ecm))
    if os.path.exists(path) and not force:
        z = np.load(path, allow_pickle=False)
        keys = [_dec(s) for s in z["keys"].tolist()]
        desc_arr, ecm_arr = z["desc"], z["ecm"]
        desc = {k: tuple(float(x) for x in desc_arr[i]) for i, k in enumerate(keys)}
        ecm = {}
        if want_ecm:
            ecm = {k: tuple(float(x) for x in ecm_arr[i]) for i, k in enumerate(keys)}
        if verbose:
            print("      [cache] hit %s (%d records)" % (os.path.basename(path), len(keys)),
                  flush=True)
        return desc, ecm, path, True

    if verbose:
        print("      [cache] miss, building %d records (want_ecm=%s) ..."
              % (len(rec), want_ecm), flush=True)
    desc, ecm = features.waveform_descriptors(dp, rec, want_ecm=want_ecm, progress=verbose)
    keys = sorted(desc)
    desc_arr = np.array([desc[k] for k in keys], float)
    ecm_arr = (np.array([ecm[k] for k in keys], float) if want_ecm
               else np.zeros((0, 5), float))
    np.savez_compressed(
        path,
        keys=np.array([_enc(k) for k in keys]),
        desc=desc_arr,
        ecm=ecm_arr,
    )
    if verbose:
        print("      [cache] wrote %s" % path, flush=True)
    return desc, ecm, path, False
