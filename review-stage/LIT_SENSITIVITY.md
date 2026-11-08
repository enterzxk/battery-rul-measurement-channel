# LIT_SENSITIVITY · 「校准/后处理选择的敏感性」查重

> **只回答一个问题**：我们准备主张的「电池 RUL 校准后处理层中，未声明的实现选择会大幅改变报告的效应量，其中**拟合作用域**与**评估总体**主导，后者能翻转符号」——这个角度在文献里被做过没有？
>
> 检索日期：**2026-11-08**（Asia/Shanghai）。检索工具：OpenAlex API、arXiv API、Crossref API、内置 web_search。
> 限制：web_fetch 不可用（按要求未使用）；MDPI/ScienceDirect 网页直连 403（MDPI 经 `mdpi-res.com` 镜像取到 PDF）；Nature 主 PDF 404，经 `_reference.pdf` 取到全文。
> 全文落在 `.research/lit/`（`peng_energies.txt`、`scirep_ref.txt`、`cai_review.txt`），可复核。

---

## 0. 被查重的主张（逐条拆开，否则无法判定）

| 子命题 | 内容 |
|---|---|
| **C1** | 电池 RUL 的**校准后处理层**（用少量标签把预测映射到目标）里，有几个**未声明**的实现选择 |
| **C2** | 这些选择**大幅改变**报告的效应量（不是"提一句 limitation"，是做成表） |
| **C3** | 其中**拟合作用域**（calibrator 在哪个子集上拟合）与**评估总体**（在哪个子集上报数）**主导** |
| **C4** | **评估总体**的选择能**翻转符号** |

判定必须逐条给，不能整体给一个"新/不新"。

---

## 1. 检索式（可复现）

### 1.1 OpenAlex（`filter=title_and_abstract.search:`，按 relevance 排序，取前 5–8）

| 轴 | 检索式 | 命中 | 处置 |
|---|---|---:|---|
| 电池·校准 | `battery remaining useful life calibration sensitivity` | 6 | 全为无关（conformal/GP 类），弃 |
| 电池·校准 | `battery state of health calibration post-processing evaluation` | **0** | — |
| 电池·校准 | `calibration battery remaining useful life`（title.search） | 噪声 | 弃 |
| 电池·校准 | `state of health calibration lithium`（title.search） | 2 | 无关（SOC/SOH 联合估计） |
| 电池·协议 | `battery health estimation benchmark` | 316 | 取 5，见 #13–#17 |
| 电池·协议 | `cell-level condition-level battery evaluation` | 375 | 无关 |
| 电池·泄漏 | `data leakage battery prognostics` | 8 | 取 1（Picid） |
| 电池·迁移 | `battery state of health transfer learning target domain samples` | 33 | 取 2 |
| 电池·纠偏 | `battery remaining useful life bias correction` | 8 | 取 1 |
| 多宇宙 | `multiverse analysis` | 1,404 | 取 6（全为社科/方法） |
| 多宇宙 | `multiverse battery` | 41 | **无相关** |
| 多宇宙 | `multiverse analysis engineering` | 32 | 取 2（TOSEM、软件工程） |
| 规格曲线 | `specification curve` | 14,795 | 取 6（Simonsohn 等） |
| 规格曲线 | `specification curve machine learning` | 389 | 取 1（金融） |
| 规格曲线 | `specification curve engineering design` | 548 | 无关（工程曲线拟合） |
| 研究者自由度 | `researcher degrees of freedom` | 42,568 | 取 6（心理学/EEG/fMRI） |
| 分析化学·定标设计 | `calibration design analytical chemistry` | 456 | 取 2（IUPAC 指南） |
| 分析化学·线性 | `linear calibration lack of fit` | 233 | 取 5 |
| 分析化学·加权 | `weighted least squares calibration heteroscedasticity` | 62 | 取 3（**关键**） |
| 分析化学·点数 | `number of calibration standards uncertainty` | 1,649 | 取 1 |
| 分析化学·单点/多点 | `single point calibration multipoint calibration comparison` | 8 | 取 2（**关键**） |
| 分析化学·标准加入 | `standard addition calibration` | 13,118 | 取 1（2021 对比研究） |
| 分析化学·基体 | `matrix matched calibration matrix effect comparison` | 83 | 取 2 |
| 分析化学·校准集大小 | `calibration set size` | 8,460 | 取 2（Vis-NIR、RMSEP 测试集） |
| 计量学·不确定度 | `uncertainty budget` | 31,050 | 取 5（GUM 类） |
| 评估协议 | `evaluation protocol machine learning reproducibility` | 1,910 | 取 1（TIC 2026） |
| 评估协议 | `hyperparameter search budget comparison` | 66 | 无关 |
| 评估协议 | `simpson paradox benchmark evaluation` | 11 | **无相关** |
| 评估协议 | `ranking reversal subgroup evaluation` | 3 | **无相关** |
| 后处理 | `post-processing predictions evaluation sensitivity` | 1,144 | 全为水文预报，弃 |
| 后处理 | `post-hoc calibration neural network` | 279 | 取 6（方法对比，无敏感性） |
| 校准层 | `monotone calibration state of health battery` | 3 | 无关 |

