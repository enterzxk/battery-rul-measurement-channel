# 一个不存在的增益：脉冲弛豫 RUL 预测中的拟合窗与标签单位伪影

> 实证研究草稿（v2，2026-11-07）。全部数字可追溯到 `docs/e1_v2_fixed_results.md`。

## 一句话

我们曾报告脉冲弛豫参数把跨工况 RUL 误差降低 8.6%。**审计发现这是两个实现缺陷的产物。** 修复后增益降到 5.3%，且在两种统计单位下都不显著。

## 两个伪影

**伪影一：拟合窗起点。** 弛豫拟合从载流采样点开始，模型必须用一个指数去桥接占总量 52.3% 的电压跳变。结果：tau1 在 **17,130 条波形的 100%** 上被钉死在下界 1.0，30 维特征里有 6 维是常数，a1 变成阶跃项而非物理极化。

**伪影二：标签单位。** `num_cycles` 是相邻体检之间的**循环段长**，不是累计量。按体检次数计的 MAE 等价于给不同电芯 0.5–1.0 的隐式权重（体检节奏 67.6–133.7 循环/次，比值 1.98）。

## 修复后

| 特征集 | 体检次数单位 | 循环单位 |
|---|---:|---:|
| 仅放电曲线 | 6.587 | 729.8 |
| + 弛豫参数（修复后） | **6.238（−5.3%）** | **694.1（−4.9%）** |
| + 波形描述量 | 6.155 | 696.8 |
| 仅弛豫参数 | 8.596 | 832.1 |
| 仅体检序号 | 13.501 | 1154.3 |

主对比（cycle 单位）：Δ = −12.11 循环，电芯级 95% CI **[−80.77, +10.45]**，工况簇 95% CI **[−115.02, +39.07]**，6/11 工况改善。**两边都跨零。**

## 仍然成立的

- **波形确实携带退化信息**：6.587 远优于仅体检序号（13.501）与仅 SOH（9.148）
- **加容量/SOH 反而更差**（6.793）——脉冲不是容量代理
- **工况级功效不足**：n=11，检出 d≈0.4 需约 49 个工况

## 一个被否证的机制假设

"可辨识性解释跨工况符号翻转"——预注册检验，**失败**。Spearman(+0.375)。最硬的反例：UConn 慢极化参数在 tau/W=0.345（最不可辨识档）同号率却是 1.000。详见 `docs/autonomous_research/B_SECTION_FALSIFIED.md`。

## 仓库结构

```
docs/
  e1_v2_fixed_results.md          唯一权威数字（v2）
  e1_final_results.md             历史结果，已标记作废
  manuscripts/v2.0-postmortem.md  论文正文
  manuscripts/v1.0-draft.md       旧稿，数字已作废
  autonomous_research/            多代理审计记录
    RESEARCH_STATE.md             项目状态
    LITERATURE_MATRIX.md          77 篇文献
    GAP_ANALYSIS.md               六类 gap
    AUDIT_AGENT3.md               28 条审计判定
    REVIEW_AGENT5.md              审稿意见
    DECISION_LOG.md               决策记录
    B_SECTION_FALSIFIED.md        否证记录
code/rulkit/                      实验框架（含 _ecm_fit 与 _ecm_fit_legacy）
scripts/                          历史脚本（保留，含 bug 版本）
```

## 复现

```bash
python code/run_baseline_a_curve.py          # A_curve 基线，期望 6.587
python code/run_e1_reproduce.py              # 完整主表
```

注意：`code/rulkit/features.py` 中的 `_ecm_fit` 是修正版；`_ecm_fit_legacy` 保留旧实现，**仅用于复现论文第 3 节的伪影**。

## 数据

UConn-ISU-ILCC（本地）、Bayreuth 2025（Zenodo 10.5281/zenodo.15755725, CC-BY-4.0）。NASA 与 CALCE 经核查不可用，原因见 `docs/nasa_results.md` 与 `docs/second_dataset_check.md`。数据不随仓库分发。

## 状态

草稿，未投稿。定位：方法学 / 负结果。目标期刊 IEEE TIM 或 J. Energy Storage。
