> ⚠️ **更正（主代理，2026-11-07 22:20）**：本文件第 79、86、302、344 行引用的 −0.583 与「保序重建循环轴」**均已作废**。`num_cycles` 是相邻 RPT 之间的段长，正确重建是 cumsum（spearman(soh,cum) 在 52/64 电芯上 = −1.0000），corr(EOL_rpt, EOL_cum) = +0.811。本文件其余审计意见（含 ICC=0.414、逐参数消融、a1 零增益等独立复算）仍然有效，权威数字见 docs/e1_v2_fixed_results.md。

# REVIEW_AGENT5 · Critical Review

> **审稿人**：Agent 5（Critical Reviewer），按 IEEE TIM / TII / Applied Energy 审稿标准执行
> **日期**：2026-11-07
> **审阅对象**：`docs/manuscripts/v1.0-draft.md`、`docs/idea_report.md`、`docs/e1_final_results.md`、`docs/bayreuth_D_results.md`
> **交叉核对**：`scripts/e1_final.py`、`scripts/bayreuth_D.py`、`scripts/tier1_pass.py`、`scripts/phys_reg.py`、`scripts/tier2_pass.py`、`docs/tier1_results.md`、`docs/tier2_results.md`、`docs/rq2_gate_results.md`、`docs/autonomous_research/NEXT_ACTION.md`、原始 `data_slowpulse_1.pkl` / `data_cc_1.pkl` / Bayreuth xlsx
> **证据等级说明**：本审阅中所有"本次复算"数字，均由我在 `%TEMP%` 下以只读方式重跑同一 pipeline 得到（未写入仓库任何文件）；文献层面我**没有**完成独立的系统检索（`web_search` 两次超时），因此本报告不对"是否与某篇具体论文重复"下断言，只判定"现有证据能否支撑其新颖性主张"。

---

## 0. 总体判定

**建议：Reject（当前形态）。** 若按第 7 节重做，可考虑 Major Revision 后重投。

不是写作问题，是证据问题。三条核心主张在**工况级**（也就是论文自己选定的统计单位）统计下分别变成：

| 论文主张 | 论文证据 | 工况级复核 | 结论 |
|---|---|---|---|
| 非循环通道带来显著增量 | −8.6%，CI [−0.999, −0.133] | cluster bootstrap CI **[−1.33, +0.22]**；11 个工况中 7 个改善（sign test p = 0.27） | 不成立 |
| 物理参数化优于波形描述量 | 6.020 vs 6.109 | 直接配对 Δ = **−0.089，CI [−0.36, +0.20]**，51.6% 电芯改善 | 不可区分 |
| 跨工况边界：a1 与 c 存活 | 19/23、18/23 | c 在任一 \|ρ\|≥0.1 的效应量门槛下即失效（14/19，p = 0.032 > 0.0083） | 仅 a1 存活 |

更根本的问题是：**标签不是 RUL**。它是"剩余体检次数"，与循环数口径的 RUL 的秩相关只有 **0.233**（本次复算，n = 2,739），且被 RPT 节奏（每工况 1.36–7.03 cycles/RPT）系统性混淆。这解释了论文从未报告的一个反常结果：**把真实的 SOH 与容量加进特征，误差反而变差**（6.587 → 6.793）。在一个以退化为对象的任务上，给定真值状态变量应当有帮助；它没有，反而变差，这强烈提示标签的方差并不主要来自退化状态。

论文在透明性上有明显优点（负结果不藏、转导结果主动排除、预注册判据、限制章节诚实），复现性也好（我独立重跑得到 6.587 / 6.020 / 7.789，与 `e1_final_results.md` 完全一致）。但透明不等于正确：**当前证据支撑的结论比论文写出来的窄得多**，而摘要与结论按现在的写法会在 TIM 一审被拒。

---

## 1. 复现基线与新增核算

### 1.1 复现（验证 pipeline 一致）

| 特征集 | 文档报告 | 本次复算 | 一致 |
|---|---:|---:|---|
| A_curve (54) | 6.587 | 6.587 | ✅ |
| A_curve + C_desc30 (82) | 6.109 | 6.109 | ✅ |
| A_curve + C_ecm (84) | 6.020 | 6.020 | ✅ |
| C_ecm only (30) | 7.789 | 7.789 | ✅ |

复现成立，说明下面新增的核算与论文同源、可比。

### 1.2 论文缺失、但审稿必问的 ablation（本次补跑）

| 特征集 | 维度 | LOGO 电芯宏平均 MAE | 说明 |
|---|---:|---:|---|
| A_curve | 54 | 6.587 | 基线 |
| **A_prefix**（+ capacity + SOH） | **56** | **6.793** | 加入真值状态变量后**变差** |
| A_prefix + C_desc30 | 84 | 6.555 | 与 A_curve+C_ecm 同维 |
| A_prefix + C_ecm | 86 | 6.359 | 仍差于 A_curve+C_ecm（6.020） |
| A_curve + {c}（6 个稳态电压） | 60 | **6.069** | **6 个数拿到 91% 的增益** |
| A_curve + {a1}（6 个快幅值） | 60 | **6.588** | **零增益** |
| A_curve + {c, a1} | 66 | 6.247 | 加 a1 反而变差 |
| A_curve + {a2, tau2} | 66 | 6.139 | 被判"不可迁移"的参数贡献接近 c |