### 1.2 arXiv API

| 检索式 | 结果 |
|---|---|
| `all:"specification curve"` | 7 条，无工程应用；取 PIMA、DECIDE |
| `all:"multiverse analysis"` | 7 条，全社科/方法 |
| `abs:"post-processing" AND abs:"remaining useful life"` | **0 条** |
| `ti:"battery" AND abs:"post-hoc"` | 1 条（HEMS 优化，无关） |
| `abs:"calibration" AND abs:"state of health"` | 6 条；取 #6（conformal 迁移）、#7（轴承 RUL 校准） |
| `abs:"label budget"` | 6 条，无电池 |
| `ti:"remaining useful life" AND abs:"benchmark"` | 6 条，无协议敏感性研究 |
| `ti:"Leakage and the reproducibility crisis"` | 1 条（Kapoor 2022/2023） |

### 1.3 web_search（全文级检索，覆盖 OpenAlex 摘要索引看不到的表格文字）

`battery RUL calibration post-processing sensitivity` / `specification curve multiverse analysis battery prognostics` / `expected calibration error binning choice changes conclusions` / `"labelled target cells" calibration snapshots battery` / `"offline" "strict online" protocol battery state of health sign reversal` / `macro vs micro averaging changes model ranking`。

> 这一步是本次查重的**转折点**：命中的两篇（#1 Peng、#2 Zhu）在 OpenAlex 摘要里都读不出"敏感性表"，只有全文级索引才看得到。

---

## 2. 结果表

阅读等级：**A** = 下载全文并读到具体表格/段落（可引用数字）；**B** = 只读摘要/图注；**C** = 只核到元数据（标题/年/venue/DOI），**不得引用其结论**。

### 2.1 电池 / 储能（Q1）

| # | 标题（简） | 年 | venue | 关系 | 等级 | 关键证据 / 确切差异 |
|---|---|---|---|---|---|---|
| 1 | Deployable Self-Referenced Features for Cross-Cell Battery SOH: Randomized Pairing Controls and Benchmarking（Peng, Wang, Zhang） | 2026 | Energies 19(20):4805 | **相邻★（最接近）** | A | 单列归一化 → RMSE 变动 **+107.8% / −49.6% / −0.5%**（三个评估单元）；"explicit self-referenced feature 的收益**符号翻转**，−5.3% → +4.5%，**仅取决于** per-cell 还是 source-fitted 归一化"；offline author protocol −16.8%/−19.1% → strict online reader **+4.3%/+10.4%**（符号翻转）。**差异：层是特征/预处理，不是校准映射层；无标签预算轴；两次单列操纵各自展示，未做联合规格空间分解，故无"谁主导"排序** |
| 2 | Longitudinal proxy pack benchmark generation for RUL of LEV battery packs（Zhu, Zheng, Zhang） | 2026 | Sci. Rep. | **相邻（校准预算表）** | A | **表 4**（barcode-disjoint target-cohort calibration audit）：0/1/5/20/100 snapshots → MAE 142.45 / 140.39 / 124.74 / 95.53 / 75.36；R² **−1.748 / −1.732 / −1.360 / −0.439 / +0.034**（**R² 穿零**）。作者注明"每个校准条件用**另一组** 16 个 target-cell，proxy snapshots 不是独立 target packs"——即校准集随条件变，本身就是一个未控制的实现选择。**差异：只有"预算"一个轴；无 fit scope；无评估总体对比；单数据集** |
| 3 | A Review of SOH Estimation and Prediction Methods … Task Definition, Benchmark Evaluation, and Deployment Challenges | 2026 | Computers and Artificial Intelligence（Zeus Press，venue 可信度待核） | **相邻（协议→结论）** | A | 同一 CALCE CS2、六模型：随机划分 MAE ≤ 0.0150；时序外推 0.0204–0.1392，**三个神经网络 R² 转负**；整电芯留出 0.0254–0.0378。"protocol selection changes **both the error level and the model ranking**"；"protocol selection 对结论的影响**不小于** model selection"。**差异：协议=划分方式，不是校准层的评估总体；review + 单数据集** |
| 4 | Empirical Calibration and Conditional-Reliability Diagnostics for Bearing RUL under Operating-Regime Shift | 2026 | arXiv 2607.08273 | 相邻（弱） | B | "Convenient mixed splits can hide that failure"；post-hoc 池化 regime 条件残差诊断把某单元覆盖率 0.666 → 0.941，但作者只当作"未来工作的动机"。**差异：轴承非电池；单数据集；无选择分解** |
| 5 | Conformalized Transfer Learning for Li-ion Battery SOH Forecasting | 2026 | arXiv 2603.24475 | 仅背景 | B | 校准层（CP）+ 域适配；不研究选择敏感性 |
| 6 | Noise regime determines model choice: a frequency-selective robustness benchmark for Li-ion prognostics | 2026 | J. Energy Storage 183:125315 | 仅背景 | C | 标题即"条件决定模型选择"；未读正文，不引用其结论 |
| 7 | Comparative Benchmarking of Five ML Regressors for Li-ion SOH: Temporal and Cross-Cell Robustness | 2026 | IEEE Access | 仅背景 | C | 协议鲁棒性 benchmark，非选择敏感性 |
| 8 | Picid: A Modular Evaluation Infrastructure for Reproducible PHM | 2026 | arXiv | 仅背景 | C | 可复现评测基础设施，非敏感性量化 |
| 9 | PHM-Bench: A Domain-Specific Benchmarking Framework … for PHM | 2025 | SSRN | 仅背景 | C | 同上 |
| 10 | Open access dataset, code library and benchmarking DL for SOH | 2023 | J. Energy Storage | 仅背景 | C | 基准数据/代码，非方法学 |

