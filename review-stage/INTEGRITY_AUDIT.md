# 诚信审计 · `docs/manuscripts/v4.0-tim.md`

- **审计对象**：`docs/manuscripts/v4.0-tim.md`（123 行，v4.0，2026-11-08）
- **审计范围**：`.research/exp/EXP-001..022`、`.research/FALSIFIED.md`、`.research/CODEX_DECISIONS.md`、`review-stage/CD-*.md`、`.research/results/*.py`、`.research/HOLM_FIX.md`、`.research/AUDIT_v4.0.md`、`.research/AUDIT_CITATIONS.md`
- **审计边界**：只查证据完整性，不评创新性；不把"没找到问题"写成问题，也不把"记录缺失"写成"记录矛盾"。
- **方法**：逐条把稿件数字/断言对回 EXP 记录与产生该数字的脚本；对关键结果读聚合代码，确认统计单位与加权；对 CD-004/005/010/011/013/015 做时间顺序与判据变更核对。

## 总判定

**SERIOUS-ISSUES**

没有发现编造数字：按 `AUDIT_v4.0.md` 的 72 个数值 token 口径复核，全部能在 EXP 文件中逐字找到（与其结论一致）。主效应方向（affine / isotonic 为正、1-NN 为负）有 EXP-013 / 016 / 017 支持。

但第 5 类有一处 **FAIL**：§4.3 报告的 isotonic `−16.85` 来自 **query 加权**的 EXP-018，而 §3.3 明确声明"先按电芯平均、再按工况平均，所有臂同权重"；同一批 199 个查询在 EXP-019 的 cell-macro 口径下是 **−24.92**。报告的数字与声明的方法不一致，修正值就在同项目的 EXP-019 里，稿件未披露。加上 EXP-005（相反结论）未报告、强制 median 未报告、"五个缺陷"漏掉 Holm 缺陷，故判 **SERIOUS-ISSUES**，而非 CLEAN 或 MINOR-ISSUES。

## 六类判定表

| # | 类别 | 判定 | 一句话 |
|---|---|---|---|
| 1 | 幽灵结果 | **WARN** | 无编造数字；但 Ridge 的 10/11 被归到"供体数"、"残差最差"在 UConn 上不成立、同协议出现 453.33/454.33 两套数 |
| 2 | 范围膨胀 | **WARN** | "did not saturate" 与同段 "inconclusive" 冲突；63→57 工况未解释；"one predictor family" 与 ridge 对照矛盾 |
| 3 | 选择性报告 | **WARN** | EXP-005（相反结论）未报告；强制 median 未展示；"五个缺陷"漏掉 Holm 缺陷 |
| 4 | 事后调整 | **WARN** | mean 主口径是看结果后的修订（CD-004），稿件写成预注册；median/seed0 的 +0.033 被说成"超过 0.05" |
| 5 | 混淆未披露 | **FAIL** | §3.3 承诺 cell-macro 同权重，§4.3 报的 EXP-018 数字是 query 加权；EXP-019 同查询 cell-macro 下 isotonic 为 −24.92，不是 −16.85 |
| 6 | 失败与缺陷 | **WARN** | 五条中 #2/#3/#5 与记录一致；#1/#4 的症状描述与记录不符；"five" 不完整；#1 的独立来源无记录 |

---

## 1. 幽灵结果 — WARN

### 未发现
- 没有凭空数字。按 `AUDIT_v4.0.md` 的 72 个数值 token 口径复核，全部能在 EXP 文件中逐字找到。
- 表 4.1 的 UConn 六项（516.88 / 500.21 / 16.67 / 11/11 / 0.0002；459.95 / 453.33 / 6.63 / 8/11 / 0.34；535.51 / 543.33 / −7.82 / 2/11 / 0.036）逐项对 EXP-016 第 24–26 行。
- 表 4.1 的 ISU 六项（2.827 / 2.670 / 0.156 / 44/57 / 0.0003；2.551 / 2.466 / 0.085 / 39/57 / 0.0005；2.756 / 2.819 / −0.063 / 7/57 / 0.0000）逐项对 EXP-013 第 29–34 行。

