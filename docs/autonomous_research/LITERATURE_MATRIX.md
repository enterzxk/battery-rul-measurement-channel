# LITERATURE MATRIX — 电池 RUL / 非循环测量通道文献证据矩阵

> 维护者：A1 Literature Researcher
> 创建：2026-11-07 | 版本：v1.0
> 范围：2023–2026 优先（保留 2016–2022 的方法学奠基文献）
> 主题：电池 RUL / SOH、EIS、脉冲与静置弛豫、退化机理、跨工况泛化、早期寿命预测、物理引导建模、状态空间模型、概率预测、稀疏不规则采样、不确定性量化
> 本文件只写自己名下的文件，不修改 `docs/` 下任何历史结果。

---

## 0. 阅读等级定义（本文件唯一口径）

| 等级 | 定义 | 判定标准 |
|---|---|---|
| **L1 全文精读** | 通读正文（去参考文献），含方法、结果、讨论、局限 | 覆盖正文 ≥85%，能复述其数字与结论 |
| **L2 主体精读** | 读摘要 + 方法 + 结果 + 结论，跳读引言/相关工作 | 覆盖正文 40%–85% |
| **L3 仅摘要** | 只读摘要/官方摘要字段 | 未见方法细节 |
| **L4 仅题录** | 只有题名、作者、venue、DOI（摘要不可得） | 不得引用其具体数字或结论 |

**统计（77 条）**：L1 = 17，L2 = 6，L3 = 44，L4 = 10。

> 关于「至少 20 篇全文精读」：实际完成 17 篇。差额 3 篇的原因与补齐路径写在 §7.1，不做凑数标注——把只读了 30%–45% 的条目改标 L1 属于虚构阅读等级。

---

## 1. 检索方法与可复现检索式

- **元数据源**：OpenAlex Works API（`api.openalex.org/works`，select 字段含 title/doi/authorships/publication_year/primary_location/abstract_inverted_index）、arXiv Atom API（`export.arxiv.org/api/query`）。
- **全文源**：本地 `docs/papers/_extracted/*.txt`（11 篇 PDF 的抽取文本，其中 5 篇另有全文版）；arXiv PDF；Nature Communications PDF。MDPI / ScienceDirect 直连 403，故 MDPI 论文只用本地已下载 PDF。
- **时间窗**：2016-01-01 起，2023–2026 优先。
- **去重规则**：同一 DOI 只保留一条；预印本与期刊版合并为一条，正文注明双出处。
- **检索式（节选，均实际执行）**：
  1. `electrochemical impedance spectroscopy remaining useful life lithium-ion battery`
  2. `impedance features versus cycling features battery state of health comparison`
  3. `distribution of relaxation times lithium-ion battery identifiability`
  4. `equivalent circuit model parameter identifiability lithium-ion battery`
  5. `identifiability analysis battery model parameters sensitivity correlation`
  6. `charge transfer resistance temperature dependence Arrhenius lithium-ion battery`
  7. `relaxation voltage feature state of health lithium-ion battery`
  8. `cross-condition generalization battery state of health estimation domain adaptation`
  9. `early life prediction battery cycle life machine learning features`
  10. `state space model battery remaining useful life irregular sampling`
  11. `probabilistic remaining useful life prediction uncertainty quantification battery`
  12. `degradation mode loss of lithium inventory loss of active material dV/dQ diagnosis`
  13. `impedance temperature coefficient state of charge dependence lithium-ion cell`
  14. `multi-exponential fitting ill-conditioned time constants relaxation`
  15. `ablation study feature importance battery lifetime prediction which features matter`
  16. arXiv：`all:"battery" AND all:"impedance" AND all:"state of health"`、`all:"equivalent circuit" AND all:"identifiability"`、`all:"battery" AND all:"irregular" AND all:"sampling"`
- **未使用**：`web_fetch`（已知损坏）；MDPI / ScienceDirect 网页抓取（403）。

---

## 2. 主表

> 列说明：**等级**见 §0；**代码**列写「未核实」表示未确认公开代码，不臆测。

### A 组｜综述与框架（确立 gap 的权威表述）