### 2.2 更广的机器学习（Q2）

| # | 标题（简） | 年 | venue | 关系 | 等级 | 关键证据 / 差异 |
|---|---|---|---|---|---|---|
| 11 | Leakage and the reproducibility crisis in ML-based science（Kapoor & Narayanan） | 2023 | Patterns（arXiv 2207.07048） | **相邻★（拟合作用域）** | B | 17 个领域、329 篇论文受泄漏影响，**8 类泄漏分类法**；其中"预处理/特征选择在划分前拟合"即我们说的**拟合作用域**。差异：讲"结果虚高"，不讲"效应量符号翻转"，不做选择分解 |
| 12 | The need to approximate the use-case in clinical ML（Saeb et al.） | 2017 | GigaScience 6(5):gix019 | **相邻★（评估总体）** | B | record-wise vs subject-wise CV；只有 subject-wise 才对应临床用例。差异：无校准层，无符号翻转主张 |
| 13 | Impact of the Choice of CV Techniques on ML-Based Diagnostic Applications | 2021 | Healthc. Inform. Res. | 相邻 | B | 系统比较 subject-wise / record-wise 两种策略。差异：分类任务，非 RUL |
| 14 | The Reproducibility Crisis in ML: Evaluation Protocols as Hidden Confounds | 2026 | TIC（venue 可信度待核） | **相邻（协议量化）** | B | 提出 Model Sensitivity Index；72 组实验 × 9 种评测变体；结论：CV 折数稳定，**分层策略与随机种子**中–高波动。差异：无"主导性排序"的显著性检验，无工程数据 |
| 15 | Accounting for Variance in ML Benchmarks（Bouthillier et al.） | 2021 | arXiv/MLSys | 相邻 | C | 方差分解后大量"改进"消失 |
| 16 | Are GANs Created Equal?（Lučić et al.） | 2018 | NeurIPS | 相邻 | C | 等预算下无方法胜出 |
| 17 | A Metric Learning Reality Check（Musgrave et al.） | 2020 | ECCV | 相邻 | C | 公平协议下排名反转 |
| 18 | Reporting Score Distributions Makes a Difference（Reimers & Gurevych） | 2017 | EMNLP | 相邻 | C | **聚合口径**改变结论 |
| 19 | Show Your Work（Dodge et al.） | 2019 | EMNLP | 仅背景 | C | 报告分布而非单点 |
| 20 | The Benchmark Lottery（Dehghani et al.） | 2021 | arXiv | 相邻 | C | benchmark 选择决定排名 |
| 21 | On the State of the Art of Evaluation in Neural LMs（Melis et al.） | 2018 | ICLR | 相邻 | C | 调参预算改变 SOTA |
| 22 | Are we really making much progress?（Dacrema et al.） | 2019 | RecSys | 相邻 | C | 弱基线+坏协议 → "进展"消失 |
| 23 | Evaluating model calibration in classification（Vaicenavicius et al.） | 2019 | AISTATS | 仅背景 | C | 校准的**评测**本身有偏，非选择敏感性 |

