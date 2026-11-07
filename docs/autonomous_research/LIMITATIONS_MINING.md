# LIMITATIONS MINING — 局限与未来工作挖掘（第二轮文献工作）

> 维护者：文献挖掘代理（A1 名下的第二轮任务）
> 创建：2026-11-07
> 目标：**不是综述**，是从 23 篇全文里挖出「可做、且统计单位足够」的问题
> 上游：`LITERATURE_MATRIX.md`（77 条）、`RESEARCH_STATE.md`、`INNOVATIONS_AND_RESULTS.md`
> 本文件只写自己名下的文件，不修改 `docs/` 下任何历史结果，不改 `LITERATURE_MATRIX.md`。

---

## 0. 方法与口径（先读这一节，否则后面的数字会被误读）

### 0.1 语料

| 项 | 数量 | 说明 |
|---|---|---|
| 入表论文总数 | 77 | `LITERATURE_MATRIX.md` §0 统计 |
| 矩阵标 L1 全文精读 | 17 | 本轮全部覆盖 |
| 矩阵标 L2 主体精读 | 6 | 本轮全部覆盖 |
| **本轮实际取到 PDF 全文** | **23 / 23** | 本地 11 篇 + 远程 12 篇 |
| 新增可取的 arXiv 全文 | 8 篇 | L17 L18 L35 L36 L37 L43 L63 L64（另 L69 亦为 arXiv） |
| Nature Communications 全文 | 3 篇 | L12 L13 L14 |

**取全文方式（可复现）**：本地 `docs/papers/*.pdf` 11 篇 + `https://www.nature.com/articles/{doi}.pdf` 3 篇 + `https://arxiv.org/pdf/{id}` 9 篇，统一用 `pypdf 5.9.0` 抽文本，得 18k–167k 字符/篇。抽出的纯文本缓存在系统临时目录，未写入项目仓库。

### 0.2 本轮阅读等级（**与矩阵的 L1 不同，必须分开看**）

矩阵的 L1 是「通读正文 ≥85%」。本轮任务是定向挖 gap，我对 23 篇做的是**定向复读**：

| 等级代号 | 定义 | 本轮篇数 |
|---|---|---|
| **L2\*** 定向精读 | 精读 Limitations / Discussion / Conclusion / Future Work 全部段落 + 方法节数字核对（样本量、条件数、数据集名） | 23 |
| L1 全文精读 | 通读正文 ≥85% | 本轮 0 篇（未重做） |

**为什么这样标**：把定向复读冒充 L1 属于虚构阅读等级，是本项目明令禁止的。凡本文引用某篇的数字，我都回到该篇方法节核过原文（见 §0.4）。若后续要写进论文，需要先补成真正的 L1。

### 0.3 引文处理规则

1. 引文为**英文原句逐字**，仅做两处规范化：PDF 连字符换行合并（`identiﬁ-\nableness` → `identifiability`）、fi/fl 连字还原。
2. 位置给「章节名 + 页码（有页码的期刊）/ 章节名（arXiv 无稳定页码）」。arXiv 篇另给该篇抽取文本的字符偏移，便于复核。
3. **未做任何改写、拼接、补词**。跨句引用用 `…` 明确标注省略。

### 0.4 计数规则（A 部分的强度指标怎么来的）

- 一个主题只有在某篇的 **① 或 ②** 中出现**明确语句**才计入「作者提到」。
- **③（复读者判读）单独计数，不与 ①② 混算**——否则会把我的推断伪装成作者的承认。
- 同一篇可在多个主题下计数（一篇可同时暴露两个失败模式），因此主题计数之和 > 23 是正常的。

### 0.5 本轮核出的、与矩阵不一致的三处数字

| 项 | 矩阵原值 | 本轮原文核实 | 出处 |
|---|---|---|---|
| L12 电芯数 | 「RUL 部分电芯数少，二手说法 4 个」 | **12 个**（25C01–25C08 共 8 个 @25 °C，35C01–02 共 2 个 @35 °C，45C01–02 共 2 个 @45 °C） | L12 §Methods "Data generation" |
| L44 电芯数 | 「26×64 Ah + 9×31 Ah = 35」 | **25 + 8 = 33**（Table 1 "Amount of Cells"） | L44 Table 1 |
| L14 是否有局限节 | 矩阵未标 | **无** Limitations / Future Work 节，Discussion 后直接 References | L14 全文结构 |

> 这三处不改矩阵（不是我的文件），只在此登记，供 A1 下次维护时采纳。

---

## 1. 逐篇三段抽取（23 篇）

> 阅读等级：全部 L2\*（见 §0.2）。
> ① = 作者承认的局限；② = 作者提出的后续方向；③ = 我从方法与实验里看出、作者没讨论的失败模式。

### 1.1 综述与框架组

#### L01｜Rizanov, Stoynova, Mihov 2026, *Batteries* 12(7):255｜176 篇批判性综述
**① 作者承认的局限**（§8 "Critical Gaps, Limitations, and Failure Modes"，p.34–35/43）
> "The review protocol also has limitations. It was designed as a critical conceptual review with a structured research set classification rather than as a PRISMA-style systematic review or statistical meta-analysis. Consequently, the comparisons should be interpreted as evidence-maturity judgments rather than pooled quantitative rankings."

**② 作者提出的后续方向**（同节，第 1 与第 4 条 gap）
> "Future benchmark datasets should therefore report such conditions explicitly rather than treating all partial-window observations as equivalent sources of health information."
> "Future studies should report interval coverage, calibration under domain shift, selective prediction, abstention policies, and decision-conditioned warning risk."

**③ 复读者判读（作者未讨论）**
- 全文分类 176 篇，但**六条 "strategic gaps" 没有一条被量化**。作者说"benchmark 过度代表满循环实验室数据"，却没有给出「176 篇里有多少篇做了跨工况留出」这个分母。**这是叙事式 gap，不是可证伪的 gap。**
- 作者自己在 §8 列的十个 failure mode（observability / domain-shift / cross-fidelity over-claiming / uncertainty miscalibration / data leakage / proxy-label failure / sensor failure / decision integration / computational infeasibility / lifecycle drift）是**一张现成的编码表**，但作者没有用它去编码任何一篇文献。→ 见 §2 主题 T2，这是本文最看好的方向。

---

#### L02｜Ahwiadi & Wang 2025, *Batteries* 11(1):31｜RUL 方法三分法综述
**① 作者承认的局限**（§5 Conclusions，p.22–23/29）
> "These methods are highly interpretable but often involve significant computational costs and sensitivity to parameter tuning, particularly under dynamic or high-intensity operating conditions."
> "While these methods demonstrate strong adaptability and flexibility, they rely heavily on large, high-quality datasets and lack the physical interpretability inherent in model-based methods."

**② 作者提出的后续方向**（同节）
> "Future research should focus on developing simpler, faster, more transparent, and robust techniques to enhance battery health monitoring and management applications."

**③ 复读者判读（作者未讨论）**
- 全文没有任何**定量横向比较表**：model-based / data-driven / hybrid 三族的"优劣"全部是定性断言。因此这篇综述**无法回答"哪一族在什么条件下赢"**，也就不可能被证伪。
- 唯一的数据演示用 NASA（项目自有结论：4 电芯，见 `docs/nasa_results.md`）。用 n=4 的数据画示例图，会让读者误以为该领域的方法比较是在 4 个电芯上做的。