> 这张表是本报告最重要的一张。它同时说明三件事：(i) 增益主要来自 `c`；(ii) 论文宣称"存活"的 `a1` 预测价值为零；(iii) 论文宣称"失败"的 `a2/tau2` 反而贡献了可观的增益。论文的"适用域边界"叙事与"增益来源"叙事互相矛盾。

### 1.3 参数拟合的可辨识性（原始 17,130 条波形）

| 参数 | 均值 | 标准差 | 范围 | 负值比例 | 唯一值数 |
|---|---:|---:|---|---:|---:|
| c | 3.3020 | 0.0343 | 3.2412 – 3.3480 | 0% | 11,976 |
| **a1** | +0.0002 | 0.0229 | −0.0278 – +0.0285 | **50.0%** | 6,690 |
| **tau1** | 1.000000 | **5.7e-9** | 1.0000000 – 1.0000007 | 0% | 8,910（全部落在 7×10⁻⁷ 内） |
| **a2** | +0.0016 | 0.0127 | −0.0149 – +0.0215 | **50.0%** | 6,531 |
| tau2 | 20.213 | 1.477 | 15.95 – 25.03 | 0% | 17,104 |

**两个"极化幅值"各有一半是负数。** 这不是物理量，是双指数分解在 61 点窗口上的符号不定解。`tau1` 被优化器钉在下界 1.0 上（极差 7×10⁻⁷，sd 5.7×10⁻⁹），在任何实际意义上都是死列。这一点 `NEXT_ACTION.md` 已记录 tau1 触界，但**没有记录 a1/a2 各 50% 为负**——后者更严重，因为它直接否定了"幅值"这一物理语义。

---

## 2. 阻断性问题（Blocking）

### B1 · 预测目标不是 RUL，且被 RPT 节奏混淆

**问题**：论文把标签定义为"到首次 SOH ≤ 80% 的剩余体检次数（0–77）"，并在 §3 用一段话把它说成是无害的单位选择（"We therefore use the inspection index as the time axis"）。实际上这是一个被测试协议决定的量，不是电池寿命。

**为什么是问题**：

1. **与循环口径的 RUL 几乎不相关。** 本次复算：行级 Pearson **0.176**、Spearman **0.233**（n = 2,739）。`NEXT_ACTION.md` 记录的电芯级 `corr(EOL_cyc, EOL_rpt) = −0.583` 方向一致（我未能直接复算该值：少量 EOL 行的 `num_cycles` 缺失，使电芯级相关退化为 NaN）。两个口径的秩相关 0.23，意味着论文测的几乎不是同一个量。
2. **标签被每工况的 RPT 节奏支配。** 11 个工况的 cadence（cycles per RPT）从 **1.36 到 7.03**，相差 5.2 倍；EOL_rpt 中位数从 20.5 到 70.5。cadence 是测试排程，不是电芯属性，也不在任何特征里。模型只能靠"猜这个工况多久做一次体检"来预测标签。
3. **决定性反证：加入真值 SOH 与容量使误差变差**（6.587 → 6.793）。如果标签度量退化，给定 SOH 应当有帮助。它没有，而且是负的。这强烈提示标签的方差有相当部分来自 cadence，而不是退化状态。
4. 论文自己在 §5.4 说"用错统计单位会翻转结论"，却从未问过"用错时间轴会不会翻转结论"。

**可执行修正**：

- 用 `NEXT_ACTION.md` 已验证的保序重建循环轴（64/64 电芯可重建，畸变中位数 0、最大 11.8 循环）重跑 E1/E2，把 **RUL(cycles)** 作为主目标，RUL(RPT) 作为敏感性分析；两个目标都报告，并报告二者的秩相关。
- 若重建轴不可用：改标题与摘要，明确写 "remaining reference-performance-test count"，并在 §3 第一段给出 **0.233 的秩相关**作为效度上界，同时说明结论不可外推到 cycles/日历时间。
- 无论哪条路，都必须报告 A_prefix 的结果（现在完全缺失），因为它是"标签是否在度量退化"的直接检验。

**验收标准**：在同一协议下，A_prefix 不劣于 A_curve；否则目标定义必须重做。

---

### B2 · 统计推断单位错误：以电芯为单位做 bootstrap，忽略 11 个工况的聚类

**问题**：主结果的 95% CI 来自"5,000 次电芯级配对 bootstrap"，把 64 个电芯当作独立样本。但 LOGO 的独立单位是 **11 个工况组**，每组 6 个电芯（group 11 为 4 个），同组电芯共享同一折、同一训练集、同一 cadence，误差强相关。

