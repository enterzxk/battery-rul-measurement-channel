# -*- coding: utf-8 -*-
"""统一特征构造。

与 scripts/e1_final.py 的 build() 逐行等价，但拆成可缓存的三层：

  rows()      行表（电芯 / 体检轮次 / 工况组 / SOH / 标签 y）+ CC 曲线特征 A_curve
  desc()      波形描述子（C_desc20 = 20 维，C_desc30 = 28 维）
  ecm()       两节 RC 拟合参数（C_ecm = 30 维）—— 昂贵，单独缓存

特征集（与 docs/e1_final_results.md 一致）
  A_curve           54  = CC 放电曲线 50 bin 均值 + mean/std/min/max
  A_curve+C_desc20  74
  A_curve+C_desc30  82
  A_curve+C_ecm     84
  C_ecm_only        30

标签口径（已知局限，见 docs/idea_report.md §3）
  y = EOL 体检轮次 - 当前体检轮次，其中 EOL = 首次 SOH <= 80 的体检轮次。
  这不是真实循环数、也不是日历时间，只是"剩余体检次数"。
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import curve_fit

from . import data_uconn

SOCS = (20, 50, 90)
TYPES = ("chg", "dchg")
EOL_SOH = 80.0
CC_BINS = 50

DESC20_COLS = 20
DESC30_COLS = 28
ECM_COLS = 30
ACURVE_COLS = CC_BINS + 4

FEATURE_SETS = {
    "A_curve": ("A",),
    "A_curve+C_desc20": ("A", "D20"),
    "A_curve+C_desc30": ("A", "D30"),
    "A_curve+C_ecm": ("A", "E30"),
    "C_ecm_only": ("E30",),
}


# --------------------------------------------------------------------------- #
# 脉冲记录索引
# --------------------------------------------------------------------------- #
def pulse_record_index(dp):
    """(cell, rpt, soc, pulse_type) -> 记录下标。重复键后者覆盖，与 e1_final.py 一致。"""
    cell = np.asarray(dp["cell_id"], dtype=np.int64)
    rpt = np.asarray(dp["rpt"], dtype=np.int64)
    soc = np.asarray(dp["soc"], dtype=np.int64)
    pt = [str(t) for t in dp["pulse_type"]]
    rec = {}
    for i in range(len(cell)):
        rec[(int(cell[i]), int(rpt[i]), int(soc[i]), pt[i])] = i
    return rec


# --------------------------------------------------------------------------- #
# CC 放电曲线特征
# --------------------------------------------------------------------------- #
def cc_features(dc):
    """(cell, rpt) -> 54 维放电曲线特征（按平均电压排序拼接后 50 等分取均值）。"""
    cc_cell = np.asarray(dc["cell_id"], dtype=np.int64)
    cc_rpt = np.asarray(dc["rpt"], dtype=np.int64)
    cc_v = dc["voltage"]
    buckets = {}
    for i in range(len(cc_cell)):
        buckets.setdefault((int(cc_cell[i]), int(cc_rpt[i])), []).append(i)
    out = {}
    for key, idxs in buckets.items():
        idxs = sorted(idxs, key=lambda i: float(np.mean(cc_v[i])))
        curve = np.concatenate([np.asarray(cc_v[i], float) for i in idxs])
        bins = np.array_split(curve, CC_BINS)
        out[key] = [float(b.mean()) for b in bins] + [
            float(curve.mean()), float(curve.std()),
            float(curve.min()), float(curve.max()),
        ]
    return out


# --------------------------------------------------------------------------- #
# 行表（标签 + 分组）
# --------------------------------------------------------------------------- #
def build_rows(dp, dc, eol_soh=EOL_SOH):
    """构造权威行表。

    返回 dict：
      keys      [(cell, rpt), ...]  已按 (cell, rpt) 升序
      A         (n, 54) A_curve
      cells/rpts/soh/grp  (n,)
      y         (n,) 剩余体检次数
      eol       {cell: eol_rpt}
      n_dropped_missing_pulse / n_dropped_missing_cc  诊断计数
    """
    rec = pulse_record_index(dp)
    all_keys = sorted({(k[0], k[1]) for k in rec})
    valid = [
        k for k in all_keys
        if all((k[0], k[1], s, t) in rec for s in SOCS for t in TYPES)
    ]
    n_drop_pulse = len(all_keys) - len(valid)

    soh_map = {
        (int(c), int(r)): float(s)
        for c, r, s in zip(dp["cell_id"], dp["rpt"], dp["soh"])
    }
    gmap = {int(c): int(g) for c, g in zip(dp["cell_id"], dp["group_id"])}

    pfeat = cc_features(dc)
    keep = [k for k in valid if k in pfeat]
    n_drop_cc = len(valid) - len(keep)

    A = np.array([pfeat[k] for k in keep], float)
    cells = np.array([k[0] for k in keep], np.int64)
    rpts = np.array([k[1] for k in keep], np.int64)
    soh = np.array([soh_map[k] for k in keep], float)
    grp = np.array([gmap[c] for c in cells], np.int64)

    eol = {}
    for c in np.unique(cells):
        m = cells == c
        order = np.argsort(rpts[m])
        rr, ss = rpts[m][order], soh[m][order]
        hit = np.where(ss <= eol_soh)[0]
        if len(hit):
            eol[int(c)] = int(rr[hit[0]])

    ok = np.array([c in eol and r <= eol[c] for c, r in zip(cells, rpts)])
    y = np.array([eol[c] - r for c, r in zip(cells[ok], rpts[ok])], float)

    return {
        "keys": [k for k, o in zip(keep, ok) if o],
        "A": A[ok],
        "cells": cells[ok],
        "rpts": rpts[ok],
        "soh": soh[ok],
        "grp": grp[ok],
        "y": y,
        "eol": eol,
        "rec": rec,
        "n_keys_all": len(all_keys),
        "n_dropped_missing_pulse": n_drop_pulse,
        "n_dropped_missing_cc": n_drop_cc,
        "n_dropped_after_eol": int((~ok).sum()),
    }


# --------------------------------------------------------------------------- #
# 波形描述子
# --------------------------------------------------------------------------- #
#: 采样间隔（秒）。UConn 脉冲为 100 s / 101 点；本地 pkl 无时间列，
#: 该值来自外部文档（Nowacki et al., J. Power Sources 2024），属待核实常量。
DT = 1.0

#: 弛豫窗长度（秒）。tau 的上界不得超出它，否则参数不可辨识。
RELAX_WINDOW_S = 60.0


def _ecm_fit(v, kind, ip):
    """两节 RC 拟合（修正版）。

    修正了两处缺陷，二者都是 v1 结果失效的原因：
      1. 拟合窗从 ip+1 开始。ip 是载流采样点，其与下一点之间存在约为总弛豫量
         52% 的电压跳变；把它当作 x=0 会让模型用一个指数去桥接这个跳变，
         快时间常数因此被压到下界。
      2. 时间轴用秒（DT），tau 上界取弛豫窗长。原实现用采样点索引、上界
         400 s（远超 60 s 窗），参数不可辨识。
    """
    v = np.asarray(v, float)
    seg = v[ip + 1:]
    if seg.size < 20:
        return (np.nan,) * 5
    x = np.arange(seg.size, dtype=float) * DT
    y = seg
    p0 = [float(y[-1]), float(y[0] - y[-1]) * 0.7, 2.0,
          float(y[0] - y[-1]) * 0.3, 20.0]
    lo = [y.min() - 0.2, -0.6, 0.5, -0.6, 5.0]
    hi = [y.max() + 0.2, 0.6, RELAX_WINDOW_S, 0.6, RELAX_WINDOW_S]
    try:
        popt, _ = curve_fit(
            lambda x, c, a1, t1, a2, t2: c + a1 * np.exp(-x / t1) + a2 * np.exp(-x / t2),
            x, y, p0=p0, bounds=(lo, hi), maxfev=6000,
        )
        return tuple(float(p) for p in popt)
    except Exception:
        return (np.nan,) * 5


def _ecm_fit_legacy(v, kind, ip):
    """有缺陷的原始实现，仅用于复现论文第 3 节的伪影，不得用于新实验。

    窗起点为 ip（含载流点）、时间轴为采样点索引、tau 上界 400 s。
    在 17,130 条波形上，tau1 因此 100% 钉在下界 1.0。
    """
    seg = np.asarray(v[ip:], float)
    if seg.size < 15:
        return (np.nan,) * 5
    x = np.arange(seg.size, dtype=float)
    y = seg
    p0 = [float(y[-1]), float(y[0] - y[-1]) * 0.6, 5.0,
          float(y[0] - y[-1]) * 0.4, 40.0]
    lo = [y.min() - 0.2, -0.6, 1.0, -0.6, 10.0]
    hi = [y.max() + 0.2, 0.6, 60.0, 0.6, 400.0]
    try:
        popt, _ = curve_fit(
            lambda x, c, a1, t1, a2, t2: c + a1 * np.exp(-x / t1) + a2 * np.exp(-x / t2),
            x, y, p0=p0, bounds=(lo, hi), maxfev=4000,
        )
        return tuple(float(p) for p in popt)
    except Exception:
        return (np.nan,) * 5


def waveform_descriptors(dp, rec, keys=None, want_ecm=False, progress=False, legacy_ecm=False):
    """对每个脉冲记录算 (dv, tau, resid, slope, area) 与可选的 2-RC 参数。

    返回 (desc, ecm)：{(cell,rpt,soc,type): tuple}
    """
    voltage = dp["voltage"]
    todo = rec if keys is None else {k: rec[k] for k in rec if (k[0], k[1]) in set(keys)}
    desc, ecm = {}, {}
    n = len(todo)
    for n_done, (k, i) in enumerate(sorted(todo.items())):
        v = np.asarray(voltage[i], float)
        v0 = v[0]
        ip = int(np.argmax(v)) if k[3] == "chg" else int(np.argmin(v))
        peak = v[ip]
        dv = abs(peak - v0)
        tau = np.nan
        if dv > 1e-6:
            target = peak - 0.632 * (peak - v0)
            tail = v[ip:]
            idx = np.where(tail <= target)[0] if k[3] == "chg" else np.where(tail >= target)[0]
            if len(idx):
                tau = float(idx[0])
        resid = (v[-1] - peak) / (v0 - peak) if abs(v0 - peak) > 1e-9 else np.nan
        slope = float(v[min(ip + 1, len(v) - 1)] - v[ip])
        area = float(np.trapz(v[ip:]) / max(1, len(v) - ip))
        desc[k] = (dv, tau, resid, slope, area)
        if want_ecm:
            ecm[k] = _ecm_fit_legacy(v, k[3], ip) if legacy_ecm else _ecm_fit(v, k[3], ip)
        if progress and (n_done + 1) % 2000 == 0:
            print("  descriptors %d/%d" % (n_done + 1, n), flush=True)
    return desc, ecm


def desc_matrix(desc, keys):
    """C_desc20 (20 维) 与 C_desc30 (28 维)。行顺序与 keys 一致。"""
    D20, D30 = [], []
    for (c, r) in keys:
        d20, d30 = [], []
        for s in SOCS:
            for t in TYPES:
                q = (c, r, s, t)
                d20 += list(desc[q][:3])
                d30 += list(desc[q][:3])
        dv_chg = [desc[(c, r, s, "chg")][0] for s in SOCS]
        dv_dchg = [desc[(c, r, s, "dchg")][0] for s in SOCS]
        tau_chg = [desc[(c, r, s, "chg")][1] for s in SOCS]
        d20 += [np.nanstd(dv_chg), np.nanstd(dv_dchg)]
        d30 += [np.nanstd(dv_chg), np.nanstd(dv_dchg)]
        for s in SOCS:
            for t in TYPES:
                d30 += [desc[(c, r, s, t)][3]]
        d30 += [
            np.nanstd(tau_chg),
            float(np.nanmean([desc[(c, r, s, "chg")][4] for s in SOCS])),
        ]
        D20.append(d20)
        D30.append(d30)
    return np.array(D20, float), np.array(D30, float)


def ecm_matrix(ecm, keys):
    """C_ecm (30 维)：6 个 (SOC × 方向) × 5 个 2-RC 参数。"""
    out = []
    for (c, r) in keys:
        row = []
        for s in SOCS:
            for t in TYPES:
                row += list(ecm[(c, r, s, t)])
        out.append(row)
    return np.array(out, float)


def feature_columns(family):
    """给特征矩阵列命名，便于诊断与落盘。"""
    if family == "A":
        return ["cc_bin%02d" % i for i in range(CC_BINS)] + [
            "cc_mean", "cc_std", "cc_min", "cc_max"]
    if family == "D20":
        cols = []
        for s in SOCS:
            for t in TYPES:
                cols += ["dv_%s%d" % (t, s), "tau_%s%d" % (t, s), "resid_%s%d" % (t, s)]
        return cols + ["dv_chg_std", "dv_dchg_std"]
    if family == "D30":
        cols = []
        for s in SOCS:
            for t in TYPES:
                cols += ["dv_%s%d" % (t, s), "tau_%s%d" % (t, s), "resid_%s%d" % (t, s)]
        cols += ["dv_chg_std", "dv_dchg_std"]
        for s in SOCS:
            for t in TYPES:
                cols += ["slope_%s%d" % (t, s)]
        cols += ["tau_chg_std", "area_chg_mean"]
        return cols
    if family == "E30":
        cols = []
        for s in SOCS:
            for t in TYPES:
                cols += ["%s_%s%d" % (p, t, s) for p in ("c", "a1", "t1", "a2", "t2")]
        return cols
    raise ValueError(family)


def assemble(rows, desc=None, ecm=None, sets=None):
    """把已构造的分块拼成 {特征集名: X}。"""
    sets = sets or ["A_curve"]
    blocks = {"A": rows["A"]}
    if desc is not None:
        d20, d30 = desc_matrix(desc, rows["keys"])
        blocks["D20"] = d20
        blocks["D30"] = d30
    if ecm is not None:
        blocks["E30"] = ecm_matrix(ecm, rows["keys"])
    out = {}
    for name in sets:
        parts = FEATURE_SETS[name]
        missing = [p for p in parts if p not in blocks]
        if missing:
            raise KeyError("特征集 %s 需要 %s，未构造（检查 desc/ecm 参数）" % (name, missing))
        out[name] = np.hstack([blocks[p] for p in parts]) if len(parts) > 1 else blocks[parts[0]]
    return out
