# code/ —— 统一实验框架（rulkit）

> 维护：Implementation & Experiment Engineer (A4)
> 状态：v0.1.0，2026-11-07。`scripts/` 下的历史脚本**不修改**，本目录只做新增。

## 为什么要有这一层

`scripts/e1_final.py` 把"特征构造 / 划分 / 训练 / 指标 / 落盘"写在一个 main 里，
后续任何新实验（新标签口径、新划分、新模型、新数据集）都得复制粘贴，容易出现
"同一实验两个数字"的问题。`rulkit` 把这些拆成可单独测试、可缓存的模块，
并强制每次运行都落盘 + 登记。

## 目录

```
code/
  rulkit/
    __init__.py    版本与模块说明
    env.py         环境快照（python / 包版本 / CPU / git），写进每条结果
    data_uconn.py  UConn pickle 只读读取 + 数据指纹（用于缓存失效）
    features.py    统一特征构造：A_curve / C_desc20 / C_desc30 / C_ecm + 标签 y
    splits.py      统一 LOGO / LOCO 折生成（与 e1_final.py 语义一致）
    metrics.py     电芯宏平均 MAE、配对 bootstrap、分电芯误差
    models.py      模型工厂（固定超参，跨实验共用）
    cache.py       昂贵特征缓存（波形描述子 / 2-RC 拟合）
    runner.py      统一执行 + 落盘（JSON + 预测矩阵 + 折日志）
    registry.py    追加写入 EXPERIMENT_REGISTRY.md（只追加）
  run_baseline_a_curve.py   A_curve 基线复现（本轮必做）
  precompute_ecm.py         2-RC 参数预计算（约 30 分钟，只需跑一次）
  results/<run_id>/         每次运行一个目录
```

## 特征集（与 docs/e1_final_results.md 对齐）

| 名称 | 维度 | 内容 |
|---|---:|---|
| `A_curve` | 54 | CC 放电曲线按平均电压排序拼接 → 50 bin 均值 + mean/std/min/max |
| `A_curve+C_desc20` | 74 | + 6 个 (SOC×方向) 的 ΔV / τ / 残差 + 2 个 ΔV 标准差 |
| `A_curve+C_desc30` | 82 | + 6 个初始斜率 + τ 标准差 + 充电段面积均值 |
| `A_curve+C_ecm` | 84 | + 6 个 (SOC×方向) 的两节 RC 参数 (c, a1, t1, a2, t2) |
| `C_ecm_only` | 30 | 只有两节 RC 参数 |

**已知局限（勿在论文里含糊）**：`C_ecm` 里的 `t1/t2` 是"采样点索引"当时间常数用，
物理单位不成立（RESEARCH_STATE 问题 B）。这一层只在"同等维度下的表示能力"意义上解释。

## 标签口径

```
y = eol_rpt - rpt,   eol_rpt = 该电芯首个 SOH <= 80 的体检轮次
```

即"**剩余体检次数**"，不是真实循环数、也不是日历时间（RESEARCH_STATE 问题 A）。
重建真实时间目标需要 `num_cycles` 与体检时间戳，见后续实验。

## 统一划分

| 协议 | 折键 | 折数 | 用途 |
|---|---|---:|---|
| `logo` | `group_id` | 11 | 主结果（留一工况组，最严格） |
| `loco` | `cell_id` | 64 | 留一电芯 |

`min_train=100` 的折被跳过，预测保持 NaN，指标只在非 NaN 行上算（与历史脚本一致）。

## 指标

主指标 **cell-macro MAE**：先在每个电芯内部求平均绝对误差，再对电芯取平均
（每个电芯等权，避免长寿命电芯主导）。显著性用**电芯级配对 bootstrap**（5000 次），
而不是种子间方差——HGB 在本数据规模上是确定性的，种子不产生方差。

## 如何跑一次新实验