**为什么是问题**：

1. **论文自己已经论证过这一点。** §5.4 写道："Each Bayreuth condition holds one or two cells, and cells within a condition are strongly correlated. Using cells as the unit would nearly double n and would flip the 0.74 parameters from non-significant to significant. We pre-registered the condition as the unit." 这段话完全正确——然后 E1 用了相反的规则。**同一篇论文里，Bayreuth 用工况级、UConn 用电芯级，而后者恰恰是主结论。** 审稿人会直接引用 §5.4 来质疑 §5.1。
2. **换成工况级后 CI 跨零。** 本次复算：电芯级 [−1.002, −0.122]；**工况级 [−1.330, +0.219]**。同一组预测、同一统计量，只换重采样单位，显著性消失。
3. **工况级方向检验也不显著。** 11 个工况的 Δ 为 +0.452、−1.417、−2.700、+0.971、+0.070、−1.915、−0.295、−0.793、−1.871、+1.460、−0.028：**7/11 改善，sign test p = 0.274；未加权组均值 −0.551，t(10) = −1.40，p = 0.192；组级 bootstrap CI [−1.273, +0.178]**。
4. **增益高度集中且方向不一致。** 4 个工况变差，其中 group 10 恶化 +1.46；增益几乎全部来自 group 3（−2.70）、6（−1.92）、9（−1.87）、2（−1.42）。摘要里的"62.5% of cells improved"掩盖了这一点。

**可执行修正**：

- 主推断改为 **condition-cluster bootstrap**（重采样 11 个 group，组内保留全部电芯），或 mixed-effects model（condition 为随机截距）。报告两种单位的 CI，并明确主结论以哪一种为准。
- 增加 **per-condition forest plot**（11 行，每行 Δ 与 CI），以及跨工况的 sign test。这是审稿人一定会要的图。
- 摘要与结论按工况级结果改写：若 CI 跨零，就不能写 "reduces error"，只能写 "point estimate suggests, not significant at the condition level"。
- 顺带修正 "62.5% of cells improved"：40/64 的 sign test p = 0.030，在聚类下不成立；且 C_desc30 也是 62.5%，该指标不具区分度。

**验收标准**：工况级 95% CI 不含零，且 11 个工况中至少 9 个方向一致。达不到，主结论降级为 exploratory。

---

### B3 · "物理参数化优于波形描述量"不成立，且物理语义已被拟合结果否定

**问题**：论文的贡献之一是"fitted physical parameters outperform unfitted waveform descriptors once the descriptor count is nearly matched"，并据此说"roughly a third to a half of the apparent parameterisation advantage is a dimension effect"。

**为什么是问题**：

1. **直接配对检验不显著。** 本次复算：C_ecm − C_desc30 = **−0.089，95% CI [−0.364, +0.201]**，只有 **51.6%** 的电芯改善（与抛硬币无异）；工况级 CI [−0.460, +0.305]。论文从未对这对比较做过 CI，却把它写进摘要。审稿人会要求这个数，而它不支持结论。
2. **"维度匹配"在算术上不成立。** C_ecm 名义 30 维，其中 6 列（6 条波形的 tau1）被钉在下界、数值上是常数，**有效维度 24**；C_desc30 是 28 维且全部变化。所谓 30 vs 28 的匹配，实际是 24 vs 28——描述量一侧反而更多。因此"三分之一到一半是维度效应"这个分解没有依据，必须删除。
3. **增益来源与论文叙事相反。** 本次复算：A+{c} = 6.069（6 个数拿到 0.518 的增益，占总增益 0.567 的 91%）；A+{a1} = 6.588（零增益）；A+{a2, tau2} = 6.139。**论文说"存活"的 a1 没有预测价值；论文说"失败"的 a2/tau2 贡献了接近 c 的增益。** 而 c 是稳态电压——整个通道里最不"非循环"、最接近一次静置电压读数的量。
4. **物理语义已被数据否定。** a1、a2 各有 **50%** 的拟合值为负（§1.3）。负的"极化幅值"没有物理意义。tau1 被钉在下界 1.0（采样极限），不是时间常数。论文 §4 说"yielding ... two polarisation amplitudes"，§5.3 用 a2 的符号翻转做物理解释——这些都建立在不成立的语义上。
5. **摘要的表述超出证据。** "Fitted physical parameters still outperform unfitted waveform descriptors" 是一个方向性断言，而证据是一个跨零的区间。

**可执行修正**：

