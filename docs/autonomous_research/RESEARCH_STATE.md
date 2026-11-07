# RESEARCH STATE

> 由主代理维护。所有代理只读本文件，写自己名下的文件。

## 项目

- 主题：电池 RUL 预测中的非循环测量通道（脉冲弛豫 / EIS / 静置弛豫）
- 本地仓库：`E:\桌面\rul\rul_v4_20261107`
- 远程：https://github.com/enterzxk/battery-rul-measurement-channel （公开）
- 研究分支：`research/autonomous-v2`
- 启动：2026-11-07

## 已验证事实（v2，2026-11-07 21:20 起唯一口径）

> v1 的数字（6.020 / −8.6% / CI [−0.999,−0.133]）**全部作废**，原因是 ECM 拟合窗 bug。见 docs/e1_v2_fixed_results.md。

| 项 | 值 | 来源 |
|---|---|---|
| UConn 规模 | 64 电芯 / 11 工况组 / 2,813 行 | docs/e1_v2_fixed_results.md |
| 主结果 LOGO（rpt 单位） | A_curve 6.587 → +C_ecm 6.238（−5.3%） | 同上 |
| 主结果 LOGO（cycle 单位） | 729.8 → 694.1（−4.9%） | 同上 |
| 主效应显著性 | 电芯级 CI [−80.77,+10.45]、工况簇 CI [−115.02,+39.07]，**均跨零** | 同上 |
| 参数化 vs 描述量 | C_ecm 6.238 **>** C_desc 6.155（参数化更差） | 同上 |
| 方法层 | 7.825 / 7.452 / 6.805 / 6.274，全负 | docs/tier2_results.md |
| Bayreuth | 48 电芯 / 23 工况；仅 a1、c 过 Bonferroni（该分析用小时单位与独立实现，不受 ECM bug 影响） | docs/bayreuth_D_results.md |
| 不可用数据集 | NASA（4 电芯）、CALCE（无随寿命 EIS） | docs/nasa_results.md |
| 标签口径 | num_cycles = 相邻 RPT 间的段长；cumsum 为真实循环轴（spearman(soh,cum)=−1.0000） | A2/A3 复核 |
| 工况级功效 | n=11，检出 d≈0.4 需约 49 工况 | A3/A6 |

## 用户指定的五个必须解决的问题

- **A 预测目标**：现标签是"剩余体检次数"，不是真实循环数或日历时间。需判定能否重建真实时间目标。
- **B 物理参数有效性**：2-RC 的时间常数被当作采样点索引解释，物理有效性存疑。
- **C 统计与泛化**：工况级 vs 电芯级统计单位、组内相关、模型选择偏差。
- **D 跨数据集**：Bayreuth 只是物理参数检验，不是 RUL 验证，不得写成精度提升证据。
- **E 方法层失败**：轨迹编码 / 测试时适配 / 物理正则为何失败，需机制诊断。

## 代理分工与文件所有权

| 代理 | 角色 | 独占写入文件 |
|---|---|---|
| A1 | Literature Researcher | `LITERATURE_MATRIX.md`, `GAP_ANALYSIS.md` |
| A2 | Method Architect | `IDEAS_AGENT2.md` |
| A3 | Data & Protocol Auditor | `AUDIT_AGENT3.md` |
| A4 | Implementation Engineer | `EXPERIMENT_REGISTRY.md`, `code/`, `scripts/` 下新文件 |
| A5 | Critical Reviewer | `REVIEW_AGENT5.md` |
| A6 | Decision-Maker | `DECISION_LOG.md`, `IDEA_RANKING.md` |
| 主代理 | PI | `RESEARCH_STATE.md`, `NEXT_ACTION.md` |

**禁止**：任何代理写入不属于自己的文件；不得覆盖 `docs/` 下已有的历史结果文件。

## 全局约束

1. 不得虚构文献、数字、结论。未读全文的论文必须标注阅读等级（全文精读 / 仅摘要 / 仅题录）。
2. 原始数据与历史结果只读。
3. 所有实验必须写入 `EXPERIMENT_REGISTRY.md`，含配置、种子、结果路径。
4. 结论必须区分：已验证 / 待核实 / 探索性 / 已否证。