### WARN-1.1 Ridge 的 "10 of 11" 被归到"供体数"
- **稿件** 10 行、98 行："chose two donors in 11 of 11 folds on UConn with the gradient-boosted predictor, **10 of 11 with ridge**, and in 57 of 57 folds on ISU."
- **EXP-021 第 34 行**：Ridge 的选择结果是 "affine m=2（10/11）、isotonic m=2（1/11）"。10 折选 affine m=2，1 折选 isotonic m=2——**两种都是 m=2**。所以供体数决策在 Ridge 上也是 11/11；10/11 是"选 affine 臂"的折数，不是"选两个供体"的折数。
- 这是把"臂选择"的数字归到"供体数选择"上。实际结果比稿件写的更强，但数字归属错误。

### WARN-1.2 "残差借用是最差的"在 UConn 上不成立
- **稿件** 80 行："residual borrowing is the worst of the four calibrators in absolute terms (528.26 on UConn, 2.939 on ISU)."
- **EXP-016 第 26–27 行**：UConn m=1 时 1-NN 借水平 = 535.51，借残差 = 528.26；m=2 时 543.33 vs 527.73。**借水平比借残差更差**，所以残差不是四个校准器里最差的。该断言只在 ISU 成立（EXP-014 第 25 行：2.939 对 isotonic 2.551）。
- 这是从 ISU 外推到 UConn 的过度概括。

### WARN-1.3 同一协议两套数：453.33 vs 454.33
- **稿件** 表 4.1（66 行）isotonic m=2 = **453.33**（EXP-016 第 25 行）。
- **稿件** 98 行："matched the best fixed strategy exactly on UConn ... (**454.33**)"（EXP-021 第 25 行）。
- 同一"锁定协议"下同一臂出现 453.33 与 454.33 两个值；EXP-021 的 HGB 各臂也整体比 EXP-016/017 高 1–2（affine 500.21→502.17，isotonic 453.33→454.33，1-NN 543.33→545.38）。稿件未说明这是两次运行，读者无法从表 4.1 复现 §4.5 的 454.33。

### WARN-1.4 一句话里混了两次运行
- **稿件** 92 行："+21.14 on the gradient-boosted predictor (631.03 to 609.89), +31.86 on ridge (597.21 to 565.35)"。
- 631.03/609.89 来自 **EXP-017 第 19 行**；597.21/565.35 来自 **EXP-021 第 20–21 行**（附录第 69 行给 +31.86）。EXP-021 自己的 HGB intercept 是 630.95→611.50（+19.45），不是 631.03→609.89。
- 两个臂来自不同运行，稿件当成同一协议的一次结果。

### WARN-1.5 追踪范围写错
- **稿件** 第 3 行："Every number traceable to `.research/exp/EXP-001..021`."
- §4.5 的 ISU 数字（57/57、2.470、2.542）来自 **EXP-022**（第 31–33 行），不在 001..021 范围内。
- 这是元数据错误，不影响数值，但说明"可追溯"声明本身不精确。

---

## 2. 范围膨胀 — WARN

### WARN-2.1 "did not saturate" 与 "inconclusive" 冲突
- **稿件** 17 行："The floor did not appear."；74 行："The single-donor row axis did not saturate." 同一段末尾又说 "that test has three paired units and is reported as inconclusive."
- **EXP-007 第 25–29 行**：四个配置全部未通过 ±0.05 闸门，且只有 9/64 电芯、3 个工况，n=3。
- **CD-016 第 16 行**明确："floor not established is defensible; **no floor exists overstates the evidence**, particularly with three paired conditions."
- "did not saturate" 是"未建立"被写成"不存在"的边缘表述；同一段自己承认 inconclusive，构成内部矛盾。判 WARN 而非 FAIL，因为稿件确实写了 inconclusive，且四个配置的 Δ 方向一致（都是 k=16 更差）。