- 删除 E2 的"优势"主张，改为："在维度不匹配且参数不可辨识的条件下，两类表示的差异不可区分（Δ = −0.089, 95% CI [−0.36, +0.20]）。"
- 从 C_ecm 中移除 tau1（6 列常数），重算维度与全部结果；在方法节明确写"effective dimensionality = 24"。
- 对 2-RC 拟合加物理约束（a1, a2 ≥ 0；tau1 < tau2），重拟合后重跑；若约束后拟合残差显著变差，说明数据不支持 2-RC，应退回 1-RC 或改用 stretched exponential / DRT。
- 报告参数的 identifiability 诊断：Jacobian 条件数、参数间相关、bootstrap 标准误、触界比例。
- 若保留"physical parameterisation"作为贡献，必须给出 A+{c} 之外的增量证据；目前证据只支持"c 这一个量有用"。

**验收标准**：C_ecm vs C_desc30 的 95% CI 不含零，且 a1/a2 的负值比例 < 5%。达不到，就不能把"物理参数化"写成贡献。

---

### B4 · Bayreuth 的 "c 存活" 是符号检验的假象

**问题**：论文的核心边界主张是"only the fast polarisation amplitude and the steady-state voltage keep a consistent direction (19/23 and 18/23, p = 0.0013 and 0.0053)"。其中 c 的结论完全依赖于把 `|ρ| ≈ 0.04` 的相关性当作方向票。

**为什么是问题**：

1. **c 的 18 票里有 4 票是噪声。** 从 `bayreuth_D_results.md` 的表：c 在 25°C/1.0C = −0.06、30°C/0.75C = −0.04、45°C/1.5C = −0.04、55°C/1.0C = −0.04。符号检验把它们算作"负向"，但它们与 0 无法区分。
2. **加任何最小效应量门槛，c 立刻失效。** 本次复算（对报告表做敏感性分析）：\|ρ\| ≥ 0.1 时 c 为 14/19，**p = 0.032**；\|ρ\| ≥ 0.2 时 13/18，p = 0.048；\|ρ\| ≥ 0.3 时 13/18，p = 0.048。全部 > 0.0083。**a1 则在所有门槛下都通过**（\|ρ\| ≥ 0.5 时仍 12/14，p = 0.0065），说明 a1 是稳健的、c 不是。
3. **检验的原假设本身不成立。** 23 个"工况"是 6 温度 × 4 倍率的**全因子设计**，每格恰好 2 个电芯，不是 23 个可交换的独立抽样。二项检验假设条件间独立同分布，这里既不独立（相邻温度/倍率共享物理机制），也不可交换（设计是结构化的）。此外，每个条件内的 ρ 来自同一电芯的 72 段静息，序列相关会使 ρ 的方差被低估。
4. **"中位数"在 n = 2 时是两数的平均。** 两个电芯符号不一致时，median 会落在 0 附近并被计入某一侧——这是那 4 个 `|ρ| < 0.1` 的一个可能来源。

**可执行修正**：

- 主分析改为**效应量感知**的检验：对每个参数做 Fisher-z 随机效应 meta-analysis（condition 为研究单位），或 mixed-effects model（condition random intercept，cell nested），或**置换检验**（在电芯内打乱 SOH 顺序，重跑完整 23 条件 pipeline，得到 sign consistency 的零分布）。符号检验降级为敏感性分析。
- 报告 `|ρ| ≥ 0.1 / 0.2 / 0.3` 三档的 sign consistency 与 p，作为 robustness table。
- 摘要与结论改为："只有快极化幅值 a1 在多重比较校正与效应量门槛下都保持同向；稳态电压 c 的结论依赖于近零相关被计为方向票，不稳健。"
- 同时报告每条件的两个电芯各自的 ρ（现在只有 median），让读者看到 n = 2 的不稳定性。

**验收标准**：主检验在效应量门槛下仍 p < 0.0083。目前只有 a1 满足。

---

### B5 · "排除更强表征学习"是稻草人，贡献 #2 不成立

**问题**：论文把"增益来自更强的建模能力"当作主要替代解释，并用四条"progressively stronger representation schemes"（7.825 / 7.452 / 6.805 / 6.274）全部劣于 6.020 来"排除"它，写进贡献列表第 2 条。

**为什么是问题**：

1. **这四条不是"更强"。** GRU 是 30→32 的单层、约 1.3 万参数、150 epoch、固定 L=16、**无验证集、无 early stopping、无超参搜索、单种子**（`tier2_pass.py` 里只有一次 `torch.manual_seed(0)`）。在 2,813 行上，这比 300 iter 的 HGB 更弱而不是更强。120 维手工轨迹描述量更不是"representation learning"，它只是更多特征。
2. **逻辑是非 sequitur。** "这些方法输了"只能推出"这些方法在当前调参预算下不适合 64 电芯"，推不出"拟合能力不是增益来源"。要排除 capacity 解释，正确做法是**在胜出的特征集上增加容量**（更深/更多 iter 的 HGB、5-seed ensemble、带 early stopping 的 MLP），看增益是否被吸收；论文没做。
3. **判据被挪用。** 12% 的门槛原本是"方法层是否值得写进贡献"的判据（`idea_report` E4），不是"是否能排除替代解释"的判据。用一个为 A 目的设计的实验去支持 B 结论，是 post-hoc 复用。
4. **转导结果被过快排除。** 5.724 来自对预测做 per-cell isotonic 投影，`phys_reg.py` 显示它**只用预测、不用标签**（`ir.fit_transform(rpts[ids], base[ids])`），所以不是标签泄漏，只是读了整批查询。但"不可部署"这个理由不充分：在**训练集**上拟合同样的单调映射再应用到测试集，是一行代码的因果版本，论文没试。而 5.724 说明模型排序能力好于其 MAE，这本身是有价值的信息。

