# RUN_LOG · online-mechanisms-20261110

T0 = 2026-11-10 01:36 +08:00 · 窗口 10 小时 · 分支 `research/online-mechanisms-20261110`

---

## T+00:00–00:40 · 治理与可识别性

**做了什么**

1. 定位本机仓库 `E:\桌面\rul\rul_v4_20261107`，确认 BASE_SHA = `44d9a69`（与用户给的一致）。
2. 从 `programme-closure-20261109` 建分支 `research/online-mechanisms-20261110`。
3. 写 `HISTORICAL_BOUNDARIES.md`：把 F-001..F-015 分成**被否定 / 未建立 / 未检验**三类，并列硬约束。
4. 冻结输入指纹（SHA256）：`isu_table.npz`、`isu_conditions.csv`、`isu_readme.txt`、`v2_main.py`。
5. 派 3 个独立上下文子代理：查新、数据可识别性、方法反方审稿。

**数据侧的真实发现（本轮新做，不沿用旧记录）**

| 发现 | 意义 |
|---|---|
| `data_cc_1.pkl` 每个 (cell,rpt) 存 **6 行**，只有 600 点电压带滚动偏移，q/soh/DCIR 完全相同 | **存储 artefact，不是 6 次重复**。不去重会把样本量虚增 6 倍 |
| `num_cycles` 是**段长**不是累计 | 与 F-005 一致。物理轴 = cumsum |
| 去重后 **2,855 行 / 64 电芯 / 11 工况** | 主数据集就绪 |
| 检测间隔中位 **98 循环**，IQR [84,119]，**CV 0.23**，max/min **16.4×** | **问题 A 可识别的前提成立**：间隔确实不规则 |
| 64/64 电芯都是**区间删失** EOL，宽度中位 **131 循环**（相对 2.9%） | 事件模型可建；但区间很窄，区间似然的增益可能很小——必须在实验里检验，不能默认 |

**产出**
- `protocol/uconn_online_tidy.csv`（2855 行）
- `protocol/uconn_eol_intervals.csv`（64 个区间）
- `protocol/uconn_data_contract.json`（节奏统计）
- `protocol/DATA_CONTRACT.md`（estimand + **字段级 leakage map**）
- `code/build_uconn_online.py`（可复算）

**未建立（明确记录）**
- 日历时间轴：本地无 `start_stop_time`（需 `rpt_data.zip` 2.35 GB）
- Ah-throughput：本地无 cycling 原始时序（需 13.6 GB）
- ISU 真实循环数：`Cycling_json.zip` 10.2 GB，figshare 下载路径被挡

**下一步**
等三个子代理报告 → Codex L2 判 GO / CONDITIONAL-GO / NO-GO → 冻结 `METHOD_SPEC.md` + `PROTOCOL_LOCK.yaml` → 才允许建模。

---

## T+00:40 · 状态

| 项 | 状态 |
|---|---|
| 分支 | ✅ `research/online-mechanisms-20261110` @ 44d9a69 |
| 治理文件 | ✅ HISTORICAL_BOUNDARIES.md |
| 数据契约 | ✅ DATA_CONTRACT.md |
| 主数据集 | ✅ 2855 行 / 64 电芯 |
| 子代理 | 🔄 3 个运行中 |
| 建模 | ⛔ 未开始（等闸门） |

---

## T+00:40–02:00 · 问题 A 判定 + 问题 B 机制结果

### A：DATA-NOT-IDENTIFIABLE（T+01:10）

关键检验：**电芯内** cadence CV 中位 **0.091**，cum_cycles ~ rpt 线性 R² 中位 **0.999**，无一个电芯 CV>0.3。
⟹ RPT 序号与累计循环数在电芯内近似严格成比例，**两种时间参数化代数等价**。
实验印证：pt_naive vs exposure_naive 差 0.2–0.3%（S0/S1/S2 都如此）；手写 KF 是最差臂（比地板基线还差 4%）。
**我先前报的 CV 0.23 是跨电芯池化值，不是电芯内不规则——这是我自己的混淆，已在 RESULTS_A.md 更正。**

### B：POSITIVE（机制）/ NEGATIVE（预测方法）（T+01:50）

- **H0（吞吐量受限）被否定**：EFC 归一化后 DoD 相关反而更强（−0.636 → −0.815）；CV 完全没变小（0.60 → 0.60）。
- **损伤律**：log(EOL_EFC) = 8.259 − 1.875·DoD − 0.312·log Cc + 0.435·log Cd，R²=0.563，n=211，DoD 系数 p≈0。
- DoD 0.2→1.0 每 EFC 寿命降到 **0.22×**（约 4.5× 损伤）。
- **决策后果**：吞吐量归一化排工况寿命 Spearman **+0.28**（前 10 命中 3/10）；损伤律 **+0.87**（6/10）。
- **但预测方法不成立**：直接拼特征的 HGB 0.2625 打败损伤律 0.3465。我的层级更新臂 0.5999（比无信息基线还差）→ EXPERIMENT-NEGATIVE。
- **原因**：log(EOL_EFC) 方差 **91% 在工况之间、9% 在工况之内** ⟹ 电芯级在线更新没有空间。

**产出**：RESULTS_A.md、RESULTS_B.md、protocol/B_*.json|csv、code/{build_uconn_online,harness,arms,B_mechanism,B_damage_law,B_loco}.py

**子代理**：3 个仍在运行（查新 / 数据 / 反方），尚未交付最终文件。

**下一步**：等子代理 → Codex L2 判定 B 的机制结果够不够 → 若不够，按用户规则转 C（协议/删失基础设施）。

---

## T+00:50–01:00 · C 第二部分：检查预算是否依赖应力

**设计**：ISU 无法抽稀（中位 20 次 RPT），改问反过来的问题——**固定观测数 N**，看预测误差是否随工况应力变化。N ∈ {3,4,6,8}，204 电芯 / 52 工况（注：日志里的「364」是 cm.size 报元素数的显示 bug，实际 52 个工况；相关系数不受影响）。

| N | cond-macro \|log err\| | ρ(err,DoD) | ρ(err,充电倍率) | ρ(err,放电倍率) |
|---:|---:|---:|---:|---:|
| 3 | 0.0673 | −0.097 (p=0.49) | +0.105 (p=0.46) | −0.198 (p=0.16) |
| 4 | 0.0616 | −0.108 (p=0.45) | +0.146 (p=0.30) | −0.256 (p=0.067) |
| 6 | 0.0685 | −0.059 (p=0.68) | +0.159 (p=0.26) | −0.131 (p=0.36) |
| 8 | 0.0626 | +0.031 (p=0.83) | +0.051 (p=0.73) | −0.294 (p=0.036) |

**判定：所需检查预算不依赖应力 —— 未建立依赖（NOT-SUPPORTED）。**
DoD 的 ρ 全部 p>0.4；充电倍率 p>0.26；放电倍率只有 N=8 一个边缘显著（p=0.036），四个 N 里出现一次，符合多重比较下的偶然。

**另一个观察**：误差在 N=3..8 之间几乎不动（0.062–0.069）。**在 ISU 的日轴上，3 次观测和 8 次观测一样好。**

**与 UConn 的对照**：UConn 上 4× 抽稀（27→7 次）显著变差 20%（p=0.024）；ISU 上 8→3 次没有变化。两个队列方向不一致，**不得合并成一条结论**。

**修正记录**：C_stress_budget.py 的 
_cond 用了 cm.size（元素数）而非 len(cm)，显示为 364；实际 52。统计量未受影响，已在此更正。
