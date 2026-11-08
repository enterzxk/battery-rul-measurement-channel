# 引用审计（2026-11-08）

## 方法

逐条核实稿件 Related Work 的四条引用。DOI 走 Crossref API；本地 PDF 直接读元数据；会议论文读 PMLR 页面。

## 结果：四条全部为真

| # | 稿件中的写法 | 核实来源 | 核实到的元数据 |
|---|---|---|---|
| 1 | Zhao (2026) | Crossref | **Zhao Pengcheng**（单作者），*When Labels Shift: Few-Shot Fine-Tuning Versus Unsupervised Domain Adaptation for Cross-Dataset Battery Cycle-Life Prediction*，Applied and Computational Engineering，2026，DOI 10.54254/2755-2721/2026.ld37070 |
| 2 | Su et al. (2025) | Crossref | **Su Lin; Tao Shengyu; Li Weihan; Sauer Dirk Uwe** 等 6 人，*Data sufficiency for transferable lithium-ion battery periodical SOH estimation under resource constraints*，Cell Reports Physical Science，2025，DOI 10.1016/j.xcrp.2025.102901 |
| 3 | BatLiNet (2025) | 本地 PDF `s42256-024-00972-x.pdf` | **Zhang Han; Li Yuqi; Zheng Shun; Lu Ziheng; Gui Xiaofan; Xu Wei; Bian Jiang**，*Battery lifetime prediction across diverse ageing conditions with inter-cell deep learning*，**Nature Machine Intelligence, Vol. 7, Feb 2025, pp. 270–277**，DOI 10.1038/s42256-024-00972-x |
| 4 | DNNR | PMLR 页面 | **Youssef Nader; Leon Sixt; Tim Landgraf**，*DNNR: Differential Nearest Neighbors Regression*，**PMLR 162:16296–16317 (ICML 2022)** |

## 需要修正的

1. **稿件此前没有参考文献表**——只有正文里的作者-年份。已补 References 节，用核实到的完整元数据。
2. BatLiNet 的 DOI 前缀是 2024（`s42256-024-`），但**出版年是 2025**（Vol 7, Feb 2025）。稿件写 2025 正确。

## 仍不确定的

- Zhao 2026 的**具体数字**（k=5/10/20、5 颗降 81% 误差）来自 LIT_SURVEY 的转引，**未核对原文**（Crossref 只有元数据，正文需订阅）。稿件只引其结论方向，未引具体数字，因此不构成风险。
- Su 2025 的「8% lifetime data」同样是摘要级转引，稿件只引其定性结论。

## 结论

四条引用**作者、年份、期刊/会议、DOI 全部核实为真**。正文未引用任何未经核实的具体数字。