**可执行修正**：

- 删除贡献 #2 与摘要中 "which locates the gain in the channel rather than in fitting capacity"。
- 改写为负结果段："四个额外的模型/正则方案未超过基线；这**不排除**容量效应，只说明在这些配置下无收益。"
- 增加一个 capacity control：同一 84 维特征上跑 (a) HGB 3× iterations、(b) 5-seed bagging、(c) 带 early stopping 的 MLP。若增益被吸收，论文的机制解释就失败；若没有，才谈得上"排除"。
- 增加可部署的单调后处理（训练集拟合 isotonic → 测试集应用），报告其 LOGO 结果。
- 若要保留"负结果阶梯"作为贡献，应改为"我们报告了四条失败路线及其失败模式"，而不是"排除了替代解释"。

---

## 3. 主要问题（Major）

### M1 · 基线不是"合理强基线"，A_curve 的构造本身有问题

- **证据**：`e1_final.py` 的 A_curve 把每个 (cell, rpt) 的 **2–6 段、每段 600 点**的 CC 记录按均值电压排序后拼接（长度 1,200–3,600 点），再 `np.array_split` 成 50 个等数量箱。段数在 2–6 之间变化（6 段 863 例、5 段 1,350 例、4 段 526 例、3 段 109 例、2 段 7 例），因此**第 k 个箱在不同体检里对应不同的电压/容量位置**。此外，我检查的样例（cell 2, rpt 0）中每段内部电压随索引上升（3.349→3.367）；若各段按时间倒序存储，则按均值电压升序拼接后整条曲线是时间反序的。
- **为什么是问题**：基线特征未配准，等于给对照组装了一个弱基线；"通道增量"可能部分是"基线被削弱"的产物。论文没有任何"强基线"（capacity-only、IC 特征、序列模型、已发表方法）。
- **修正**：把曲线重采样到固定电压网格（如 3.6→2.5 V，200 点）或固定容量分数网格后再分箱；报告箱对齐后的 A_curve 结果；补 capacity-only 与 IC-feature 基线；补至少一个已发表方法（如 BatteryLife 的 CyclePatch 或简单 LSTM on capacity）。

### M2 · 效应量表述误导：8.6% 是相对一个 27% 误差的基线

- **证据**：本次复算，电芯宏平均 MAE 6.587 → 6.020，以全体平均 RUL（24.35）粗归一化为 **27.1% → 24.7%（2.3 个百分点）**；行级 WAPE（Σ|e|/Σy）**27.1% → 26.0%（1.1 个百分点）**；MAPE(y>0) 35.4% → 31.0%；R² 0.697 → 0.721。**绝对改善取决于口径，但都在 1–2 个百分点量级，不是 8.6%。**
- **为什么是问题**：摘要只给 8.6%，读者无法判断这是"从 27% 到 25%"还是"从 3.8% 到 3.5%"。TIM/TII 审稿人会要求 MAPE/RMSE/R² 与 EOL 邻域误差。
- **修正**：主表加 MAPE、RMSE、R²；单独报告 RUL < 10 区间的 MAE（决策最敏感区）；说明过预测与欠预测的非对称代价。

### M3 · 没有任何不确定度量化

- **证据**：全文只有点预测与一个 bootstrap CI（还是对均值差的）。
- **为什么是问题**：RUL 是安全相关量，TIM 审稿人默认要求 prediction interval 与 coverage。
- **修正**：quantile HGB 或 conformal prediction，报告 90% 区间的 empirical coverage 与区间宽度；至少报告 per-cell 误差分布。

### M4 · 11 个工况组从未被定义

- **证据**：仓库内 `data/external/uconn/` 只有两个 pkl，无任何 metadata；manuscript 只说 "11 operating-condition groups"，未给温度/倍率/SOC 窗口/协议。
- **为什么是问题**：读者无法判断 LOGO 到底在多远的分布外推——这是"cross-condition"主张的全部意义所在。`NEXT_ACTION.md` 自己说 UConn 的工况族"远窄于 Bayreuth"，但窄到什么程度没有数字。
- **修正**：加一张表列出 11 个 group 的工况参数与电芯数；说明 group 间的最小/最大差异；若原始数据无此信息，向数据集作者确认或从 `num_cycles`/RPT 间隔反推并标注为推断。