### 2.3 分析化学 / 计量学（Q3 —— Codex 标的"最危险未检索区"）

| # | 标题（简） | 年 | venue | 关系 | 等级 | 关键证据 / 差异 |
|---|---|---|---|---|---|---|
| 24 | **Weighted least-squares in calibration: What difference does it make?**（Tellinghuisen） | 2007 | The Analyst | **相邻★★（同构最强）** | B | 蒙特卡洛：忽略权重 → x₀ 精度损失**可达一个数量级**；"Incorrect weighting also **invalidates the apparent standard errors**"。**这就是"一个定标实现选择改变报告的不确定度"，且标题即"差多少"**。差异：单变量线性定标，**没有符号翻转**，没有"哪个选择主导"的分解，对象是化学浓度不是 RUL |
| 25 | Weighted LS in calibration: the problem with using "quality coefficients" to select weighting formulas | 2008 | J. Chromatogr. B | 相邻 | C | 选权重公式的**选择规则本身**不可靠 |
| 26 | Comparison of accuracy and precision between multipoint, single point calibration, and relative quantification | 2018 | Anal. Bioanal. Chem. | **相邻（设计对比表）** | C | 三种定标设计的准确度/精密度系统对比。差异：代谢组学，非"效应量翻转" |
| 27 | Linearity of calibration curves: use and misuse of the correlation coefficient | 2002 | Accred. Qual. Assur. | 相邻 | C | 用 r 判线性是误用 → **判据选择改变结论** |
| 28 | Is my calibration linear? | 1994 | The Analyst | 相邻 | C | 线性性检验的方法选择 |
| 29 | Comparison of linear and non-linear equations for univariate calibration | 2004 | J. Chromatogr. A | 相邻 | C | 定标函数形式选择 → 结果不同 |
| 30 | Evaluation of different approaches to applying the standard additions calibration method | 2021 | Anal. Bioanal. Chem. | 相邻 | C | **同一方法的多种实现**系统对比 |
| 31 | Effect of calibration set size on prediction … Vis-NIR | 2016 | Geoderma | 相邻 | C | 校准集大小 → 预测精度（化学计量学版"标签预算"） |
| 32 | Estimating uncertainty in RMSEP … size of an adequate test set | 1999 | Chemom. Intell. Lab. Syst. | 相邻 | C | 测试集大小的不确定度 → 即"评估总体大小" |
| 33 | Guidelines for Calibration in Analytical Chemistry, Part I（IUPAC） | 2016 | IUPAC | 仅背景 | C | 规范文本，非敏感性研究 |
| 34 | Uncertainty budget 类（GUM / "Verification of uncertainty budgets" 2005） | 2005– | Accred. Qual. Assur. 等 | **相邻（形式）** | C | 计量学的"不确定度预算"= 把各来源贡献做成表。**形式上是"敏感性预算"的祖宗，但对象是测量不确定度，不是"报告的效应量"** |

### 2.4 多宇宙 / 规格曲线 / 敏感性预算（Q4）

