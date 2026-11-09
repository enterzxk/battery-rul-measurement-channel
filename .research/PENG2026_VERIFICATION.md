# P0-1 · Peng, Wang & Zhang (2026) 原文核对

- **日期**：2026-11-09
- **对象**：`doi:10.3390/en19204805`，稿件 `docs/manuscripts/v4.0-tim.md` 的 References 第 5 条
- **结论**：**数字全部为真；标题是编造的；而且原文已有 2×2 联合设计，稿件 §2 的差异化表述不成立。**
- **判定**：`FIX`（元数据）+ `REPLACE-CONTEXT`（差异化主张）

---

## 1 取文路径（MDPI 直连 403 的绕行）

| 路径 | 结果 |
|---|---|
| `www.mdpi.com/1996-1073/19/20/4805`（直连 / 代理） | **403** |
| `r.jina.ai` 渲染 | 200，117,838 字符 HTML（正文可读，但公式与表格丢失） |
| **`mdpi-res.com/d_attachment/energies/energies-19-04805/article_deploy/energies-19-04805.pdf`** | **200，1,890,279 字节 → 落盘成功** |

落盘：`.research/peng2026/peng2026.pdf`（29 页，1.89 MB）
文本：`.research/peng2026/peng2026.txt`（106,545 字符，PyMuPDF 抽取）

**这是全文，不是摘要。** 下述每一条都可在该文件内定位。

---

## 2 元数据核对

| 字段 | 稿件原写法 | 原文实际 | 判定 |
|---|---|---|---|
| **标题** | "Normalisation scope and evaluation protocol in battery state-of-health regression" | **"Deployable Self-Referenced Features for Cross-Cell Battery State-of-Health Estimation: Randomized Pairing Controls and Benchmarking"** | **❌ 编造** |
| 作者 | Peng, Wang and Zhang | Bo Peng, Xiaofen Wang, Ke Zhang（电子科技大学） | ✅ |
| 期刊 / 卷期 / 文章号 | Energies, vol. 19, no. 20, art. 4805 | Energies 2026, 19(20), 4805；2026-10-12 出版 | ✅ |
| DOI | 10.3390/en19204805 | 同 | ✅ |
| 许可 | — | CC BY 4.0 | — |

标题在三个独立位置一致：PDF 元数据、正文首页页眉、Crossref `message.title`。

**原稿件标题凭空构造，且构造得"很合理"——它把论文的两个操纵拼成了一个听起来像本项目的标题。这正是 citation-audit 要抓的那类错误：元数据校验只对 DOI 会通过，只有对标题才会暴露。**

---

## 3 数字逐条核对

稿件 §2 第 35 行：

> "Peng, Wang and Zhang (2026) show that a normalisation choice moves RMSE by up to 108% and reverses the sign of a benefit, and that an offline-to-online protocol change reverses it again; they report each manipulation separately."

| 稿件断言 | 原文出处 | 原文措辞 | 判定 |
|---|---|---|---|
| "moves RMSE by **up to 108%**" | Abstract；§1；Table 1 / Figure 1 | "Changing one column's normalization moves root-mean-square error (RMSE) by up to 108%."；实测最大值 HUST **+107.8%** | ✅ |
| "**reverses the sign of a benefit**" | §1；Table 3 | "the benefit of an explicit self-referenced feature on the 67-dimensional feature set reverses sign, **from −5.3% to +4.5%**, depending solely on whether features are normalized per cell or against source-fitted statistics" | ✅ 逐字 |
| "**offline-to-online protocol change reverses it again**" | Abstract；§4；§5 | offline author protocol **−16.8%**（冻结基础模型）/ **−19.1%**（GBDT）→ strict online reader **+4.3%**（GBDT，5/11 改善）/ **+10.4%**（基础模型，3/11） | ✅ |
| "they **report each manipulation separately**" | 全文检索 | 两个操纵分处不同小节/表（Table 1 / Figure 1 与 Table 3）；两个操纵之间**没有交叉** | ✅ |

**次要问题**：HANDOFF §5 记的 "−5.3%→+4.5%" 这组数字**不在现行稿件里**（v4.0-tim.md 只引了 108% 与定性翻转）。它出现在 `review-stage/LIT_SENSITIVITY.md`。现行稿件的数字表述是准确的。

---

## 4 关键发现：原文已有 2×2 联合设计

稿件 §2 第 37 行：

> "What those studies do not do, and what we attempt here, is place several such choices in one joint specification space within a single layer, so that their interaction and their relative dominance can be read off the same experiment."

**这句不成立。** 原文确实做了一个 2×2 factorial（`peng2026.txt`）：

> "In a **2 × 2 factorial** over feature richness (16-dimensional reference features versus 67-dimensional benchmark features) and normalization (per-cell versus source-fitted), the benefit of adding the explicit origin-self column reverses sign, as shown in Table 3."

Table 3 四格：16-dim per-cell −6.7 / 16-dim source-fitted −1.0 / 67-dim per-cell −5.3 / 67-dim source-fitted +4.5。

所以「把两个选择放进联合规格空间」这件事 **Peng 已经做了**。

### 原文确实没有的（全文检索计数）

| 词 | 命中 |
|---|---:|
| `interaction` | **0** |
| `dominance` / `dominat` | **0** |
| `multiverse` | **0** |
| `specification space` | **0** |

即：Peng 有 2×2，但**从不报告交互项**，也**不按效应量给多个决定排序**。

**因此本项目的可用差异只剩两条**：(a) 跨 ≥5 个决定按量级排序；(b) 报告交互项。而 (a) 已被 EXP-029 破坏（见 F-010：作用域因子未实现，(b) 的交互项无工况级检验）。

---

## 5 对稿件的处置

| 位置 | 处置 |
|---|---|
| References 第 5 条 | **改标题**为原文标题（已执行） |
| §2 第 35 行 | 数字保留；补上「2×2」这一事实 |
| §2 第 37 行 | **删除"联合规格空间"作为差异点**，改为 Codex 给定的替代句（见 `.research/CODEX_DECISIONS.md` 本轮 L2 记录） |
| §5 | 按 CD 本轮决定撤回排序与交互主张 |

---

## 6 教训（写给下一次）

上一轮 `AUDIT_CITATIONS.md` 判定「四条引用全部核实为真」，方法是对 DOI 做 Crossref 查询并比对**作者/年份/期刊**。**标题没比对。** 一条标题完全编造的引用因此通过了审计。

**规则**：引用核实必须逐字段比对**标题**，不能只验 DOI 可解析。DOI 只能证明"有个东西在那里"，不能证明"那是你引的东西"。