---

#### L03｜Beatty, Strickland, Ferreira 2024, *Energies* 17(17):4309｜IC/DV 曲线生成方法
**① 作者承认的局限**（Conclusion 前段，p.26–27/31）
> "The calculated SOH varies between 63.7% and 79.8% depending on the method of analysis and SOH metric chosen. This is quite widespread for the same dataset. This variation means that it is difficult to draw good conclusions at this time. This is due to insufficient rigor in measurement consistency, especially around the relationship between IC curve features and SOH results."

**② 作者提出的后续方向**（"Future work" 段，p.29/31）
> "Future work will focus on implementing this methodology for generating IC curves with battery datasets currently being recorded at Loughborough University. This will provide an opportunity to explore the potential of using these IC curves to classify the state of health of batteries, specifically aiming at their suitability for second-life repurposing."

**③ 复读者判读（作者未讨论）**
- 实验是 3 数据集 × 5 方法 × 3 指标。作者报告了**极差**（63.7–79.8%，16.1 个百分点），但**没有做方差分解**——没有 ANOVA、没有 ICC、没有"方法效应 vs 电芯间效应"的对比。
- 后果：读者无法判断 16.1 个百分点里有多少是"方法选择"、多少是"电芯个体差异"。**这正是本项目 P3（推断单位必须匹配泛化单位）在别人论文里的同构版本。**
- 另一个隐藏问题：Table 6 只报了**第 1000 循环**一个时间点。若方法间排序随循环数变化，单点比较会给出错误结论。

---

### 1.2 非循环测量通道组（EIS / 弛豫）

#### L12｜Zhang, Tang, Zhang, Wang, Stimming, Lee 2020, *Nat Commun* 11:1706｜整谱 EIS + GPR
**① 作者承认的局限**（Discussion 末段，p.4/9）
> "Predictions from our model can be attributed back to the impedance spectra, yielding the observation that the low-frequency region of the EIS spectrum is the most predictive."
> "…without the knowledge of the cycling temperature as long as the future operating temperature of a battery is close to its previous operating temperature."
> "We anticipate that our observation about the value of EIS and GPR can be extended to consider more challenging and realistic settings, such as variations in cycling temperature over time or variations in charge/discharge rate. However, a significantly larger training set is required to cover the different eventualities. We defer consideration of those aspects to future work."

**② 作者提出的后续方向**（同段）
> "An interesting future direction, stemming from this observation, is that one might not need to perform a full sweep over a broad range of frequencies to obtain signals relevant to degradation."

**③ 复读者判读（作者未讨论）**
- **温度轴上的 n=2。** §Methods 明确：25 °C 有 8 个电芯（25C01–25C08），35 °C 只有 2 个（35C01、35C02），45 °C 只有 2 个。Fig. 3 的 35 °C / 45 °C 外推图，每个温度点背后是 2 个电芯。
- 也就是说：**"温度外推可行"这个结论，是在温度轴上每档 2 个独立单位的证据上得出的**。这与本项目 n=11 死于功效不足是同一类病，只是更隐蔽（作者把它写成"without the knowledge of the cycling temperature"这种强断言）。
- 作者说"需要大得多的训练集"，但没有给出功效计算——需要多大，未知。

---

#### L13｜Jones, Stimming, Lee 2022, *Nat Commun* 13:4806｜单次 EIS + 概率预测 + 通道消融表
**① 作者承认的局限**（Discussion 末段，紧接 Methods 之前）
> "Furthermore, although in this work we only consider forecasting starting from an initially discharged state, we hypothesise that it should be possible in future work to forecast discharge capacity starting from any state of charge based on the EIS measurement, since EIS spectrum implicitly tracks state of charge."

**② 作者提出的后续方向**（同段）
> "Our work can additionally be extended to consider more complicated dynamic usage protocols, such as WLTC."
> "For example, predicting the effect of a proposed charging protocol on next cycle discharge capacity as well as long term degradation is important for optimising rapid charging applications."

**③ 复读者判读（作者未讨论）**
- 88 个电芯，但**温度是一个常数而不是一个因子**：§Methods "Cells are cycled in a temperature-controlled lab room at 23 ± 2 °C"。所以那张著名的通道消融表（Protocol only 15.4%、EIS only 20.7%、EIS+Protocol 8.2%…）**全部是在单一温度下得到的**，不能支撑任何跨温度陈述。
- 更关键：每个电芯被分配**随机的充放电电流序列**，即"工况"与"电芯"一一对应、不可分离。于是"工况"作为统计单位在数据里根本不存在——只有电芯。作者的留两电芯交叉验证（重复 N/2 次）是在**电芯**这一层重采样，不是工况层。
- 因此这张表能回答"换通道有没有用"，**不能回答"换通道在多少种工况下有用"**。本项目想接着做的那一步（工况层），这篇的数据结构不允许。

---

#### L14｜Zhu et al. 2022, *Nat Commun* 13:2261｜充电后弛豫电压 → 容量
**① 作者承认的局限**
> **无 Limitations 节。** Discussion 之后直接进 References。最接近的自我限制只有一句（§Results，p.5/9）：
> "All R2 values are greater than 0.999, indicating the credible fitting accuracy."

**② 作者提出的后续方向**
> **无。** 全文无 "future work" / "outlook" 段。

**③ 复读者判读（作者未讨论）**
- 这篇是**"拟合好 ≠ 参数可辨识"最干净的反例**：R² > 0.999 对每一条谱都成立，紧接着下一句就是 "The dominating degradation factors are different under different working conditions."——即拟合精度对"哪个元件在老化"完全没有约束力。
- 另一处：Min / Mean 两个统计量随容量**先升后降**（"The Min and Mean first increase and then decrease versus the capacity reduction"）。作者当作现象描述，没意识到这已经否证了"弛豫统计量是 SOH 的单调代理"这一默认前提。
- 作者用了 130 电芯，这是本项目所缺的样本量；但作者把 130 电芯全部投进"迁移学习微调"，零样本（ZSL）那一列误差明显更大（Table 3）。**"无历史即可估容量"的卖点，在零样本口径下并不成立。**

---

#### L17｜Khan, Thatipamula, Onori 2024, *arXiv* 2410.15271｜DRT + LSTM 做 SOH
**① 作者承认的局限**
> **无 Limitations 节。** 但 §4 开头暴露了一个事后选择过程（字符偏移 15 557）：
> "To extend battery life, it is generally recommended to avoid fully discharging (SOC → 0%) and fully charging (SOC → 100%) a battery. Hence, from the remaining DRT curves at 25%, 50% and 75% SOC, we select DRT curves at 25% SOC for the SOH estimation model."
> "Furthermore, initial studies conducted using DRT curves obtained at various SOCs show that DRT curves at 25% SOC gave the best overall performance for SOH estimation."

**② 作者提出的后续方向**（§5 Conclusion 末句）
> "In the future, we plan to extend this work to analyze the impact of individual degradation modes from the DRT curve on SOH, and using it to predict failure of lithium-ion batteries."