### WARN-2.2 63 个工况 vs 57 个工况
- **稿件** 摘要 8 行、§3.1 41 行说 ISU "248 cells in **63 conditions**"；主结果和 §6 用 **57**（44/57、39/57、7/57、57/57）。
- **EXP-012 第 23 行**：63 个工况组；**EXP-013 第 23 行**：共同支撑后 **57 个**。
- 稿件从未说明另外 6 个工况为何被排除、排除是否与结果有关。这是未披露的排除。

### WARN-2.3 "one predictor family" 与 ridge 对照矛盾
- **稿件** §6 112 行："Two datasets, **one predictor family**..."；但 §3.2 45 行说"第二个冻结预测器（ridge）作对照"，§4.4 94 行还比较了两个基模型上的校准器排序。
- 至少用了 HGB 与 Ridge 两个基模型。"one predictor family" 不准确，应写"两个基模型，均未调参"。

### WARN-2.4 "3 to 6% of baseline"
- **稿件** §6 112 行："The donor effect is small in relative terms (3 to 6% of baseline)"。
- **EXP-016 第 25 行**：UConn isotonic 的相对效应是 **1.44%**（不显著）。3–6% 只覆盖显著的 affine/isotonic-ISU 效应，未覆盖稿件自己报告的 1.44%。这是范围选择，不是编造。

---

## 3. 选择性报告 — WARN

### WARN-3.1 EXP-005 的相反结论未报告
- **EXP-005 第 31–35 行**：单供体 k=16→64，Δ = **−0.062**，t=−3.453，p=0.0033，n=17；判定"**命门成立**……行轴在 k≈16 处饱和"。
- **稿件** 17/74 行的结论是"floor did not appear / did not saturate"，全文未提 EXP-005。
- 我理解 EXP-005 是电芯级配对（n=17），后来被 EXP-007 的工况级 n=3 检验取代；CD-005/CD-004 也批评过把 3 个工况的 45 个配对当独立单位。**但"取代"不等于"不存在"**：一个已登记、结论相反、p=0.0033 的实验，稿件应至少用一句说明它为何被降级。现在的写法让读者以为从未有任何分析发现过饱和。

### WARN-3.2 强制 median 敏感性没有报告
- **稿件** §3.3 51 行："Monte-Carlo draws are aggregated with the mean (primary) and the **median (mandatory sensitivity)**."
- 表 4.1（65–70 行）只有 mean；§4.2–4.5 也没有 median。唯一出现 median 的地方是行轴的 +0.033/+0.074（74 行）。
- **EXP-013 第 30–34 行**有完整的 median 结果（affine +0.155、isotonic +0.080、1-NN −0.052，全部 Holm 显著）；EXP-016 没有 median 行。
- 稿件把 median 写进方法和 Holm 家族，却不展示结果；读者无法核对"mandatory sensitivity"是否通过。

### WARN-3.3 "五个缺陷"漏掉 Holm 缺陷
- **稿件** §5 104 行："**Five errors** in our own analysis were found by an independent model reading our code."
- **HOLM_FIX.md 第 1–11 行、CD-013 第 4 条**：Holm 实现缺累积最大值，是**独立审阅读代码发现的第六个实现缺陷**。HOLM_FIX 说修正后 EXP-013 家族有两个 adj p 变化（0.0004→0.0005、0.0005→0.0006），结论不变。
- 稿件只列五个，未说明这是"五个之一部分"还是"全部"。若声称全部，则与记录不符。

---

## 4. 事后调整 — WARN

### 已核实为预注册的部分
- 0.05 等价边界确实是预注册的：**EXPERIMENT_PLAN 第 119 行**"等价边界定为 0.05，不是 0.03"，第 121 行给出通过线。稿件 74 行称"pre-registered 0.05 equivalence margin"，这一半准确。