| 编号 | 标题 | 作者 | 年 | venue | DOI | 代码 | 贡献一句话 | 实验协议 | 缺陷 | 可借鉴机制 | 等级 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L01 | Toward Trustworthy and Transferable SOH/RUL Estimation for Li-Ion Batteries: A Critical Review and Multi-Fidelity Validation | Rizanov, Stoynova, Mihov | 2026 | Batteries 12(7):255 | 10.3390/batteries12070255 | 无 | 176 篇批判性综述，提出「估计器应匹配可观测性」与 context disentanglement 两条准则，并给出 cell→pack→fleet 多保真验证框架 | 文献分类 + 证据审计工作簿；无新实验 | 准则停在框架层，未对 EIS/弛豫通道给出任何定量贡献；无代码 | 可观测状态 $x_t=[I,V,T,Z_t,R_t,m_t]$；worst-domain error / coverage 验收口径 | L1 |
| L02 | Battery Health Monitoring and RUL Prediction Techniques: A Review | Ahwiadi & Wang | 2025 | Batteries 11(1):31 | 10.3390/batteries11010031 | 无 | 按 model-based / data-driven / hybrid 三分法梳理 RUL，确认现有方法输入以循环曲线为主 | 综述；用 NASA 数据作图示例 | 无定量横向比较、无跨工况协议讨论 | 分类学与 baseline 选择依据 | L1 |
| L03 | A Review of Methods of Generating IC–DV Curves for Battery Health Determination | Beatty, Strickland, Ferreira | 2024 | Energies 17(17):4309 | 10.3390/en17174309 | 无 | 系统比较 IC/DV 曲线生成与滤波方法，三数据集验证，推荐 point-count + Savitzky–Golay | Oxford×2 + Nature + Loughborough 数据集 | 只到曲线生成；未触及 RUL 或通道增量 | 「无标准化流程」作为预处理声明依据 | L1 |
| L04 | A comprehensive review of data-driven EIS approaches for Li-ion battery SoH and RUL estimations | Raza et al. | 2026 | Renew Sustain Energy Rev | 10.1016/j.rser.2026.117559 | 未核实 | 数据驱动 EIS 用于 SoH/RUL 的最新综述 | 综述 | 摘要级；未读全文 | 定位 EIS→RUL 文献簇 | L3 |
| L05 | On the use of EIS to characterize and model the aging phenomena of Li-ion batteries: a critical review | Iurilli et al. | 2021 | J Power Sources | 10.1016/j.jpowsour.2021.229860 | 未核实 | EIS 表征与建模老化的批判性综述 | 综述 | 2021 年，未覆盖 2023+ 的 DRT/ML 进展 | EIS 特征与 ECM 的对应关系 | L3 |
| L06 | SoH estimation of Li-ion batteries based on EIS: a review | Liu et al. | 2023 | Prot Control Mod Power Syst | 10.1186/s41601-023-00314-w | 未核实 | EIS 用于 SoH 的综述 | 综述 | 目标为 SoH 而非 RUL | EIS 特征分类 | L3 |
| L07 | Measurement, interpretation, and application of EIS to Li-ion batteries | Zhang et al. | 2025 | EES Batteries | 10.1039/d5eb00153f | 未核实 | EIS 测量—解释—应用全链条综述 | 综述 | 摘要级 | 测量误差与解释歧义的表述 | L3 |
| L08 | Lithium ion battery degradation: what you need to know | Edge et al. | 2021 | Phys Chem Chem Phys | 10.1039/d1cp00359c | 无 | 退化机理（LLI / LAM / CL）权威综述 | 综述 | 无定量预测 | 机理术语基准 | L3 |
| L09 | A Review and Perspective on Path Dependency in Batteries | Röder et al. | 2022 | Energy Technol | 10.1002/ente.202200627 | 未核实 | 路径依赖（老化、功率、滞回、记忆效应）综述 | 综述 | 摘要级 | 「同 SOH 不同状态」的依据 | L3 |
| L10 | Review of "grey box" lifetime modeling for Li-ion battery | Guo et al. | 2022 | J Energy Storage | 10.1016/j.est.2022.105992 | 未核实 | 物理 + 数据混合寿命建模综述 | 综述 | 摘要级 | grey-box 定位 | L3 |
| L11 | A Review of Degradation Models and RUL Prediction for Testing Design and Predictive Maintenance | Patrizi et al. | 2024 | Sensors | 10.3390/s24113382 | 未核实 | 退化模型与 RUL 综述，含测试设计与预测维护决策框架 | 综述 | 摘要级 | 决策框架视角 | L3 |

### B 组｜非循环测量通道：EIS 与弛豫（本项目主战场）

