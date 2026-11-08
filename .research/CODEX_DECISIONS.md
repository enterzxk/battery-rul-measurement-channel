# CODEX_DECISIONS · L2 决策记录

> 目的：避免新会话重新讨论已经决定的问题。只追加，不改写。
> 每条必须能被 `.research/` 或 `review-stage/` 的证据追溯。

| 编号 | 日期 | 问题 | 决定 | 依据 | 状态 |
|---|---|---|---|---|---|
| CD-001 | 2026-11-08 | 标签预算方向是否值得继续 | 继续，但主张改为「供体身份地板」，放弃「成本轴」 | review-stage/CROSSMODEL_REVIEW_20261108.md | 已执行 |
| CD-002 | 2026-11-08 | 是否采用「Saturate at the Second Donor」作标题 | 否——数据不支持该饱和点位置（三次运行三个 knee） | refine-logs/FINAL_PROPOSAL.md §5 | 已执行 |
| CD-003 | 2026-11-08 | 「RUL 范围覆盖」是否作为机制 | 否——实测 uncovered 0.3138 vs covered 0.2899，差 0.024，成比例 | refine-logs/FINAL_PROPOSAL.md | 已执行 |
| CD-004 | 2026-11-08 | M0 是否先跑 | **D：跑完整 M0，再跑修正后的 M1**。理由：只解决 mean/median 仍剩 ~0.10 漂移，大于 0.062 的行预算增益 | review-stage/CD-004-m0-decision.md | 待执行 |
| CD-006 | 2026-11-08 | M1 两项未过线后怎么办 | **D：撤回 floor 标题、M1 标记为未接受、按原协议正确重跑 P2**。理由：Codex 读代码发现 `e1_2` 无 MC 抽样循环，8/11 不是预注册检验 | review-stage/CD-006-m1-decision.md | 已执行 |
| CD-007 | 2026-11-08 | CD-006 的反转条件是否满足 | **是。** 正确重跑后 P2 通过未改动的联合闸门（mean +0.289 11/11；median +0.275 11/11）→ 决策转 **B**：限定为描述性供体数结果 | .research/exp/EXP-008-p2-corrected.md | 已执行 |
| CD-005 | 2026-11-08 | 实验计划是否可直接执行 | **否**。Codex 发现两处错误：(a) 45 个配对单元只来自 3 个工况却按 45 独立算 MDE（伪重复）；(b) 交互项符号与预测方向相反（计划写「>0」，实际应为「<0」）| EXPERIMENT_PLAN.md L115-117, L154-160 | 待修正 |

## 路由规则

- 新问题先判层级：L1 自决 / L2 交 Codex / L3 停下问用户
- L2 决定必须在这里留一行，写清决定与依据路径
- 同一问题不重复问：先检索本表

## CD-004 详情（gpt-6.1-sol / xhigh）

决定 D。核心论证：
- 解决 mean/median 只消掉 60% 漂移，**仍剩约 0.10 MAE**，大于被检验的 0.062 行预算增益 → B/C 会产生「结论可能被剩余自由度翻转」的结果
- 我报的 0.062 **超过计划自定的 ±0.05 等价边界**，因此它**不能**用来证明等价
- p=0.065 vs p=0.00098 **不构成矛盾证据**——两个估计都偏向「更多供体有益」，问题在识别与不确定性，不在是否跨 0.05

最高风险假设：**单供体平台代表的是可迁移的「供体身份地板」，而不是有限预算平台或仿射估计器的不稳定**。重复同一条曲线不能建立这个机制。

反转条件：**若在匹配标签预算与稳定替代校准器下供体优势消失，则终止该方向**，转为协议敏感性报告。

## 对 DSH 的约束

- 主口径改为 **mean MAE**（决策目标是期望误差），median 作强制敏感性
- 不得用「只报 mean」来救回失败的稳健性闸门
- 只有 3 个合格工况时，地板主张必须相应收窄

| CD-008 | 2026-11-08 | 匹配行预算结果能否支撑「供体身份」主张 | **否**。Codex 读代码发现 `per_donor = k // m` 使行预算不匹配（k=8/m=3 只得 6 行）；且 k=32 有供体长度合格性混淆；Holm 后多数不显著 | review-stage/CD-008-matched-budget.md | 已执行 |
| CD-009 | 2026-11-08 | 修正后（EXP-010）的可用主张 | **k=8 预算下 1→2 供体降 0.19–0.20 MAE，11/11，Holm adj p=0.012–0.037**；k=16/32 不可写；标题限为描述性 | .research/exp/EXP-010-exact-k.md | 已执行 |

## CD-007 的标题后果

**必须放弃**：`Labels Cannot Buy Diversity`、`Identity Floor`、一切饱和表述。

**当前可支撑的标题**（Codex 在 CD-006 中给定）：

> One versus Two Full-Trajectory Donors in Cross-Condition Battery RUL Calibration: An Exploratory Study

**可写的主张**：在抽样到的供体分配下，用两条完整供体轨迹比一条降低平均校准误差 0.29 MAE（4.4%），11/11 工况、mean 与 median 双聚合都成立。

**不可写的主张**：这是「供体身份/多样性」的独立贡献——全轨迹供体数同时增加标签行数，两者未分离。

| CD-010 | 2026-11-08 | 估计器对照打破供体主张后怎么办 | **A：终止供体方法方向，冻结，写协议敏感性报告**。理由：两个仿射正结果都不过 Holm；唯一存活的是 1-NN 下的**反向**结果；「换校准器比加供体值钱」也只是描述性比较，不能当交互作用 | review-stage/CD-010-estimator-control.md | 已执行 |