### WARN-4.1 mean 主口径是看结果后的修订
- **CD-004 第 24–26 行**："Use mean MAE over donor draws as primary... **Record this as an amendment after inspecting results.**"
- **EXPERIMENT_PLAN 第 53 行**原本写的是"mean 与 median 双报，两者都必须满足通过线"，没有指定 mean 为主。
- **稿件** 51 行把 mean 写成 "(primary)"，55 行说"Four degrees of freedom were frozen before the main experiments: the aggregation rule..."。聚合规则的主口径是在看了 EXP-007 的 median 8/11 之后由 CD-004 修订的；修订记录在 CD-004，但稿件未披露。
- 缓解：EXP-008 正确重跑后 mean 与 median 都 11/11，所以主结果不依赖这个选择。但"冻结在 main experiments 之前"的表述不准确。

### WARN-4.2 "+0.033 ... all above the 0.05 margin" 不准确
- **稿件** 74 行："changed error by +0.108 and +0.146 (mean, two seeds) and **+0.033** and +0.074 (median), **all above the pre-registered 0.05 equivalence margin**."
- **EXP-007 第 22 行**：median/seed0 Δ=+0.033，CI [−0.009, +0.057]，标注"⚠️ 上界 0.057 略超"。
- +0.033 的**点估计低于 0.05**；超过 0.05 的是 CI 上界。四个配置都"未通过"闸门是对的，但"all above the margin"把点估计和 CI 混为一谈。

### WARN-4.3 四分位分层是事后提出的候选
- **EXP-019 第 45 行**把"效应随 RUL 改变符号"列为"**候选，未直接检验**"；**EXP-020 第 12–14 行**明确"本实验直接检验"这个候选。
- **稿件** 86 行把它写成"Stratifying queries by RUL quartile ... preserves the sign"，没有标注这是 EXP-019 之后的事后分层。EXP-020 第 39 行甚至写"不需要预注册分层"——这个理由本身有诚信风险（事后分层不能因为"不需要预注册"就当成确证）。
- 判 WARN：分层结果本身是描述性的，稿件也说"Individual cells are underpowered"，没有把它当确证；但"事后"这一点未披露。

---

## 5. 混淆未披露 — **FAIL**

### FAIL-5.1 §3.3 的 cell-macro 承诺被 §4.3 的 EXP-018 数字违反

**稿件**
- **51 行**："The statistical unit is the operating condition, never the cell or the query. **Within a condition, queries are averaged within each cell and then across cells, so every arm uses identical weights.**"
- **88 行**："A donor-availability constraint ... restricts evaluation to 199 queries and reverses the affine and isotonic effects (**−21.76 and −16.85**, 2/11 and 0/11 conditions improved)."

**实验记录**
- **EXP-018 第 26–27 行**：affine 402.41→424.16，Δ **−21.76**，2/11；isotonic 389.05→405.91，Δ **−16.85**，0/11。数字确实来自这里。
- 但 **`asof.py` 第 72–75 行**：`per[(cal,m)].append(mean(acc[cal]))` 后 `res[key][g] = mean(per[key])`——**在工况内对 query 取平均**，不是先按电芯平均再按工况平均。
- **CD-014 第 10 行**独立指出："EXP-017 averages queries within each cell before averaging cells; **EXP-018 pools eligible queries within each condition. Cells with more eligible queries therefore receive more weight.** You changed donor eligibility, evaluation population, and aggregation simultaneously."
- **EXP-019 第 26–27 行**在**同一批 199 个查询**上改用 query→cell→condition 的同权重（`factorial.py` 第 83–90 行）：受限池 affine **−21.57**，isotonic **−24.92**。
- 也就是说：在稿件 §3.3 承诺的口径下，isotonic 的反转是 **−24.92**，不是稿件报的 **−16.85**；相差 8.07（约 48%）。affine 的 −21.76 与 −21.57 接近，问题主要在 isotonic。