| 编号 | 标题 | 作者 | 年 | venue | DOI | 代码 | 贡献一句话 | 实验协议 | 缺陷 | 可借鉴机制 | 等级 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L12 | Identifying degradation patterns of Li-ion batteries from impedance spectroscopy using ML | Zhang, Tang, Zhang, Wang, Stimming, Lee | 2020 | Nat Commun 11:1706 | 10.1038/s41467-020-15235-7 | 未核实 | 2 万+ EIS 谱 + GPR，整谱免特征工程预测容量与 RUL，优于放电曲线特征 | LCO/graphite；多温度多 SOC；单次阻抗测量即可预测 | 做 RUL 的电芯数少；无跨工况 LOGO；无通道消融表 | 整谱输入；显著频率回溯 | L2 |
| L13 | Impedance-based forecasting of Li-ion battery performance amid uneven usage | Jones, Stimming, Lee | 2022 | Nat Commun 13:4806 | 10.1038/s41467-022-32422-w | 有：github.com/PenelopeJones/battery-forecasting（数据 Zenodo 10.5281/zenodo.6645536） | 单次 EIS + 概率 ML 预测下一循环容量，无需任何使用历史；并给出**同模型换状态表示**的完整对照表 | 88 coin cells（Powerstream 40 + RS Pro 48）；随机倍率；EIS 在**满放状态**下取 57 频点 0.02 Hz–20 kHz（5 mA 正弦）；10×XGBoost 集成；留两电芯交叉验证重复 N/2 次 | 目标是下一循环容量而非 RUL；coin cell 小容量；无 LOGO/LOCO 统计；未报告电芯级配对 CI | **通道消融表**：Protocol only 15.4%、EIS only 20.7%、EIS+Protocol 8.2%、ECM-R+Protocol 10.7%、ECM-ER+Protocol 8.4%、CVF+Protocol 8.8%、EIS+CVF+Protocol 6.7%、全特征 6.2%；35 °C 外推 34.2%→14.0% | L1 |
| L14 | Data-driven capacity estimation of commercial Li-ion batteries from voltage relaxation | Zhu et al. | 2022 | Nat Commun 13:2261 | 10.1038/s41467-022-29837-w | 未核实 | 充电后弛豫电压 6 个统计量 → 容量，明确「不需要历史循环信息」；迁移后 <1.7% | 130 cells / 3 数据集（NCA、NCM、NCM+NCA）；[Var, Ske, Max]；cell-stratified 划分；30–60 min 弛豫 | 统计特征非物理参数；Min/Mean 随容量**先升后降**；SEI 电阻在部分循环「未识别」 | 「无历史」设定；非单调特征现象；ECM 参数不可辨识的实证 | L1 |
| L15 | A Comparison between EIS and ICA-DV as Li-ion Diagnostic Techniques | Pastor-Fernández et al. | 2017 | J Power Sources | 10.1016/j.jpowsour.2017.03.042 | 未核实 | 直接比较 EIS 与 ICA/DVA 对 CL / LAM / LLI 的辨识能力 | 摘要级 | 目标是退化模式诊断而非 RUL；不是「同模型只换通道」 | 两通道互补性的最早系统表述 | L3 |
| L16 | Predicting battery capacity from impedance at varying temperature and SOC using ML | Gasper et al. | 2022 | Cell Rep Phys Sci | 10.1016/j.xcrp.2022.101184 | 未核实 | 用 ML 解耦容量 / SOC / 温度对 EIS 的混杂影响后预测容量 | 摘要级 | 未读全文 | 「EIS 同时编码 T 与 SOC」的问题化方式 | L3 |
| L17 | Onboard Health Estimation using Distribution of Relaxation Times | Khan, Thatipamula, Onori | 2024 | arXiv 2410.15271 | — | 未核实 | DRT 曲线 + LSTM 做 SOH，22 cells、10 个测试集平均 RMSPE 1.69% | NMC/graphite 5 Ah；5 日历 + 17 循环老化；0/25/40 °C；EIS@0–100% SOC；Tikhonov + L 曲线 | SOH 非 RUL；22 cells；DRT 正则参数敏感；选 25% SOC 属事后择优 | **DRT 峰随老化「升高 + 左移」**；扩散峰 0–50% SOC 升高、**75–100% SOC 下降**（作者归因于高 SOC 下 Li⁺ 迁移率提升） | L1 |
| L18 | Prognosis of Multivariate Battery State of Performance and Health via Transformers | Paulson, Kubal, Babinec | 2023 | arXiv 2309.10014（期刊版 Cell Rep Phys Sci 2024, 10.1016/j.xcrp.2024.101928） | 10.1016/j.xcrp.2024.101928 | 未核实 | 28 个健康描述量（含 ECM 的 OCV/R、内阻、效率）多变量 transformer 预后，LFP 快充 EOL MAE 19 cycles | 178 LFP + 300 pouch（6 化学体系）；1–64 起始循环 | 循环规则、无真实不规则使用；**ECM 派生特征在 CAMP 数据上噪声过大被剔除** | 「多描述量而非标量 SOH」；ECM 特征噪声的实证 | L2 |
| L19 | EIS-based deep ensemble for RUL considering data imbalance and uncertainty | Ruan et al. | 2025 | J Energy Storage | 10.1016/j.est.2025.118797 | 未核实 | EIS + 深度集成做 RUL，处理数据不平衡与不确定性 | 摘要不可得 | 仅题录级 | EIS→RUL 的直接对照 | L4 |
| L20 | Multi-Source Impedance and Discharge Feature Learning for Cross-Battery SOH | Sardar et al. | 2026 | Batteries | 10.3390/batteries12080291 | 未核实 | 阻抗 + 放电多源特征融合，跨未见电芯 SOH | 摘要级 | 未读全文 | 融合而非隔离的设计对照 | L3 |
| L21 | SOH with Embedded Impedance Spectrum Features under Multiple Chemistry and Temperature | Xiang et al. | 2026 | Batteries | 10.3390/batteries12020077 | 未核实 | 嵌入阻抗谱特征，跨化学体系与温度 | 摘要级 | 未读全文 | 阻抗特征的跨工况嵌入 | L3 |
| L22 | Dynamic EIS: A Forward Application Approach for Li-ion Battery Status Assessment | Zhang et al. | 2025 | EcoMat | 10.1002/eom2.70018 | 未核实 | 动态 EIS 用于非稳态工况下的状态评估 | 摘要级 | 未读全文 | 非稳态测量可行性 | L3 |
| L23 | A hybrid intelligent model using DRT of EIS for SOH estimation | Zhao et al. | 2024 | J Energy Storage | 10.1016/j.est.2024.110814 | 未核实 | DRT + 混合模型 SOH，针对 EIS 半圆重叠问题 | 摘要级 | 未读全文 | 半圆重叠的处理 | L3 |
| L24 | Computation of DRT by Tikhonov regularization: usage of L-curve | Paul et al. | 2021 | Sci Rep | 10.1038/s41598-021-91871-3 | 未核实 | Tikhonov 正则 + L 曲线求 DRT | 合成 + 实验阻抗数据 | 未读全文 | DRT 求解的默认配置 | L3 |
| L25 | Rapid dynamic EIS reconstruction using GAN | Li et al. | 2026 | J Energy Storage | 10.1016/j.est.2026.125087 | 未核实 | GAN 重建动态 EIS | 摘要不可得 | 仅题录级 | 快速测量的可行性边界 | L4 |
| L26 | SOH estimation based on time-frequency features | He et al. | 2024 | J Power Sources | 10.1016/j.jpowsour.2023.234002 | 未核实 | 时频域联合特征做 SOH | 摘要级 | 未读全文 | 时域+频域同源性处理 | L3 |
| L27 | Data-driven SOH estimation: Impact of voltage, time, and derivative features | Amiri et al. | 2026 | Int J Electrochem Sci | 10.1016/j.ijoes.2026.101372 | 未核实 | 系统比较电压/时间/导数类特征对 SOH 的贡献 | 摘要级 | 未读全文 | 特征族比较的实验设计 | L3 |
| L28 | Incremental capacity feature selection considering estimation capability and efficiency | Su, Tao, Chen, Zou, Zhang | 2026 | Cell Rep Phys Sci 7:103083 | 10.1016/j.xcrp.2025.103083 | 未核实 | 统一评估 IC 特征的预测性 / 可迁移性 / 数据效率；首个 IC 峰两特征即可 | CALCE + TJU，24 电池 / 6000 循环；XGBoost；微调迁移 1C→0.5C、25→35 °C；MAPE 4.82% / 0.65% | 「可迁移」是微调式而非零样本；目标为 SOH | PC/TC/DE 三准则；特征数–精度曲线 | L1 |

### C 组｜可辨识性、不适定反问题与参数估计偏差（决定 B 问题能否成立）

