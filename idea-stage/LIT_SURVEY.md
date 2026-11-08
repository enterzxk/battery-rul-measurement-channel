# LIT_SURVEY — 「标签预算（label budget）」文献综述

> 执行者：Phase 1 / research-lit 子代理（独立上下文，未参与主代理实验）
> 创建：2026-11-08
> 项目根：E:/桌面/rul/rul_v4_20261107
> 上游必读：AGENTS.md §1、docs/autonomous_research/LITERATURE_MATRIX.md（L01–L77）、LIMITATIONS_MINING.md、GAP_ANALYSIS.md（G1–G6）、PIVOT_OPTIONS.md（D2）、research-wiki/claims/claim-label-budget.md
> 本文件只写自己名下的文件；不修改 docs/ 下任何历史结果，不修改 LITERATURE_MATRIX.md。

---

## 0. 一页结论

**判定：在「跨工况电池 RUL」这个任务上，没有任何一篇已发表工作把「目标工况的标签预算曲线」当作研究对象。但「k 作为实验设置被扫描」这件事已经存在，且比预想的多——包括顶刊上的一条源侧参照集曲线（BatLiNet Fig. 5b，见 §C.1-⑥）。**

四条最接近的，按接近程度排序：

| 排序 | 工作 | 它做了什么 | 它没做什么 | 对我们意味着什么 |
|---:|---|---|---|---|
| 1 | **Zhao 2026, Applied and Computational Engineering**（B02，全文可读） | 跨数据集循环寿命，k = 5 / 10 / 20 颗目标电芯做微调，明确写「the effect saturates quickly, so large labeling budgets are unnecessary」 | 3 个 k 值、单一数据对、无置信区间、无逐工况配对检验、任务是标量循环寿命而非 RUL 轨迹 | **这是唯一一篇把 k 扫成「预算」并下结论的**。必须引用并正面对比，不能装作不存在 |
| 2 | **Zhou et al. 2021, ACM UbiComp/ISWC Adjunct**（B01，仅摘要） | 「various few-shot experiment settings」下跨数据集容量估计，10–30% 增益 | 对象是 Semi-JDOT 算法，k 是稳健性检查；ACM 403，全文不可得 | 说明「扫 k」的动机在 2021 年就有了，但停在算法论文的附录里 |
| 3 | **Xia 2026, Chalmers 硕士论文**（B03，全文可读） | 跨工况 RUL + 微调迁移；RQ3 直接问「limited target condition data 够不够」；21 次随机目标域划分，ΔMAE 从 −32.9% 到 +16.2%，均值 +0.5%，12/21 正迁移 | **变的是「选哪些电芯」，不是「选几颗」**；灰文献、非同行评审 | 它给出的正是我们 k=8 不显著（p=0.196）的同构现象：小 k 下迁移收益方差极大 |
| 4 | **Rieger et al. 2023, Digital Discovery**（B04）+ **Dechent et al. 2021, Batteries & Supercaps**（B05） | 域内训练电池数的学习曲线（「as few as six batteries」）；群体变异度所需的每工况电芯数（9/11/13） | 都不是跨工况、不是目标工况标签 | 证明「多少颗电芯才够」这个问题在电池界被问过，但问的是**别的量** |

**一句话**：文献里存在「k 的扫描」、存在「k 的结论」、存在「多少电芯才够」、也存在「源侧参照集大小的曲线」，但不存在「**目标工况**标签数的预算曲线（带不确定性与逐工况配对统计）」。

**两个必须提前准备的说法**：

1. **Zhao 2026（B02）** 标题里就有 Few-Shot，正文里就有 labeling budgets，且结论是「5 颗就饱和」。若审稿人拿它来质疑，我们的主张必须收窄到三件它没有的东西：**电芯不相交的同工况标签、逐工况配对统计、k=0 锚点**。
2. **BatLiNet（B37）Fig. 5b** 已经画过「参照电芯数 1–64 vs 误差（n=8 trials）」。必须主动区分：那是**源侧、带标签的推理参照集**，落点是推理吞吐；我们扫的是**目标工况的标注预算**。详见 §C.1-⑥ 与 §C.4。

---

## A. 检索式与数据源（可复现）

### A.1 数据源与可达性实测（2026-11-08 实测，非推测）

| 源 | 端点 | 实测状态 | 用途 |
|---|---|---|---|
| OpenAlex Works API | api.openalex.org/works | 可用（第一、二轮共 634 条去重记录）；第三轮起持续 **429**（当日额度耗尽） | 主检索、摘要重建（abstract_inverted_index） |
| Crossref REST API | api.crossref.org/works | 可用，未限流 | **题录核实**（作者/年/venue/DOI），单篇 DOI 查询 |
| arXiv Atom API | export.arxiv.org/api/query | 可用 | 预印本检索、arXiv ID 核实 |
| arXiv PDF | arxiv.org/pdf/{id} | 可直连 | 全文精读 |
| Semantic Scholar Graph API | api.semanticscholar.org | 批量 429；单篇 200 但 Elsevier 条目**无摘要字段** | 摘要补充（失败为主） |
| ACM DL | dl.acm.org | **403**（Zhou 2021 全文不可得） | — |
| IEEE Xplore | ieeexplore.ieee.org | **202 / 空响应**（全部 IEEE 条目仅摘要或仅题录） | — |
| Elsevier / ScienceDirect / Cell Press | sciencedirect.com, cell.com | 未尝试绕过（按任务约束）；Crossref / S2 亦无摘要 | — |
| MDPI | mdpi.com | 403（按任务约束不绕过） | — |
| EWA Publishing（ACE） | ace.ewapub.com | 可用，PDF 可下 | Zhao 2026 全文 |
| Chalmers ODR | odr.chalmers.se | 可用，PDF 可下 | Xia 2026 全文 |
| DTU Orbit | backend.orbit.dtu.dk | 可用，PDF 可下 | Rieger 2023 全文 |
| web_fetch 工具 | — | **已知损坏（404），全程未使用** | — |

> 说明：所有网络请求通过 Python requests（trust_env=False，因本机环境变量里的代理不可用会导致 ProxyError；PowerShell Invoke-RestMethod 亦可）。

### A.2 实际执行的检索式

**（1）OpenAlex 第一轮 —— 7 组 25 条查询**（search= 全文检索，按 relevance 排序，每条取 25 条）