**③ 复读者判读（作者未讨论）**
- **"25% SOC 最好"是在 3 个候选里挑的，且挑选依据就是最终指标本身。** 三个候选（25/50/75%）意味着选择偏差的量级约为 1/3 的随机优势，作者没有做任何校正，也没报告另两个 SOC 的完整结果。
- 22 个电芯，但报告了 **10 个测试集**。Table 2 显示测试集成员大量重叠（S23 出现在 set 1/7/9；S9 出现在 set 3/6/7/10）。**10 个测试集不是 10 次独立验证**，把它们并列会系统性低估方差。
- 这是本项目 P3 的又一个同构案例：名义单位 10，有效独立单位 22 个电芯（且同一电芯被反复使用）。

---

### 1.3 可辨识性与参数估计组

#### L35｜Soleymani Aghdam, Alavi, Saif 2021, *arXiv* 2103.00226｜2-CPE 分数阶 ECM 结构可辨识
**① 作者承认的局限**（§V，字符偏移 17 535）
> "The proposed method confirms that the two-CPE FO-ECM in Fig. 1 is globally identifiable for a wide range of parameter values that is common in battery applications."

**② 作者提出的后续方向**（同节，紧接上句）
> "Structural identifiability analysis for higher-order FO-ECMs and/or by using other approximations of fractional derivatives, as well as practical identifiability analysis, i.e., selection of the excitation signal, the effect of measurement noise, etc., are suggested for future research."

**③ 复读者判读（作者未讨论）**
- 结论的适用范围是**一个人为划定的参数盒子**：R∞∈(0.01,0.2)、R₁∈(0.05,5)、C₁∈(1,20)、C₂∈(100,500)、α₁,α₂∈(0.1,0.9)。盒子外的一一映射性未验证，而老化的电芯恰恰会跑出盒子。
- 无噪声、无激励约束。作者自己把"实践可辨识性"列为 future work——**也就是说，这篇论文回答的问题，和"这些参数能不能当 RUL 特征"之间，还隔着一整层**。
- 该文的正确用法不是"ECM 参数可辨识"，而是"**结构可辨识是必要不充分条件**"。本项目的 B 问题（τ 被当采样点索引）正好落在这条缝里。

---

#### L36｜Zhao & Howey 2016, *arXiv* 1604.01293｜2-RC 参数全局敏感性（Morris）
**① 作者承认的局限**（§V Conclusion，字符偏移 15 545）
> "Sensitivity analysis demonstrates that the output of the second order RC model is most sensitive to Rs and τ2, while the other three parameters C1, C2 and τ1 can be set to constants."

**② 作者提出的后续方向**（同节，紧接上句）
> "Future work includes taking temperature effects into account and extending the analysis into more complex battery models."

**③ 复读者判读（作者未讨论）**
- **单电芯、单温度（20 °C）、单参数点。** Morris 法 N=1024 是在一个名义参数点上撒点，得到的敏感性排序本身**没有误差棒**。作者用 UDC 做了 3 个 case 的验证（RMSE 5.67→7.12→15.35 mV），但那仍是同一颗电芯、同一温度。
- 关键推论（作者没写）：如果 τ₁ 对端电压几乎无影响（本文结论），那么**任何用端电压 RMSE 来"验证"τ₁ 估计的研究，其验证指标对被测对象是不敏感的**。这直接命中 L43（EIS2MOD）用 <1.5% 端电压 RMSE 验证 DRT 参数的做法。
- 温度未纳入，而本项目 Bayreuth 结果恰恰是 a1、c 存活、τ 判负——**τ 的不可辨识性与跨温度不稳定性可能是同一件事**，本文提供了检验它的工具但没做。

---

#### L37｜Balasingam & Pattipati 2021, *arXiv* 2101.05349｜低 SNR 下 LS 有偏、TLS 无偏
**① 作者承认的局限**（§V，字符偏移 55 826）
> "Unlike the Monte-Carlo experiments presented so far, the true parameter R0 is not available with the real data being experimented in this section."
> "…this scenario is out of the scope of this present paper and left for a future discussion."

**② 作者提出的后续方向**（§VI "Applications and Future Work"）
> "A good example of such a scenario is found in Li-ion batteries [37]–[40], shown in Figure 11(b) where the battery electromotive force (EMF) represents the unknown system. Real-time battery impedance identification is an active research topic. The objective for the scenario in Figure 11(b) is to estimate the series resistance of the battery, R0."

**③ 复读者判读（作者未讨论）**
- 全文的蒙特卡洛设定是：**恒定电流 i(k)=2 A、恒定电阻 R=0.25 Ω、白高斯噪声 σ_v=1 mV、m=100/500**。也就是说，偏差结论是 SNR 的函数，而 SNR 在真实弛豫/脉冲测量里是**随 SOC、温度、老化同时变化的**（噪声不是同方差的）。
- 作者自己把电池场景列为 future work——**这篇论文没有做过任何电池实验**。任何引用它来论证"电池内阻估计有偏"的写法，都属于把理论结论外推到未验证域。
- 一个可做的检验（作者没提）：把 σ_v 设成随 SOC 变化的函数，看 LS 的偏差曲线是否仍单调。若否，则"低 SNR 用 TLS"这条工程建议在电池上不成立。

---

#### L43｜Iurilli, Brivio, Carrillo, Wood 2022, *arXiv* 2203.08515（IEEE TIA）｜EIS2MOD：DRT → 物理 ECM
**① 作者承认的局限**（§IV，字符偏移 21 017）
> "However, in the case of diffusive processes, i.e. at high time constant, the use of a simple RC branch leads to high residuals between the measured and the estimated impedance spectrum. One possible solution to overcome this limitation is to introduce a Warburg element in the model."

**② 作者提出的后续方向**（结论末段，字符偏移 45 619 起）
> "Future works will concentrate on two main directions. On one side, a first objective will be to extend the methodology for SoH estimation by exploiting DRT analysis. … These variations will be used to adjust the model parameters over lifetime and to allow not only for an accurate SoC estimation, but also SoH estimation. On the other side, a second objective will be to port the code in a dedicated BMS hardware/software solution…"

**③ 复读者判读（作者未讨论）**
- **验证指标与被验证对象不匹配。** 作者用端电压 RMSE（<1.5%，−10–35 °C）来证明 DRT 派生的 ECM 是"对的"；但 L36 已经证明 τ₁、C₁、C₂ 对端电压几乎无影响。**用一个对参数不敏感的指标去验证参数，等于没验证。**
- 峰位=τ、峰面积=R 的映射在峰重叠时需要人工裁定，而论文只给了一个电芯规格（55 Ah NMC pouch）。**"6 峰 ↔ 6 过程"的可复现性没有跨电芯证据。**
- 温度范围 −10–35 °C，但每个温度点的电芯数未报告。跨温度的参数轨迹（这正是本项目关心的）在这篇里不可提取。

---

### 1.4 退化机理与指标定义组

#### L44｜Spitthoff, Vie, Wahl, Wind, Burheim 2023, *J Electroanal Chem* 944:117627｜ICA + 33 电芯跨温度/夹紧力
**① 作者承认的局限**（§5 Conclusion，p.13/14）
> "It appears, that no single FOI is a good direct indicator of SOH across all ambient temperatures. Validation data is needed across a wider temperature range when FOI are to be used for SOH estimation."