| 编号 | 标题 | 作者 | 年 | venue | DOI | 代码 | 贡献一句话 | 实验协议 | 缺陷 | 可借鉴机制 | 等级 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L29 | Structural Identifiability of Equivalent Circuit Models for Li-Ion Batteries | Grandjean et al. | 2017 | Energies 10(1):90 | 10.3390/en10010090 | 未核实 | 只有特定 ECM 拓扑可全局结构可辨识 | 理论推导 | 结构可辨识 ≠ 实践可辨识 | 「先证可辨识，再谈参数」 | L3 |
| L30 | Fisher identifiability analysis for a periodically-excited ECM | Sharma et al. | 2014 | ACC | 10.1109/acc.2014.6859360 | 未核实 | 用 Fisher 信息 / CRLB 量化内阻与容量的可辨识性 | 一阶非线性 ECM，周期激励 | 未读全文 | CRLB 作为参数估计方差下界 | L3 |
| L31 | Identifiability and Parameter Estimation of the Single Particle Model | Bizeray et al. | 2018 | IEEE TCST | 10.1109/tcst.2018.2838097 | 未核实 | SPM 的结构与实践可辨识性；参数分组降维 | 理论 + 仿真 | 面向电化学模型 | 参数分组（lumping） | L3 |
| L32 | Practical identifiability of electrochemical P2D models | Laue et al. | 2021 | J Appl Electrochem | 10.1007/s10800-021-01579-5 | 未核实 | P2D 的实践可辨识性分析 | 摘要级 | 未读全文 | 实践可辨识性判定流程 | L3 |
| L33 | Nonlinear Identifiability Analysis of the Porous Electrode Theory Model | Berliner et al. | 2021 | J Electrochem Soc | 10.1149/1945-7111/ac26b1 | 未核实 | 多孔电极理论的非线性可辨识性 | 摘要级 | 未读全文 | 非线性可辨识性工具 | L3 |
| L34 | A guide to equivalent circuit fitting for impedance analysis and battery state estimation | Santoni et al. | 2024 | J Energy Storage | 10.1016/j.est.2023.110389 | 未核实 | ECM 拟合 → SoC/SoH 提取的完整方法学指南 | 摘要级 | 未读全文 | 拟合流程与陷阱清单 | L3 |
| L35 | Structural Identifiability of Impedance Spectroscopy Fractional-Order ECMs With Two CPEs | Soleymani Aghdam, Alavi, Saif | 2021 | arXiv 2103.00226 | 有：github.com/smmalavi/str-identifiability-frac-sys | 用系数映射法证明 2-CPE 分数阶 ECM 在常用参数范围内**全局结构可辨识** | 无噪声；α∈(0.1,0.9)、R₁∈(0.05,5) 等范围扫描；Matlab vpa | 只做结构可辨识；作者明言不含噪声与激励选择 | 「结构 ≠ 实践」的分界；系数映射法 | L1 |
| L36 | Global sensitivity analysis of battery equivalent circuit model parameters | Zhao & Howey | 2016 | arXiv 1604.01293 | 未核实 | Morris 全局敏感性：输出对 R_s、τ₂ 最敏感，C₁/C₂/τ₁ 可当常数 | Kokam NMC 740 mAh；FUDS；N=1024 次 Monte Carlo；UDC 验证 | 仅 20 °C、单电芯；未涉老化 | 参数重要性排序 → **哪些参数不值得当特征**；验证 RMSE 5.67→7.12→15.35 mV | L1 |
| L37 | On the Identification of Electrical Equivalent Circuit Models Based on Noisy Measurements | Balasingam & Pattipati | 2021 | arXiv 2101.05349 | 未核实 | 证明低 SNR 下最小二乘**有偏**；TLS + Kalman 无偏且达 CRLB | 理论 + 真实电流剖面；R-int 与低阶 ECM | 只针对低阶 ECM；未涉及老化 | 「参数估计偏差随 SNR 变化」的定量框架 | L2 |
| L38 | How Reliable is DRT Analysis? A Dual Regression-Classification Perspective | Huang et al. | 2022 | Electrochim Acta | 10.1016/j.electacta.2023.141879 | 未核实 | 用双回归-分类视角评估 DRT 的估计、解释与精度 | 摘要不可得 | 仅题录级 | DRT 可靠性的质疑框架 | L4 |
| L39 | Advancing electrochemical impedance analysis through innovations in the DRT method | Maradesa et al. | 2024 | Joule | 10.1016/j.joule.2024.05.008 | 未核实 | DRT 方法的峰值分辨与正则化改进 | 摘要不可得 | 仅题录级 | DRT 峰值分离的最新技术 | L4 |
| L40 | The Deep-Prior Distribution of Relaxation Times | Liu et al. | 2020 | J Electrochem Soc | 10.1149/1945-7111/ab631a | 未核实 | 用深度先验解 DRT 病态反问题 | 摘要级 | 未读全文 | 「反问题病态」的正则化视角 | L3 |
| L41 | Distribution of relaxation times: foundations, methods, diagnostics, prognosis | Wang et al. | 2025 | Curr Opin Electrochem | 10.1016/j.coelec.2025.101789 | 未核实 | DRT 从机理解卷积到诊断/预后引擎的综述 | 摘要级 | 未读全文 | DRT→预后 的现状定位 | L3 |
| L42 | Identifiability study of battery capacity fade using degradation mode sensitivity | Lin et al. | 2024 | J Power Sources | 10.1016/j.jpowsour.2024.234446 | 未核实 | 用退化模式敏感性分析容量衰减的可辨识性 | 摘要不可得 | 仅题录级 | 把可辨识性接到退化模式上 | L4 |
| L43 | EIS2MOD: a DRT-based modelling framework for Li-ion cells | Iurilli, Brivio, Carrillo, Wood | 2022 | arXiv 2203.08515（IEEE TIA） | 未核实 | DRT → 物理 ECM 的自动建模；**τ 取峰位、R 取峰面积** | 55 Ah NMC pouch；−10–35 °C；全 SOC；端电压 RMSE <1.50% | 峰数仍需人工交叉核对；未做 RUL；未做跨工况统计 | 6 峰 ↔ 6 个物理过程；峰重叠时需人工裁定 | L2 |

### D 组｜退化机理与「方向翻转」的物理根源

