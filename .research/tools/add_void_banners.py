# -*- coding: utf-8 -*-
"""Add 'SUPERSEDED' banners to experiment records whose conclusions were later
withdrawn, following AGENTS.md 6 ('historical results are read-only: new
conclusions go in new files, old files get a void banner, do not overwrite').

Idempotent: skips a file that already carries the banner marker.
"""
import os, io

EXP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exp")
EXP = os.path.abspath(EXP)
MARK = "> **⛔ 已作废（SUPERSEDED）**"

BANNERS = {
 "EXP-005-donor-floor.md":
   "本记录结论「命门成立 / 行轴在 k≈16 处饱和」**已被推翻**。后续预注册检验（EXP-007）四个配置全部未过 ±0.05 等价界，且只有 3 个配对工况；正确保留的结论是「**地板未建立**」，不是「已建立」。见 `.research/FALSIFIED.md`、`review-stage/CD-016-goal-status.md`。",
 "EXP-021-utility.md":
   "本记录中「供体数决策是可学的、且稳定」与「不需要偷看测试集」两处解读**不成立**：选择程序**不是嵌套留一**（FAIL-C），选择集工况 x 的预测模型见过外层留出工况 g 的标签。只有**描述性重选结果**可用。见 `review-stage/INTEGRITY_AUDIT_v4.1.md`。",
 "EXP-022-isu-utility.md":
   "本记录中「不需要偷看测试集就能定出该用哪个臂」**不成立**：与 EXP-021 同一 FAIL-C，选择不是嵌套留一。只有描述性重选结果可用。",
 "EXP-024-sensitivity-budget.md":
   "本记录的核心解读**已被推翻**：「仿射作用域 → 每工况共享（+274%）」**该因子从未实现**（拟合仍在被评估电芯循环内），且「行分配」在 K=8 下是空操作。两次 200 抽估计之间行预算对应 +32%，但两次运行的实际供体抽样已分叉、无区间，「对剩余膨胀的精确分解」未确立。见 `FALSIFIED.md` F-010/F-011。",
 "EXP-025-isu-budget.md":
   "本记录「两个主导项相同——作用域与总体」**不成立**（作用域因子未实现，见 F-010）。且本记录的 ISU 扫描两臂评估了**不同电芯集合**（m=1 233 个 vs m=2 223 个），已由 **EXP-030** 用共同支撑（两臂各 223）取代。",
 "EXP-026-joint-space.md":
   "本记录的前提**误读原文**：Peng et al. 2026 **确有 2×2 factorial**（见 `FALSIFIED.md` F-012）。且本记录的 2×2 有一条轴是未实现的作用域因子，故交互项 −39.70 **不可解释**。",
 "EXP-027-isu-joint.md":
   "本记录的「拟合作用域」轴**未实现**（拟合仍在被评估电芯循环内），故作用域主效应与交互的解读**全部作废**。见 `FALSIFIED.md` F-010。",
 "EXP-028-ranking.md":
   "本记录的排序**作废**：作用域因子未实现（F-010），ISU 一列来自不匹配支撑（已由 EXP-030 取代）。**不得引用该排序**。",
 "EXP-029-scope-probe.md":
   "本记录第 62、75 行仍称「隔离出的行预算效应」——**措辞强于证据**。两次 200 抽运行的**实际供体抽样已分叉**（k8 分支多消耗随机数），无区间，「对剩余膨胀的精确分解」未确立。以第 71 行的更正版为准。",
 "EXP-030-isu-common-support.md":
   "本记录第 56 行「全文唯一一个明确超出噪声的敏感度因子」**过强**：两个空操作只是**单次实现值**，不构成采样噪声分布或校准阈值（同文件第 70 行已承认）。应表述为「观察到的实现值远小于总体效应」。",
 "EXP-031-c3-result.md":
   "本记录中「重复不能替代覆盖」（第 35 行）与「12×2 不优于 24×1」（第 66 行）**强于证据**：G_A 的边际区间上界为正（允许小的正收益），且实现未按电芯等权、区间为边际非同时。准确表述是「**未能建立所指定的 5% 实用优势**」。",
}

def has_banner(txt):
    return MARK in txt

def insert_banner(txt, banner):
    lines = txt.split("\n")
    if lines and lines[0].strip() == "---":
        try:
            end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
        except StopIteration:
            end = 0
        head = lines[:end+1]
        rest = lines[end+1:]
        return "\n".join(head + ["", MARK, ">", "> " + banner, ""] + rest)
    return MARK + "\n>\n> " + banner + "\n\n" + txt

changed, skipped = [], []
for name, banner in BANNERS.items():
    p = os.path.join(EXP, name)
    if not os.path.exists(p):
        print("MISSING:", name); continue
    txt = io.open(p, encoding="utf-8").read()
    if has_banner(txt):
        skipped.append(name); continue
    io.open(p, "w", encoding="utf-8").write(insert_banner(txt, banner))
    changed.append(name)

print("banners added: %d" % len(changed))
for n in changed: print("  +", n)
print("already had banner: %d" % len(skipped))
for n in skipped: print("  =", n)
