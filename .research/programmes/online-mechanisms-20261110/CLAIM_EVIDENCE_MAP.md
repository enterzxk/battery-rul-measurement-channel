> ## ⚠️ 本文件含已被终审推翻的主张
>
> Codex 终审（T+02:50，SERIOUS-ISSUES）推翻了本文件中的以下内容。**凡与 `REVIEW_RESPONSE.md` 冲突，以 `REVIEW_RESPONSE.md` 为准。**
>
> | 本文件中的主张 | 终审结论 |
> |---|---|
> | C5「25% 寿命 → 10–12%，两队列一致」 | **UConn 半边被推翻**：无健康信息的年龄规则 0.0824 < 模型 0.1011（3/3） |
> | A3「三种子采样下两臂差 0.2–0.3%」 | **作废**：抽稀从未传到臂，三个「采样」是同一份全量历史 |
> | A2「代数等价」 | 降级为 **WEAKLY-IDENTIFIED**（近共线，非严格成比例） |
> | B7/B9「拼特征赢 24% / 层级输 8%」 | **作废**：仍依赖已作废的 `B_loco.py` |
> | B5「充电倍率被证伪」 | 降级为 **NOT-DETECTED**（p=0.138 是未检出） |
> | 「91% 方差在工况间」 | **已撤回，不得引用** |
> | C1–C3 UConn 抽稀 | **作废**：抽稀未实施，且读的是旧轴 |
>
> 仍然站得住的见 `REVIEW_RESPONSE.md §4`。

---

# CLAIM → EVIDENCE MAP · online-mechanisms-20261110

> 每条主张标注：判定 / 统计单位 / 样本 / 文件 / 代码 / 复算命令。
> 判定用词：POSITIVE / NEGATIVE / INCONCLUSIVE / DATA-NOT-IDENTIFIABLE / UNDERPOWERED / NOT-TESTED / WITHDRAWN

---

## A · 在线暴露推进 + 区间删失

| # | 主张 | 判定 | 单位 / n | 证据 | 代码 |
|---|---|---|---|---|---|
| A1 | 电芯内检测节奏近乎规则（CV 0.091），`cum_cycles ~ rpt` R²=0.999 | **POSITIVE** | 电芯，64 | `protocol/uconn_data_contract.json`；RESULTS_A §2 | `code/build_uconn_online.py` |
| A2 | 因此「按暴露推进」与「每检一步」在电芯内**代数等价** | **DATA-NOT-IDENTIFIABLE** | 电芯，64 | RESULTS_A §2–3 | 同上 |
| A3 | 实测印证：两臂差 0.2–0.3%（S0/S1/S2） | **POSITIVE**（支持 A2） | 电芯，64 | `protocol/results_S0/1/2.csv` | `code/arms.py` |
| A4 | 手写卡尔曼滤波比地板基线还差 4% | **NEGATIVE** | 电芯，64 | `protocol/results_S0.csv` | `code/arms.py` |
| A5 | 该组合已被前人分块占据 | **NOVELTY-OVERLAP** | — | `literature/PRIOR_ART_A.md`（Johnen 2020、BatteryCDE 2025、Tao 2026、Shi 2026） | — |
| A6 | UConn 的 `num_cycles` 在 RPT 42 处为中段 NaN（32/64 电芯），循环轴在 42 之后未定义 | **POSITIVE**（缺陷） | 电芯，64 | `CORRECTIONS.md` C1；`protocol/_probe/uconn_cycle_axis_status.csv` | 数据代理 |

**A 的总结**：核心机制在**本数据上不可识别**，不是被证伪。要检验它，需要同一电芯内检测间隔真正变化的现场数据或自适应协议。

---

## B · 应力条件化退化律