**② 作者提出的后续方向**（同节末段）
> "A possible option for applying this process is identifying cells with unknown cycling histories suitable for second-life applications."

**③ 复读者判读（作者未讨论）**
- **头号结论的支撑是 n=1。** Table 2（"Amount of cells cycled under the same condition"）给出：64 Ah 电芯在 15 °C 只有 **1 个**，35 °C 2 个，45 °C 2 个；31 Ah 电芯 5 °C 2 个、25 °C 4 个、45 °C 3 个。而全文最响的那句是 "the rate of capacity loss appeared to be very similar for cells cycled at an ambient temperature of 15 °C and 25 °C … the degradation modes and mechanisms appear to be very different."——**15 °C 那一侧是 1 个电芯。**
- 夹紧力效应（clamped vs unclamped，900 vs 3000 FEC）比温度效应大得多，但夹紧力与电芯批次、C-rate 部分混淆，作者只用一句 "it is two different cells" 带过。
- 这是本文最有用的一篇：它**用实验证明了"同一衰减率、不同机理"**，即本项目"参数–SOH 相关系数符号可翻转"的物理根据。但它自己也只有 3–6 个温度档、每档 1–4 个电芯——**它能证明现象存在，不能给出符号翻转的频率。**

---

#### L28｜Su, Tao, Chen, Zou, Zhang 2026, *Cell Rep Phys Sci* 7:103083｜IC 特征 PC/TC/DE 三准则
**① 作者承认的局限**（Discussion 末段，p.11/12）
> "Nevertheless, several limitations remain within this preliminary and demonstrative work since the current analysis is conducted under isothermal conditions; thus, the generalizability of the selected features under dynamic operating profiles or varying temperatures requires further validation. In addition, while the study focuses on handcrafted IC curve features, emerging approaches based on end-to-end deep learning may capture additional patterns beyond manually defined features."

**② 作者提出的后续方向**（同段，紧接上句）
> "Future research should therefore extend this framework to non-isothermal and real-world cycling conditions, investigate the integration of physically interpretable features with advanced machine learning models, and further explore data efficiency under broader transfer learning scenarios."

**③ 复读者判读（作者未讨论）**
- **"可迁移"是微调，不是零样本。** 实验是 1C→0.5C、25→35 °C 的**微调式**迁移，目标域标签被用到了。这与"特征本身可迁移"是两个命题，作者在标题与摘要里没有区分。
- DE（data efficiency）这一维的分数是**人工指定**的（第一个峰 5 分、第二个峰 3 分、跨峰面积 1 分），不是测量出来的。用一个手赋分的维度去排"三准则"，等于把一个主观量塞进了客观排名。
- 精度榜首 P12_Ar（MAPE 0.22%）需要"extended measurement"——**精度榜与采集成本混在一起报**，读者容易把 0.22% 当成可部署精度。
- 24 个电池、2 个化学体系。对"跨化学体系"这一维，n=2。

---

### 1.5 跨域 / 统计单位组

#### L56｜Zhang, Li, Zheng, Lu, Gui, Xu, Bian 2025, *Nat Mach Intell* 7:270–277｜BatLiNet 电芯间差值学习
**① 作者承认的局限**（Discussion，p.274）
> "While this study demonstrates the data-driven feasibility of inter-cell learning across various conditions, a deeper physical understanding and modelling remain essential."

**② 作者提出的后续方向**（同段，紧接上句）
> "Future research should prioritize a comprehensive approach to understanding and modelling diverse ageing factors to advance battery research, development and application."

**③ 复读者判读（作者未讨论）**
- **方法依赖一个推理期的参考集。** §Results："We find that using a batch of 64 reference cells is effective in maintaining a reasonable inference speed yet delivering robust predictions." 也就是说，要给目标电芯预测寿命，必须同时拿到 64 个**带标签**的参照电芯。这是一个部署假设，作者只讨论了它对推理速度的影响，**没有讨论它对数据可得性的影响**。
- 增益来自**标签侧**（预测两电芯寿命差）而非输入侧。这意味着"BatLiNet 更能泛化"与"我们换了个标签"难以分离——缺一个同标签的对照。
- 数据集是 MATR / HUST / CALCE / SNL / UL-PUR / RWTH / HNEI 七源合并，但 MIX-20 / MIX-100 的划分是按循环数，不是按工况留出。**"跨工况"在这里是"跨数据集混合"，不是"留出未见工况"。**

---

#### L57｜Tan, Hong, Tang, Lu, Ma, Zheng, Li, Huang, Zhang 2025, *KDD '25*｜BatteryLife 基准（16 数据集 / 990 电芯 / 421 协议）
**① 作者承认的局限**（§4.3 末 + §5，p.5795–5796）
> "…suggests that extracting relevant information from diverse lab-test data (with hundreds of aging conditions) to other battery types remains challenging. The cross-domain evaluation results indicate that BatteryLife still has substantial room for improvements in cross-domain transferability."

**② 作者提出的后续方向**（§5 Conclusion and Future Work）
> "In future studies, we also focus on the research areas discovered in this work and plan to incorporate more datasets into BatteryLife."

**③ 复读者判读（作者未讨论）**
- **基准的规模与迁移结果互相矛盾，但被放在同一篇里不做调和。** 990 电芯的卖点与 Table 6 的跨域结果（Frozen 迁移 MAPE 3.153 vs 基线 0.515，ACC 0.046 vs 0.297）并存。也就是说：**数据量涨了 2.5 倍，零样本迁移仍然崩溃。**
- 论文把 16 个数据集合并成一个"数据集"，但**没有做域级划分**（domain-level split）。聚合指标会把"在某些域上很好、在某些域上完全失败"平均掉。这是本项目 P3 的宏观版本。
- 421 个协议、9 个温度、59 个化学体系——**这是目前唯一一个能在"工况/协议"这一层凑够 ≥30 独立单位的公开资源**（见 §3 主题 T1）。

---

#### L64｜Zhou & Howey 2022, *arXiv* 2211.05697｜层级贝叶斯 + VPC=74.5%
**① 作者承认的局限**（§4 Results and Discussion 末，字符偏移 33 332）
> "In our dataset, eight clusters is a reasonable number to balance within-group usage variability versus sample size. However, this was an empirical choice based mainly on trial and error."

**② 作者提出的后续方向**（同段）
> "There are two directions for future work. First, the influence of cluster number and cluster size needs to be further investigated, as these two parameters are known to be important in many other fields when using hierarchical models (Gelman and Hill (2006)). Second, nonlinear functions, or even non-parametric models such as Gaussian processes, could be implemented hierarchically, and may give better performance compared to linear regression models."

**③ 复读者判读（作者未讨论）**
- **VPC=74.5% 这个数依赖一个事后选的 K=8。** 作者自己承认 K 是 trial and error。那么"74.5% 的寿命方差来自工况组"这个被本项目当作 P3 判据引用的数字，**其不确定性完全未报告**——没有 K=4/6/8/10/12 的 VPC 曲线。
- 169 电芯 / 61 工况来自 Severson(124) + Attia(45)，两者**实验批次不同**。把两个批次合成一个层级模型，"工况层方差"里混进了"批次层方差"。
- 这是本项目最该复用的一篇：**它给出了把"工况"当统计单位的正确工具（部分池化 + VPC），但没有做敏感性分析。** 补上 K 的敏感性曲线，本身就是一个单位数 ≥30（61 工况）的可做问题。

