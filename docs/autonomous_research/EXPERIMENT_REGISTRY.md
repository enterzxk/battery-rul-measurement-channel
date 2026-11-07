# EXPERIMENT REGISTRY

> 维护：Implementation & Experiment Engineer (A4)
> 规则：**任何实验都必须先在此登记**；只追加、不覆盖；配置 / 种子 / 结果路径三者缺一不可。

## 如何复现

每条记录给出 run_id、命令、配置、种子、耗时、指标、结果目录
（`code/results/<run_id>/` 含 `result.json` / `preds.npz` / `preds.csv` / `fold_log.json`）。
统一实验框架见 [`code/README.md`](../../code/README.md)（rulkit v0.1.0）。

## 0. 环境基线（2026-11-07 实测，本机）

| 项 | 值 |
|---|---|
| OS | Windows 10 专业版，build 19045（`Windows-10-10.0.19041-SP0`） |
| CPU | 13th Gen Intel Core i5-13400F，**10 物理核 / 16 逻辑核** |
| 内存 | 16 GB |
| Python | 3.8.7（CPython，`C:\Users\Administrator\AppData\Local\Programs\Python\Python38\python.exe`） |
| numpy | 1.24.4 |
| scipy | 1.10.1 |
| scikit-learn | 1.3.2 |
| pandas | 2.0.3 |
| torch | 2.4.1+cpu —— **`torch.cuda.is_available() == False`，无可用 GPU** |
| lightgbm | 4.6.0 |
| xgboost | 2.1.4 |
| git | `research/autonomous-v2` @ `2b4cee1` |

**环境限制（会影响实验设计）**

1. **无 GPU**。任何深度学习方案（轨迹编码器 / TTT / 神经网络）只能 CPU 训练，
   在本机做 64 折 LOCO 级别的大规模神经网络实验不现实。
2. **CPU 是共享的**。本机同时运行其他 agent 的 CPU 密集进程，`elapsed_s` 只能当量级参考。
   需要可比耗时请独占运行并设 `OMP_NUM_THREADS=1`。
3. **内存 16 GB**。两个 pickle 全量载入约 0.4 GB，可接受；但 Bayreuth 875 MB 压缩包
   全量解压需注意峰值内存。

## 1. 已登记实验一览（手动维护）

| # | run_id | 配置 | 主指标 | 耗时 | 状态 |
|---|---|---|---:|---:|---|
| 1 | `20261107-201507_baseline_A_curve` | A_curve 54 维 / LOGO 11 折 / seed 0 | **6.587** | 41.3 s | ✅ 复现成功 |
| 2 | `20261107-201905_baseline_A_curve_loco` | A_curve 54 维 / LOCO 64 折 / seed 0 | **5.069** | 540.0 s* | ✅ 复现成功 |
| 3 | `20261107-203233_e1_reproduce_full_table` | 5 个特征集 / LOGO 11 折 / seed 0 | **6.020**（A_curve+C_ecm） | 570.0 s | ✅ 主表 5/5 复现 |

\* LOCO 耗时被并发进程拉高（见 §0 限制 2），无竞争时约 4 分钟。

## 2. 基线复现（本轮必做项）

### 目标

确认新框架 `code/rulkit` 与历史脚本 `scripts/e1_final.py` **数值等价**，
从而后续所有实验都可以在新框架上做，不再改动历史脚本。

### 命令

```bash
python code/run_baseline_a_curve.py --seeds 0 --protocols logo
python code/run_baseline_a_curve.py --seeds 0 --protocols loco --name baseline_A_curve_loco
```

### 结果

| 协议 | 折数 | 本框架 | `docs/e1_final_results.md` | 差 | 判定 |
|---|---:|---:|---:|---:|---|
| LOGO | 11 | 6.587 | 6.587 | +0.0004 | 一致 |
| LOCO | 64 | 5.069 | 5.069 | −0.0001 | 一致 |

行表：**2,813 行 / 64 电芯 / 11 工况组 / 54 维**，与权威记录完全一致
（`pulse_incomplete=0`、`cc_missing=0`、`after_eol=42` 行被裁掉）。
标签范围 0–77，均值 24.35。

### 结论（已验证）

1. **框架与历史脚本数值等价**：LOGO 与 LOCO 两条主结果都在第 3 位小数上一致。
   后续实验可以安全地在 `code/rulkit` 上进行。
2. **训练过程完全确定性**：单种子即可复现，与 `docs/e1_final_results.md` 的
   "4 个种子 std = 0" 结论一致。真正的方差来自划分与电芯抽样，必须用 bootstrap 刻画。
3. **耗时结构被分离出来了**：见下。

### 主表完整复现（run #3，LOGO，单种子）

| 特征集 | 维度 | 本框架 | `docs/e1_final_results.md` | 差 |
|---|---:|---:|---:|---:|
| A_curve | 54 | 6.587 | 6.587 | +0.0004 |
| A_curve + C_desc20 | 74 | 6.155 | 6.155 | +0.0003 |
| A_curve + C_desc30 | 82 | 6.109 | 6.109 | −0.0003 |
| **A_curve + C_ecm** | 84 | **6.020** | **6.020** | −0.0004 |
| C_ecm 单独 | 30 | 7.789 | 7.789 | +0.0004 |

