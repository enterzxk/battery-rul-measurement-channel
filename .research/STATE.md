# STATE · 唯一真相

> 任何新会话、新子代理接手，先读本文件。

## 当前位置

- 阶段：**7 · Research Director（决策中）**
- 项目：电池 RUL · 非循环测量通道
- 主仓库：E:\桌面\rul\rul_v4_20261107（分支 main，已推 GitHub）
- 更新时间：2026-11-07T23:59

## 一句话现状

原方向（脉冲弛豫通道对跨工况 RUL 的增量）已在本数据规模下被证伪：两个统计单位都是零效应，根因是统计功效而非方法。

## 已确定（带证据）

| 结论 | 证据 |
|---|---|
| 修复 ECM 拟合窗后，增益从 −8.6% 降到 −5.3% | rul_v4_20261107/docs/e1_v2_fixed_results.md |
| 工况级 p=0.368（6/11），电芯级 p=0.873（34/64，Δ=−3.72） | 同上 + .research/exp/ |
| 参数化不再优于波形描述量（6.238 vs 6.155） | 同上 |
| tau1 修复前 100% 钉在下界，修复后 1.08–3.79 s | 同上 |
| n=11 的 MDE = 17.1%，检出 d=0.28 需 120 个工况 | .research/exp/ |
| 可辨识性不预测跨工况稳定性（Spearman +0.375；κ=0.345 处同号率 1.000） | docs/autonomous_research/B_SECTION_FALSIFIED.md |
| 非循环通道 × 工况级推断在公开数据中做不到 n≥30 | docs/autonomous_research/LIMITATIONS_MINING.md |

## 还不能确定

- 是否存在「单位 ≥30 且保留非循环通道」的可行方向（A1 给 T6，单位=电芯 112，待 A6 裁决）
- 论文级统计实践审计（T2）是否真有 gap —— 本机 11 篇全文的粗探针显示报告率极低，但探针未经验证

## 已证伪（不得重试）

| 对象 | 原因 | 登记 |
|---|---|---|
| 脉冲通道对 RUL 的增量（本数据） | 双单位零效应，功效不足 | F-001 |
| 物理参数化优于描述量 | 修复 bug 后方向反转 | F-002 |
| 轨迹编码器 / 测试时适配 / 物理正则 | 四条路线全负 | F-003 |
| 可辨识性解释跨工况符号翻转 | 预注册检验失败 | F-004 |

## 方向（2026-11-08 00:25 起，00:20 已复核）

**主攻：标签预算（D2）。** 跨工况零标签不可行；给目标工况 k 个**其他电芯的**标签即可大幅降低误差。

| k | strict MAE | Δ | 检验 |
|---|---:|---:|---|
| 0 | 6.516 | — | — |
| 8 | 5.185 | −1.331 | p=0.196，5/11（不显著）|
| **16** | **4.505** | **−2.010** | **Wilcoxon p=0.0049，9/11** |
| 32 | 4.248 | −2.268 | p=0.0010，11/11 |

G-D2a（电芯不相交）已通过：F1 未触发。幅度由 49%（leaky）修正为 31%（strict）。

**备选：T2 论文级统计实践审计**（第二篇，非替代）。
**否决**：T1。

## Stage 1 完成（2026-11-08 14:52）

方向定稿：**Labels Cannot Buy Diversity: A Donor-Identity Floor in Cross-Condition RUL Calibration**

| 阶段 | 状态 | 产物 |
|---|---|---|
| research-lit | done | idea-stage/LIT_SURVEY.md |
| idea-creator | done | idea-stage/IDEA_CANDIDATES.md |
| novelty-check | **accepted**（gpt-6.1-sol/xhigh）| review-stage/NOVELTY_REVIEW.md |
| research-review | done | review-stage/RESEARCH_REVIEW.md |
| research-refine-pipeline | done | refine-logs/FINAL_PROPOSAL.md + EXPERIMENT_PLAN.md |

命门已验证：单供体下 k=16→64 只值 0.062 MAE（0.95% 基线）。见 EXP-005。

## 下一步

阶段 7 决策：在 T2（论文级统计审计，单位=论文）、T1（工况级符号一致性，单位=61/72/421 工况）、T6（可辨识性门控，单位=112 电芯）中选主攻。

## 配置（2026-11-08）

- 项目级契约：rul_v4_20261107/AGENTS.md（合并七阶段纪律 + ARIS 自主科研规则）
- 知识库：rul_v4_20261107/research-wiki/（已 init，已 seed 1 idea / 1 exp / 1 claim）
- 助手：rul_v4_20261107/.aris/tools/research_wiki.py

## 能力降级

gate.py 缺失、LaTeX 缺失、无 GPU。见 CAPABILITIES.md。