| # | 标题（简） | 年 | venue | 关系 | 等级 | 关键证据 / 差异 |
|---|---|---|---|---|---|---|
| 35 | Increasing Transparency Through a Multiverse Analysis（Steegen et al.） | 2016 | Perspect. Psychol. Sci. | 方法源头 | B | 对全部合理预处理组合做分析；"a single data set can be misleading" |
| 36 | Specification curve analysis（Simonsohn et al.） | 2020 | Nat. Hum. Behav. | 方法源头 | C | 规格曲线 + 推断 |
| 37 | **Exploring the Garden of Forking Paths in Empirical SE: A Multiverse Analysis**（Cassee & Feldt） | 2026 | ACM TOSEM 35(10) | **相邻★（工程领域已落地）** | B | 9 个决策 → **3,072 条流水线**；**只有 6 条（<0.2%）复现原结果**，多数"定性不同，有时甚至相反"。**差异：软件工程实证研究，非电池；无校准层** |
| 38 | The Analyst Matters More Than the Algorithm: Specification Sensitivity in ML Models of Financial Crises | 2026 | SSRN | 相邻 | C | 标题即"分析师比算法更重要"；无摘要可读 |
| 39 | Pinpointing Pivot Points: The DECIDE Framework for Data Analysis Decision Importances | 2026 | arXiv 2610.38797 | **相邻（主导性方法）** | B | 专门量化"**哪个分析决策最重要**"（multiverse / spec curve / vibration of effects 的推广）。**差异：通用统计框架，未用于工程，未用于校准层** |
| 40 | Quantifying the researcher degrees of freedom in fMRI preprocessing | 2025 | HAL | 相邻 | B | 数出三个软件的预处理选项数量 + 代码库实际偏好。差异：只数选项，不量化效应量 |
| 41 | Many Analysts, One Dataset（Silberzahn et al.） | 2018 | Nature（预印本 PsyArXiv） | 相邻 | B | 29 组 61 位分析者同一数据：OR **0.89–2.93**，69% 显著、31% 不显著。**"分析者自由度"的经典量化** |
| 42 | Introducing multiverse analysis to bibliometrics | 2025 | arXiv | 仅背景 | C | 领域移植案例 |
| 43 | PIMA: Post-selection inference in multiverse analysis | 2022 | arXiv | 仅背景 | C | 多宇宙的推断框架 |
| 44 | Multiverse analysis, abdication of responsibility and manufacturing of doubt | 2026 | arXiv | 仅背景（反方） | C | 对多宇宙的批评，写作时可作 counterpoint |

---

## 3. 判定

### 3.1 逐条

| 子命题 | 判定 | 依据 |
|---|---|---|
| **C1** 校准后处理层里有未声明的实现选择 | **部分相邻** | 电池领域已有人指出"未声明选择"这件事本身（#1 归一化参考、#2 校准集不独立），但**没有一篇把它定位在"校准后处理层"并作为研究对象** |
| **C2** 这些选择大幅改变报告效应量（做成表） | **已被占据（通用形式）** | #1 单列归一化 → RMSE ±108%，且做了表（Table 2）；#24 忽略权重 → 精度损失一个数量级；#37 3,072 条流水线只有 6 条复现 |
| **C3** 拟合作用域与评估总体**主导** | **空位** | 没有任何一篇（电池或方法学）对"校准层实现选择"做**主导性排序**。最接近的方法学工具是 #39 DECIDE（通用，未用于工程）；最接近的实证是 #37（软件工程，未排序"哪两个主导"） |
| **C4** 评估总体能**翻转符号** | **已被占据** | #1 明确：per-cell vs source-fitted → −5.3%/+4.5%；offline vs strict-online → −19.1%/+10.4%；#3 R² 由正转负（三个网络） |

### 3.2 总判定：**部分相邻**（比"空位"更靠近"已被占据"，但被占据的是**通用命题**，不是**校准层版本**）

- **不能**再主张"电池健康里未声明的实现选择能翻转符号"是新的——#1（Peng 2026）已经用两个具体的、各自独立的操纵演示了两次符号翻转，其中一次就是**拟合作用域**（per-cell vs source-fitted）。
- **不能**再主张"协议选择改变结论"是新的——#3 已经把"协议对结论的影响不小于模型选择"写进摘要，且给出 R² 转负。
- **可以**主张的是：**把选择放进同一个规格空间、只针对校准后处理层、给出主导性排序**。这一条没找到任何一篇做过。

### 3.3 最接近的一篇 + 确切差异

**最接近：Peng, Wang & Zhang (2026), "Deployable Self-Referenced Features for Cross-Cell Battery State-of-Health Estimation: Randomized Pairing Controls and Benchmarking", *Energies* 19(20):4805, doi:10.3390/en19204805。**

它已经做到的事（原文，已核）：
1. "Changing one column's normalization moves RMSE by up to **108%**"；
2. 同一单列操纵在三个评估单元上分别是 **+107.8% / −49.6% / −0.5%**（即"效应量随评估单元变号"）；
3. "the benefit … **reverses sign, from −5.3% to +4.5%**, depending **solely** on whether features are normalized **per cell** or **against source-fitted statistics**" ← **这就是"拟合作用域翻转符号"**；
4. offline author protocol −16.8%/−19.1% → strict online reader **+4.3%/+10.4%** ← **这就是"评估总体翻转符号"**；
5. 有 Table 2，且注明"RMSE pools test-cycle rows within each unit before averaging over five seeds; **it is not equal-cell macro**"——连**聚合口径**都点名了。