### M5 · 新颖性主张缺乏检索支撑

- **证据**：11 篇参考文献；§2 没有任何 inline citation（草稿里全是描述性句子）；"none of this work performs the comparison that would settle the matter" 是一个强负向断言，但没有检索协议（库、检索式、时间、纳入/排除标准）。
- **为什么是问题**：负向新颖性主张的举证责任在作者。11 篇文献不足以支撑"没人做过"。我未能完成独立检索（工具超时），因此不断言重复，只断言**当前证据不足以支撑该主张**。
- **修正**：补系统检索段落（数据库、检索式、日期、命中数、筛选流程）；列一张"最接近的 5 篇工作 × 他们做了什么/没做什么"的表；把 "none of this work" 改为 "to our knowledge, none of the works we surveyed"。

### M6 · 机制主张与证据不符：增益不是"跨工况"专属

- **证据**：LOGO −8.6%，LOCO −9.4%；LOGO−LOCO gap 仅从 1.518 变到 1.429（−0.089）。
- **为什么是问题**：如果通道的作用是"去工况化"，LOGO 的改善应显著大于 LOCO，gap 应明显缩小。它几乎没变。这说明通道带来的是**一般性信息增益**，不是条件不变性。论文的标题、Introduction 的"condition entanglement"叙事、以及"the gain is located in the channel"都暗示了后者。
- **修正**：改写机制段：明确"增益在两个协议下近似同比例，因此不支持'通道主要解决工况偏移'这一机制"；若要主张去工况化，需要 gap 显著缩小的证据（目前没有）。

### M7 · 维度混淆未被真正控制

- **证据**：主对比 54 vs 84 维；C_desc30 是 82 维且多出的 8 个描述量是最弱的（6 个初始斜率 + 2 个跨 SOC 离散度）；没有随机噪声填充对照。
- **为什么是问题**：树模型的有效容量随特征数增长，54→84 的增益无法与"多了 30 个特征"分离。
- **修正**：加 A_curve + 30 维 Gaussian noise 的对照；加 permutation importance 或 SHAP，证明增益来自 c 而非噪声维度；用相同维度做 nested CV 的超参选择。

### M8 · 多重比较与选择性报告

- **证据**：E1 有 3 个特征集 vs 基线、2 个协议；E2 1 个对比；E4 4 个；E5 6 个参数。论文只对 E1 的 3 个做了 bootstrap，未做 family-wise 校正，也未声明哪些是 exploratory。
- **为什么是问题**：在 3 个 E1 对比上做 Bonferroni（α = 0.0167），电芯级仍过（p ≈ 0.005–0.007），但工况级全不过。选择性报告会放大"显著"的印象。
- **修正**：预指定一个 primary contrast（A_curve vs A_curve+C_ecm），其余标为 secondary/exploratory；报告校正后的 p；在表中标注哪些结论经过校正。

### M9 · 组间异质性未报告

- **证据**：11 个工况中 4 个变差（+0.45、+0.97、+0.07、+1.46），增益集中在 4 个工况。
- **为什么是问题**：一个"平均改善但四分之一的工况变差"的通道，在部署上是不同的问题；审稿人会问"我的工况属于哪一类"。
- **修正**：forest plot + 按工况特征（cadence、温度、倍率）解释异质性；报告 worst-case 工况的退化幅度。

### M10 · 承诺过的已发表基线一个都没跑

- **证据**：`idea_report` §3.6 把 BatLiNet [9]、BatteryTTT [6]、RUL-QMoE [10] 列为 baseline；manuscript 一个都没有，全部换成了自建模型。
- **为什么是问题**：论文的"更强表征"论证因此没有外部参照；读者无法知道 6.020 相对领域 SOTA 是什么位置。
- **修正**：至少复现一个（BatLiNet 的 inter-cell 差值学习在 UConn 上可行，且与"消工况"直接相关）；若不可行，明确说明原因并降级主张。

---

## 4. 次要问题（Minor）