```python
import sys, os
sys.path.insert(0, os.path.join(REPO_ROOT, "code"))
from rulkit import cache, data_uconn, features, runner

dp = data_uconn.load_pulse()
dc = data_uconn.load_cc()
rows = features.build_rows(dp, dc)
desc, ecm, path, hit = cache.descriptors(REPO_ROOT, dp, rows["rec"], want_ecm=True)
X = features.assemble(rows, desc=desc, ecm=ecm,
                      sets=["A_curve", "A_curve+C_ecm"])

result = runner.run(
    name="my_experiment",
    X_sets=X,
    y=rows["y"], cells=rows["cells"], grp=rows["grp"], rpts=rows["rpts"],
    protocols=("logo",), seeds=(0,),
    repo_root=REPO_ROOT,
    meta={"command": "...", "notes": ["..."]},
)
```

`runner.run` 会自动：建 `code/results/<run_id>/`、写 `result.json` /
`preds.npz` / `preds.csv` / `fold_log.json`，并**追加**一条记录到
`docs/autonomous_research/EXPERIMENT_REGISTRY.md`。

## 复现性注意：bootstrap 的随机流

`scripts/e1_final.py` 在三个对比的循环**外面**建了一个 `rng = np.random.default_rng(0)`，
三个对比依次消耗同一条随机流；`runner` 默认给每个对比各自新建 `default_rng(0)`。
后果：**第一个对比的 CI 完全一致，后续对比的 CI 端点差 0.01–0.02**（点估计与改善比例不受影响）。

```bash
python code/check_bootstrap_rng.py   # 用同一份分电芯误差对比两种随机流
```

实测（`docs/e1_final_results.md` 的值 = 共享随机流）：

| 对比 | 共享随机流 | 独立随机流 |
|---|---|---|
| +C_desc20 | [−0.710, −0.144] | [−0.710, −0.144] |
| +C_desc30 | [−0.811, −0.141] | [−0.796, −0.157] |
| +C_ecm | [−0.999, −0.133] | [−1.002, −0.122] |

引用 CI 时以文档值为准，或显式声明所用随机流。

## 单种子就够了

HGB 在 2,813 行 / 54–84 维上是确定性的（`docs/e1_final_results.md` 记 4 种子 std = 0，
本轮 LOGO/LOCO 单种子复现也证实）。`e1_final.py` 的 4 个种子是纯重复计算。
真正的不确定性来自**划分与电芯抽样**，用配对 bootstrap 刻画。

## 缓存现状（2026-11-07）

`code/.cache/desc_21fa1cc835f9.npz` 已生成：17,130 条记录的波形描述子 + 2-RC 参数，
耗时 125.6 s。后续所有需要 `C_ecm` 的实验直接命中缓存（键含数据指纹，数据一换自动失效）。

## 硬性约定

1. **先登记后跑**：不写 registry 的实验不算数。
2. **随机性必须显式**：`seeds=` 显式传入，禁止隐式随机（HGB 的 `random_state` 由 runner 统一注入）。
3. **不覆盖历史**：`results/` 下每个 run 一个新建目录（`exist_ok=False`，重名直接报错）。
4. **不修改** `scripts/` 下的历史脚本与 `docs/` 下的历史结果。
5. **缓存失效**：缓存键含数据文件大小+mtime，数据换了会自动重算。

## 环境

Python 3.8.7 / numpy 1.24.4 / scipy 1.10.1 / scikit-learn 1.3.2 /
pandas 2.0.3 / torch 2.4.1+cpu（无 CUDA）/ lightgbm 4.6.0 / xgboost 2.1.4。
CPU：i5-13400F，10 物理核 / 16 逻辑核，16 GB 内存。

> 注意：本机常有其他 agent 的 CPU 密集进程并发，`elapsed_s` 只能作为量级参考，
> 不能当作严格基准。需要可比耗时请用 `OMP_NUM_THREADS=1` 并独占运行。