**确切差异（四条，缺一不可）**：
1. **层不同**：它操纵的是**特征/预处理层**（归一化参考、cycle 列约定），不是"用少量标签把预测映射到目标"的**校准后处理层**；全文无标签预算轴。
2. **任务不同**：SOH 回归（RMSE），不是跨工况 RUL，没有"标签预算 k"这个自变量。
3. **结构不同**：两次 **single-column manipulation** 各自展示，**没有**把选择放进一个联合规格空间，因此**没有"哪两个决定主导"的排序**，也没有主导性的统计检验。
4. **主张不同**：它把符号翻转当作"可部署性/协议"论证的一环（结论落在"deployability concerns feature computability"），**不主张**"未声明选择的效应量主导报告结论"这一方法论命题。

**次接近（校准层维度）**：Zhu et al. 2026, *Sci. Rep.*, Table 4 —— 电池 RUL 里唯一一张"校准预算 → 效应量"的表（R² 从 −1.748 走到 +0.034，**穿零**）。差异：只有预算一个轴，没有 fit scope，没有评估总体对比，单数据集，且校准集随条件更换（作者自承"proxy snapshots are not independent target packs"）。

**第三接近（协议维度）**：#3 CAI review —— "protocol selection changes both the error level and the model ranking"，R² 三个网络转负。差异：协议=数据划分，不是校准层的评估总体；且是 review + 单数据集 benchmark。

---

## 4. 未找到（负结果，同等重要）

1. **未找到**任何一篇把"校准/后处理层的实现选择"做成 multiverse / specification curve 的**电池或储能**论文。检索式 `multiverse battery`（41 条）、`specification curve machine learning`（389 条）、arXiv `all:"multiverse analysis"` 均无。
2. **未找到**电池领域把"**拟合作用域**"（per-cell vs pooled calibrator fit）作为自变量的研究。最接近的是 #1 的归一化参考，但那是特征尺度，不是 calibrator 的拟合集。
3. **未找到**任何一篇对分析选择做"**主导性排序**"（哪两个决定主导）的**工程领域**论文。方法学工具存在（#39 DECIDE），但未见工程落地。
4. **未找到**分析化学里"定标设计选择 → **符号翻转**"的研究。分析化学有的是**精度/不确定度变化**（#24 一个数量级）与**判据误用**（#27），没有"效应量变号"。
5. **未找到**"sensitivity budget"作为一个**成词术语**在工程/测量文献中的使用；对应概念分别叫 **uncertainty budget**（计量学，#34）与 **multiverse / specification curve**（社科，#35–#36）。
6. **未找到**电池 RUL 里"后处理步骤"作为方法学对象的论文：arXiv `abs:"post-processing" AND abs:"remaining useful life"` = **0 条**。
7. **未找到**"Simpson 悖论 / 亚组反转"在电池或 PHM 评测中的系统研究（`simpson paradox benchmark evaluation`、`ranking reversal subgroup evaluation` 均无相关）。

---

## 5. 对写作的直接影响（不写综述，只列约束）

1. **Related Work 必须点名 #1 与 #2**，否则审稿人（尤其 MDPI/Elsevier 电池口）会认为我们不知道 2026 年已有"符号翻转"和"校准预算表"。
2. **主张要收缩**：把"符号翻转"从**发现**降级为**已知现象在新层上的复现**；把"主导性排序"升格为**唯一的新东西**。
3. **实验设计必须能支撑 C3**：同一校准层、同一标签预算 k 下，`fit scope × evaluation population` 的联合设计（至少 2×2，建议含第三轴如校准器族），并给出**主导性**的量化（方差分解 / 规格曲线上的效应量排序），否则 C3 无法与 #1 区分。
4. **必须显式声明聚合口径**（cell-macro vs row-pooled）——#1 已经因为这一点被审稿人盯上（"it is not equal-cell macro"）。
5. **不能引用 #3 作为强证据**：venue（Zeus Press）可信度待核，只可作"同现象亦见于综述"的旁证。

---

## 6. 复核入口

| 文件 | 内容 |
|---|---|
| `.research/lit/peng_energies.txt` | #1 全文（29 页），第 2 节含 Table 2 与符号翻转原句 |
| `.research/lit/scirep_ref.txt` | #2 全文（18 页），Table 4 = 校准预算表 |
| `.research/lit/cai_review.txt` | #3 全文（15 页），§4.3–§4.4 = 三协议对比 |