| # | 问题 | 修正 |
|---|---|---|
| m1 | `A_prefix` 写成 58 维；按 manuscript 自己的定义（A_curve 54 + capacity + SOH）应为 **56**；`tier1_pass.py` 的旧实现是 **57**（多一个 curve[-1]−curve[0]）；58 与两者都不符 | 改为 56 并在最终脚本中实现核对 |
| m2 | `C_desc30` 名字是 30，实际 **28** 维（18 + 2 + 6 + 2） | 改名 `C_desc28` 或补齐到 30 |
| m3 | "All 17,130 traces converged (0% NaN)" 被当作拟合有效的证据 | 收敛 ≠ 可辨识；改为报告触界比例、负幅值比例、条件数 |
| m4 | 摘要 "50 ms-to-100 s pulse relaxation" 的 50 ms 在仓库内无出处（`NEXT_ACTION.md` 只确认 100 s） | 给出处或删除 |
| m5 | Bayreuth "72 long rests" 与 "74-cycle windows" 两个数字并存 | 统一并说明窗口定义 |
| m6 | 参考文献 [1][2][5][6][11] 的作者/卷期/页码待核实，§2 无 inline citation | 投稿前补齐；否则 desk reject |
| m7 | 三张图都还没做（`Pending before submission` 自认） | 见第 7 节图清单 |
| m8 | `idea_report` §3.3 说"6 条波形 × 每条 5 参数 + 1 = 20 维"，算术上应为 31，与 C_ecm 的 30 维也不一致 | 修正文档 |
| m9 | 5.724 被称为 "upper bound"，但它只是另一个估计量 | 改称 "transductive reference point" |
| m10 | LOCO 被当作 LOGO 的独立确认；两者共享数据与特征，且 LOCO 更易 | 改为 "same-direction check"，不称 independent |
| m11 | "up to 77 reference performance tests" — 实际每电芯 22–77 次 | 给出分布 |
| m12 | 各组有 0–2% 的 `num_cycles` 缺失（含部分 EOL 行），论文未披露；这使 "379 vs 16" 的排序论证无法被读者复算 | 在数据节给出缺失率与处理方式 |
| m13 | 摘要 "6.020 remaining-inspection units" 未定义单位 | 给出一句定义与量纲 |

---

## 5. 叙述超出证据的句子清单（可直接替换）

| 位置 | 原文 | 问题 | 建议改写 |
|---|---|---|---|
| Abstract | "reduces cell-macro error ... (8.6%, ... CI [−0.999, −0.133])" | 电芯级 CI，工况级跨零 | 报工况级 CI，或写 "point estimate −8.6%; not significant when conditions are the unit of analysis" |
| Abstract | "Fitted physical parameters still outperform unfitted waveform descriptors" | Δ = −0.089，CI 跨零 | "the two representations are not distinguishable (Δ = −0.089, 95% CI [−0.36, +0.20])" |
| Abstract | "Stronger representation learning does not help, which locates the gain in the channel rather than in fitting capacity" | 非 sequitur | "four additional models did not beat the baseline; a capacity effect is not excluded" |
| Abstract | "only the fast polarisation amplitude and the steady-state voltage keep a consistent direction" | c 不稳健 | "only the fast polarisation amplitude survives a magnitude-aware test; the steady-state voltage does not" |
| §1 | "We test that objection directly and it fails" | 同上 | "we tested one version of that objection; it did not help" |
| §5.1 | "roughly a third to a half of the apparent parameterisation advantage is a dimension effect" | 无依据的分解 | 删除 |
| §5.1 | "62.5% of cells improve" | 聚类下不成立；C_desc30 也是 62.5% | 移到附录，并给工况级方向 |
| §5.3 | "Within-condition monotonicity is nevertheless strong ... so the failure is one of direction, not of signal" | 72 段静息来自 1–2 电芯，序列相关使 ρ 的方差被低估 | 加"within-cell 序列相关"限定，并给 per-cell ρ |
| §5.4 | "Using cells as the unit would ... flip the 0.74 parameters" | 与 §5.1 自相矛盾 | 保留，但在 §5.1 应用同一原则 |
| Conclusion | "the increment survives a cross-condition protocol" | 工况级不成立 | "the point estimate is stable across protocols, but the condition-level interval includes zero" |
| Title | "for cross-condition battery RUL prediction" | 目标不是 RUL，增益也非跨工况专属 | 改为 "for cross-condition remaining-test-count prediction" 或重做标签后再用 RUL |

---

## 6. 对用户五个指定问题的判定

| 问题 | 判定 | 关键证据 |
|---|---|---|
| **A 预测目标** | **确认是阻断性缺陷，且比预想严重** | 与循环 RUL 秩相关 0.233；cadence 1.36–7.03；加 SOH 反而变差（6.587→6.793） |
| **B 物理参数有效性** | **确认，且不止 tau1** | tau1 被钉在下界（数值常数，极差 7×10⁻⁷）；**a1、a2 各 50% 为负**；2-RC 在 61 点窗口上不可辨识 |
| **C 统计与泛化** | **确认，主结论在工况级不成立** | 电芯级 [−1.00, −0.12] → 工况级 [−1.33, +0.22]；7/11 工况改善，p = 0.27 |
| **D 跨数据集** | **确认 Bayreuth 不是 RUL 验证；且参数检验本身只剩 a1** | c 在 \|ρ\|≥0.1 门槛下 p = 0.032；23 个条件是 6×4 因子设计，非独立 |
| **E 方法层失败** | **失败是真的，但"排除替代解释"的推论不成立** | GRU 1.3 万参数、无验证集、单种子；无 capacity-matched control |

---

## 7. 最小可发表路径（若团队要救这篇）

按顺序做，每步有验收标准；任一步不过，就降级目标而不是改叙述。