| 编号 | 标题 | 作者 | 年 | venue | DOI | 代码 | 贡献一句话 | 实验协议 | 缺陷 | 可借鉴机制 | 等级 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L44 | ICA (dQ/dV) as a tool for analysing the effect of ambient temperature and mechanical clamping on degradation | Spitthoff, Vie, Wahl, Wind, Burheim | 2023 | J Electroanal Chem 944:117627 | 10.1016/j.jelechem.2023.117627 | 未核实 | 35 个大软包电芯：15 与 25 °C 容量衰减速率相近但**退化模式截然不同**；夹紧力是最重要抑制因素 | 26×64 Ah NMC532 + 9×31 Ah NMC433；5 步 ICA 流程；与 alawa 退化模式仿真交叉验证 | 无 RUL；无 ECM 参数；无统计检验 | 「同衰减不同模式」→ 特征方向可翻转的机理证据 | L1 |
| L45 | Temperature Dependent EIS Studies Separating Charge Transfer Impedance from Contact Impedance | Keefe et al. | 2019 | J Electrochem Soc | 10.1149/2.0541914jes | 未核实 | 低温对称电池 EIS 可无歧义分离 charge-transfer 与 contact 阻抗 | 摘要级 | 未读全文 | 低温改变过程可分离性 | L3 |
| L46 | Arrhenius plots for Li-ion battery ageing as a function of temperature, C-rate, and ageing state | Kučinskis et al. | 2022 | J Power Sources | 10.1016/j.jpowsour.2022.232129 | 未核实 | V 形 Arrhenius 图：低温 SEI 生长、高温镀锂两种机制**交叉** | 摘要级 | 未读全文 | 「机制交叉」作为符号翻转的机理解释 | L3 |
| L47 | Temperature dependency of diagnostic methods in lithium-ion batteries | Fly et al. | 2022 | J Energy Storage | 10.1016/j.est.2022.104721 | 未核实 | CC / current-interrupt / EIS 诊断量随温度漂移 | 摘要级 | 未读全文 | 诊断量的温度不变性检验 | L3 |
| L48 | Aging effect on the variation of Li-ion battery resistance as function of temperature and SOC | Barcellona et al. | 2022 | J Energy Storage | 10.1016/j.est.2022.104658 | 未核实 | 内阻随温度、SOC 与老化的联合变化 | 摘要不可得 | 仅题录级 | 内阻的 T/SOC 依赖 | L4 |
| L49 | Durability and Reliability of EV Batteries: Path Dependence of Battery Degradation | Dubarry et al. | 2018 | J Electrochem Soc | 10.1149/2.0421805jes | 未核实 | 不同使用序列导致不同退化模式 | 摘要级 | 未读全文 | 路径依赖的实验证据 | L3 |
| L50 | Degradation path prediction of Li-ion batteries under dynamic operating sequences | Kim et al. | 2025 | Energy Environ Sci | 10.1039/d4ee04787g | 未核实 | 利用路径依赖预测未来老化路径 | 摘要级 | 未读全文 | 路径→未来轨迹的建模范式 | L3 |
| L51 | Battery aging mode identification across NMC compositions and designs using ML | Chen et al. | 2022 | Joule | 10.1016/j.joule.2022.10.016 | 未核实 | 跨成分/设计识别退化模式 | 摘要不可得 | 仅题录级 | 模式识别标签 | L4 |
| L52 | Best practices for incremental capacity analysis | Dubarry et al. | 2022 | Front Energy Res | 10.3389/fenrg.2022.1023555 | 未核实 | ICA 的操作规范与常见伪影 | 摘要级 | 未读全文 | 预处理规范 | L3 |
| L53 | Review—"Knees" in Lithium-Ion Battery Aging Trajectories | Attia et al. | 2022 | J Electrochem Soc | 10.1149/1945-7111/ac6d13 | 未核实 | 膝点定义与三类内部状态轨迹（snowball / hidden 等） | 综述 | 未读全文 | 膝点定义的分歧 | L3 |
| L54 | Identification and ML prediction of knee-point and knee-onset | Fermín-Cueto et al. | 2020 | Energy and AI | 10.1016/j.egyai.2020.100006 | 未核实 | 前 50 循环特征 + 特征选择预测膝点 / 膝起点 | 摘要级 | 未读全文 | 膝点作为事件目标的设定 | L3 |
| L55 | Nonlinear aging knee-point prediction for Li-ion batteries faced with different application scenarios | You, Zhu, Wang, Jiang, Wei, Dai | 2023 | eTransportation 18:100270 | 10.1016/j.etran.2023.100270 | 未核实 | 最大距离法识别膝点 + S-LSTM 直接预测 + 滑窗，面向开发/早期评估/在线/梯次四类场景 | A123 124 cells / 72 快充协议 / 30 °C；4C 放电 | 输入仍是循环容量与内阻曲线；无跨工况留出 | 场景分层（直接 vs 间接预测） | L1 |

### E 组｜跨工况泛化、标签侧去工况与统计单位

| 编号 | 标题 | 作者 | 年 | venue | DOI | 代码 | 贡献一句话 | 实验协议 | 缺陷 | 可借鉴机制 | 等级 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L56 | Battery lifetime prediction across diverse ageing conditions with inter-cell deep learning (BatLiNet) | Zhang, Li, Zheng, Lu, Gui, Xu, Bian | 2025 | Nat Mach Intell 7:270–277 | 10.1038/s42256-024-00972-x | 未核实 | 电芯间差值学习：把「预测寿命」改成「预测两电芯寿命差」，MAPE 相对单电芯学习降 >40% | MATR/HUST/CALCE/SNL/UL-PUR/RWTH/HNEI；MIX-100 与 MIX-20 两个极早预测设定 | 手段在**标签侧**而非输入侧；快充协议族仍有限 | 参照电芯锚定；MIX-20（20 循环预测 90% 点） | L1 |
| L57 | BatteryLife: A Comprehensive Dataset and Benchmark for Battery Life Prediction | Tan, Hong, Tang, Lu, Ma, Zheng, Li, Huang, Zhang | 2025 | KDD '25 | 10.1145/3711896.3737372 | 有：github.com/Ruifeng-Tan/BatteryLife | 16 数据集 / 990 电芯 / 99k 样本；18 方法基准；提出 CyclePatch；发现时序领域流行模型在 BLP 上不适用 | 8 形态 / 59 化学体系 / 9 温度 / 421 协议；1–100 循环预测 | 以循环数据为主，无 EIS/弛豫通道 | 跨域评测协议；「领域外模型不适用」的负结果 | L1 |
| L58 | Increasing generalization capability of battery health estimation using continual learning | Che et al. | 2023 | Cell Rep Phys Sci | 10.1016/j.xcrp.2023.101743 | 未核实 | 用无标签 + 稀疏标签持续更新提升跨电池泛化 | 摘要级 | 未读全文 | 持续学习作为跨工况手段 | L3 |
| L59 | The challenge and opportunity of battery lifetime prediction from field data | Sulzer et al. | 2021 | Joule | 10.1016/j.joule.2021.06.005 | 未核实 | 现场数据的标签延迟、使用历史不规则、共因不可控 | 摘要不可得 | 仅题录级 | 现场数据的问题化 | L4 |
| L60 | A hierarchical multi-domain adaptation method for generalizable cross-domain SOH | Wang et al. | 2026 | J Energy Storage | 10.1016/j.est.2026.124391 | 未核实 | 层级多域适配 | 摘要不可得 | 仅题录级 | 域适配的分层设计 | L4 |
| L61 | Quantifying the impact of cell-to-cell inconsistency on EV battery degradation | Zhou et al. | 2026 | Nat Energy | 10.1038/s41560-026-02131-5 | 未核实 | 电芯间不一致性对退化与利用的系统级影响 | 摘要级 | 未读全文 | 电芯级 vs 系统级统计单位 | L3 |
| L62 | Adapting Amidst Degradation: Cross Domain Li-ion Battery Health Estimation via Physics-Guided Test-Time Training (BatteryTTT) | Feng, Hu, Li, Zhang | 2024 | arXiv 2402.00068 | 未核实 | 用降解中陆续到达的**单条**无标签样本持续 TTT，以 1-RC ECM ODE 作自监督 | KOKAM 等；QdLinear 特征；SOH 任务 | 任务是 SOH 非 RUL；需源域预训练；ODE 残差约束的是电压而非参数 | 单样本 TTT；物理自监督损失构造 | L1 |
| L63 | State of Health Estimation using a Time-Informed Dynamic Sequence-Inverted Transformer (TIDSIT) | Patel, Ramezankhani, Deodhar, Birru | 2025 | arXiv 2507.18320 | 未核实 | 连续时间嵌入 + 时间注意力处理不规则采样与变长序列，NASA 上 SoH 误差 <0.58% | NASA 退化数据；变长放电序列 | 单数据集；SOH 非 RUL | 连续时间嵌入作为不规则采样的一等公民 | L2 |
| L64 | Bayesian hierarchical modelling for battery lifetime early prediction | Zhou & Howey | 2022 | arXiv 2211.05697 | 未核实 | 层级贝叶斯：个体特征 + 工况层特征；**VPC = 74.5%** 的寿命方差来自工况组效应 | MIT 169 cells / 61 工况；前 100 循环；5 折 CV；RMSE 3.20 天、MAPE 8.6%，优于基线 12–13% | 线性模型；仅充电协议差异；K=8 聚类属经验选择 | 部分池化；VPC 作为「是否该按工况分层」的判据 | L1 |