**为什么是 FAIL**
- 这不是"两个实验略有出入"，而是稿件把**一个明确声明不用的加权方式**产生的数字，放在"every arm uses identical weights"的方法节之后报告。
- 稿件紧接着用 EXP-019 的因子设计说"no interaction ... the unrestricted pool also reverses"，但没有说明 EXP-019 的受限臂与上一句的 −16.85 不是同一个加权；读者会把两个数字当成同一分析的两部分。
- 2/11、0/11 的条件计数也来自 query 加权的 EXP-018；EXP-019 没有打印每臂的条件计数，无法确认在 cell-macro 下仍是这两个数。
- 结论方向（反转）在两种加权下都成立，所以这不是"结论造假"；但**报告的数字与声明的方法不一致**，属于证据完整性问题，且修正后的数字就在同一项目的 EXP-019 里。

### FAIL-5.2 相关的未披露项
- **k=32 的单供体合格性混淆**：**EXP-010 第 56 行**明确"k=32 的 m=1 = 5.336 比 k=16 的 m=1 = 4.816 更差——单供体臂要求供体有 ≥32 行，只剩 9 个工况。这是合格性混淆"。稿件没有报告 k=16/32，所以不直接受影响；但 §4.1 只说"8 rows"，未说明为何只报 k=8（EXP-010 第 54 行："k=16/k=32 不可写"）。这不是 FAIL，只是范围选择的披露不足。
- 63→57 的排除已在 2.2 记为 WARN。

---

## 6. 失败与缺陷 — WARN

### 与记录一致的三条
- **#2 无 MC 循环**：EXP-007 顶部横幅 + EXP-008 第 12–22 行。✓
- **#3 floor(k/m)**：EXP-009 顶部横幅 + EXP-010 第 12–18 行；k=8/m=3 只得 6 行。✓
- **#5 Ridge 全数据标准化**：EXP-021 第 14 行 + `controls.py` 第 100–104 行（在 LOGO 前算 μ/σ）。✓

### WARN-6.1 #1 的症状描述与 R0 记录不符
- **稿件** 106 行："A label-budget experiment drew a single random sample per configuration and reported it as an expectation; **apparent non-monotonicity in the p-values disappeared once a thousand draws were used.**"
- **EXP-002 第 30–35 行**的 p 值：0.0186、0.1748、0.0068、0.2783、0.5195、0.2783——非单调。
- **R0（`r0_reanalysis.txt` 第 4–10 行）**的 p 值：0.0674、0.7002、0.7002、1.0000、0.2402、1.0000——**仍然非单调**。
- 消失的是"k=2/k=4 的显著"，不是"p 值的非单调"。这句话把症状说反了。

### WARN-6.2 #4 的后果描述与 EXP-013 不符
- **稿件** 106 行："A cross-dataset replication drew one-donor and two-donor arms from different donor pools, **which produced an apparent dataset disagreement that disappeared under a common support.**"
- **EXP-012 第 42–48 行**：UConn isotonic +0.036（p=0.368）vs ISU +0.109（p=0.002），这是"数据集不一致"。
- **EXP-013 第 31 行**修正后：ISU isotonic +0.085（Holm 0.0005），**仍然显著**；UConn +0.036（p=0.368）仍不显著。不一致的显著性并没有消失，EXP-013 第 49 行把它解释为"UConn 功效不足"。
- 真正消失的是 EXP-012 里"1-NN 均值看起来变好、配对 Δ 却有害"的内部不一致（CD-011 第 3 条）。稿件把"内部口径不一致"说成了"数据集不一致消失"。

### WARN-6.3 "five" 不完整，#1 的独立来源无记录
- **HOLM_FIX.md / CD-013 第 4 条**的 Holm 缺陷是第六个（见 3.3）。
- **EXP-006 第 48–50 行**的"第一版 M0 把 condition 作用域实现成在全部非评估行上拟合，m 根本没参与"也是实现缺陷；记录未说谁发现。若这是自查发现，稿件 104 行"None was found by self-inspection"就不成立。
- #1 的来源只有 `r0_reanalysis.py` / `.txt`，没有 CD 条目、没有独立审阅者的 threadId；#2–#5 分别有 CD-006/008/011/015。稿件说"each found by independent review of our code"，对 #1 缺乏记录支持。
- 判 WARN：五条中三条完全对得上，另外两条是描述错误而非虚构；"five"的不完整和 #1 的来源是披露问题，不改变结果。