---

#### L55｜You, Zhu, Wang, Jiang, Wei, Dai 2023, *eTransportation* 18:100270｜膝点直接/间接预测
**① 作者承认的局限**（§4 Conclusion 前的对比段）
> "Furthermore, the application of the direct prediction method requires a large number of actual aging data, feature extraction and model training, and a large number of experimental verification before it can be applied in practice."

**② 作者提出的后续方向**（§4 Conclusion 末段）
> "Looking forward to the future, the proposed knee-point prediction methods will promote the improvement of the knee-point prediction accuracy in multiple scenarios, so as to find an ideal battery replacement opportunity, which is of great significance to the prognostic and health management (PHM) of LIBs."

**③ 复读者判读（作者未讨论）**
- 124 个 A123 电芯 / 72 种快充协议，**但全是 LFP、全在 30 °C**。所以"multiple scenarios"里的"scenario"实际只指"充电协议"，不含温度与化学体系。
- 直接法报 RMSE 84.6 / MAE 64 循环，**没有按协议分解的误差分布**。72 个协议里若误差集中在少数几个协议上，聚合指标会掩盖它——而这恰恰是"跨工况泛化"要问的问题。
- 膝点定义用最大距离法，但**没有报告换定义后的结果变化**。L03 已经证明同一数据集换方法 SOH 差 16 个百分点；膝点对定义只会更敏感。

---

### 1.6 概率预测 / 不确定性组

#### L65｜Ly, Yang, Dixit, Nguyen 2025, *arXiv* 2512.23725（AAAI-26）｜RUL-QMoE 非交叉分位数
**① 作者承认的局限**（§1 Introduction，对既有工作的批评，字符偏移 4 862）
> "2. Uncertainty propagation: Existing methods provide point estimates of the battery RUL without confidence intervals, which are inaccurate since the factors to RUL are uncertain during the operational life of the targeted Li-ion battery."

**② 作者提出的后续方向**（§7 Conclusion and Future Work）
> "Pilot deployments in collaboration with automotive and energy partners will be the critical next step toward commercialization."

**③ 复读者判读（作者未讨论）**
- **门控变量是化学体系，而化学体系是数据集级标签。** "specialized expert networks aligned with distinct cathode materials" + 7 个公开数据集 = 模型可以靠**识别数据集**而非识别物理来路由。这在评测里表现为"泛化好"，实际是查表。
- 输入 1010 维 = 100 循环 × 10 个电压-容量点。**输入维度里已经含了 100 个循环的历史**，所以"early-cycle"这个卖点的边界需要看具体设置，摘要里的"early-cycle data"没有给循环数。
- 结论段没有一句讨论自己的局限——**全文 "limitation" 一词只用于批评别人。**

---

#### L66｜Ke, Jiang, Zhu, Peng, Tan 2024, *IEEE TTE* 10(2):2873｜BNN + STD scaling 校准
**① 作者承认的局限**（§III-D "Uncertainty Calibration"）
> "Due to the inherent limitations of approximation inference method, uncertainty quantified by BNNs sometimes cannot be captured correctly. For instance, the true value might be out of the 95% confidence interval predicted by the BNN. Inaccurate uncertainty cannot provide reliable suggestions for battery management."

**② 作者提出的后续方向**（§V Conclusion 末段）
> "For future research, exploring the underlying mechanisms that contribute to the knee point phenomenon can be considered. In addition, the challenge of jointly predicting multiple health indicators, not limited to knee point and knee capacity, for fast-charging Li-ion batteries holds significant potential."

**③ 复读者判读（作者未讨论）**
- **校准集与测试集同分布。** "A calibration dataset is needed for uncertainty calibration"——但这个校准集来自同样 3 个数据集。因此报告的 ECE 改善（"about 0.04%–84%"）**只在无偏移条件下成立**，而 L01 明确指出真正缺的是 "calibration under domain shift"。
- ECE 改善写成 **0.04%–84%** 这样一个跨三个数量级的区间，等于没报。没有逐数据集的值，读者无法判断最差的那一档是不是 0.04%。
- 只用前 30 循环，3 个公开快充数据集。**数据集数 = 3，是这一族工作共同的天花板。**

---

#### L69｜Jia et al. 2026, *arXiv* 2601.15942｜层级贝叶斯模型基预后
**① 作者承认的局限**（§4.2.2，字符偏移 41 563）
> "Despite this improvement, a 2% model error persists, which can be attributed to measurement noise and the inherent limitations of the model."

**② 作者提出的后续方向**（§5 Conclusion 末段）
> "Future work can extend this framework to multi-level systems, such as an aircraft engine, which comprises subsystems (e.g., turbofan, combustion chamber, lubrication system) and individual components (e.g., fan blades, fuel nozzles, bearings)."

**③ 复读者判读（作者未讨论）**
- **"框架"的电池验证只有 1 个实例。** 两个案例是裂纹扩展 + 一个电池，所以电池侧的 n=1。一个 n=1 的案例不能支撑"framework"这个词。
- 结论里埋了一个负结果："integrating correlation between model parameters as additional hyperparameters has the potential to refine model predictions, but not always." ——**"not always" 没有任何量化**，也没有说在哪个案例上失效。这是把负结果降格为脚注的典型写法。

---

### 1.7 状态空间 / 序列骨架组

#### L62｜Feng, Hu, Li, Zhang 2024, *arXiv* 2402.00068｜GPT4Battery：物理引导测试时适配
**① 作者承认的局限**（§5.2，字符偏移 37 403）
> "However, we should note the limitation that involving an LLM does increase the inference time even with PPA, which is a trade-off between accuracy and computation efficiency."

**② 作者提出的后续方向**（§6 Conclusion）
> "By introducing GPT4Battery, we hope this work will inspire the research community to fully leverage advanced AI techniques, such as Test-Time Adaptation (TTA) and large language models (LLMs), for more AI4Science problems, thereby saving enormous t…"

**③ 复读者判读（作者未讨论）**
- **"物理引导"的物理没有进到参数层。** 自监督损失是 1-RC ECM 的 ODE 残差，约束的是**电压**，不是 R/C 参数。所以这个方法在物理上等价于"用一个物理模型的输出当正则项"，与"估计出可解释参数"是两回事。论文标题里的 physics-guided 会让人误读成后者。
- 在线实验只有 **2 个组合**（4 个品牌里 2 个当源、2 个当目标 → C(4,2)=2 种组合）。Table 6 的 "Combination 1/2" 就是全部。
- 单样本 TTT 意味着**每个测试样本都要更新一次**，而推理时间 103–105 ms（Table 6）。在 BMS 的采样率下这个量级需要单独论证，作者只用"trade-off"一句带过。

---

#### L63｜Patel, Ramezankhani, Deodhar, Birru 2025, *arXiv* 2507.18320｜TIDSIT 连续时间嵌入
**① 作者承认的局限**（§3.1.1 Dataset Description）
> "We evaluate the proposed TIDSIT architecture using the battery degradation dataset provided by the NASA Ames Prognostics Center of Excellence (PCoE)."