### F 组｜概率预测与不确定性量化

| 编号 | 标题 | 作者 | 年 | venue | DOI | 代码 | 贡献一句话 | 实验协议 | 缺陷 | 可借鉴机制 | 等级 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L65 | RUL-QMoE: Multiple Non-crossing Quantile Mixture-of-Experts for Probabilistic RUL | Ly, Yang, Dixit, Nguyen | 2025 | arXiv 2512.23725 / AAAI-26 (10.1609/aaai.v40i47.41472) | 10.1609/aaai.v40i47.41472 | 未核实 | 材料门控 MoE + 非交叉分位数回归；7 数据集 MAE 65 cycles / MAPE 9.59% | CALCE/MATR/HUST/HNEI/RWTH/SNL/UR-PUR；1010 维输入（100 循环 × 10 电压-容量点） | 门控的是**材料/工况**而非通道；无 EIS；无跨工况 LOGO | 非交叉分位数约束；分位数 → 分布 | L1 |
| L66 | Early Prediction of Knee Point and Knee Capacity with UQ and Calibration | Ke, Jiang, Zhu, Peng, Tan | 2024 | IEEE TTE 10(2):2873 | 10.1109/tte.2023.3304670 | 未核实 | BNN + MC-dropout 联合预测膝点与膝点容量，并用 STD scaling 校准；仅用前 30 循环 | 3 个公开快充数据集（124 / 45 / N）；容量矩阵滑动特征；Bacon–Watts 膝点定义 | 输入为循环容量曲线；无通道对照；校准只在同分布内验证 | STD scaling 校准；联合预测两个相关目标 | L1 |
| L67 | Data-Driven Approach With Uncertainty Quantification for Predicting Capacities and RUL | Liu et al. | 2020 | IEEE TIE | 10.1109/tie.2020.2973876 | 未核实 | 数据驱动 + UQ 预测容量与 RUL | 摘要级 | 未读全文 | 区间覆盖率报告口径 | L3 |
| L68 | Probabilistic RUL prediction without lifetime labels | Pan et al. | 2024 | Reliab Eng Syst Saf | 10.1016/j.ress.2024.110313 | 未核实 | 贝叶斯深度学习 + 随机过程融合，无需寿命标签 | 摘要不可得 | 仅题录级 | 无标签概率预测 | L4 |
| L69 | A Hierarchical Bayesian Framework for Model-based Prognostics | Jia et al. | 2026 | arXiv 2601.15942 | 未核实 | 层级贝叶斯 + 模型基预后 | 未读全文 | 未读全文 | 层级先验的写法 | L2 |

### G 组｜状态空间模型与序列骨架

| 编号 | 标题 | 作者 | 年 | venue | DOI | 代码 | 贡献一句话 | 实验协议 | 缺陷 | 可借鉴机制 | 等级 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L70 | SambaMixer: State of Health Prediction using Mamba State Space Models | Olalde-Verano et al. | 2024 | IEEE Access | 10.1109/access.2024.3524321 | 未核实 | Mamba 选择性状态空间做 SOH | 摘要级 | 未读全文 | SSM 作为长序列骨架 | L3 |
| L71 | DpMamba: a dual-path state space model for reliable RUL prediction | Li et al. | 2026 | Meas Sci Technol | 10.1088/1361-6501/ae9573 | 未核实 | 双路 SSM，针对容量再生与非单调波动 | 摘要级 | 未读全文 | 再生/波动建模 | L3 |
| L72 | U-H-Mamba: An Uncertainty-Aware Hierarchical State-Space Model for RUL | Wen et al. | 2026 | Energies 19(2):414 | 10.3390/en19020414 | 未核实 | 层级 SSM + 不确定性，实验室→真实数据迁移 | 摘要级 | 未读全文 | 层级 + UQ 组合 | L3 |
| L73 | Learning Li-ion battery health and degradation modes from data with aging-aware circuit models | Zhou et al. | 2025 | Appl Energy | 10.1016/j.apenergy.2025.126375 | 未核实 | 老化感知电路模型 + 数据学习，兼顾可解释与长期稳定 | 摘要级 | 未读全文 | 电路模型作归纳偏置 | L3 |
| L74 | Diagnosis and prognosis through re-evaluation and GPR of electrochemical model parameters | Streb et al. | 2023 | J Power Sources | 10.1016/j.jpowsour.2023.233686 | 未核实 | 重估电化学模型参数 + GPR 做诊断与预后 | 摘要级 | 未读全文 | 参数轨迹 → 预后 | L3 |