| # | 主张 | 判定 | 单位 / n | 证据 | 代码 |
|---|---|---|---|---|---|
| B1 | 按 EFC 吞吐量归一化**不吸收** DoD 效应，反而更强 | **POSITIVE** | 电芯，249 | ρ(DoD,EOL_days)=−0.630；ρ(DoD,EOL_EFC)=−0.795；`protocol/B_corrected.json` | `code/B_corrected.py` |
| B2 | 归一化后离散度不降反升 | **POSITIVE** | 电芯，249 | CV 0.633 → 0.760 | 同上 |
| B3 | 经典幂律（log DoD）略优于线性 DoD | **POSITIVE** | 电芯，249 | R² 0.590 vs 0.582，工况聚类 SE | 同上 |
| B4 | DoD 系数显著（聚类 SE） | **POSITIVE** | 工况，63 | −1.735，p=1.6e−15 | 同上 |
| B5 | 充电倍率系数在聚类 SE 下**不显著** | **NEGATIVE** | 工况，63 | −0.225，p=0.14 | 同上 |
| B6 | 应力预测留出工况寿命优于无信息中位数 | **POSITIVE** | 工况，63 | 0.3181 vs 0.5753（−44.7%），Wilcoxon p=1.2e−5 | 同上 |
| B7 | 损伤律优于直接拼特征的 HGB | **NEGATIVE** | 工况，63 | 0.3465 vs 0.2625（旧版）；修正版未重跑该对比 | `code/B_loco.py`（已作废） |
| B8 | 91% 寿命方差在工况之间 | **WITHDRAWN** | — | 在错误的 211 电芯子集上算的，未在 249 上重算 | — |
| B9 | 层级「应力先验 + 电芯观测更新」有效 | **NEGATIVE** | 工况，53 | 0.5999，比无信息基线差 | `code/B_loco.py`（已作废） |

**B 的总结**：**测量结论成立**（吞吐量归一化失败、DoD 幂律、应力有跨工况预测力），**方法结论不成立**（拼特征更好）。Codex 判：NO-GO 作为独立 Q1。

---

## C · 检查预算

| # | 主张 | 判定 | 单位 / n | 证据 | 代码 |
|---|---|---|---|---|---|
| C1 | UConn 上检查抽稀 4× 使绝对误差涨 20.1% | **POSITIVE** | 工况，11 | 0.1094→0.1314，Wilcoxon p=0.024 | `code/C_thinning_uconn.py` |
| C2 | 抽稀 2× 的 5.7% 变化 | **UNDERPOWERED** | 工况，11 | 低于 MDE 10.7% | 同上 |
| C3 | 抽稀 4× 不损害工况排序 | **NOT-ESTABLISHED** | 工况，11 | ρ 0.855→0.900，11 点不可解释 | 同上 |
| C4 | 所需检查预算不依赖应力 | **WITHDRAWN** | — | `C_stress_budget.py` 总体随 N 漂移，作废 | — |
| C5 | **25% 寿命处 EOL 预测误差约 10–12%，两队列一致** | **POSITIVE** | 工况 11 / 49 | UConn 0.1012、ISU 0.1125 | `code/C_landmark_fraction.py` |
| C6 | 25% 之后 ISU 继续改善 47% | **POSITIVE** | 工况，49 | 0.1125→0.0598 | 同上 |
| C7 | 25% 之后 UConn 平台化（−14%） | **WEAKLY-SUPPORTED** | 工况，11 | 0.1012→0.0870 | 同上 |
| C8 | 两队列后期分化的原因 | **NOT-ESTABLISHED** | — | 候选：EOL 轴不同（循环 vs 天） | — |

**C 的总结**：C5 是本程序**最干净的测量结果**，两独立队列在无量纲寿命分数上一致。但它**是测量，不是方法**。

---

## 被作废的分析（4 个）

| 分析 | 作废原因 |
|---|---|
| `C_thinning.py` v1 | 抽稀倍数增大时 RPT 少的电芯被挤出 → 总体漂移 |
| `C_stress_budget.py` | 每个 N 单独筛总体（204/52）与固定总体（186/50）矛盾 |
| `C_landmark_both.py` | 固定 N 而 N 与寿命分数耦合 |
| `RESULTS_B.md` 初版 | 「40 个右删失」错误，静默丢 16% 电芯；两个相关统计单位不同；LOCO 拿电芯预测比工况中位 |

**共同错误类**：评估总体或统计单位随被改的条件变化。**没有一个会让程序报错。**

---

## 不可主张的事

1. 不得主张「按暴露推进是错的」——只能说**本数据上不可识别**。
2. 不得主张「工况选择无效」「分配不重要」——**未检验**。
3. 不得主张任何等价性——未定义等价界。
4. 不得主张成本节省——完成电芯数 ≠ 通道小时/时间/能耗/金额。
5. 不得主张 c*(N)、交叉律或普适性。
6. 不得主张方法创新——三条线都是测量或证伪。