**5 个特征集全部在第 3 位小数上一致，维度也全部一致（54 / 74 / 82 / 84 / 30）。**

配对 bootstrap（电芯级，5000 次）的点估计与改善比例也完全一致：
Δ = −0.432 / −0.479 / −0.568，改善电芯 64.1% / 62.5% / 62.5%。

#### 必须写清楚的复现细节：CI 端点差 0.00x 的来源（已定位并验证）

第一次跑出来的 95% CI 是 `[−0.796, −0.157]`（C_desc30）与 `[−1.002, −0.122]`（C_ecm），
与文档的 `[−0.811, −0.141]`、`[−0.999, −0.133]` 差 0.01–0.02，而 Δ 与改善比例完全相同。

原因**不是**数值错误：`scripts/e1_final.py` 在三个对比的循环**外面**只建了一个
`rng = np.random.default_rng(0)`，三个对比依次消耗同一条随机流；
本框架 `runner` 给每个对比各自新建 `default_rng(0)`。
所以**第一个对比（C_desc20）完全一致，后两个的 resample 下标不同**。

用 `code/check_bootstrap_rng.py` 以同一份分电芯误差重算，实测：

| 对比 | 共享随机流 | 文档值 | 独立随机流（本框架默认） |
|---|---|---|---|
| +C_desc20 | [−0.710, −0.144] | [−0.710, −0.144] | [−0.710, −0.144] |
| +C_desc30 | **[−0.811, −0.141]** | [−0.811, −0.141] | [−0.796, −0.157] |
| +C_ecm | **[−0.999, −0.133]** | [−0.999, −0.133] | [−1.002, −0.122] |

**结论（已验证）**：两种做法都是合法的 bootstrap，只是重采样下标不同；
框架与历史脚本在**点估计上完全等价**。引用 CI 时必须以文档的"共享随机流"值为准，
或显式声明所用随机流。这是真实的复现性细节，不是随机波动。

### 耗时结构（实测，全部在本机并发负载下测得）

| 环节 | 实测耗时 | 备注 |
|---|---:|---|
| 读两个 pickle（70 MB + 16 MB） | ~0.5 s | |
| 行表 + A_curve（54 维） | ~0.7 s（含读盘） | 14,373 条 CC 曲线分箱 |
| **2-RC 参数预计算（17,130 条 curve_fit）** | **125.6 s** | 一次性，之后命中缓存 |
| LOGO 11 折（1 个特征集） | 40.6 s ～ 81 s | 并发负载波动大 |
| LOGO 11 折 × 5 个特征集 | 569 s | run #3 |
| LOCO 64 折（1 个特征集） | 540 s | run #2 |

**关键结论（与直觉相反，已实测）**：计算时间由**折数 × HGB 拟合**主导，不是由 2-RC 拟合主导。
2-RC 只占 5 集 LOGO 全流程（126 + 569 ≈ 695 s）的约 18%。

这解释了 `scripts/e1_final.py` 的 32 分钟：它跑 5 个特征集 ×
（4 种子 × 11 折 LOGO + 1 × 64 折 LOCO）= **540 次模型拟合**，
按每次约 3.5 s 计正好约 32 分钟。

对本团队的直接含义：

1. 本框架用**单种子**即可：HGB 在该数据规模上确定性（std = 0，文档与本轮复现双向验证）。
   `e1_final.py` 的 4 个种子是纯重复计算，占它 540 次拟合里的 3/4。
2. 需要新特征时，2-RC 只付一次 126 s；之后每增加一个特征集的 LOGO 代价约 80–110 s。
3. 若要跑 LOCO × 5 特征集，预算约 45 分钟（并发负载下）。

## 3. 运行记录（自动追加，勿手工编辑）

## 20261107-201507_baseline_A_curve

| 项 | 值 |
|---|---|
| 名称 | baseline_A_curve |
| 时间 | 2026-11-07T20:15:48+0800 |
| 命令 | `python code/run_baseline_a_curve.py --seeds 0 --protocols logo` |
| 结果目录 | `code/results/20261107-201507_baseline_A_curve` |
| 行数 / 电芯 / 工况组 | 2813 / 64 / 11 |
| 标签范围 (min/mean/max) | 0.0 / 24.35 / 77.0 |
| 协议 | logo |
| 种子 | [0] |
| 模型 | HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0) |
| min_train | 100 |
| 耗时 | 41.3 s |

### 特征集与指标（cell-macro MAE，越低越好）

| 特征集 | 维度 | LOGO (mean±std) |
|---|---:|---:|
| A_curve | 54 | 6.587 |

### 折结构

- LOGO：11 折，使用 11 折，跳过 0 折（无），min_train=100

### 运行环境