**② 作者提出的后续方向**（§8 Conclusion 末段）
> "Overall, TIDSIT establishes a strong foundation for reliable battery health monitoring and paves the way for future research into scalable, interpretable, and real-time prognostics using deep sequence models."

**③ 复读者判读（作者未讨论）**
- **单数据集，且是 NASA PCoE。** 按本项目已核实结论（`docs/nasa_results.md`），NASA 只有 **4 个电芯**。论文报的 SoH 误差 <0.58%，分母是 4 个电芯的时间序列窗口。
- 因此：**窗口级划分 = 泄漏。** 同一电芯的不同循环窗口被分到训练/测试两侧，模型学到的是"这颗电芯的曲线"，不是"这类电芯的规律"。这类泄漏在时间序列论文里极常见，本文没有讨论划分方式。
- "generalizable" 一词在摘要里出现，但泛化对象只有 1 个数据集。这是 23 篇里**单位数最少**的一篇（有效 n=4）。

---

## 2. A + B + C 合并：主题卡

> 格式按要求：主题 / 提到它的论文编号（数量）/ 原文摘录 / 可用统计单位与估计数量 / 是否已被占据 / 可做性。
> **单位判定规则**：只认「有效独立单位」，不认名义观测数。名义 45 个配置但只有 15 个独立单元，记 15。

---

### T1｜跨工况泛化：同一特征/参数在不同温度、协议、化学体系下方向不稳

**提到它的论文（8 篇）**：L01, L12, L13, L14, L28, L36, L44, L57

**原文摘录**
> "It appears, that no single FOI is a good direct indicator of SOH across all ambient temperatures. Validation data is needed across a wider temperature range when FOI are to be used for SOH estimation." — L44 §5
> "The dominating degradation factors are different under different working conditions." — L14 §Results

**可用统计单位与数量**
| 单位 | 数量 | 出处 |
|---|---|---|
| 循环工况（MIT / Severson+Attia） | **61** | L64 §3 "169 cells from 61 different cycling conditions" |
| 快充协议（A123，L55 使用） | **72** | L55 §2（matrix 已记；L55 原文用 Severson 124 电芯数据集） |
| 协议（BatteryLife） | **421** | L57 §1 "421 charge/discharge protocols" |
| 工况（UConn，本项目自有） | 11 | `RESEARCH_STATE.md` |
| 工况（Bayreuth，本项目自有） | 23 | `RESEARCH_STATE.md` |

→ **有效独立单位可达 61 / 72 / 421，满足 ≥30。但注意：UConn 11 与 Bayreuth 23 单独都不满足——这正是本项目死亡的直接原因。**

**是否已被占据**：**部分占据，密度高。**
- L64 用 VPC 量化了工况层方差（74.5%），但**不做符号统计**，且 K=8 是事后选。
- L44 用 ICA 证明了"同衰减率不同机理"，但**每温度 1–4 个电芯**，无法给频率。
- L57 报了跨域迁移失败，但**不做特征级符号分析**。
- **未被占据的空隙**：把"特征–SOH 相关系数的符号"当统计量，在 ≥30 个工况上做二项检验 + 效应量分布。检索未见（本矩阵 77 篇内）。

**可做性：5/5**
- 数据全公开（Severson 2019、Attia 2020、BatteryLife）。
- 本项目已有 Bayreuth 的符号一致性管线，改数据集即可复用。
- **代价**：MIT / A123 / BatteryLife 都**没有 EIS / 弛豫通道**，只有循环曲线。若坚持非循环通道，单位数掉回 11/23 → 不满足。**这是本方向唯一的硬约束，见 §4.1。**

---

### T2｜统计单位与推断可比性：领域内没有人编码过"大家用什么单位做推断"

**提到它的论文（3 篇）**：L01, L03, L64

**原文摘录**
> "…rather than as a PRISMA-style systematic review or statistical meta-analysis. Consequently, the comparisons should be interpreted as evidence-maturity judgments rather than pooled quantitative rankings." — L01 §8
> "This variation means that it is difficult to draw good conclusions at this time. This is due to insufficient rigor in measurement consistency…" — L03 Conclusion

**可用统计单位与数量**
| 单位 | 数量 | 出处 |
|---|---|---|
| 论文 | **77**（矩阵现有）；OpenAlex 扩到 150+ 可行 | `LITERATURE_MATRIX.md` §0 |
| 论文 × 统计口径（电芯级/工况级/未报告） | 77 × 3 = 231 | 编码表设计 |

→ **有效独立单位 = 77（论文），满足 ≥30。** 这是所有候选方向里**唯一不依赖任何数据集**的方向。

**是否已被占据**：**未被占据。**
- L01 是 176 篇的批判性综述，但**明确声明自己不是 statistical meta-analysis**，且**没有对任何一篇做统计口径编码**。它列出了十个 failure mode（含 "proxy-label failure"、"data or validation leakage"），却没用这张表编码任何文献。
- 换言之：**L01 给了编码表，没做编码。** 这就是空位。

**可做性：5/5**
- 零算力、零数据下载，只需读摘要/方法节 + 一张编码表。
- 与本项目 P3（ICC=0.414、design effect=2.99、等效 n=21.4）直接接续：把"我们自己的单位错误"升级成"领域的单位错误有多普遍"。
- 风险：审稿人可能说"这是 meta-research 不是 battery research"。需要在引言里把落点写成"给出该领域功效审计的基线"，而不是"我们数了数"。

---

### T3｜标签/指标定义依赖（SOH 定义、膝点定义、FOI 定义）

**提到它的论文（3 篇）**：L01, L03, L44

**原文摘录**
> "The calculated SOH varies between 63.7% and 79.8% depending on the method of analysis and SOH metric chosen." — L03
> "no single FOI is a good direct indicator of SOH across all ambient temperatures" — L44

**可用统计单位与数量**
| 单位 | 名义 | **有效独立** |
|---|---|---|
| 数据集 × 方法（L03 口径：3×5） | 15 | 15 |
| × 指标（3） | 45 | 仍是 15（指标是同一单元的重复测量） |
| 若扩到 BatteryLife 16 数据集 × 5 方法 | 80 | 80（**但需要 16 个数据集都有可比的 IC 曲线，可行性未验证**） |

→ **有效独立单位 15（L03 口径），不满足 ≥30。** 只有扩到 16 数据集才够，而那要求 16 个数据集都能算出可比的 IC 曲线——L03 自己只做到 3 个。

**是否已被占据**：部分占据（L03 已做 IC 曲线这一支）。
**可做性：2/5 —— 淘汰（见 §4.2）。**

---

### T4｜数据稀缺 / 样本量不足

**提到它的论文（6 篇）**：L02, L12, L17, L18, L55, L63

**原文摘录**
> "Unfortunately, in this work we employed a limited set of metrics due to limitations inherent in existing datasets." — L18 Discussion
> "However, a significantly larger training set is required to cover the different eventualities. We defer consideration of those aspects to future work." — L12 Discussion