### H 组｜测量误差、可重复性与定义依赖

| 编号 | 标题 | 作者 | 年 | venue | DOI | 代码 | 贡献一句话 | 实验协议 | 缺陷 | 可借鉴机制 | 等级 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L75 | EIS error analysis and round robin on dummy cells and Li-ion batteries | Kasper et al. | 2022 | J Power Sources | 10.1016/j.jpowsour.2022.231407 | 未核实 | 三实验室 round-robin，微欧级阻抗的校准流程 | 摘要级 | 未读全文 | 测量不确定度量级 | L3 |
| L76 | EIS Accuracy and Repeatability Analysis of 10 kWh Automotive Battery Module | Kasper et al. | 2025 | Batteries | 10.3390/batteries11110389 | 未核实 | SOC 与温度变化在 <100 Hz 引入显著误差；夹具不当引入伪影 | 摘要级 | 未读全文 | 「参数变化是否超过测量噪声」的判据 | L3 |
| L77 | A study of the influence of measurement timescale on internal resistance characterisation | Barai et al. | 2018 | Sci Rep | 10.1038/s41598-017-18424-5 | 未核实 | 测量时间尺度决定内阻数值 | 摘要级 | 未读全文 | 内阻定义依赖时间尺度 | L3 |

---

## 3. 三个决定新颖性的问题：证据定位

> 完整论证与 gap 结构见 `GAP_ANALYSIS.md`。此处只给「有/无」与最强证据编号。

### Q① 有没有工作做过类似的「通道隔离对照」？

**有先例，但都不满足本项目的三个条件（同模型 / 同查询 / 跨工况统计）。**

- **最强的先例是 L13（Jones 2022）**：同一概率 ML 模型、同一批查询，只换状态表示，得到完整对照表——EIS only 20.7%、Protocol only 15.4%、EIS+Protocol 8.2%、ECM-R+Protocol 10.7%、ECM-ER+Protocol 8.4%、CVF+Protocol 8.8%、EIS+CVF+Protocol 6.7%。这在方法论上就是「通道隔离」。
- 但它**不是 RUL**（目标是下一循环容量），**不是跨工况留出**（随机/分层划分，无 LOGO），**没有电芯级配对统计**。
- 第二类先例是「无历史设定」：L14（Zhu 2022）只用充电后弛豫电压、L12（Zhang 2020）只用单次 EIS，都证明「不依赖循环历史也能估 SOH」。
- 第三类是融合而非隔离：L20、L21、L26、L28 把阻抗/IC 特征与其他特征拼接，无法把增益归因到通道。
- **结论**：方法学上的「换通道对照」已有人做过（SOH 任务）；**在 RUL 任务上、以工况留出为协议、带配对 bootstrap 的隔离对照，检索未见**。

### Q② 有没有解释过 RC 参数跨工况「方向翻转」的物理原因？

**有物理解释，但没有把它作为统计对象系统刻画，也没有与可辨识性合并。**

三条独立证据链：

1. **机制交叉**：L46（Kučinskis 2022）V 形 Arrhenius——低温 SEI 生长主导、高温镀锂主导，两种机制在某一温度交叉，故同一「老化速率」的符号可随温度翻转。L44（Spitthoff 2023）更直接：15 与 25 °C 的容量衰减速率相近，但退化模式「截然不同」。
2. **过程重叠与 SOC 依赖**：L17（Khan 2024）用 DRT 定量显示——SEI 峰在所有 SOC 下升高；charge-transfer 峰除 0% SOC 外变化很小；**扩散峰在 0–50% SOC 升高、在 75–100% SOC 下降**，作者归因于高 SOC 下 Li⁺ 迁移率与浓度梯度更均匀。这是「同一参数在不同工况下符号相反」的直接观测。
3. **参数族的工况依赖**：L14（Zhu 2022）显示主导退化因子随工况切换——0.25C 时 R₁（SEI）加速上升，0.5C/1C 时 R₀ 最大而 R₁/R₂ 相对更低（电解液干涸/接触损失），NCM 在 35/45 °C 时 R₂ 主导。同一 R 参数在不同工况下「谁在涨」完全不同。

**缺口**：没有工作把「参数–SOH 相关系数的符号」当作统计量，报告其跨工况分布、用二项检验判定一致性，并把翻转拆成「机制交叉 + 过程重叠 + 可辨识性退化」三个可分离的成分。这正是本项目 E5 结果（a1 19/23、c 18/23 存活，τ 与 a2 判负）可以被解释、而不是被当作失败的地方。

### Q③ 有没有用可辨识性理论分析 EIS / 弛豫参数？

**理论工具成熟，但从未接到「这些参数能否当 RUL 特征」这个问题上。**

- **结构可辨识性**：L29（Grandjean 2017）ECM 拓扑依赖；L35（Soleymani Aghdam 2021）证明 2-CPE 分数阶 ECM 在常用范围内全局结构可辨识——但作者明确写「结构可辨识是 noise-free 概念，实践可辨识性（激励选择、噪声）不在本文范围」。
- **实践可辨识性**：L30（Fisher/CRLB）、L31（SPM 参数分组）、L32（P2D）、L33（PET）、L34（ECM 拟合指南）、L37（低 SNR 下 LS 有偏、TLS 无偏）。
- **不适定反问题**：L38–L41、L43 一整条 DRT 线——DRT 之所以存在，正是因为「多 RC 分离」是病态的（L17 原文：矩阵条件数过高，Ag=Z 无唯一解，必须 Tikhonov + 正性约束 + L 曲线）。L43 还说明峰数需要人工交叉核对。
- **敏感性**：L36（Zhao & Howey 2016）显示 2-RC 的输出对 R_s 与 τ₂ 敏感，而 C₁、C₂、τ₁ 几乎不影响端电压——即**部分参数在数据里几乎不存在**。
- **实证**：L14 报告「SEI 电阻在部分循环未被识别」，尽管拟合 R² > 0.999——**拟合好 ≠ 参数可辨识**，这是本项目 B 问题（τ 被当作采样点索引解释）的文献对照。

