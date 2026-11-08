# BatLiNet Fig. 5b 核查（2026-11-08）

来源：docs/papers/s42256-024-00972-x.pdf（Nature Machine Intelligence, BatLiNet），本地全文。

## 原文（p4）

> While selecting the optimal reference cell is challenging, we mitigate performance variations by sampling a batch of reference cells and using their median predictions, as shown in Fig. 5b. Figure 5c reveals that this batch sampling mechanism does result in a significant reduction in inference speed as the batch size increases exponentially. However, given the extensive battery cycling time, these differences in inference speed are negligible. **We find that using a batch of 64 reference cells is effective in maintaining a reasonable inference speed yet delivering robust predictions.**

## 图注（p6）

> Fig. 5 | Analysis of reference cell selection in BatLiNet. a, Best, worst and median prediction errors ... b, **Effects of increasing reference cell numbers on predictions in the MIX-100 dataset** ...

## 判定

1. **他们确实扫了参照电芯数（1–64）**，形式上是一条「数量-误差」曲线。
2. **但目的是鲁棒性，不是预算**：取一批参照电芯的中位数预测，是为了消除「选到哪一颗」的方差；64 是他们选的工作点，理由是速度与鲁棒性的折中，**不是观察到饱和**。
3. **参照电芯来自源侧已完整循环的电芯**，目标电芯无标签。
4. **他们没有报饱和点**，也没有把参照数量当作成本。

## 对我们 GO 成分的影响

- 「一条寿命够用」**没有被 BatLiNet 占据**——他们的曲线不是为了回答这个问题，且工作点选在 64 说明他们没观察到早饱和。
- 但**必须在 Related Work 里显式区分**：源侧参照集（无标签、为降方差）vs 目标工况标签（有标签、为校准）。
- 风险仍在：审稿人可能说「你只是把 BatLiNet 的参照数量换成目标标签数量」。**差异化必须落在「成本」与「饱和点」上，而不是「数量」本身。**

## 未核实

- Fig. 5b 的具体数值（PDF 文本层是散落的坐标标签，无法可靠重建曲线）。若需要精确饱和点，须看原图。
