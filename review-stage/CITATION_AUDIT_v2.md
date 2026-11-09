# Citation Audit Report — `docs/manuscripts/v4.0-tim.md`

- **日期**：2026-11-09
- **审计对象**：`docs/manuscripts/v4.0-tim.md`（v4.0，173 行，5 条引用）
- **审计层级**：存在性 / 元数据 / **上下文适当性**
- **方法说明**：ARIS `citation-audit` 假定 LaTeX + `.bib`；本项目是 Markdown 手写 References，故按该 skill 的三层语义适配执行。元数据一律对**一手来源**（Crossref API、PMLR、出版方 PDF、期刊页面），不依赖模型记忆。
- **总判定**：**FAIL**（1 条编造标题 + 1 条错误上下文）

---

## 汇总

| # | 引用 | 存在性 | 元数据 | 上下文 | 判定 |
|---|---|---|---|---|---|
| 1 | Zhao 2026 | ✅ | ⚠️ 缺卷/页 | ✅ | **KEEP**（建议补全） |
| 2 | Su et al. 2025 | ✅ | ⚠️ 6 作者只列 4 | ✅ | **FIX** |
| 3 | BatLiNet 2025 | ✅ | ✅ | ❌ **数值错** | **FIX** |
| 4 | DNNR 2022 | ✅ | ✅ 逐字 | ✅ | **KEEP** |
| 5 | Peng et al. 2026 | ✅ | ❌ **标题编造** | ❌ 差异化主张不成立 | **FIX + REPLACE-CONTEXT** |

---

## 1 · Zhao (2026) — KEEP

- **元数据**（Crossref + 出版方页面）：Pengcheng Zhao, "When Labels Shift: Few-Shot Fine-Tuning Versus Unsupervised Domain Adaptation for Cross-Dataset Battery Cycle-Life Prediction", *Applied and Computational Engineering*, **263(1):88–94**, 2026-09-22. doi:10.54254/2755-2721/2026.ld37070
- **稿件缺**卷期页（263(1):88–94），DOI 正确。
- **上下文核对**（下载原文 PDF，7 页）：§3.3 原文 "Three adaptation budgets are compared, **k = 5, 10 and 20 target cells**, corresponding to about 12%, 24% and 49% of the Stanford fleet"；结论 "the effect saturates quickly, so **large labeling budgets are unnecessary**"；"the output is the scalar total cycle life"。
- **稿件断言** "scans five, ten and twenty target cells for scalar cycle-life transfer and concludes that large budgets are unnecessary; its unit is a cell" → **全部逐条成立**。
- 行动：补卷期页。

## 2 · Su et al. (2025) — FIX（元数据）

- **元数据**（Crossref）：Lin Su; Shengyu Tao; Weihan Li; Dirk Uwe Sauer; **Guangmin Zhou; Xuan Zhang** — 共 **6** 作者。*Cell Reports Physical Science* 6(10):102901, 2025-10. doi:10.1016/j.xcrp.2025.102901
- **稿件只列 4 位**（L. Su, S. Tao, W. Li, D. U. Sauer），漏掉 Guangmin Zhou 与 Xuan Zhang。
- **上下文核对**：出版社页面被 CAPTCHA 拦截（ScienceDirect 403 / cell.com JS challenge），未能直取全文。已核对两个独立来源：(a) x-mol 收录的完整摘要；(b) 亚琛工大机构库 PDF（`publications.rwth-aachen.de/record/1021145`）被检索索引到的正文原句——"our model achieves less than 1% median mean absolute percentage error (MAPE) in predicting the capacity of target batteries using approximately **8% of the lifetime data**, as a conservative guideline derived from the observed data space"。
- **稿件断言** "frame the budget as a percentage of lifetime data and report that a small fraction suffices" → **成立**（8% of lifetime data）。
- 行动：补全 6 位作者。**标注**：上下文层只核到摘要 + 机构库正文摘句，未取得全文；投稿前若能取全文应复核。

## 3 · BatLiNet (2025) — FIX（上下文）

- **元数据**（Crossref）：Han Zhang; Yuqi Li; Shun Zheng; Ziheng Lu; Xiaofan Gui; Wei Xu; Jiang Bian, "Battery lifetime prediction across diverse ageing conditions with inter-cell deep learning", *Nature Machine Intelligence* 7(2):270–277, 2025-01-15. doi:10.1038/s42256-024-00972-x → 与稿件逐字一致 ✅
- **上下文核对**（arXiv 2310.05052v3 全文，54,442 字符）：
  - 原文："In BatLiNet, we employ the **median of the predictions of a reference battery group of size 32** as the final prediction, which runs at 353 target batteries per second during inference."
  - 原文："even with a very large reference size of **64** for each cell, the inference speed of the model remains notably fast, operating at 178.8 cells per second."
  - 原文："As the number of reference batteries increases, both the average prediction error and the variance between different random seeds decrease."
- **稿件断言**："varies the number of source-side reference cells from one to sixty-four to reduce variance in its median prediction, and **settles on sixty-four for inference speed**"。
  - **"settles on sixty-four" 错**：实际运营配置是 **32**；64 只是"即使这么大也还很快"的演示。
  - **"for inference speed" 因果归因也错**：选 32 是因为误差随参考数增加而下降；速度那句是在论证 64 也够快。
  - "reduce variance in its median prediction" ✅；"references carry no target labels" ✅（参考电芯取自训练集，非目标工况）。
- 行动：改写为 32，并修正因果。

## 4 · DNNR (2022) — KEEP

- **元数据**（PMLR 官方页）：Youssef Nader, Leon Sixt, Tim Landgraf, "DNNR: Differential Nearest Neighbors Regression", *Proceedings of the 39th ICML*, PMLR **162:16296–16317**, 2022 → 与稿件逐字一致 ✅
- **上下文**：稿件用它支撑"局部方法对校准集密度与同质性敏感，参数拟合在其上取平均"。DNNR 的核心正是以局部差分/梯度校正 KNN 回归，与"局部 vs 参数"的区分一致 → ✅

## 5 · Peng et al. (2026) — FIX + REPLACE-CONTEXT

- **元数据**：见 `.research/PENG2026_VERIFICATION.md`。**标题编造**。
- **上下文**：数字全部为真；但 §2 第 37 行的差异化主张不成立（原文已有 2×2 factorial）。
- 行动：改标题；改写 §2 第 37 行。

---

## 优先级修复（投稿前必做）

1. **CRITICAL** — Ref 5 标题编造 → 改为原文标题。（已执行）
2. **CRITICAL** — §2 第 37 行"联合规格空间"差异化主张不成立 → 改写。（已执行）
3. **HIGH** — Ref 3 "settles on sixty-four" → 32，并修正因果。（已执行）
4. **MEDIUM** — Ref 2 补全 6 位作者。（已执行）
5. **LOW** — Ref 1 补卷期页。（已执行）

---

## 未发现问题的部分

- 没有不存在的 DOI，没有不存在的会议/卷期。
- Ref 1 的具体数字（k=5/10/20）与结论方向**全部核对为真**——上一轮审计怀疑它来自二手转引，实际核对后成立。
- Ref 4 的页码、作者、年份、会议届次逐字一致。

---

## 为什么上一轮没抓到

`.research/AUDIT_CITATIONS.md` 的判据是"DOI 可解析 + 作者/年份/期刊匹配"。**标题从未逐字比对。** 一条 DOI 真实、作者真实、期刊真实、唯独标题是编造的引用，能完整通过那种审计。

本轮已把"标题逐字比对"列为强制项。