| 组 | 查询串 |
|---|---|
| D1 few-shot | few-shot battery state of health estimation / few-shot remaining useful life lithium battery / meta-learning battery state of health few-shot / k-shot calibration battery state of health |
| D2 域适配 | domain adaptation battery state of health operating condition / transfer learning battery remaining useful life operating conditions / unsupervised domain adaptation battery capacity estimation / domain generalization battery health estimation |
| D3 主动学习/标签高效 | active learning battery state of health / label-efficient battery health estimation / data-efficient battery lifetime prediction / sample selection battery aging experiment design |
| D4 样本复杂度 | sample size learning curve remaining useful life prediction / training data size battery cycle life prediction accuracy / data requirement machine learning battery lifetime prediction |
| D5 校准/偏差修正 | transfer calibration regression model new domain few labels / bias correction pretrained model domain shift regression / few-shot regression adaptation calibration / test-time adaptation regression distribution shift |
| D6 基准 | battery life prediction benchmark cross-condition / cross-domain battery state of health benchmark / generalization battery degradation dataset benchmark |
| D7 ML 通用 | learning curve sample efficiency transfer learning regression / how many labels fine-tuning target domain / sample complexity domain adaptation labeled target samples |

→ 去重后 **543** 条。

**（2）OpenAlex 第二轮 —— 15 条补充查询**（关键词：number of labeled samples、effect of training data size、learning curve ... number of cells、shots、BatteryLife benchmark、calibration transfer ... limited target labels、theory of learning from different domains labeled target samples bound 等）→ 新增 **91** 条，合计 **634**。

**（3）arXiv —— 8 条查询，每条 40 条**

all:"battery" AND all:"few-shot" · all:"battery" AND all:"label" AND all:"budget" · all:"battery" AND all:"transfer learning" AND all:"state of health" · all:"battery" AND all:"sample size" · all:"battery" AND all:"active learning" · all:"few-shot regression" · all:"label budget" · all:"learning curve" AND all:"transfer"

→ **159** 条，其中电池相关 27 条。

**（4）Crossref —— 10 条 query.bibliographic 查询 + 约 30 条单篇题录核实**

few-shot battery state of health estimation · few-shot battery remaining useful life · label-efficient battery state of health · active learning battery state of health estimation · sample size battery degradation test cells required · number of labeled samples transfer learning battery · domain adaptation battery state of health limited target labels · semi-supervised battery state of health few labels · learning curve data efficiency battery lifetime prediction · k-shot battery state of health

**（5）全文级检索（对已下载 PDF 做正则）**：few-shot|shot|k-shot|label|budget|number of (training )?cells|reference cell —— 用于判定基准论文**是否真的报过少标签结果**（§C.1 的负证据即由此产生）。

### A.3 筛选流程与计数

| 步骤 | 数量 |
|---|---:|
| OpenAlex 去重记录 | 634 |
| 其中题名或摘要含电池相关词 | 372 |
| 进入人工筛读（打印摘要） | ~60 |
| 进入主表（§B） | **45** |
| 取得并实际阅读全文 | **7**（Zhao 2026、Dechent 2021、Rieger 2023、Xia 2026、Tan 2025、Zhang 2025、Filgueira 2026） |
| 仅摘要 | 17 |
| 仅题录 | 21 |

### A.4 复现材料

原始检索结果与脚本（均在本机，可逐行重跑）：