| 项 | 值 |
|---|---|
| OS | Windows-10-10.0.19041-SP0 |
| Python | 3.8.7 |
| CPU 逻辑核 | 16 |
| 包版本 | numpy 1.24.4, scipy 1.10.1, sklearn 1.3.2, pandas 2.0.3, torch 2.4.1+cpu, lightgbm 4.6.0, xgboost 2.1.4 |
| git | research/autonomous-v2 @ 2b4cee1 |

### 备注

- 复现 docs/e1_final_results.md 的 A_curve 基线（LOGO 6.587 / LOCO 5.069）。
- 特征构造与 scripts/e1_final.py 的 build() 逐行等价，未做任何超参改动。
- 耗时拆分：数据加载+特征构造 0.7 s；其余为训练与落盘。

---

## 20261107-201905_baseline_A_curve_loco

| 项 | 值 |
|---|---|
| 名称 | baseline_A_curve_loco |
| 时间 | 2026-11-07T20:28:05+0800 |
| 命令 | `python code/run_baseline_a_curve.py --seeds 0 --protocols loco` |
| 结果目录 | `code/results/20261107-201905_baseline_A_curve_loco` |
| 行数 / 电芯 / 工况组 | 2813 / 64 / 11 |
| 标签范围 (min/mean/max) | 0.0 / 24.35 / 77.0 |
| 协议 | loco |
| 种子 | [0] |
| 模型 | HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0) |
| min_train | 100 |
| 耗时 | 540.0 s |

### 特征集与指标（cell-macro MAE，越低越好）

| 特征集 | 维度 | LOCO (mean±std) |
|---|---:|---:|
| A_curve | 54 | 5.069 |

### 折结构

- LOCO：64 折，使用 64 折，跳过 0 折（无），min_train=100

### 运行环境

| 项 | 值 |
|---|---|
| OS | Windows-10-10.0.19041-SP0 |
| Python | 3.8.7 |
| CPU 逻辑核 | 16 |
| 包版本 | numpy 1.24.4, scipy 1.10.1, sklearn 1.3.2, pandas 2.0.3, torch 2.4.1+cpu, lightgbm 4.6.0, xgboost 2.1.4 |
| git | research/autonomous-v2 @ 2b4cee1 |

### 备注

- 复现 docs/e1_final_results.md 的 A_curve 基线（LOGO 6.587 / LOCO 5.069）。
- 特征构造与 scripts/e1_final.py 的 build() 逐行等价，未做任何超参改动。
- 耗时拆分：数据加载+特征构造 0.7 s；其余为训练与落盘。

---

## 20261107-203233_e1_reproduce_full_table

| 项 | 值 |
|---|---|
| 名称 | e1_reproduce_full_table |
| 时间 | 2026-11-07T20:42:03+0800 |
| 命令 | `python code/run_e1_reproduce.py --protocols logo --seeds 0` |
| 结果目录 | `code/results/20261107-203233_e1_reproduce_full_table` |
| 行数 / 电芯 / 工况组 | 2813 / 64 / 11 |
| 标签范围 (min/mean/max) | 0.0 / 24.35 / 77.0 |
| 协议 | logo |
| 种子 | [0] |
| 模型 | HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0) |
| min_train | 100 |
| 耗时 | 570.0 s |

### 特征集与指标（cell-macro MAE，越低越好）

| 特征集 | 维度 | LOGO (mean±std) |
|---|---:|---:|
| A_curve | 54 | 6.587 |
| A_curve+C_desc20 | 74 | 6.155 |
| A_curve+C_desc30 | 82 | 6.109 |
| A_curve+C_ecm | 84 | 6.020 |
| C_ecm_only | 30 | 7.789 |

### 配对 bootstrap（电芯级，5000 次重采样，seed=0）

| 对比 | Δ | 95% CI | 改善电芯比例 |
|---|---:|---|---:|
| A_curve+C_desc20 vs A_curve | -0.432 | [-0.710, -0.144] | 64.1% |
| A_curve+C_desc30 vs A_curve | -0.479 | [-0.796, -0.157] | 62.5% |
| A_curve+C_ecm vs A_curve | -0.568 | [-1.002, -0.122] | 62.5% |
| C_ecm_only vs A_curve | +1.202 | [+0.414, +2.056] | 40.6% |

### 折结构

- LOGO：11 折，使用 11 折，跳过 0 折（无），min_train=100

### 运行环境

| 项 | 值 |
|---|---|
| OS | Windows-10-10.0.19041-SP0 |
| Python | 3.8.7 |
| CPU 逻辑核 | 16 |
| 包版本 | numpy 1.24.4, scipy 1.10.1, sklearn 1.3.2, pandas 2.0.3, torch 2.4.1+cpu, lightgbm 4.6.0, xgboost 2.1.4 |
| git | research/autonomous-v2 @ 2b4cee1 |

### 备注

- 完整复现 docs/e1_final_results.md 主表（5 个特征集 + 电芯级配对 bootstrap）。
- 2-RC 参数来自缓存 code/.cache/（键含数据指纹）；构建耗时 2.0 s。
- 特征构造与 scripts/e1_final.py 的 build() 逐行等价。