**可用统计单位与数量**：单位 = 电芯，990（BatteryLife）/ 169（MIT）/ 130（L14）/ 88（L13）。数量充足。
**但是**：这不是一个"研究方向"，是一个**所有人都承认、且已经被 BatteryLife 部分解决**的条件。做它 = 再做一个更大的数据集，与本项目的方法论定位不符。

**是否已被占据**：已被占据（L57 BatteryLife 就是这个问题的答案）。
**可做性：1/5 —— 淘汰。**

---

### T5｜不确定性量化与跨域校准

**提到它的论文（4 篇）**：L01, L65, L66, L69

**原文摘录**
> "Future studies should report interval coverage, calibration under domain shift, selective prediction, abstention policies, and decision-conditioned warning risk." — L01 §8
> "the true value might be out of the 95% confidence interval predicted by the BNN" — L66 §III-D

**可用统计单位与数量**
| 单位 | 名义 | **有效独立** |
|---|---|---|
| 数据集（BatteryLife）× 偏移类型（温度/协议/化学） | 16 × 3 = 48 | **48**（偏移是人为施加的因子，独立） |
| 若只用 7 个常用数据集 | 7 × 3 = 21 | 21 ✗ |
| × 校准方法（3）作为重复测量 | 144 | 仍是 48 |

→ **48 ≥ 30，但仅在用满 BatteryLife 16 数据集时成立。** 用 7 个常用数据集（CALCE/MATR/HUST/SNL/RWTH/HNEI/UL-PUR）只有 21，不达标。

**是否已被占据**：**未被占据，但被点名。**
- L66 只在同分布内校准；L65 做非交叉分位数但无跨域；L01 明确把 "calibration under domain shift" 列为缺口但没做。
- **"被点名的空位"意味着新颖性弱于 T1/T2**：审稿人会问"L01 已经说了，你只是执行"。

**可做性：2/5**
- 需要训练 16×3 组模型 + 3 种校准，算力与工程量都大。
- 若缩到 21 个单元则不达标 → 要么做满，要么不做。

---

### T6｜可辨识性：拟合质量不约束参数有效性，且没人把它当特征筛选门

**提到它的论文（5 篇）**：L14, L35, L36, L37, L43（+ L56 的物理诉求可算第 6）

**原文摘录**
> "All R2 values are greater than 0.999, indicating the credible fitting accuracy." 紧接 "The dominating degradation factors are different under different working conditions." — L14
> "Sensitivity analysis demonstrates that the output of the second order RC model is most sensitive to Rs and τ2, while the other three parameters C1, C2 and τ1 can be set to constants." — L36 §V

**可用统计单位与数量**
| 单位 | 数量 | 出处 |
|---|---|---|
| **电芯**（UConn + Bayreuth 合并） | **64 + 48 = 112** | `RESEARCH_STATE.md` |
| 参数 × 工况 | 6 × 23 = 138（名义） | 本项目自有 |
| 波形/拟合 | 17,130 | `INNOVATIONS_AND_RESULTS.md` P1 |

→ **若以"电芯"为单位：112 ≥ 30 ✓。**
→ **若以"工况"为单位：23 ✗。** 这是本方向最关键的一次单位选择。

**是否已被占据**：**未被占据。**
- L35 / L37 是可辨识性理论（无电池实验 / 无老化）。
- L36 是敏感性排序（单电芯、单温度）。
- L14 是"拟合好但主导因子变了"的实证轶事（130 电芯，但没做可辨识性指标）。
- L43 是 DRT 工程实现。
- **空隙**：把条件数 / CRLB / 参数相关矩阵当作**预测特征的准入检验**，并检验"不可辨识的参数是否正是跨工况符号翻转的那一批"。这正是本项目 P6 的正面版本（P6 只证伪了"可辨识性预测稳定性"，没有做"可辨识性筛选特征"）。

**可做性：4/5**
- 17,130 条波形已在本地，重拟合 + 算条件数是纯计算。
- 单位从"工况"换成"电芯"即可跨过 30 的门槛——**这是把本项目从 n=11 死亡里救回来的最直接路径**。
- 风险：Bayreuth 与 UConn 的脉冲协议不同，合并 112 个电芯需要先论证可比性。

---

### T7｜计算 / 部署成本

**提到它的论文（3 篇）**：L02, L57, L62

**原文摘录**
> "involving an LLM does increase the inference time even with PPA" — L62 §5.2
> "vanilla Transformer and RNNs are not suitable for BLP due to memory limitations" — L57 §4.3

**可用统计单位**：模型 × 数据集 = 10 × 7 = 70 名义，但**有效独立单元 = 数据集 7** ✗。
**是否已被占据**：已被 L57 的 18 方法基准占据。
**可做性：1/5 —— 淘汰。**

---

### T8｜测量状态依赖（在哪个 SOC、哪个温度下测 EIS/弛豫）

**提到它的论文（3 篇）**：L12, L13, L17

**原文摘录**
> "initial studies conducted using DRT curves obtained at various SOCs show that DRT curves at 25% SOC gave the best overall performance for SOH estimation." — L17 §4
> "although in this work we only consider forecasting starting from an initially discharged state" — L13 Discussion

**可用统计单位**：SOC × 温度 = 5 × 3 = 15 个测量配置 ✗（L17 只有 22 电芯、3 个 SOC）。
**是否已被占据**：部分占据（L16 Gasper 2022 专门做 T/SOC 解耦；L76 做测量误差）。
**可做性：2/5 —— 淘汰（单位不足且邻近工作密集）。**

---

### T9｜机理 / 物理解释缺失

**提到它的论文（4 篇）**：L01, L28, L56, L66

**原文摘录**
> "a deeper physical understanding and modelling remain essential" — L56 Discussion
> "exploring the underlying mechanisms that contribute to the knee point phenomenon can be considered" — L66 §V

**可用统计单位**：机理标签（LLI / LAM / CL）= **3** ✗。
**是否已被占据**：不适用（这是"缺什么"的元陈述，不是一个可测假设）。
**可做性：1/5 —— 淘汰（不可数）。**

---

### T10｜DRT 峰分离与分辨率

**提到它的论文（2 篇）**：L17, L43

**原文摘录**
> "in the case of diffusive processes, i.e. at high time constant, the use of a simple RC branch leads to high residuals between the measured and the estimated impedance spectrum." — L43 §IV

**可用统计单位**：峰（6）× 电芯 = 132 名义，但**峰的身份需人工裁定，独立单元 = 6 个峰** ✗。
**是否已被占据**：部分占据（L38–L41 一整条 DRT 可靠性线）。
**可做性：1/5 —— 淘汰。**

---

## 3. C. 保留清单（单位 ≥30 且未被占据），按可做性排序

> 规则：**有效独立单位 ≥ 30** 且 **未被现有工作占据**。T3/T4/T7/T8/T9/T10 已淘汰（理由见 §4）。

| 排名 | 主题 | 有效独立单位 | 数量 | 占据状态 | 可做性 | 一句话 |
|---|---|---|---|---|---|---|
| **1** | **T2 统计实践审计** | 论文 | 77（可扩 150+） | 未占据（L01 给了编码表未编码） | **5/5** | 零算力、零数据、与 P3 直接接续 |
| **2** | **T1 工况级符号一致性** | 循环工况 | 61 / 72 / 421 | 部分占据（L64 VPC、L44 ICA），符号统计空位 | **5/5** | 数据公开、管线已有；但**失去非循环通道** |
| **3** | **T6 可辨识性门控** | 电芯 | 112（64+48） | 未占据 | **4/5** | 唯一能**保住非循环通道**且单位 ≥30 的方向 |
| **4** | **T5 跨域校准** | 数据集 × 偏移 | 48 | 被 L01 点名但未做 | **2/5** | 做满才达标，工程量最大 |