| 文件 | 内容 |
|---|---|
| idea-stage/_lit_oa.py | 第一轮 OpenAlex 25 条查询 → %TEMP%/lit_survey/openalex.json |
| idea-stage/_lit_oa2.py | 第二轮 15 条 OpenAlex + 8 条 arXiv → arxiv.json |
| idea-stage/_lit_screen.py | 相关度打分与筛选 → screened.json |
| idea-stage/_lit_crossref.py, _lit_cr3.py | Crossref 题录核实与检索 |
| idea-stage/_lit_fetch*.py | PDF 下载与 pypdf 5.9.0 抽文本 |
| %TEMP%/lit_survey/*.txt | 7 篇全文抽取文本（19k–160k 字符/篇） |

> 环境：Python 3.8.7、requests 2.32.4、pypdf 5.9.0。

### A.5 检索的已知局限（必须先声明，否则后面的「没有」会被误读）

1. **OpenAlex 第三轮起 429**，导致最后 10 条「最小数据量 / HUST / 标注成本」类查询**未执行**。这 10 条恰好是最可能命中「标签预算」的查询方向，**是本综述最大的覆盖缺口**。
2. **IEEE 全部不可读正文**（202），Elsevier 连摘要都拿不到。因此 21 条「仅题录」的条目里，**不能排除**有工作做了 k 扫描——本文件的「没有」只对**已读到的证据**成立。
3. **ACM 403** 使 Zhou 2021 停在摘要级。
4. 检索语种为英文；未检索中文文献（CNKI / 万方不可达）。中文期刊里可能有「小样本」类工作未被覆盖。
5. web_fetch 损坏，所有网页内容均通过 requests 直接取，未做 JS 渲染页面（个别出版商页面因此不可读）。

---

## B. 主表（45 条）

> **阅读等级**（沿用 LITERATURE_MATRIX.md §0 口径，本文件独立计数）：
> **L1** 全文通读 ≥85% ｜ **L2** 定向精读关键节（方法/结果/讨论）｜ **L3** 仅摘要 ｜ **L4** 仅题录（无摘要）
> **关系**：**直接研究** = 把标签数 k 当自变量扫描并据此下结论；**间接相关** = 用了少样本/迁移/半监督，但 k 不是研究对象；**仅背景** = 提供方法学或统计框架。
> 凡标 L4 的条目，**不得引用其任何数字或结论**。

### B-A 组｜把 k 当自变量的实验（本综述的核心）

| 编号 | 标题 | 作者 | 年 | venue | DOI | 链接 | 与标签预算的关系 | 等级 |
|---|---|---|---|---|---|---|---|---|
| B01 | Few-Shot Cross Domain Battery Capacity Estimation | Zhou Z., Ran A., Chen S., Wei G., Sun H., Zhang X. | 2021 | Adjunct Proc. ACM UbiComp/ISWC '21 | 10.1145/3460418.3480409 | https://doi.org/10.1145/3460418.3480409 | **直接研究**（various few-shot experiment settings；对象是 Semi-JDOT 算法） | L3 |
| B02 | When Labels Shift: Few-Shot Fine-Tuning Versus Unsupervised Domain Adaptation for Cross-Dataset Battery Cycle-Life Prediction | Zhao P. | 2026 | Applied and Computational Engineering（CONF-MLA 2026 会议论文集） | 10.54254/2755-2721/2026.LD37070 | https://doi.org/10.54254/2755-2721/2026.LD37070 | **直接研究**（k = 5/10/20 目标电芯；结论「5 颗即饱和」） | L2 |
| B03 | Transfer Learning for Battery Health Prediction under Varying Operating Conditions | Xia C. | 2026 | Chalmers 硕士论文（灰文献，非同行评审） | 无 | https://odr.chalmers.se/bitstreams/04a5c071-9950-4f5c-ab89-9be5e7ad5564/download | **直接研究**（RQ3 = 有限目标数据是否够；变「选哪些」而非「选几颗」） | L2 |
| B04 | Uncertainty-aware and explainable machine learning for early prediction of battery degradation trajectory | Rieger L., Flores E., Nielsen K., Norby P., Ayerbe E., Winther O., Vegge T., Bhowmik A. | 2023 | Digital Discovery (RSC) | 10.1039/d2dd00067a | https://doi.org/10.1039/d2dd00067a | 间接相关（**域内**训练电池数的学习曲线，as few as six batteries） | L2 |
| B05 | Estimation of Li-Ion Degradation Test Sample Sizes Required to Understand Cell-to-Cell Variability | Dechent P., Greenbank S., Hildenbrand F., Jbabdi S., Sauer D.U., Howey D.A. | 2021 | Batteries & Supercaps | 10.1002/batt.202100148 | https://doi.org/10.1002/batt.202100148（预印本 arXiv:2107.07881） | 间接相关（每工况最少 9/11/13 颗，用于估**群体变异度**） | L2 |
| B06 | Automatic method for the estimation of li-ion degradation test sample sizes required to understand cell-to-cell variability | Strange C., Allerhand M., Dechent P., dos Reis G. | 2022 | Energy and AI | 10.1016/j.egyai.2022.100174 | https://doi.org/10.1016/j.egyai.2022.100174 | 间接相关（B05 的自动化版本） | L4 |

### B-B 组｜少样本 / 元学习（k 以「目标电芯的循环数」计，不是电芯数）

| 编号 | 标题 | 作者 | 年 | venue | DOI | 链接 | 与标签预算的关系 | 等级 |
|---|---|---|---|---|---|---|---|---|
| B07 | A Meta-Learning Method for Few-Shot Multidomain State-of-Health Estimation of Lithium-Ion Batteries | Zhao X., Wang Z., Han T., Yang W., Gu F., Ball A.D. | 2024（在线）/2025（卷期） | IEEE Trans. Transportation Electrification | 10.1109/tte.2024.3470551 | https://doi.org/10.1109/tte.2024.3470551 | 间接相关（only using six cycles from one target battery） | L3 |
| B08 | Multisource Domain Metalearning Network for Battery State-of-Health Estimation Under Multitarget Working Conditions | Miao M., Xiao C., Yu J. | 2025 | IEEE Trans. Power Electronics | 10.1109/tpel.2025.3538469 | https://doi.org/10.1109/tpel.2025.3538469 | 间接相关（多目标工况；k = 任务数） | L3 |
| B09 | Domain Similarity Meta-Learning for Lithium-Ion Battery State-of-Health Estimation of Spacecraft Systems | Wu W., Fu H., Cui K., Liu Z., Yang D., Shi D. | 2025 | IEEE Trans. Aerospace and Electronic Systems | 10.1109/taes.2025.3540806 | https://doi.org/10.1109/taes.2025.3540806 | 间接相关 | L3 |
| B10 | Few-Shot Battery State-of-Health Estimation via Meta-Learning and Cross-Domain Adaptation | Zhang S., Shen W. | 2026 | 2026 IEEE PES International Meeting | 10.1109/pesim67009.2026.11438910 | https://doi.org/10.1109/pesim67009.2026.11438910 | 间接相关 | L4 |
| B11 | Enabling Accurate Battery Remaining Useful Life Prediction and Through-Life Degradation Mapping With Scarce End-of-Life Samples | Guo R., Zhang K., Ke S., He S., Tian J., Shen W. | 2026 | IEEE Trans. Industrial Informatics | 10.1109/tii.2026.3658872 | https://doi.org/10.1109/tii.2026.3658872 | 间接相关（scarce EOL samples，伪监督扩样） | L3 |
| B12 | PLT-GRU: physics-informed lightweight Transformer-GRU algorithm for few-shot battery state-of-health estimation | Yin Y., Gao Z., Huang Y., Liu Q. | 2025 | Measurement Science and Technology | 10.1088/1361-6501/ae0495 | https://doi.org/10.1088/1361-6501/ae0495 | 间接相关 | L3 |
| B13 | State of health estimation for lithium-ion batteries on few-shot learning | Zhang S., Liu Z., Su H. | 2023 | Energy | 10.1016/j.energy.2023.126726 | https://doi.org/10.1016/j.energy.2023.126726 | 间接相关 | L4 |
| B14 | Semi-supervised learning for explainable few-shot battery lifetime prediction | Guo N., Chen S., Tao J., Liu Y., Wan J., Li X. | 2024 | Joule | 10.1016/j.joule.2024.02.020 | https://doi.org/10.1016/j.joule.2024.02.020 | 间接相关（PBCT：无标签 + 少标签） | L4 |
| B15 | Battery State of health estimation with fewer labelled data: a semi-supervised approach | Tian J., Xiong R. | 2023 | IEEE CIEEC 2023 | 10.1109/cieec58067.2023.10165770 | https://doi.org/10.1109/cieec58067.2023.10165770 | 间接相关 | L3 |
| B16 | Online state-of-health prediction of lithium-ion batteries with limited labeled data | Yu J., Yang J.R., Wu Y., Tang D., Dai J. | 2020 | International Journal of Energy Research | 10.1002/er.5750 | https://doi.org/10.1002/er.5750 | 间接相关 | L3 |
| B17 | Early Prediction of Lithium-Ion Batteries Lifetime via Few-Shot Learning | Sui X., He S., Zheng Y., Che Y., Teodorescu R. | 2023 | IECON 2023 | 10.1109/iecon51785.2023.10312622 | https://doi.org/10.1109/iecon51785.2023.10312622 | 间接相关（only 6 cycles） | L3 |
| B18 | Battery Life Prediction Under Few-Shot Conditions | Wan J. | 2024 | ECS Meeting Abstracts | 10.1149/ma2024-023386mtgabs | https://doi.org/10.1149/ma2024-023386mtgabs | 间接相关（B14 的会议摘要版，PBCT） | L3 |
| B19 | Battery health prediction under data scarcity: A cross-domain physics-informed 5-shot framework with GRU-Transformer | （Crossref 未返回作者列表，未核实） | 2026 | Applied Energy | 10.1016/j.apenergy.2025.127012 | https://doi.org/10.1016/j.apenergy.2025.127012 | 间接相关（固定 5-shot） | L4 |
| B20 | Empowering knowledge-guided intelligence for accurate and robust few-shot lithium-ion battery state of health estimation | （未核实） | 2026 | eTransportation | 10.1016/j.etran.2026.100582 | https://doi.org/10.1016/j.etran.2026.100582 | 间接相关 | L4 |
| B21 | Enhanced few-shot state-of-health estimation for lithium-ion batteries via Masked Autoencoder | （未核实） | 2025 | Energy | 10.1016/j.energy.2025.138263 | https://doi.org/10.1016/j.energy.2025.138263 | 间接相关 | L4 |
| B22 | A survey on few-shot learning for remaining useful life prediction | （未核实） | 2025 | Reliability Engineering & System Safety | 10.1016/j.ress.2025.110850 | https://doi.org/10.1016/j.ress.2025.110850 | 仅背景（该领域已有少样本 RUL 综述） | L4 |

### B-C 组｜域适配 / 迁移学习（k=0 或未扫描）

| 编号 | 标题 | 作者 | 年 | venue | DOI | 链接 | 与标签预算的关系 | 等级 |
|---|---|---|---|---|---|---|---|---|
| B23 | Multisource Weighted Domain Adaptation for Cross-Conditions Capacity Estimation of Lithium-Ion Batteries | Hua H., Wu L. | 2024 | IEEE Trans. Power Electronics | 10.1109/tpel.2024.3398063 | https://doi.org/10.1109/tpel.2024.3398063 | 仅背景（无监督，k=0 一侧的强基线） | L3 |
| B24 | Predictive Battery Health Management With Transfer Learning and Online Model Correction | Che Y., Deng Z., Lin X., Hu L., Hu X. | 2021 | IEEE Trans. Vehicular Technology | 10.1109/tvt.2021.3055811 | https://doi.org/10.1109/tvt.2021.3055811 | 仅背景（在线微调，未报 k） | L3 |
| B25 | Capacity Estimation of Cross Domain Lithium-ion Battery Based on Semi-Supervised Transfer Learning | Zhang Y., Wang Y., Huang D. | 2024 | IEEE CIEEC 2024 | 10.1109/cieec60922.2024.10583610 | https://doi.org/10.1109/cieec60922.2024.10583610 | 间接相关（trace amount of labeled data） | L3 |
| B26 | Investigating explainable transfer learning for battery lifetime prediction under state transitions | Lin T., Chen S., Harris S.J., Zhao T.S., Liu Y., Wan J. | 2024 | eScience | 10.1016/j.esci.2024.100280 | https://doi.org/10.1016/j.esci.2024.100280 | 间接相关（目标域信息量未扫描；RMSE 降 41%） | L3 |
| B27 | A Transferable Prediction Approach for the Remaining Useful Life of Lithium-Ion Batteries Based on Small Samples | Qin H., Fan X., Fan Y., Wang R., Shang Q., Zhang D. | 2023 | Applied Sciences | 10.3390/app13148498 | https://doi.org/10.3390/app13148498 | 间接相关（fewer data samples，非 k 扫描） | L3 |
| B28 | Rapid health estimation of in-service battery packs based on limited labels and domain adaptation | （未核实） | 2024 | Journal of Energy Chemistry | 10.1016/j.jechem.2023.10.056 | https://doi.org/10.1016/j.jechem.2023.10.056 | 间接相关（题名即 limited labels + DA） | L4 |
| B29 | Physics-aligned transfer learning for cross-condition remaining useful life prediction | （未核实） | 2026 | Sustainable Energy Technologies and Assessments | 10.1016/j.seta.2026.105533 | https://doi.org/10.1016/j.seta.2026.105533 | 间接相关（跨倍率/跨批次 RUL） | L4 |
| B30 | A label-free battery state of health estimation method based on adversarial multi-domain adaptation | （未核实） | 2024 | Energy | 10.1016/j.energy.2024.132881 | https://doi.org/10.1016/j.energy.2024.132881 | 仅背景（k=0 一端） | L4 |

### B-D 组｜半监督 / 现场数据 / 标签高效

| 编号 | 标题 | 作者 | 年 | venue | DOI | 链接 | 与标签预算的关系 | 等级 |
|---|---|---|---|---|---|---|---|---|
| B31 | Semi-supervised battery state of health estimation for field applications | Hadzalic N., Hamar J.C., Fischer M., Erhard S.V., Schmidt J.P. | 2025 | Energy and AI | 10.1016/j.egyai.2025.100575 | https://doi.org/10.1016/j.egyai.2025.100575 | 间接相关（3000 台 BMW i3；incrementally incorporating newly available labeled data） | L3 |
| B32 | Adaptive State-of-Health Estimation for Lithium-Ion Battery With Partially Unlabeled and Incomplete Charge Curves | Liu X., Hu Z., Mao L., Xie M. | 2024 | IEEE Trans. Transportation Electrification | 10.1109/tte.2024.3500072 | https://doi.org/10.1109/tte.2024.3500072 | 间接相关（顺序更新，非 k 扫描） | L3 |
| B33 | Increasing generalization capability of battery health estimation using continual learning | Che Y., Zheng Y., Onori S., Hu X., Teodorescu R. | 2023 | Cell Reports Physical Science | 10.1016/j.xcrp.2023.101743 | https://doi.org/10.1016/j.xcrp.2023.101743 | 仅背景（矩阵 L58 已收，L3） | L4 |
| B34 | Adapting Amidst Degradation: Cross Domain Li-ion Battery Health Estimation via Physics-Guided Test-Time Training | Feng Y., Hu G., Li X., Zhang Z. | 2024 | arXiv:2402.00068 | 10.48550/arXiv.2402.00068 | https://arxiv.org/abs/2402.00068 | 仅背景（单样本 TTT，k=1 条无标签样本） | L1（矩阵已精读） |
| B35 | Conformalized Transfer Learning for Li-ion Battery State of Health Forecasting under Manufacturing and Usage Variability | Filgueira da Silva S., Ozkan M.F., El Idrissi F., Canova M. | 2026 | arXiv:2603.24475（预印本） | 10.48550/arXiv.2603.24475 | https://arxiv.org/abs/2603.24475 | 间接相关（校准集固定 10 颗源域电芯；**未扫 k**） | L2 |

### B-E 组｜基准与数据集（「有没有报少标签结果」的负证据来源）

| 编号 | 标题 | 作者 | 年 | venue | DOI | 链接 | 与标签预算的关系 | 等级 |
|---|---|---|---|---|---|---|---|---|
| B36 | BatteryLife: A Comprehensive Dataset and Benchmark for Battery Life Prediction | Tan R., Hong W., Tang J., Lu X., Ma R., Zheng S., Li H., Huang J., Zhang Z. | 2025 | KDD '25 | 10.1145/3711896.3737372 | https://doi.org/10.1145/3711896.3737372 | 仅背景（**全文无 few-shot / k-shot 实验**，见 §C.1-⑤） | L2 |
| B37 | Battery lifetime prediction across diverse ageing conditions with inter-cell deep learning (BatLiNet) | Zhang H., Li Y., Zheng S., Lu Z., Gui X., Xu B., Bian Y. | 2025 | Nature Machine Intelligence | 10.1038/s42256-024-00972-x | https://doi.org/10.1038/s42256-024-00972-x | 仅背景（推理需**带标签**参照电芯；Fig.5b 扫了参照电芯数 1–64（n=8 trials），但参照集来自**训练集**、落点是推理加速） | L2 |
| B38 | Data-driven prediction of battery cycle life before capacity degradation | Severson K.A., Attia P.M., Jin N., Perkins N., Jiang B., Yang Z., et al. | 2019 | Nature Energy | 10.1038/s41560-019-0356-8 | https://doi.org/10.1038/s41560-019-0356-8 | 仅背景（数据源） | L4 |
| B39 | Closed-loop optimization of fast-charging protocols for batteries with machine learning | Attia P.M., Grover A., Jin N., Severson K.A., Markov T.M., et al. | 2020 | Nature | 10.1038/s41586-020-1994-5 | https://doi.org/10.1038/s41586-020-1994-5 | 仅背景（数据源） | L4 |
| B40 | Machine learning pipeline for battery state-of-health estimation | Roman D., Saxena S., Robu V., Pecht M., Flynn D. | 2021 | Nature Machine Intelligence | 10.1038/s42256-021-00312-3 | https://doi.org/10.1038/s42256-021-00312-3 | 仅背景（管线范式） | L4 |

### B-F 组｜ML 方法学背景（非电池，用于定义「标签预算」这个概念从哪来）

| 编号 | 标题 | 作者 | 年 | venue | DOI | 链接 | 与标签预算的关系 | 等级 |
|---|---|---|---|---|---|---|---|---|
| B41 | A theory of learning from different domains | Ben-David S., Blitzer J., Crammer K., Kulesza A., Pereira F. | 2010 | Machine Learning 79:151–175 | 10.1007/s10994-009-5152-4 | https://doi.org/10.1007/s10994-009-5152-4 | 仅背景（**带目标域标签的泛化界**——标签预算的理论出处） | L4 |
| B42 | Model-Agnostic Meta-Learning for Fast Adaptation of Deep Networks | Finn C., Abbeel P., Levine S. | 2017 | ICML 2017 / arXiv:1703.03400 | 10.48550/arXiv.1703.03400 | https://arxiv.org/abs/1703.03400 | 仅背景（k-shot 协议的标准来源） | L4 |
| B43 | Accurate Uncertainties for Deep Learning Using Calibrated Regression | Kuleshov V., Fenner N., Ermon S. | 2018 | ICML 2018 / arXiv:1807.00263 | 10.48550/arXiv.1807.00263 | https://arxiv.org/abs/1807.00263 | 仅背景（回归器校准；与我们「仿射校准」是不同意义上的 calibration） | L4 |
| B44 | Revisiting Unreasonable Effectiveness of Data in Deep Learning Era | Sun C., Shrivastava A., Singh S., Gupta A. | 2017 | ICCV 2017 | 10.1109/iccv.2017.97 | https://doi.org/10.1109/iccv.2017.97 | 仅背景（数据量-精度关系的经典表述） | L4 |
| B45 | Bayesian hierarchical modelling for battery lifetime early prediction | Zhou Z., Howey D.A. | 2022 | arXiv:2211.05697 | 10.48550/arXiv.2211.05697 | https://arxiv.org/abs/2211.05697 | 仅背景（VPC=74.5%，工况层方差；矩阵 L64 已收） | L1（矩阵已精读） |

---

## C. 关键判定

### C.1 有没有工作把「标签预算曲线」作为研究对象？

**答：没有。但「k 被扫描」这件事有 3 篇，必须逐条交代。**

**① Zhao 2026（B02）—— 唯一一篇把 k 扫成「预算」并给出预算结论的**

原文（§3.3，PDF p.91）：

> Target cells are ordered by a fixed seed, the first k cells are used for fine-tuning and all remaining cells for testing, with strict isolation. A from-scratch control trained on the same k cells separates the transfer benefit from the value of the target data itself. **Three adaptation budgets are compared, k = 5, 10 and 20 target cells, corresponding to about 12%, 24% and 49% of the Stanford fleet**, the reverse direction uses k up to 40 because the Tongji fleet is larger.

原文（§4 Discussion）：

> Five labeled target cells reduce the error by 81%, the from-scratch controls confirm that the gain originates in the source-domain priors, and **the effect saturates quickly, so large labeling budgets are unnecessary**.

它确实做了「标签预算」的因果操纵（k 是自变量），也下了「预算结论」。**但它是 3 个点、单一数据对（Stanford 41 颗 ↔ Tongji 130 颗）、无置信区间、无逐工况配对检验**，且：

- 任务是**标量循环寿命**（cycle life），不是 RUL 轨迹；
- 「预算」以**目标车队百分比**表述（12%/24%/49%），不是绝对标签数，跨数据集不可迁移；
- 表 1 只报了 k=5 这一档的完整结果（98.3 cycles），k=10/20 的数字**未在正文表中给出**（正文只说进一步增加 k 收益递减）；
- 没有任何统计检验。

→ **判定：它是「标签预算」的雏形，不是「标签预算曲线」的研究。** 它回答「5 颗够不够」，没回答「到多少颗才可用、这个门槛有多确定」。

**② Zhou 2021（B01）—— 扫了 k，但 k 是附录里的稳健性检查**

摘要原文（OpenAlex 全文摘要，完整）：

> In this paper, we consider the scenario when only a few of labeled samples from the testing data set are available and formulate the battery estimation problem as a semi-supervised transfer learning problem. … The results show that the proposed approach outperforms existing supervised and semi-supervised methods by **10-30% under various few-shot experiment settings**.

→ k 是被操纵的，但研究对象是 **Semi-JDOT 算法**；k 只用来证明「我的方法在少标签下也稳」。ACM 403，**无法核实它扫了哪些 k、有没有画曲线**。

**③ Xia 2026（B03）—— 最接近「统计地看待有限标签」，但变的是「选哪些」**

RQ3 原文：

> RQ3: Can fine-tuning-based transfer learning improve cross-condition RUL prediction with limited target condition data?

结果（§5.6 + Table 5.3，21 次随机目标域划分）：

> positive transfer is observed in 12 out of 21 selections, but some selections produce substantial negative transfer. The ΔMAE values range from −32.9% to +16.2%, with a mean of only +0.5% across the seed sweep.

→ 它证明了**小 k 下迁移收益的方差极大、可为负**——这正是我们 k=8（p=0.196，5/11）那个不显著档的同构现象。但它固定目标支撑比例（target_support_ratio 0.67），**没有把 k 本身当自变量**。且是硕士论文（灰文献）。

**④ 「多少颗电芯才够」被问过，但问的是别的量**

- Dechent 2021（B05）：「ageing models with 1, 2 or 3 parameters respectively required data from at least **9, 11 or 13 cells** for a consistent fit」——目的是**估群体变异度**（hierarchical Bayesian 参数稳定性），不是模型在新工况上的精度。
- Rieger 2023（B04）：「We examine the accuracy of the model dependent on the number of batteries in the training dataset in Fig. 5. … the error decreases when we increase the size of the dataset but **rapidly levels off**, implying that the model can generalize … from a data set with **as few as six batteries**」——这是**域内**训练集规模的学习曲线，不是「目标工况标签」。
- Filgueira 2026（B35）：目标域有 limited number of labeled samples，但**校准集固定 10 颗源域电芯**，k 未被扫描。

**⑤ 两个最重要的基准：BatteryLife 完全没有少标签实验；BatLiNet 有源侧参照集扫描，但不是目标工况**

对本地 PDF 做全文正则检索（负证据，可复核）：

| 论文 | few-shot | k-shot | shot 出现处 | 结论 |
|---|---:|---:|---|---|
| BatteryLife（KDD'25，B36，73,843 字符） | 0 | 0 | 1 次，仅在参考文献标题 One-shot battery degradation trajectory prediction | **无少标签实验** |
| BatLiNet（Nat Mach Intell 2025，B37，39,235 字符） | 0 | 0 | 1 次，仅在参考文献标题 | **无 few-shot 实验**；但 reference cell 出现 18 次，Fig.5b **确实扫了参照电芯数 1–64**——见 §C.1-⑥ 的更正 |

BatteryLife 的跨域表（Table 6）只有 frozen / fine-tuning / domain adaptation 三种**范式**对比，**没有 k 这一维**（Zn-ion 行：Baseline MAPE 0.515±0.067、Frozen 3.153±0.187、FT 0.562±0.125、DA 0.752±0.102，已核原文 Table 6）。

**⑥ 必须更正的一处：BatLiNet 确实有一条「标签数 vs 误差」曲线（源侧）**

原文（Fig. 5 caption，已核 PDF）：

> "b, Effects of increasing reference cell numbers on predictions in the MIX-100 dataset, with eight random selections per case (n = 8 trials). Every box plot displays medians as centre lines…"

参照电芯是**带标签**的（fully cycled，寿命已知），Fig. 5b 扫了 1/2/4/8/16/32/64 颗，并给了 8 次随机选择的箱线图。**这在形式上就是一条「标签数–误差」曲线，而且带离散度。** 它与我们的问题有三点不同：

1. 参照电芯来自**训练集**（源域），不是目标工况；
2. 目标电芯始终**无标签**，所以它回答的是「推理时要备多少颗已知寿命的参照电芯」，不是「新工况要标多少颗」；
3. 论文的落点是**推理吞吐**（Fig. 5c，GTX 4090），不是标签成本。

→ **「扫参照集大小」这件事在顶刊上已经做过；「扫目标工况标签数并给出门槛」没有。** 这个区分必须写进 Related Work，否则会被一句话打回。

### C.2 若没有，最接近的是什么、差在哪

| 维度 | Zhao 2026（最接近） | Zhou 2021 | Xia 2026 | Rieger 2023 / Dechent 2021 | **本项目** |
|---|---|---|---|---|---|
| k 的语义 | 目标车队百分比（12/24/49%） | few-shot settings（未核实） | 固定支撑比例，变「选哪些」 | 域内训练电池数 / 每工况电芯数 | **目标工况内其他电芯的标签数（绝对颗数）** |
| 电芯是否不相交 | 是（strict isolation） | 未核实 | 是（cell-level split） | 是 | **是（strict；leaky 版差 49% vs 31%）** |
| k 的取值数 | 3（5/10/20） | 未核实 | 1（固定） | 曲线（2–8 / 1–20） | **4（0/8/16/32）** |
| 是否有 k=0 锚点 | 有（direct transfer 517） | 无 | 有（benchmark） | 不适用 | **有（LOGO 6.516）** |
| 统计单位 | 电芯（聚合 MAE） | 未核实 | 21 次随机划分 | 无检验 | **工况（n=11），逐工况配对** |
| 检验 | 无 | 无 | 计数（12/21） | 无 | **Wilcoxon 符号秩，9/11、11/11** |
| 任务 | 标量循环寿命 | 容量（SOH） | RUL | 寿命 / 参数稳定性 | **RUL（剩余体检次数）** |
| 结论形态 | 「5 颗即饱和」 | 「少标签下仍优 10–30%」 | 「小 k 下方差大、可为负」 | 「6–9 颗够」 | **「k=8 不显著，k=16 才显著」** |

**差在哪，一句话**：现有工作把 k 当**实验设置**（证明方法稳），我们把 k 当**被估计的量**（给出门槛与不确定性）；现有工作报「够/不够」，我们报「从哪一档开始显著、以及不显著的那一档长什么样」。

### C.3 我们的差异化（逐条对应文献，不写「首次」）

| # | 差异化点 | 文献对照（谁没有） | 可写进论文的措辞 |
|---:|---|---|---|
| 1 | **k 的单位 = 目标工况内其他电芯的标签**（电芯不相交），回答「新电芯进厂、工况已知、能测几颗」 | Zhao 2026 用「车队百分比」；B07/B17 用「目标电芯自身循环数」；B03 固定比例 | we vary the number of labeled cells drawn from *other cells in the same target condition*, holding the evaluation cells fully disjoint |
| 2 | **k=0 锚点**（LOGO 6.516），使增益可归因 | Zhou 2021 未报 k=0；B07 系列不报 | the k=0 anchor is the leave-one-group-out model, so every gain is measured against zero-target-label transfer |
| 3 | **逐工况配对统计**（Wilcoxon，9/11、11/11） | Zhao 2026 无检验；B03 只有 12/21 计数 | per-condition paired differences, not a pooled MAE |
| 4 | **报「不显著」的那一档**（k=8，p=0.196，5/11） | 文献几乎只有「few-shot 有效」的正向叙事；B03 是唯一报负迁移的，但未扫 k | the k=8 regime is not distinguishable from zero-label transfer at n=11 — the threshold is between 8 and 16 |
| 5 | **门槛与工况距离的关系**（待做） | 全部文献均无 | 目前**不能写**，需 P4/P5 结果支撑（见 GAP_ANALYSIS §G2） |

> **纪律提醒**（AGENTS.md §4.2）：以上五条是**对本综述 45 条文献的陈述**，不是独立查重结论。进入实验/写作前必须走 novelty-check 四轴查重；本文件任何「没有/未见」字样都不得直接进论文。

### C.4 被抢先风险与措辞禁区

| 风险 | 具体 | 缓解 |
|---|---|---|
| **高** | Zhao 2026（B02）标题含 Few-Shot、正文含 labeling budgets、结论「5 颗饱和」。审稿人若检索到，会问「你和它有什么区别」 | **主动引用并正面对比**（C.2 表）。差异必须落在：电芯不相交的同工况标签 / 逐工况配对检验 / k=0 锚点 / RUL 而非标量寿命 |
| **中** | Applied Energy 2026 的 5-shot physics-informed（B19）—— 强 venue，仅题录，**不知道它扫没扫 k** | 投稿前必须取全文核实；若它扫了 k，我们的主张要再加一层（统计/工况距离） |
| **中** | RESS 2025 已有少样本 RUL 综述（B22）—— 说明「少样本 RUL」已成体系 | 不能把「少样本 RUL」当新领域；主张必须落在「标签预算的**估计**」而非「少样本方法」 |
| **中** | BatLiNet（B37，Nat Mach Intell 2025）Fig. 5b 已有「参照电芯数 1–64 vs 误差」的箱线图（n=8 trials） | 必须写清三条差异：**源侧参照集 ≠ 目标工况标签**、目标电芯仍无标签、原文落点是推理吞吐。见 §C.1-⑥ |
| **低–中** | 2026 年 arXiv 出现 Conformalized Transfer（B35）等「校准」路线 | 明确区分：conformal calibration 校准的是**区间覆盖率**，我们的仿射校准校准的是**点预测偏差**，两者不是同一件事 |

**措辞禁区**：

- 不写「首次研究电池的标签预算」——B02/B01 已把 k 当自变量。
- 不写「首次发现少样本可显著改善跨工况」——B01/B07/B17/B19 一大片。
- 不写「首次做跨工况 RUL 的迁移」——B29 等已做。
- 可写：「首次在**电芯不相交**的**同工况其他电芯**标签设定下，给出跨工况 RUL 的**标签预算曲线**，并以**逐工况配对检验**给出显著门槛（k 在 8 与 16 之间）及其不确定性」。

---

## D. 这个问题的文献边界

### D.1 已被解决（可以安全地当背景引用，不必再证）

1. **零标签跨工况迁移会崩**：B23（无监督 DA 是主流应对）、B36（BatteryLife Table 6：frozen 迁移 MAPE 3.153 vs 基线 0.515）、B02（direct transfer MAE 517 vs naive-mean 464.9，**比均值基线还差**）。
2. **少样本/元学习在「目标电芯早期循环」这个意义上有效**：B07（6 cycles）、B17（6 cycles）、B19（5-shot）。
3. **无标签目标数据有用**：B14/B15/B16/B31/B32（半监督一族），B34（TTT）。
4. **「多少颗电芯」在群体变异度意义上被回答过**：B05（9/11/13 颗）、B06。
5. **域内训练集规模的学习曲线会饱和**：B04（6 颗即趋平）。
6. **小 k 下迁移收益方差极大、可为负**：B03（ΔMAE −32.9% ~ +16.2%，12/21 正迁移）。
7. **源侧参照集大小对精度的影响被扫过**：B37（BatLiNet Fig. 5b，1–64 颗参照电芯，n=8 trials）。

### D.2 未被解决（可作为主张的落点）

1. **没有「跨工况 RUL 的精度 vs 目标工况标签数 k 的曲线」**，尤其没有带置信区间/配对检验的版本。最接近的是**源侧**参照集曲线（B37 Fig. 5b）——它扫的是「推理时备多少颗已知寿命的参照电芯」，不是「新工况要标多少颗」。
2. **没有「可用门槛」的定义**：现有工作说「够/不够」，没有一篇把门槛与一个**可达上界**（如组内 oracle）挂钩。本项目的 2.11–2.32 是文献里找不到对应物的锚。
3. **没有「所需 k 随工况距离变化」的研究**：所有工作把目标工况当同质的一个域。B03 的 21 次划分说明「选哪些电芯」影响巨大，但没人把「工况离源域多远」当自变量。
4. **没有区分「卡在标签侧还是输入侧」**：文献一致假设「多给标签就好」，没有一篇先问「标签的组间方差是否已经把上限锁死」（本项目 EOL 组间 η²=0.942 是这条的入口）。
5. **统计单位问题**：除 B03（21 次划分计数）外，没有一篇以**工况**为推断单位做配对检验；绝大多数报的是跨若干数据集的聚合 MAE。

### D.3 术语陷阱：「k」在文献里至少有五种含义（本综述最实用的一节）

| 语义 | 代表工作 | 单位 | 回答的部署问题 | 与我们的可比性 |
|---|---|---|---|---|
| (a) 目标电芯**自身**的早期循环数 | B07（6 cycles）、B17（6 cycles） | cycles | 这颗电芯要观察多久 | **不可比**（不是标签预算） |
| (b) 目标**工况内其他电芯**的标签数 | **本项目** | cells | 新电芯进厂要测几颗 | — |
| (c) 目标域占车队的**比例** | B02（12%/24%/49%） | % fleet | 要多少比例的产线数据 | 需换算才可比 |
| (d) **任务数 / 工况数**（元学习） | B08、B09 | tasks | 要覆盖几个工况 | **不可比**（是域数不是标签数） |
| (e) **无标签**目标样本数 | B14、B31、B34 | unlabeled samples | 不需要标签 | 互补，非同一轴 |
| (f) **源侧带标签参照电芯数** | B37（BatLiNet Fig. 5b，1–64 颗） | reference cells | 推理时要备多少颗已知寿命的电芯 | 形式同构、语义不同（非目标工况） |

> **这条 taxonomy 本身是可用于论文 Related Work 的产出**：它解释了为什么文献里「few-shot 有效」的结论彼此不可比，也解释了为什么「标签预算」作为一个**被估计的量**至今缺位。

### D.4 我们的数字与文献的对接（写作时的对照表）

| k（目标工况标签数） | cell-macro MAE | vs k=0 | 检验 | 文献里最接近的对照 |
|---:|---:|---:|---|---|
| 0（LOGO） | 6.516 | — | — | B02 direct transfer 517（比均值基线还差）；B36 frozen 迁移崩溃 |
| 8 | 5.185 | −1.331（−20.4%） | p=0.196，5/11 | B02「5 颗即 81% 改善」（**方向相反：它在 5 颗就饱和**） |
| 16 | **4.505** | **−2.010（−30.8%）** | **p=0.0049，9/11** | 无对应物 |
| 32 | 4.248 | −2.268（−34.8%） | p=0.0010，11/11 | B04「6 颗后趋平」（域内，方向一致） |

> 数字来源：AGENTS.md §1 的表与 research-wiki/claims/claim-label-budget.md。
> **注意**：任务书要求读的 .research/exp/EXP-001-label-budget.md **在本仓库中不存在**（.research/ 整个目录缺失，已用 Get-ChildItem 核实）。本表数字取自 AGENTS.md §1 与 wiki claim 节点，**未与实验原始输出核对**——写作前必须回到 preds.csv 复核。
> 另注：PIVOT_OPTIONS.md D2 的 pilot（1-NN）给出 k=8→4.23、k=16→3.33、k=32→3.01，与上表**不是同一个估计器**，两套数字不可混用。

---

## E. 未核实清单（写作前必须处理）

- [ ] **B19（Applied Energy 2026, 5-shot physics-informed）**：仅题录。**它是否扫了 k、扫了哪些 k，完全未知**。这是本清单里风险最高的一条。
- [ ] **B20 / B21 / B22 / B28 / B29 / B30**：Elsevier 摘要不可得（Crossref 无 abstract、S2 无 abstract），仅题录。**不得引用其任何结论**。
- [ ] **B01（Zhou 2021）**：ACM 403，仅摘要。摘要只说 various few-shot experiment settings，**具体 k 值未知**。
- [ ] **B07 / B08 / B09 / B10 / B11 / B12**：IEEE 202 / 空响应，仅摘要。「6 cycles」这一说法来自 B07 摘要原文，**其 k 是否被扫描未知**。
- [ ] **B14（Joule 2024）**：Cell Press 不可达；仅从检索片段得知是 PBCT（partial Bayesian co-training）+ 少标签 + 无标签。**是否扫 k 未核实**。
- [ ] **B03（Xia 2026）**：硕士论文，非同行评审；其 target_support_ratio 0.67 对应的绝对电芯数未在正文中明确（附录 A.3.2 只给比例）。
- [ ] **B13 / B17 / B18 / B19 的作者列表**：Crossref/OpenAlex 返回不全或为空，表中标「未核实」者**不得写进参考文献**。
- [ ] 本综述**未检索中文文献**（CNKI/万方不可达）；中文期刊的「小样本」工作未覆盖。
- [ ] OpenAlex 第三轮 429 导致 10 条「最小数据量 / 标注成本 / HUST」查询未执行；**建议额度恢复后补跑**（脚本 _lit_oa5.py 已就绪，直接重跑即可）。

---

## F. 对下一步的三条建议

1. **立刻把 Zhao 2026（B02）写进 Related Work 并正面对比**。它是唯一能对我们构成「已被做过」指控的文献；主动引用 + C.2 的四维差异表，比被审稿人翻出来强得多。
2. **补一条「选哪些电芯」的稳健性分析**（对齐 B03 的 21 次划分做法）。我们现在只报了「k 颗随机取」的均值，没有报「取到差电芯时会不会负迁移」。这一条成本极低（复用 preds.csv 重采样），但能直接回应「你的 k=16 是不是运气好」。
3. **投稿前必须取到 B19（Applied Energy 2026）全文**。它是唯一一篇可能已经把 k 扫描做在强 venue 上的工作；若属实，我们的主张需要再加一层（工况距离 / 统计单位 / 标签侧上界），否则会撞车。

---

*本文件由 Phase 1 文献子代理独立撰写。所有「未核实」均未写成断言；所有 L4 条目未用于任何数值主张。*