**缺口**：没有工作把可辨识性分析（条件数 / CRLB / 参数相关矩阵）作为**筛选预测特征的前置门**，并检验「不可辨识的参数是否正是跨工况符号翻转的那一批」。这是一个可立即执行、且能解释既有负结果的分析。

---

## 4. 主题交叉索引

| 主题 | 编号 |
|---|---|
| EIS 作为观测通道 | L04–L07, L12, L13, L15, L16, L19–L25, L28 |
| 弛豫电压 / 脉冲 | L14, L17, L26, L63 |
| 可辨识性 / 不适定 | L29–L43 |
| 退化机理与模式 | L08, L15, L44–L54 |
| 跨工况 / 去工况 | L01, L09, L56–L62, L64 |
| 早期寿命 / 膝点 | L53–L55, L65, L66 |
| 概率预测 / UQ | L65–L69 |
| 状态空间 / 序列骨架 | L62, L63, L70–L74 |
| 测量误差 | L75–L77 |

---

## 5. 与本地 11 篇 PDF 的对应关系（已读全文的基线）

| 本地文件 | 编号 | 备注 |
|---|---|---|
| `batteries-12-00255-v2.pdf` | L01 | 作者已核实：Rizanov, Stoynova, Mihov（原 `idea_report.md` 标「作者待核实」） |
| `batteries-11-00031.pdf` | L02 | |
| `energies-17-04309-v2.pdf` | L03 | 全文版 `dvdq_review_full.txt`（128k 字符）为同一篇，未重复入表 |
| `mmc2.pdf` | L28 | 全文版 `ic_features_full.txt` 同篇 |
| `1-s2.0-S1572665723004873-main.pdf` | L44 | 全文版 `dqdv_aging_full.txt` 同篇 |
| `1-s2.0-S2590116823000450-main.pdf` | L55 | |
| `s42256-024-00972-x.pdf` | L56 | 全文版 `batlinet_full.txt` 同篇 |
| `3711896.3737372.pdf` | L57 | |
| `RUL-QMoE …pdf` | L65 | |
| `BatteryTTT …pdf` | L62 | |
| `Early_Prediction_of_Knee_Point …pdf` | L66 | 全文版 `knee_uq_full.txt` 同篇 |

> 本地 11 篇中，5 篇有更长的全文抽取版本，已用全文版阅读；矩阵中不重复计数。

---

## 6. 对本项目最有用的 5 条「可借鉴机制」

1. **通道消融表的形式**（L13 Table 1）：把「仅通道 / 仅历史 / 通道+历史 / 通道的 ECM 参数化 / 通道+历史描述量」放进同一张表、同一模型、同一指标。本项目 E1 的表结构可直接对标，并补上 L13 缺的跨工况划分与配对 CI。
2. **「拟合好 ≠ 参数可辨识」的实证写法**（L14：R²>0.999 但 SEI 电阻未被识别；L36：τ₁ 对输出几乎无影响）。这是把 B 问题从「怀疑」升级为「可检验命题」的现成范式。
3. **VPC 作为统计单位的判据**（L64：74.5% 方差来自工况组）。可直接回答「该按工况还是按电芯做统计单位」——不是口味问题，而是可算的量。
4. **DRT 的「峰位=τ、峰面积=R」映射及其人工裁定环节**（L43、L17）：说明 2-RC 的 τ 本身是**分辨率受限的估计量**，跨工况比较 τ 时必须先报告分辨率与重叠情况。
5. **非交叉分位数 + 校准**（L65、L66）：概率预测的两种正交做法——约束分位数单调性 vs 事后 STD scaling；本项目若要补 UQ，应先做覆盖率报告再做校准。

---

## 7. 未达标项与待核实清单

### 7.1 未达标项（如实记录）

- **全文精读 17 篇，未达 20 篇目标，差 3 篇。**
  - 客观约束：本地 11 篇 PDF 中 5 篇有重复的全文抽取版（净 11 篇）；新增可开放获取的文献以 arXiv / Nature Communications 为主，Elsevier 与 MDPI 正文不可直连（403），可全文精读的候选池实际约 22 篇，其中 6 篇正文超过 45k 字符。
  - 主观取舍：把预算优先给了「决定新颖性判定」的 3 个问题（G1/G2/G3）与本地 11 篇的完整核对，长综述类只做主体精读。
  - **不做的事**：不把只读了 25%–45% 的条目改标 L1 来凑数。
- **补齐顺序（按对本项目的边际价值，含当前进度）**：
  1. **L18 Paulson 2023**（已读 45%，缺结果后半与讨论）——决定「多描述量 vs 标量 SOH」的论证强度；
  2. **L63 TIDSIT**（已读 25%，缺不规则采样实验细节）——G5 的唯一直接对标；
  3. **L43 Iurilli 2022 / EIS2MOD**（已读 34%，缺跨温度验证与误差分解）——Q③ 的工程侧证据；
  4. L37 Balasingam 2021（已读 18%，缺 TLS/Kalman 结果）——G3 的偏差定量；
  5. L12 Zhang 2020（已读 30%，缺 RUL 部分的方法与电芯数）——需核实「4 个电芯」这一二手说法。
- 补齐上述 3 篇即可达到 20 篇；预计每篇需完整读 25k–30k 字符正文。

### 7.2 待核实

- [ ] L15 / L16 / L19 / L25 / L38 / L39 / L42 / L48 / L51 / L59 / L60 / L67 / L68：OpenAlex 无摘要字段，仅有题录。若需引用其数字，必须先取得全文。
- [ ] L12 的 RUL 部分电芯数（二手描述为 4 个电芯，未见原文表格，未写入矩阵）。
- [ ] L57 BatteryLife 的「18 数据集」与「16 数据集」两种表述：正文摘要写 16 datasets，表格列 16 行 + BatteryLife 自身；引用时以「16 个来源数据集」为准。
- [ ] 各条「代码」列凡标「未核实」，均未确认公开仓库；不得在论文中声称「作者开源」。

---

*本文件仅由 A1 维护。任何数字改动须同时更新 §7.2 的核实状态。*
