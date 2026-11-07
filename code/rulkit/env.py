# -*- coding: utf-8 -*-
"""环境快照：把一次实验的运行环境固化成可比较的 JSON。"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time

_PKGS = ("numpy", "scipy", "sklearn", "pandas", "torch", "lightgbm", "xgboost")


def _pkg_version(name):
    try:
        mod = __import__(name)
        return getattr(mod, "__version__", "unknown")
    except Exception as exc:  # pragma: no cover
        return "MISSING (%s)" % type(exc).__name__


def _git(repo, *args):
    try:
        out = subprocess.check_output(
            ["git"] + list(args), cwd=repo, stderr=subprocess.DEVNULL
        )
        return out.decode("utf-8", "replace").strip()
    except Exception:
        return "n/a"


def snapshot(repo_root=None):
    """返回环境快照 dict（可直接 json.dump）。"""
    repo_root = repo_root or os.getcwd()
    info = {
        "timestamp_local": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable": sys.executable,
        "cpu_logical": os.cpu_count(),
        "cwd": os.getcwd(),
        "packages": {name: _pkg_version(name) for name in _PKGS},
        "git": {
            "branch": _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD"),
            "commit": _git(repo_root, "rev-parse", "--short", "HEAD"),
            "dirty": bool(_git(repo_root, "status", "--porcelain")),
        },
    }
    try:
        import numpy as np

        info["numpy_int_default"] = str(np.int_)
        info["threads_env"] = {
            k: os.environ.get(k)
            for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
            if os.environ.get(k)
        }
    except Exception:
        pass
    return info


def as_markdown_table(info):
    rows = [
        ("OS / platform", info["platform"]),
        ("CPU 逻辑核", str(info["cpu_logical"])),
        ("Python", "%s (%s)" % (info["python_version"], info["python_implementation"])),
        ("解释器", info["python_executable"]),
        ("git 分支 / commit", "%s / %s%s" % (
            info["git"]["branch"], info["git"]["commit"],
            " (dirty)" if info["git"]["dirty"] else "")),
    ]
    for name, ver in info["packages"].items():
        rows.append((name, ver))
    return "\n".join("| %s | %s |" % (a, b) for a, b in rows)


if __name__ == "__main__":
    print(json.dumps(snapshot(), ensure_ascii=False, indent=1))
