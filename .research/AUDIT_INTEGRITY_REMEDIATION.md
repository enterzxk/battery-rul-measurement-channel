# 诚信审计结论与修复记录（2026-11-08）

## 审计判定：SERIOUS-ISSUES

| 类别 | 判定 |
|---|---|
| 1 幽灵结果 | WARN |
| 2 范围膨胀 | WARN |
| 3 选择性报告 | WARN |
| 4 事后调整 | WARN |
| **5 混淆未披露** | **FAIL** |
| 6 失败与缺陷 | WARN |

## 唯一 FAIL 与修复

**问题**：§3.3 声明「queries are averaged within each cell and then across cells, so every arm uses identical weights」，但 §4.3 报的 isotonic −16.85 来自 EXP-018 的 **query 加权**；同一批 199 查询在 EXP-019 用 cell-macro 后是 **−24.92**，差 8.07（48%）。

**修复**：§3.3 改为「除非另有说明」并声明旧口径会在正文标注；§4.3 改用 EXP-019 的 cell-macro 数字（−21.57 / −24.92），并**并列披露**旧口径（−21.76 / −16.85），写明「isotonic 在两个加权下差异显著，我们报告而不调和」。

## 其余九处修复

| # | 问题 | 修复 |
|---|---|---|
| 2 | Ridge「10 of 11」被归到供体数，实际 11/11 都选了两个供体（10 affine + 1 isotonic）| 改为「every fold on every dataset」，并写明拆分 |
| 3 | 「残差最差」在 UConn 不成立（1-NN 535.51 > 残差 528.26）| 改为「ISU 上最差，UConn 上不是」 |
| 4 | §4.1 的 453.33 与 §4.5 的 454.33 是两次运行 | 明说「两次独立运行，不可互换」 |
| 5 | §4.1「did not saturate」与同段「inconclusive」冲突 | 改为「did not reach the pre-registered equivalence margin」 |
| 6 | ISU 63→57 未解释 | 补「6 个工况在 8 行预算下合格供体不足 2 个，所有臂同样排除」 |
| 7 | EXP-005（Δ=−0.062, p=0.0033）未报告 | 补入 §4.1，并写明「当时读作饱和，现在不维持该解读」 |
| 8 | median 是 mandatory sensitivity 但主表只有 mean | 主表加 median 行；UConn 循环单位的 median **未计算**，如实标 `not computed` 并说明是敏感性分析的缺口 |
| 9 | 五个缺陷漏掉 Holm 缺陷 | 改为六个，补 Holm 累积最大值那条 |
| 10 | mean 主口径是事后修订，写成预注册 | §3.4 明确写「after inspecting results, not pre-registered」 |
| 11 | 「non-monotonicity disappeared」与 R0 不符 | 改为「点估计大幅变动，但 p 值序列仍非单调」 |
| 12 | 「dataset disagreement disappeared」与 EXP-013 不符 | 改为「共同支撑下分歧变小但未消失，如实报告」 |

## 修复后的状态

- 数值：**95 个小数，0 个找不到来源**
- 字数：3,127
- 新增缺口（如实记录）：UConn 循环单位的 median 聚合未计算

## 教训

审计员抓到的核心问题不是「编造」，而是**声明的口径与实际计算的口径不一致**——这类问题在结果表里完全看不出来，只有对照代码与正文才能发现。

这与五个实现缺陷是同一类：**都在代码里，不在表里**。