**Step 1 — 重做标签（2–3 天）**
用保序重建的循环轴重跑 E1/E2，主目标 RUL(cycles)，副目标 RUL(RPT)。
*验收*：A_prefix ≥ A_curve（SOH 不再是负信息）；循环轴上的主效应与 RPT 轴同向（否则说明结论依赖时间轴定义）。

**Step 2 — 重做推断（1 天）**
condition-cluster bootstrap + per-condition forest plot + 跨工况 sign test。
*验收*：工况级 95% CI 不含零；≥9/11 工况同向。

**Step 3 — 参数审计（2 天）**
移除 tau1；约束 a1, a2 ≥ 0 重拟合；报告 identifiability 诊断；重跑 C_ecm vs C_desc30 的配对 CI。
*验收*：负幅值 < 5%；C_ecm vs C_desc30 的 CI 不含零（否则删除该主张）。

**Step 4 — 基线补齐（3 天）**
固定电压网格重采样 A_curve；加 noise-padding 对照；加 capacity-only、IC-feature、一个已发表方法。
*验收*：主结论在强基线下仍成立（哪怕效应量变小）。

**Step 5 — 边界重做（2 天）**
Fisher-z 随机效应或置换检验；报告效应量门槛敏感性；只保留 a1。
*验收*：主检验 p < 0.0083 且 \|ρ\| 门槛下稳健。

**Step 6 — 不确定度与图（3 天）**
quantile/conformal 区间；三张图（forest plot、per-condition sign-flip heatmap、negative-result ladder with CIs）。

**若 Step 1 或 Step 2 不过**：改为 "A negative result: non-cyclic channels add little beyond the cycling curve under a condition-level protocol"，投 J. Energy Storage / Batteries，篇幅减半，把负结果做成贡献。这条路是诚实的，也比现在这版更容易过审。

---

## 8. 附录：复算清单与未完成事项

### 8.1 我做了什么

- 读取四个审阅对象全文，以及 5 个相关脚本与 9 份历史结果文档。
- 在 `%TEMP%` 下重写 `e1_final.py` 的 build/fit/predict 流程（同超参、同折、同指标），复现 6.587 / 6.109 / 6.020 / 7.789，确认同源。
- 补跑 7 个论文缺失的特征集（A_prefix、A_prefix+C_ecm、A_prefix+C_desc30、A+{c}、A+{a1}、A+{c,a1}、A+{a2,tau2}），以及 6 个 naive/linear 基线。
- 重算 17,130 条 2-RC 拟合的参数分布（负值比例、唯一值数、触界）。
- 做 cell-level 与 condition-cluster 两种 bootstrap；做 per-condition Δ 与 sign test；做 C_ecm vs C_desc30 的直接配对 CI。
- 对 Bayreuth 报告表做效应量门槛敏感性分析（0 / 0.1 / 0.2 / 0.3 / 0.4 / 0.5）。
- 核对 Bayreuth xlsx：48 电芯 / 24 条件 / 每格 2 电芯，45 电芯进入分析 → 23 条件（与 manuscript 一致，与 `bayreuth_dataset.md` 的"12 组 × 4 电芯"不一致；后者是文档错误）。
- **未发现标签泄漏**：所有特征均为当次体检及之前的信息；64/64 电芯均达到 80% SOH，不存在右删失选择偏差；5.724 的 isotonic 只对预测做单调化，未用标签。这三点是论文做得对的地方，应在 rebuttal 中主动说明。

### 8.2 我没做 / 不能做

- **未完成独立系统文献检索**（`web_search` 两次 60 s 超时）。因此本报告不对"是否与某篇论文重复"下结论，只判定新颖性主张缺乏支撑。`docs/papers/` 的 9 篇 PDF 我**没有逐篇精读全文**；引用的文献信息均来自 manuscript / idea_report 的转述，阅读等级为"仅题录/仅摘要"。
- 未验证 `NEXT_ACTION.md` 中 2-RC vs 1-RC 的 RMSE 对比（0.000428 vs 0.001982）与 `corr(EOL_cyc, EOL_rpt) = −0.583`（因少量 EOL 行的 `num_cycles` 缺失，电芯级相关无法直接计算；改用行级相关 0.176/0.233 作为替代证据）。
- 未重跑 E4（GRU/物理正则）；相关判断基于 `tier2_pass.py`、`phys_reg.py` 的代码审阅与 `tier2_results.md` 的数字。
- 未修改仓库任何文件；所有复算脚本在 `%TEMP%`（`rv5_build.py`、`rv5_models.py`、`rv5_surv.py`、`rv5_boot.py`、`rv5_bysens.py` 等），可复现。

### 8.3 给 PI 的一句话

论文的**诚实度**高于同类工作，但**证据强度**低于其叙述。三个数字决定这篇能否投 TIM：工况级 CI 是否含零、C_ecm vs C_desc30 的 CI 是否含零、c 在效应量门槛下是否存活。目前三个都指向"不成立"。先把标签修好，再谈通道。
