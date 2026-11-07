# NEXT ACTION

> 主代理维护。

## 当前阶段

Phase 2 审计完成 → Phase 3 方向已裁定（A+B），进入写作与补充实验。

## 方向裁定（A6 · D-14，2026-11-07 21:35）

**A 负结果/方法学为骨架 + B 可辨识性定律为受界探索节。**

标题级主张：

> A Gain That Was Not There: Label-Unit and Fitting-Window Artifacts in Pulse-Relaxation RUL Prediction, and the Identifiability Limits of Relaxation Parameters

预注册判据：

| 项 | 判据 | 状态 |
|---|---|---|
| 负结果主张成立 | 修复后 LOGO 增益 <5% 或 cycle 标签 CI 含零 | ✅ 已满足（−5.3%，CI 双单位跨零）|
| B 节成立 | 同号率随 kappa=tau/W 单调下降，Spearman 95% CI 不含零 | 待做 |
| B 不成立 | 改写为「机制未获支持」，标题摘要不得出现「定律」 | — |
| 禁止 | 不得把 5.3% 写成「仍有改善」；不得省略 8.6% 那段历史 | 执行中 |

## 已完成

| 项 | 结果 | 文件 |
|---|---|---|
| ECM 拟合窗 bug 修复 | tau1 从 100% 触界恢复为 1.08–3.79 s | scripts 待固化 |
| 主实验 v2（双单位 + 双推断） | 增益 −5.3%，CI 双单位跨零 | docs/e1_v2_fixed_results.md |
| 权威口径转移 | v1 已标记作废 | docs/e1_v2_fixed_results.md |
| RESEARCH_STATE 更正 | 已验证事实表改为 v2 | 本目录 |
| T3 Bayreuth tau 触界检查 | 0% 触界；两数据集时间尺度不重叠 | T3_BAYREUTH_TAU.md |
| 文献矩阵 | 77 条，精读 17 | LITERATURE_MATRIX.md |
| Gap 分析 | G1–G6 + 15 条命题 | GAP_ANALYSIS.md |
| 方法提案 | 5 个 Idea | IDEAS_AGENT2.md |
| 审计 | 28 条判定 + R1–R10 重做清单 | AUDIT_AGENT3.md |
| 审稿 | 5 阻断 + 10 主要 | REVIEW_AGENT5.md |
| 决策框架 | 六维 + 证据分级 E0/E1/E2 | IDEA_RANKING.md / DECISION_LOG.md |

## D-16 补充裁定（2026-11-07 22:20）

- 标题与纯 A 定位确认，采用预案标题
- 否证节保留，但强弱两句必须分开写（已改：第 7 节）
- 不报 p=0.286 作为主结果，改用 10 点表 + 反例逻辑反驳（已改）
- H-D 正式作废；T3 取消（但已于 21:26 跑完，结论：Bayreuth 侧 0% 触界，两数据集时间尺度不重叠，仍有记录价值）
- **模型层组件论证基础改写**：从"不可辨识性解释失败"改为"不可辨识性存在，须显式表达——诚实性而非增益"（已写入第 8 节）
- 评分 S 由 4.53 升至 4.71（未验证猜测被已执行否证替换）

## 待做（按优先级）

1. ~~B 节实验~~ 已完成并否证，见 B_SECTION_FALSIFIED.md
2. **A5 的 REVIEW_AGENT5.md 需修正**：仍引用已作废的 −0.583 与保序重建
3. **A2 的 IDEAS_AGENT2.md 需标注**：I2 的可行性受 T3 限制（两数据集时间尺度不重叠）
4. **论文写作**：按 A+B 骨架重写手稿（当前 v1.0-draft.md 的全部数字已作废）
5. **代码固化**：把修复后的 ECM 与双单位/双推断流程写进 code/rulkit（A4 的框架需更新 features.py 与 metrics.py）

## 阻塞

无。