## 标题（CD-010 定稿，取代 CD-008）

> Donor Count and Calibrator Choice at a Fixed Label Budget: An Exploratory Study of Cross-Condition Battery RUL Calibration

**CD-010 明确禁止**：
- 声称供体多样性有普适收益
- 声称「换校准器主导供体数」（0.559 vs 0.206 只是描述性比较，未做配对不确定性，不构成交互作用）
- 在看到对照结果后把故事收窄到 affine（那是把失败的稳健性要求变成有利子组）
- 再做任何「抢救这条线」的机制实验

## 标题（CD-008 旧稿，已作废）

> One versus Two Donor Cells at Equal Label Counts for Cross-Condition Battery RUL Calibration: An Exploratory Study

**明确禁止**：identity floor、saturation、optimal donor count、general diversity benefit。

## 一条方法学观察（写进论文）

本项目的三次实现 bug（EXP-002 单次抽样、EXP-007 无 MC 循环、EXP-009 行预算不匹配）**全部由跨模型审稿读代码发现，无一次自查发现**。

| CD-011 | 2026-11-08 | ISU 复现与 CD-010 矛盾，是否解冻 | **暂不解冻，授权一次修正复现**。Codex 发现 ISU 脚本供体合格性不匹配、失败抽样静默移除电芯、MAE 与配对 Δ 用不同工况集；并**撤回「效应是仿射族伪影」这一解释** | review-stage/CD-011-replication.md | 已执行 |
| CD-012 | 2026-11-08 | 修正复现（EXP-013）是否通过 CD-011 的判定规则 | **通过。六项全部 Holm < 0.001**（affine +0.156、isotonic +0.085、1-NN −0.063，57 工况）。按 CD-011 预置规则：**解冻，重开分配/敏感性研究** | .research/exp/EXP-013-isu-corrected.md | 已执行 |

| CD-015 | 2026-11-08 | 现在能不能写稿 | **开始写，但不得宣称 TIM-ready**。缺的是「相对强竞争策略的、经校验的分配指南」。给了最终标题与三条可写主张 | review-stage/CD-015-scope.md | 已执行 |

| CD-016 | 2026-11-08 | 目标应标记 blocked 还是改写 | **A：冻结实验，按未达成记录**。Codex 给出精确的 blocked 措辞，并指出「未建立」不等于「不存在」 | review-stage/CD-016-goal-status.md | 待执行 |

## CD-016 的 blocked 措辞（原样采用）

> **FIXED GOAL UNMET; CURRENT EXPERIMENTAL LINE EXHAUSTED.** M1 did not establish the preregistered single-donor row-axis saturation criterion. Subsequent experiments support estimator-dependent allocation findings, not the original donor-identity-floor claim. EXP-021/022 did not demonstrate improvement over the strongest fixed allocation/calibration strategy. The manuscript therefore does not fulfill the fixed objective; independent integrity review also remains outstanding. Freeze further experiments under this line. Reopen only following human-authorized scope revision, or materially new, independently reviewed evidence directly addressing the unmet gates. Additional seeds, cosmetic variants, and manuscript polishing are insufficient grounds.

## CD-016 的两条纪律

1. **措辞精度**：「floor not established」可辩护；「no floor exists」过度主张，因为只有三个配对单元。
2. **停止幻想**：这条线上**没有任何**实验能补上缺口。要做前瞻性饱和研究或新的分配机制，都是**新项目**，不是这个 campaign 的延续。

## CD-015 定稿（2026-11-08 21:40）

**标题**：

> Donor Allocation at a Fixed Label Budget: Estimator Dependence and Population Boundaries in Battery RUL Calibration

**只可写这三条**：

1. 在来自目标工况其他电芯的 8 个标签预算下，供体数从 1 增到 2 对 affine 与 isotonic 校准产生小幅平均改善，跨两个数据集，但统计支持不等。
2. 供体数效应依赖估计器：原始标签 1-NN 方向相反；借残差削弱了该伤害。这些对照约束了可能的机制，但**不能证明是聚合本身造成差异**。
3. 全总体收益有总体边界：四分位分层保持符号，而选中查询子集在两种供体池下都反转 affine/isotonic 效应。**不能推出普适的供体数或校准器建议。**

## CD-012：方向重开（2026-11-08 19:05）

**冻结解除。** CD-010 的终止理由已被两个数据集的数据推翻。

**可写的主张**（CD-011 措辞）：在 8 个标签预算下，分给两个供体电芯能小幅改善仿射与 isotonic 校准；仿射收益与 1-NN 的有害效应在两个数据集上复现。

**Codex 原话**：「The 1-NN reversal belongs in its central result; a reproducible 4–6% gain alone is not a reason to stop.」

**仍不可写**：供体身份的因果机制、普适多样性收益、原创方法。

## CD-010 的结论原文（已被 CD-012 取代）

> Is there a paper? **No—not currently a convincing Q1 methods paper.** There is an auditable negative result and material for a protocol-sensitivity report.

> **Next step:** freeze the donor-method programme, retain every control and unfavorable result, and finalize the sensitivity report. Do not authorize another mechanism experiment to preserve this direction.

## 冻结声明

供体方法方向自 2026-11-08 19:15 起冻结。不再做新的供体/校准器机制实验。已有 11 个实验（EXP-001~011）与全部对照保留。