### 3.1 四个方向的关系（为什么 T1 与 T6 不能合并成一个）

- **T2 与数据无关**，可以立刻启动，且产出的编码表可以直接支撑 T1 与 T6 的动机段。
- **T1 与 T6 是同一个问题的两条路**：T1 换单位（工况）但**丢掉非循环通道**；T6 保通道但换单位（电芯）。**二者不能同时满足"非循环通道 + 工况为单位 + 单位≥30"**，因为现有带 EIS/弛豫的数据集里工况最多的 Bayreuth 只有 23 个。
- 因此本轮的**核心结论**不是"哪个方向好"，而是：**"非循环测量通道 × 工况级推断"这个组合在当前数据生态下单位不足 30，必须二选一。**

---

## 4. 被淘汰的方向（显式记录，防止下次重蹈）

### 4.1 最重要的淘汰：非循环通道 × 工况级单位

| 数据集 | 电芯 | 工况 | 有 EIS/弛豫？ | 能否支撑工况级 ≥30？ |
|---|---:|---:|---|---|
| UConn | 64 | 11 | 是（脉冲/RPT） | ✗ |
| Bayreuth | 48 | 23 | 是（脉冲） | ✗（23 < 30） |
| L17 Khan | 22 | 多 SOC/温度 | 是（EIS） | ✗（电芯 22） |
| L13 Jones | 88 | 88 个随机协议（与电芯一一对应） | 是（EIS） | **技术上 88，但工况≡电芯，单位混淆** |
| L14 Zhu | 130 | 3 数据集 | 是（弛豫） | ✗（数据集 3） |
| MIT / A123 | 169 / 124 | 61 / 72 | **否** | ✓（但无非循环通道） |
| BatteryLife | 990 | 421 | **否** | ✓（但无非循环通道） |

**结论**：**"用非循环测量通道做工况级统计推断"这件事，在当前公开数据里做不到 n≥30。** 本项目不是方法错了，是**数据生态不支持这个单位**。
→ 出路只有两条：(a) 换单位到电芯（T6）；(b) 换通道到循环曲线（T1）。

### 4.2 其余淘汰项与理由

| 主题 | 有效单位 | 淘汰理由 |
|---|---|---|
| T3 标签定义依赖 | 15 | 单位不足；且 L03 已占 IC 一支 |
| T4 数据稀缺 | — | 不是可测假设；已被 L57 解决 |
| T7 计算成本 | 7 | 单位不足；已被 L57 的 18 方法基准占据 |
| T8 测量状态依赖 | 15 | 单位不足；L16/L76 邻近工作密集 |
| T9 机理缺失 | 3 | 不可数 |
| T10 DRT 分辨率 | 6 | 单位不足；L38–L41 已占 |

---

## 5. 与项目自身教训的对齐

本项目的死因是 **n=11 个工况**。本轮挖掘把它拆成三个可迁移的判断：

1. **不是"样本少"，是"单位选错"。** UConn 有 64 个电芯，但我们选了 11 个工况作单位。同一个数据集，换单位就从 11 变 64。**T6 就是这条的正面应用。**
2. **单位必须与泛化目标一致，且必须写进预注册。** 若声称"泛化到新工况"，单位就是工况；若声称"泛化到新电芯"，单位就是电芯。二者不能事后互换。**本项目 P3 的 ICC=0.414 / 等效 n=21.4 已经量化了代价。**
3. **"再跑一次说不定显著"必须被功效计算封死。** 本轮所有保留方向的单位数都 ≥30，且都能在开题前算出最小可检测效应。建议把这条件写进下一个预注册的**准入检查**（对应 P4：预注册必须自带可检验性检查）。

**一条新增教训（本轮产生）**：
> **P7｜数据集选择先于方向选择。** 一个方向的可行性上限由"有没有一个数据集在该方向的统计单位上 ≥30"决定，而不是由方法新颖性决定。本项目先选了方向（非循环通道），后发现没有数据集能在工况层凑够 30——这个顺序应该反过来。

---

## 6. 局限与待核实（本文件自己的）

1. **"是否已被占据"不是穷尽检索的结论。** 依据是本矩阵 77 篇 + 本轮 23 篇全文。T1/T2/T6 在开题前必须各做一次针对性检索（检索式见 `LITERATURE_MATRIX.md` §1），确认没有遗漏。
2. **本轮为定向复读（L2\*），不是 L1 全文精读。** 23 篇中我只完整读了局限/未来/结论/讨论四节 + 方法节数字。若要写进论文，涉及的数字需回原文逐条复核。
3. **③ 段全部是我的判读，不是作者的话。** 尤其 L13「工况≡电芯」、L17「10 个测试集重叠」、L63「窗口级泄漏」三条，是我从方法节结构推断的，作者未承认。引用时必须写成"本文作者未讨论的一个问题是…"，不得写成"作者承认"。
4. **数字来源分级**：
   - 来自论文原文（已核）：61 工况（L64）、421 协议（L57）、990 电芯（L57）、169 电芯（L64）、124 电芯（L55）、130 电芯（L14）、88 电芯（L13）、22 电芯（L17）、33 电芯（L44 Table 1）、24 电池（L28）、12 电芯（L12）。
   - 来自本项目自有结果：UConn 64/11、Bayreuth 48/23、17,130 波形、ICC=0.414、NASA 4 电芯。
   - **未核**：A123 的 72 个协议数（matrix 记，L55 原文只写 124 电芯，未逐条核对 72）。
5. **L44 电芯数与矩阵不一致**（25+8=33 vs 矩阵 26+9=35）。已按原文 Table 1 记录，矩阵待 A1 更正。
6. **T5 的 48 个单元是设计值，不是已实现值。** 能否真的在 BatteryLife 16 个数据集上施加 3 类偏移，需要先做一次数据可用性检查。

---

## 7. 建议主代理的下一步（按优先级）

1. **立刻可做（0 算力）**：启动 T2（论文级统计实践审计）。产出物是一张 77 行的编码表 + 一个"该领域有多少篇用对了统计单位"的百分比。这与本项目 P3 直接接续，且不依赖任何数据集。
2. **一周内可做（复用现有管线）**：T6 的可辨识性门控，单位改为**电芯（112）**。这是唯一同时满足「保住非循环通道」+「单位 ≥30」+「未被占据」的方向。
3. **需要决策**：是否接受 T1 的代价——用循环曲线换 61/72 个工况单位，放弃非循环通道的新颖性。**这是一个方向性取舍，建议由 A6 在 DECISION_LOG 里显式记录。**
4. **不要做**：任何以 UConn 11 或 Bayreuth 23 为工况单位的进一步统计推断。功效不足，已封死。

---

*本文件仅由文献挖掘代理维护。所有引文可用 §0.1 的方式复现；所有数字可用 §6.4 的分级追溯。*