---

## 未发现问题的部分（避免只列问题）

- 四分位 16 个格子（+28.81 / +21.08 / +17.12 / +17.55；+11.53 / +27.00 / +27.88 / +22.39；+7.29 / +12.83 / +9.39 / +7.39；−10.41 / −7.41 / −5.88 / −11.48）逐项对 **EXP-020 第 24–27 行**。
- 行轴 +0.108 / +0.146 / +0.033 / +0.074、9/64、3 个工况、n=3 逐项对 **EXP-007 第 20–29 行**。
- 0.018 漂移 / 0.0063 seed sd 对 **EXP-006 第 36 行**。
- 199 查询、−21.76 / −16.85、2/11、0/11 对 **EXP-018 第 26–27 行**（但加权问题见 5.1）。
- 462.04 / 454.33 / 514.00 / 492.58 / 2.542 / 2.470 / 499.98 / 7.40 / 0.34 对 **EXP-021 第 25、33–34 行**和 **EXP-022 第 25、31–33 行**。
- 五个缺陷中的 #2/#3/#5 与 EXP-007/009/010/021 一致。
- 引用元数据本身（作者、年份、DOI）与 `AUDIT_CITATIONS.md` 一致；本次不重复核验。

## 附注（六类之外，但审计必读材料之间有一处矛盾）

- **稿件 29 行**写 "Zhao (2026) scans **five, ten and twenty** target cells"。
- **AUDIT_CITATIONS 第 23 行**写 "稿件只引其结论方向，**未引具体数字**"——这与稿件 29 行不符。Zhao 的 k=5/10/20 来自 LIT_SURVEY 的二手转引，AUDIT_CITATIONS 自己说未核对原文。这不是六类实验证据问题，但属于引用证据完整性，投稿前应补原文核对或删去具体数字。

---

## 总判定：SERIOUS-ISSUES

**理由**
1. 无编造数字，主效应方向（affine/isotonic 正、1-NN 负）有 EXP-013/016/017 支持；所以不是"数据造假"。
2. 但第 5 类有一处 FAIL：§4.3 报的 isotonic −16.85 来自 query 加权的 EXP-018，与 §3.3 声明的 cell-macro 同权重冲突；同项目 EXP-019 在 cell-macro 下给出 −24.92。报告的数字与声明的方法不一致，且修正值未披露。
3. 第 3、6 类有实质遗漏：EXP-005 的相反结论、强制 median、Holm 第六缺陷。
4. 第 1、2、4 类有多处归属/表述错误，但均不改变主结论。
5. 因此不是 CLEAN，也不是只有文字问题的 MINOR-ISSUES；按"报告数字与声明方法不一致 + 关键相反实验未报告"判 SERIOUS-ISSUES。

**修复优先级（供作者）**
1. §4.3 改用 EXP-019 的 cell-macro 数字（affine −21.57、isotonic −24.92），或明确标注 −16.85 是 query 加权的旧分析并给出两者差异；同时说明 2/11、0/11 的计数口径。
2. 在 §4.1 加一句 EXP-005 的电芯级饱和结果及其被工况级 n=3 取代的理由。
3. 补 median 主表或删去 "mandatory sensitivity" 的措辞。
4. §5 改为"六个缺陷"或明确"五个（另有 Holm 缺陷在附录）"；修正 #1/#4 的症状描述；说明 #1 的发现来源。
5. 统一 453.33/454.33 与 HGB intercept 的两套数，注明是两次运行还是取哪一个。
6. 说明 63→57 的工况排除；把 "one predictor family" 改为"两个基模型"。
