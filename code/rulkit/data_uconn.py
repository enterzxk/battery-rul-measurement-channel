# -*- coding: utf-8 -*-
"""UConn-ISU-ILCC 原始数据读取（只读）。

数据路径不随仓库分发，默认指向本机 data/external/uconn/。
两个 pickle 的字段结构（2026-11-07 实测）：

data_slowpulse_1.pkl  17,130 条脉冲弛豫记录
  cell_id, group_id, rpt, num_cycles, soc, 'soc - coulomb', pulse_type,
  voltage (17130, 101), q_dchg, soh, dcir_{chg,dchg}_{20,50,90}

data_cc_1.pkl        14,373 条恒流放电曲线记录
  cell_id, group_id, rpt, num_cycles, voltage (14373, 600), q_dchg, soh,
  dcir_{chg,dchg}_{20,50,90}
"""
from __future__ import annotations

import os
import pickle

DEFAULT_DATA_DIR = r"E:\桌面\rul\data\external\uconn"
PULSE_FILE = "data_slowpulse_1.pkl"
CC_FILE = "data_cc_1.pkl"


def data_dir(path=None):
    return path or os.environ.get("RUL_UCONN_DIR", DEFAULT_DATA_DIR)


def _load(path):
    with open(path, "rb") as fh:
        return pickle.load(fh, encoding="latin1")


def load_pulse(path=None):
    """脉冲弛豫（非循环测量通道）主表。"""
    return _load(os.path.join(data_dir(path), PULSE_FILE))


def load_cc(path=None):
    """恒流放电曲线（循环测量通道）主表。"""
    return _load(os.path.join(data_dir(path), CC_FILE))


def fingerprint(path=None):
    """数据指纹：用于特征缓存失效判断。"""
    out = {}
    for name in (PULSE_FILE, CC_FILE):
        p = os.path.join(data_dir(path), name)
        st = os.stat(p)
        out[name] = {"size": st.st_size, "mtime": int(st.st_mtime), "path": p}
    return out
