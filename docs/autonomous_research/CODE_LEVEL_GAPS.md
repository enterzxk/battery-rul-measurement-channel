# 代码层面的未解决问题（CODE-LEVEL GAPS）

> 作者：Code Auditor 子代理（本文件为本次任务独占写入）
> 日期：2026-11-07
> 目的：**从代码出发**找高水平论文的实现局限，为下一个研究方向找依据。
> 原则：只写**我亲自读到的代码行**。凡未读到、未验证、未复现的，都在第 7 节显式标注。

---

## 0. 证据边界（先读这一节，再看结论）

### 0.1 仓库与版本

| # | 仓库 | 论文/会议 | clone 的 HEAD | 提交日期 |
|---|---|---|---|---|
| R1 | PenelopeJones/battery-forecasting | Nat Commun 2022, 13:4806（Jones & Lee） | `b5c865e25c4a08991e2826d928b30d6d808bf858` | 2022-07-13 |
| R2 | Ruifeng-Tan/BatteryLife | KDD 2025 | `3b17bb53202e10711deae0448c91f84144bb3dd9` | 2026-08-17 |
| R3 | microsoft/BatteryML | NeurIPS 2024 D&B | `2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd` | 2024-12-18 |
| R4 | wang-fujin/PINN4SOH | Nat Commun 2024, 15:4332 | `cc3cc5053caf38f04e0665f7f88cb109144d035e` | 2026-09-02 |

全部 `git clone --depth 1`，落在 `external/repos/`。行号均指上述 HEAD。

### 0.2 阅读等级（硬约束：未读到的必须标注）

| 对象 | 等级 |
|---|---|
| 四个仓库的**代码** | **全文精读**（每条发现都能在给定行号复现） |
| R1 论文正文 | **仅摘要**（Nature 网页抓取；未读 Methods/Supplementary） |
| R2 论文正文 | **仅 README + 代码**（KDD 论文 PDF 未读） |
| R3 论文正文 | **仅 README + 代码**（arXiv 2310.14714 未读） |
| R4 论文正文 | **仅 README + fix.md + 代码**（Nat Commun 正文与 Supplementary 未读） |
| 四个仓库的**原始数据** | **未读**。R1 完全没有 `data/` 目录；R2/R3 需从 HuggingFace/Zenodo 下载；R4 带预处理后的 CSV（16 维统计特征 + capacity），非原始曲线。**因此本文没有任何端到端复现实验，全部结论是静态代码审计。** |
| 本项目 UConn 原始数据 | **未读**。凡涉及 UConn 结构的描述，均来自 `docs/autonomous_research/RESEARCH_STATE.md` 与 `INNOVATIONS_AND_RESULTS.md`，属二手转述 |

### 0.3 为什么这种审计值得做

本项目自己的致命错误（拟合窗把载流点算进去）在正文、摘要、Limitations 里都看不出来，只存在于代码里。下面 24 条同理：**每一条都是"论文不会写、审稿人不会查、但直接决定数字真假"的东西。**

---

## 1. R1 battery-forecasting（Nat Commun 2022，EIS + XGBoost）

### 1.1 逐条发现

#### F1｜通道消融的样本集不固定：任一通道缺失即整行丢弃
- **文件/行**：`utils/exp_util.py:213-215`（`extract_data`），同样逻辑在 `:871-873`（`extract_n_step_data`）
- **原文**：
`@python
if any(elem is None for elem in (eis_d, t_charge, cap_c, cap_d)):
    #print('{:02d}\t{} {} {}'.format(true_cycle, t_charge, cap_c, cap_d))
    continue
`@
- **为什么是问题**：这篇论文的核心实验是"输入通道消融"（`eis-*` / `cvfs-*` / `ct-*` / `ecm*`，见 `exp_util.py:593-718` 的 20 多个分支）。但样本是否进入数据集，取决于**四条通道是否同时解析成功**。也就是说，"EIS-only"模型的训练/测试样本，仍然是被"充电容量、放电容量、充电时间都可用"筛过的那批。**通道消融没有做到通道隔离**：去掉的是特征，不是样本选择偏差。更糟的是 `models.py:117-118` 的划分是按 cell 名字取的，同一个 cell 在不同 input_name 下的行数可能不同，于是不同消融之间的 train/test 点集也不完全一致。
- **暗示的方向**：真正的通道隔离要求 (a) 报告每个通道的逐样本可用性掩码；(b) 消融时固定"所有通道都可用"的共同子集，或 (c) 直接做 missing-modality 训练（mask token，而不是 drop row）。本项目正在做的"非循环测量通道"研究，如果也按"缺就丢"，会重复这个错误。

#### F2｜裸 `except` 把解析失败静默变成 None，没有任何计数
- **文件/行**：`utils/exp_util.py:190-193`、`:196-203`、`:205-211`
- **原文**：
`@python
try:
    eis_d = eis_features(ptf_discharge_eis, new_log_freq=new_log_freq, n_repeats=1)
except:
    eis_d = None
`@
- **为什么是问题**：`except:` 捕获 `KeyboardInterrupt` 与 `MemoryError`，且不打印、不计数、不落盘。一个坏文件（列数不对、频段不覆盖、reshape 失败）与"这台设备根本没测 EIS"在数据层面完全不可区分。`INNOVATIONS_AND_RESULTS.md` 里那条"6/30 维为常数"的教训同源：**失败被静默吸收，最终以"特征没信息"的形式出现在结果里**。
- **暗示的方向**：任何波形/弛豫管线都必须有"丢弃账本"（drop ledger）：每条样本被丢的原因、条数、占比，随结果一起发布。这本身可以是一篇方法学短文的核心贡献（provenance-aware preprocessing）。

#### F3｜EIS 被硬插值到固定频段网格，越界即抛错→被 F2 吞掉→样本消失
- **文件/行**：`utils/exp_util.py:69`（网格定义）、`:563-568`（插值）
- **原文**：
`@python
new_log_freq = np.linspace(-1.66, 3.9, 100)      # L69
...
f1 = interp1d(log_freq, re_z, kind='cubic')      # L563
f2 = interp1d(log_freq, im_z, kind='cubic')      # L564
re_z = f1(new_log_freq)                          # L567
im_z = f2(new_log_freq)                          # L568
`@
- **为什么是问题**：`interp1d` 默认 `bounds_error=True`。任何一台仪器的频段比 10^-1.66–10^3.9 Hz（约 0.022–7943 Hz）窄，插值就抛 `ValueError`，被 F2 吞掉，**整条样本静默消失**。也就是说：**"频段"这个物理量，在这份代码里不是特征，而是隐式的入选标准**。同一批电芯若换了量程，样本量会变，而论文只会报"我们用了 N 条谱"。
- **暗示的方向**：跨数据集 EIS 的第一性问题不是模型，而是**频段对齐**：要么把特征定义在"重叠频段"上（并对重叠度做敏感性分析），要么把频段本身作为协变量建模。这是 R1 完全没有处理的。

#### F4｜两段式 CC-CV 被写成 `assert`，换协议即整 cell 全丢
- **文件/行**：`utils/exp_util.py:452`
- **原文**：`assert change.shape[0] == 2, "Error in computing time to change"`
- **为什么是问题**：`change` 是"电流为 0 的连续段"的边界数。作者假设每个充电循环恰好有 **2 段静置**（CC 后一段、CV 后一段）。一旦协议是三段（如 CC-CV-hold）、单段（纯 CC）、或数据里多了一段静置，断言失败 → `AssertionError` → 被 `:199` 的裸 except 捕获 → `t_charge=None` → 该循环被 F1 丢弃。**一条与物理无关的协议假设，直接决定整个 cell 是否进入数据集。**（同一函数 `:474` 还用 `df.iloc[idx_start2]`、`:459` 用 `idx_change2-1`，都建立在这个"恰好两段"的假设上。）
- **暗示的方向**：充电阶段划分应当是**数据驱动**的（找 `i==0` 的游程、按时长/容量占比判定），并对"阶段数≠2"的样本单独建档。我们 UConn 的 RPT 若是恒流恒压以外的协议，这条会立刻炸。

#### F5｜轨迹被硬截断在 30 个"循环块"、每块 4 步
- **文件/行**：`utils/exp_util.py:68`（`n_steps = 4`）、`:172`（`for cycle in range(start_cycle, start_cycle+30)`）、`:178`（`true_cycle = 1+(cycle-2)*n_steps + step`）、`:825`（同样的 30）
- **原文**：`for cycle in range(start_cycle, start_cycle+30):`
- **为什么是问题**：每条轨迹最多 30×4=120 点，且"真实循环号"由 `1+(cycle-2)*4+step` 反推——**假设每个循环块恰好 4 个测量段**。这两条硬编码一起，把"寿命"截成了"前 120 次体检"。对 UConn 这种 RPT 间隔不等（本项目已测：67.6–133.7 循环/次）的数据，`true_cycle` 公式给出的不是循环数，而是一个自造的序号。**这正是我们 P2（代理单位）在别人代码里的同构体**：标签单位由代码里的算术式决定，而不是由物理量决定。
- **暗示的方向**："标签轴重建"不是我们一家的洁癖，而是这一整类代码的共性缺陷。可做成一个通用工具：从原始文件时间戳重建真实循环/日历轴，并量化"序号轴 vs 真实轴"对排序与 MAE 的影响。

#### F6｜留二电芯交叉验证 + **点级** bootstrap，集成方差不是电芯间方差
- **文件/行**：`utils/models.py:117-118`（测试电芯）、`:142`（`n_bootstrap = int(0.9*X_train.shape[0])`）、`:156`（`idx = np.random.permutation(X_train.shape[0])[0:n_bootstrap]`）
- **原文**：
`@python
n_bootstrap = int(0.9*X_train.shape[0])                        # L142
idx = np.random.permutation(X_train.shape[0])[0:n_bootstrap]   # L156
`@
- **为什么是问题**：10 个"集成成员"各自对**点**做 90% 无放回子采样，然后 `np.sqrt(np.var(...))` 当作预测不确定度（`:192-194`）。但每个 cell 贡献约 117 个高度自相关的点，点级重采样几乎不动电芯构成——**这个"不确定度"度量的是点噪声，不是电芯间异质性**。把它当置信区间报出去，会系统性低估跨电芯泛化误差。这与我们 P3（ICC=0.414、design effect=2.99、等效 n=21.4）是同一个错误的两种外观。
- **暗示的方向**：**按电芯/工况做 cluster bootstrap**，并在论文里同时报"点级 CI"和"簇级 CI"两个数。我们 v2 已经证明这两个 CI 会给出相反结论（电芯级不含零、工况簇跨零）。这条可以直接写成方法学贡献。

#### F7｜同一行日志里混用两种聚合单位
- **文件/行**：`utils/models.py:301-310`
- **原文**：
`@python
r2s_te.append(r2_score(y_test1, y_pred_te1))            # 每 cell 一个 R2
pes_te.append(np.abs(y_test1 - y_pred_te1) / y_test1)   # 每点一个 APE
...
r2_te = np.median(np.array(r2s_te))                     # 对 cell 取中位数
pe_te = 100*np.median(np.hstack(pes_te).reshape(-1))    # 对点取中位数
`@
- **为什么是问题**：`Test R2` 的单位是"电芯×划分"，`Test error` 的单位是"点"。两者写在同一行日志、同一张表里，读者会默认它们是同一个推断单位。长寿命电芯点多、权重自然大；短寿命电芯点少、被稀释。**这是 P2/P3 的第三个同构体**，而且是最隐蔽的一种：不是算错，是"两种单位被并排放"。
- **暗示的方向**：报告规范应强制标注每条指标的**推断单位**（cell / condition / point），并对单位不匹配的组合给出警告。可作为"评估协议审计"清单的一条。

#### F8｜数据效率实验无随机种子、硬编码 24 个电芯
- **文件/行**：`experiments/data-efficiency.py:22-23`、`:44`、`:83`
- **原文**：
`@python
n_cells_list = [2, 4, 8, 16, 20]     # L22
p = np.random.permutation(24)        # L23
`@
- **为什么是问题**：`np.random.permutation(24)` 没有 seed，且 24 是写死的（variable-discharge 只有 3 cell/channel × 8 channel = 24）。`XGBModel.__init__` 里虽然有 `np.random.seed(start_seed+10)`（`models.py:55`），但它在**排列之后**才被调用，管不到 L23。**"数据效率曲线"这张图每次运行都不一样，且无法复现。** 另外 `cell_ids_s = cell_ids[0:n_cells+2]`（L44）算出来只作为构造参数传入，真正的划分在 L48-50 另行计算，两处口径不一致。
- **暗示的方向**：数据效率/少样本结论必须报**多种子均值±方差**。我们自己 v2 里"n=11 工况、检出 d≈0.4 需 49 工况"的结论，同样要求把"种子方差"和"工况方差"分开报。

#### F9｜迁移实验用的模型配置与主实验不同（10/25/2 vs 100/500/10）
- **文件/行**：`experiments/variable-discharge-train.py:12-15`、`experiments/fixed-discharge-predict.py:17`
- **原文**：
`@python
params = {'max_depth':10, 'n_splits':2, 'n_estimators':25, 'n_ensembles':2}   # variable-discharge-train.py:12-15
pred_fixed, pred_fixed_err = ensemble_predict(x_fixed, 'variable-discharge', input_name)  # fixed-discharge-predict.py:17
`@
- **为什么是问题**：`fixed-discharge-predict.py` 加载的是 `variable-discharge-train.py` 产出的 `{experiment_name}_{i}.pkl`（`models.py:332` 的命名，无 cell 后缀），而那套模型是用 `max_depth=10, n_estimators=25, n_ensembles=2` 训的——与主实验的 `max_depth=100, n_estimators=500, n_ensembles=10`（`next-cycle-capacity.py:12-15`）差一个数量级。**"训练于变工况、测试于固定工况"这条泛化结论，是在一个明显更弱的模型上得到的**，而仓库里没有任何一处说明这件事。
- **暗示的方向**：跨工况迁移的结论对**容量**极其敏感（树深/树数直接决定外推能力）。任何"跨工况"声明都应附"容量曲线"（learning curve）而不是单点。这也解释了我们 v1→v2 的一个现象：方法层四条路线全负，很可能部分是容量/正则没调，而不是方法本身不行。

### 1.2 对 R1 五问的直接回答

| 问题 | 回答 |
|---|---|
| ① 静默丢弃/填充/插值 | **有，且很严重**。丢弃：`:213-215`、`:871-873`（任一通道 None 即丢整行）；`:190-193/199/208` 裸 except。插值：`:563-568` 三次插值到固定 100 点频段，越界即抛错→被吞。填充：未发现 NaN 填充，但有 `:272-273` 构造了 `cap_inits/eis_inits` 却从未使用（死代码）。 |
| ② 划分与指标 vs 论文 | 划分是**留二电芯**（`models.py:117-118`），不是留一工况；电芯按**硬件通道**分组（`exp_util.py:720-763` 的 `cell_map`），同一通道的电芯分处 train/test，**通道效应与电芯效应混杂**。指标：R2（按 cell 取中位）+ APE（按点取中位），两种单位并列（F7）。论文摘要声称 "single EIS measurement, without any knowledge of usage history"，但仓库主脚本 `next-cycle-capacity.py:21` 的三个输入名全部含 `cvfs`（当圈放电曲线）+ `ct`（累计吞吐）+ `c`（当前容量）——**这三者都编码了使用历史**。只有 `eis-actions` 一种与摘要描述相符。**哪一种产生了论文的主数字，仓库里没有任何配置/种子/结果映射可以追溯。** |
| ③ 硬编码假设 | 频率网格 `linspace(-1.66,3.9,100)`；`n_steps=4`；30 个循环块；`cell_no in [145,146,147,148]` 特判（`:126-129`、`:806-809`）；`d_rate = dfd['i'][-10]*-1`（`:400`，取倒数第 10 个电流样本当倍率）；`ocv = mean(df.iloc[0:5].ewe)`（`:445`）；`(c1*t1+c2*t2)/3600`（`:472`，秒→小时）；`t_charge/3600`（`:478`）。 |
| ④ TODO/FIXME/死代码 | 无 TODO/FIXME（grep 零命中）。但有**死分支**：`exp_util.py:76` 令 `nl=0` 后，`:274-291` 的 `elif nl == 1` 永不执行；`models.py:94-97` 的 `split_into_four` 写死了 `PJ248–PJ279` 共 32 个电芯名，而 `identify_cells`（`:720-763`）里根本没有这些电芯；`models.py:13-51` 整段 `d3pg` 旧代码被三引号注释掉。 |
| ⑤ 用到 UConn 第一个崩的地方 | `utils/exp_util.py:352-355`（`discharge_features`）：<br>`while len(df.columns) != 7: print('Wrong parameters exported...'); time.sleep(120)`<br>UConn 没有 `GCPL`/`GEIS` 的 tab 分隔原始导出文件，`pd.read_csv` 要么抛 `FileNotFoundError`（被外层 except 吞成 None，然后 F1 把**所有**样本丢光，得到空数据集并在 `np.vstack` 处炸），要么读进一个列数≠7 的表 → **进入 120 秒睡眠的无限重试循环，脚本静默挂死**。这不是崩溃，是挂起，比崩溃更难查。 |

---

## 2. R2 BatteryLife（KDD 2025，跨源电池寿命基准）

### 2.1 逐条发现

#### G1｜未达 EOL 的电芯被整条丢弃，无计数、无删失建模
- **文件/行**：`data_provider/data_loader.py:342-344`
- **原文**：
`@python
if eol is None:
    # This battery has not reached end of life
    continue
`@
- **为什么是问题**：寿命预测数据集天然**右删失**（实验停了但电芯没坏）。这里把删失样本整体删掉，等价于"只保留已经死掉的电芯"。删失样本恰恰是**长寿命**那一端，删掉它们会让标签分布左偏，并让模型系统性低估寿命。README 高调宣传的 "990 batteries with life labels"（README:30）——**这个 990 已经是删失之后的口径，不是采集口径**。整条路径没有 print、没有计数、没有写日志。
- **暗示的方向**：删失感知的损失（censored likelihood / survival NLL）在电池寿命预测里几乎是空白。这是**一个有明确代码证据的空白**，不是凭空想的 gap。

#### G2｜容量异常行被整行置 NaN 再 `bfill`，会把别的循环的数据搬进来
- **文件/行**：`data_provider/data_loader.py:462-464`
- **原文**：
`@python
cycle_df.loc[cycle_df['charge_capacity_in_Ah']<0] = np.nan # deal with outliers in capacity
cycle_df.loc[cycle_df['discharge_capacity_in_Ah']<0] = np.nan
cycle_df.bfill(inplace=True) # deal with NaN
`@
- **为什么是问题**：`df.loc[mask] = np.nan` 是**整行**赋值——电压、电流、时间、`cycle_number` 全部变 NaN，不只是容量列。随后 `bfill()` 用**下一行**的值回填：`time_in_s` 会倒退（拿到更晚的时间戳），`cycle_number` 会被改写成下一行的循环号（如果异常行正好在循环末尾，就跨循环污染），容量则变成下一采样点的值。**"清洗"实际上是在循环内部（甚至循环之间）做了一次无约束的行复制。** 而且全程无日志。
- **暗示的方向**：数据清洗必须**列级**、**可追溯**、**带语义约束**（时间必须单调、循环号必须不变）。这类 bug 在四个仓库里以不同形式重复出现（见 D2），说明它是个系统性问题，不是个别疏忽。

#### G3｜所有样本共享同一条"前 100 循环"曲线，只改 mask；标签恒为 EOL 而非 EOL−i
- **文件/行**：`data_provider/data_loader.py:497`、`:501-523`
- **原文**：
`@python
early_charge_discharge_curves_data = charge_discharge_curves_data[:self.early_cycle_threshold]   # L497
...
for i in range(self.seq_len, self.early_cycle_threshold+1):
    ...
    tmp_attn_mask = np.zeros(self.early_cycle_threshold)
    tmp_attn_mask[:i] = 1 # set 1 not to mask                                    # L511-512
    labels.append(eol)                                                            # L523
`@
- **为什么是问题**：同一个电芯的第 5 个样本和第 100 个样本，**输入张量完全相同**（都是前 100 圈的曲线矩阵），只有 attention mask 不同；标签永远是 `eol`，不是 `eol - i`。这意味着：(a) 模型若在任何池化/归一化步骤中未严格遵守 mask，就直接看到未来（我**没有**逐个核对 18 个模型的 forward，见第 7 节）；(b) 任务定义是"从 k 圈数据估计**总寿命**"，不是"剩余寿命"。二者在 i 很小时数值接近，在 i→100 时差 100 圈。**论文叫 RUL，代码算的是 total life。** 这与我们 P2 是同一类错误：**标签的单位（总量 vs 剩余量）由代码决定，而不是由论文定义决定**。
- **暗示的方向**："RUL vs total-life"的口径必须显式声明，并给出两者互转时的偏差界。我们的 `num_cycles = 相邻 RPT 间段长`、`cumsum` 为真实循环轴，正是同一个问题的本地版本。

#### G4｜缺循环用全零曲线填充，NaN 检查查不出来
- **文件/行**：`data_provider/data_loader.py:544-546`、`:620-622`
- **原文**：
`@python
else:
    # fill zeros when the cell doesn't have enough cycles
    curve_data = np.zeros((3, self.charge_discharge_len))    # L621-622
`@
- **为什么是问题**：`for cycle in range(1, early_cycle_threshold+1)` 里，文件里没有的循环直接塞一条全零曲线。而 `:234-237` 的健全性检查只查 `np.isnan`，**查不出零**。于是"这台电芯第 37 圈没测"与"第 37 圈容量为 0"在数据里不可区分。模型会把全零当成真实的退化信号。另外 `:507-509` 对 CALB 有 `if i > valid_cycle_number: break`（注释说"只有 99 圈数据"），但那只截断样本数，不解决曲线矩阵里的零填充。
- **暗示的方向**：缺失必须以**掩码**进入模型（learnable missing embedding），而不是零向量。这是"非循环测量通道"研究可以直接复用的机制。

#### G5｜电压按本循环最大值归一、容量按数据集级常数归一
- **文件/行**：`data_provider/data_loader.py:614-616`；容量常数在 `:446-451`
- **原文**：
`@python
voltage_records = voltage_records.reshape(1, self.charge_discharge_len) / max(voltage_records)  # L614
current_records = current_records.reshape(1, self.charge_discharge_len) / nominal_capacity      # L615
capacity_in_battery = capacity_in_battery.reshape(1, self.charge_discharge_len) / nominal_capacity  # L616
`@
`@python
if file_name.startswith('RWTH'):
    nominal_capacity = 1.85            # L446-447
elif file_name.startswith('SNL_18650_NCA_25C_20-80'):
    nominal_capacity = 3.2             # L448-449
`@
- **为什么是问题**：两处硬编码假设。(a) 电压除以**本循环自己的最大值**——绝对电压水平（正是退化最直接的信号之一）被彻底消掉，只剩形状；同一电芯早期与晚期的 4.2 V 与 4.05 V 被映射到同一个 1.0。(b) 电流/容量除以 `nominal_capacity`，而这个"额定容量"是**按文件名字符串**给的常数（RWTH 全系 1.85 Ah、某个 SNL 子系 3.2 Ah），不是每个电芯的实测 BOL 容量。若某个 RWTH 电芯实际是 2.0 Ah，它的 C-rate 与 SOH 分母同时错 8%。**这是"容量参照硬编码"的教科书案例**，也正是我们 P2 讨论的尺度问题在别人代码里的形态。
- **暗示的方向**：SOH 的分母应当**每电芯**从 BOL 若干圈估计，并作为协变量/不确定性一起传播。我们 Bayreuth 那套"小时单位 + 独立实现"的经验说明：分母选错，结论方向都会变。

#### G6｜按"采样点序号"线性重采样，而不是按容量/时间轴
- **文件/行**：`data_provider/data_loader.py:629-644`
- **原文**：
`@python
raw_bases = np.arange(1, len(voltages)+1)
interp_bases = np.linspace(1, len(voltages)+1, num=charge_discharge_len, endpoint=True)
interp_voltages = np.interp(interp_bases, raw_bases, voltages)
`@
- **为什么是问题**：把一条曲线的**第 k 个采样点**当作自变量。不同循环、不同倍率、不同记录频率下，同样的"第 50 个点"对应完全不同的容量位置。重采样后的 100 点曲线因此**不是同一个物理量的采样**，跨倍率/跨数据集的形状差异里混进了采样率差异。这条与 F5（R1 的序号轴）是同一个病：**用序号冒充物理轴**。
- **暗示的方向**：统一到"容量轴"或"归一化时间轴"重采样，并把重采样方式作为消融项。这对跨源基准尤其致命——不同实验室的记录频率差 1–2 个数量级。

#### G7｜公开的评估入口脚本跑不起来：`args.alpha` 未定义
- **文件/行**：`evaluate_model.py:161-162`（只定义了 `--alpha1/--alpha2`）、`:184-185`（读 `args.alpha`）、`:38`（函数体内 `alpha` 是自由变量）
- **原文**：
`@python
parser.add_argument('--alpha1', type=float, default=0.15, ...)   # L161
parser.add_argument('--alpha2', type=float, default=0.1,  ...)   # L162
...
alpha = args.alpha                                                # L184  <- Namespace 无此属性
alpha2 = args.alpha2                                              # L185
`@
- **为什么是问题**：argparse 命名空间里没有 `alpha`（只有 `alpha1`）。L184 在 `args.__dict__ = args_json`（L191）**之前**执行，所以拿不到 json 里的键 → `AttributeError`，脚本在第一屏就死。即便绕过，`calculate_metrics_based_on_seen_number_of_cycles`（L28）的函数体在 L38 用了 `alpha`，而形参叫 `alpha1` —— 又一处 `NameError`。**这说明评估脚本在最后一次重构后没有被完整跑过。**
- **暗示的方向**：论文里"α-accuracy 随观测圈数变化"的那张曲线（对应仓库里的 `figures/error_curve.pdf`），其生成路径**不可执行**。任何引用该曲线的复现工作都会卡在这里。这提醒我们：**别把"代码公开"当成"结果可复现"**。

#### G8｜per-cycle 指标函数的调用处 `dataset` 未定义
- **文件/行**：`evaluate_model.py:397`
- **原文**：`calculate_metrics_based_on_seen_number_of_cycles(total_preds, total_references, total_seen_number_of_cycles, alpha, alpha2, args.model, dataset, finetune_dataset=finetune_dataset, start=args.seq_len, end=args.early_cycle_threshold, seed=args.seed)`
- **为什么是问题**：该文件里只有 `trained_dataset`（L193）和 `args.dataset`，没有裸 `dataset` → `NameError`。而且这个函数内部（L32-43）对每个 cycle 数 `number` 都做 `hit_num / len(references)`，**当某个 cycle 数没有样本时是 0/0**，直接 `ZeroDivisionError`。两条独立的致命路径，都落在"逐圈精度曲线"这条产线上。
- **暗示的方向**：同上。**评估代码比训练代码更容易烂掉，因为它跑得少。** 我们自己的 `docs/e1_v2_fixed_results.md` 那类复核，应当把"评估脚本能否从零跑通"列为验收项。

#### G9｜划分是 200+ 个写死的文件名，seen/unseen 是第二份手写 JSON
- **文件/行**：`data_provider/data_split_recorder.py:1-106`（整个文件就是一份电芯名单）
- **原文**（节选）：`CALB_42_test_files = ['CALB_35_B247.pkl', 'CALB_0_B185.pkl', 'CALB_0_B182.pkl', 'CALB_25_T25-2.pkl', 'CALB_25_T25-1.pkl']`（L77）
- **为什么是问题**：划分**不是规则，是快照**。没有"按温度留一"、没有"按倍率留一"的函数，只有 26 组手写列表。我核对了 `dataset/seen_unseen_labels/cal_for_test_CALB42.json`：`CALB_25_T25-1/2` 标 `unseen`，`CALB_0_*`、`CALB_35_*` 标 `seen`——**与"25 ℃ 未出现在训练集"一致，这一点作者做对了**。但代价是：新增一个数据集（例如 UConn）必须同时改 `data_split_recorder.py`、`data_loader.py` 的 if/elif 前缀链（L379-431）、`datasetName2ids`、以及再造一份 `cal_for_test_*.json`。**基准的"可扩展性"是零。**
- **暗示的方向**：需要一个**声明式**的划分 DSL（按元数据字段过滤：温度/倍率/SOC 窗/化学体系），并自动生成 seen/unseen 标签。我们 11 个工况组、64 电芯的 LOGO，正好可以直接用这种 DSL 表达，避免"手写名单"的不可审计性。

#### G10｜寿命分箱是硬编码的，且训练用得到
- **文件/行**：`data_provider/life_classes.json`（全文 1 行）；`data_provider/data_loader.py:346-350`
- **原文**：`{"1":[0,300],"2":[300,1000],"3":[1000,2000],"4":[2000,100000000]}`
- **为什么是问题**：四个箱子的边界（300/1000/2000 圈）是拍出来的，没有引用、没有敏感性分析。它进入 `class_labels` → `scaled_life_classes`（L247/255）→ 对比学习的伪类。**分箱边界直接改变训练目标**，而论文（据 README 的 benchmark 表）只报 MAPE/α-accuracy，看不出这个自由度。若某数据集寿命集中在 900–1100 圈，第 2/3 类几乎不可分，对比学习信号就退化了。
- **暗示的方向**：寿命分箱应当**按数据集分位数自适应**，或干脆去掉（回归即可）。任何"分类型辅助损失"都要报边界敏感性。

### 2.2 对 R2 五问的直接回答

| 问题 | 回答 |
|---|---|
| ① 静默丢弃/填充/插值 | **全都有**。丢弃：`:342-344`（未达 EOL 整条丢）、`:488`（`eol<=early_cycle_threshold` 丢）、`:514-519`（eval cycle 过滤 continue）、`:677`（标签缺失 continue）。填充：`:464` `bfill`（跨行/跨循环搬值）、`:622` 全零曲线。插值：`:641-643` 按采样点序号的线性 `np.interp`。 |
| ② 划分与指标 vs 论文 | 划分：写死文件名（G9），**但 seen/unseen 标注与温度条件自洽**（我核对了 CALB42 的 5 个测试电芯）。指标：MAPE + α-accuracy（`evaluate_model.py:345-354`），**per-cycle 曲线那条路径不可执行**（G7/G8）。**注意**：`mean_absolute_percentage_error` 返回的是**小数**（0.1=10%），而 `:356` 的打印把它直接接在 `MAPE:` 后面，没有任何 ×100——如果论文表格里的数字是百分数，这里就有一处 100 倍的量纲口径需要核对（我**没有**核对论文表格，见第 7 节）。 |
| ③ 硬编码假设 | 额定容量 1.85/3.2（`:446-451`）；0.01C 充放电分段阈值（`:555`、`:558`、`:589`）；"先放后充"的电芯白名单 `['RWTH','CALB_0','CALB_25','CALB_45']` + ZN-coin 特判（`:562`）；`early_cycle_threshold=100`（`evaluate_model.py:96`）；`charge_discharge_len=100`（`:157`）；寿命分箱（G10）。 |
| ④ TODO/FIXME/未完成路径 | TODO 1 处：`process_scripts/preprocess_CALCE.py:104` `# TODO: specify the charge and discharge protocols`。**更严重的是"看起来完成、实际跑不通"**：G7/G8 的两条 NameError/AttributeError；`layers/StandardNorm.py:28` `raise NotImplementedError`；仓库根目录的 `monotonicity_check_results.pkl` 只有 **5 字节**——我 hexdump 过，是 `80 04 5D 94 2E`，即 pickle 序列化的**空列表**。也就是说"容量单调性校验"这个动作留下了一个空结果文件，却被提交进了主分支。 |
| ⑤ 用到 UConn 第一个崩的地方 | `data_provider/data_loader.py:379-431` 的 `read_cell_data_according_to_prefix`：一长串 `if prefix.startswith(...)` / `elif`，**没有 else 分支**。UConn 的 pkl 前缀不匹配任何一个 → 循环走完，局部变量 `data` 从未被赋值 → 下一行 `data['cycle_data']`（`:453`）抛 **UnboundLocalError**。在它之前，`:336` 的 `datasetName2ids[file_name.split('_')[0]]` 更可能先抛 **KeyError: 'UConn'**。两个错误都没有友好提示，且都在"加数据集"这一步。 |

---

## 3. R3 BatteryML（NeurIPS 2024 D&B，电池退化 ML 平台）

### 3.1 逐条发现

#### M1｜RUL 标签：删失电芯被"编造"一个寿命，短寿命电芯被丢弃
- **文件/行**：`batteryml/label/rul.py:23-35`
- **原文**：
`@python
label, found_eol = 1, False
for cycle in cell_data.cycle_data:
    label += 1
    Qd = max(cycle.discharge_capacity_in_Ah)
    if Qd <= cell_data.nominal_capacity_in_Ah * self.eol_soh:
        found_eol = True
        break

if not found_eol:
    label = label + 1 if self.pad_eol else float('nan')   # L31-32
if label <= self.min_rul_limit:
    label = float('nan')                                  # L34-35
`@
- **为什么是问题**：两条静默的标签操纵，方向相反。(a) `pad_eol=True` 是默认值，未达 EOL 的电芯不是被丢弃，而是被赋 `label = 观测循环数 + 2` —— **一个凭空多出来的、恰好等于"实验停在哪"的寿命值**。这些恰恰是长寿命电芯，于是模型学到"长寿命电芯的 RUL 等于它被测到的圈数"，系统性压低长寿命预测。(b) `min_rul_limit=100.0`：RUL ≤ 100 的**短寿命电芯被置 NaN 丢弃**（丢弃发生在 `task.py:62-68`）。**两端同时截断，标签分布被人工塑形**，而 README 里只写 "990 batteries"。
- **暗示的方向**：删失样本的正确处理是**生存似然**或至少显式标注 `censored=True` 并单独评估。这是四个仓库里**唯一一个把删失处理写成代码默认行为**的地方，也最容易被误用——因为它不报错，只是悄悄改标签。

#### M2｜`cell_to_drop` 的 `continue` 写在内层循环，等于没删
- **文件/行**：`batteryml/train_test_split/random_split.py:29-38`
- **原文**：
`@python
def _filter_cells(names):
    result = []
    for name in names:
        basename = name.rsplit('/', 1)[1]
        for cell in self.cell_to_drop:
            if cell in basename:
                continue          # <- 内层循环的 continue
        result.append(name)        # <- 无条件执行
    return result
`@
- **为什么是问题**：`continue` 只跳到 `for cell` 的下一次迭代，`result.append(name)` 在循环结束后**无条件执行**。所以 `cell_to_drop` 是一个**完全无效的参数**：调用者以为排除了某些电芯，实际一个都没排。这是一个"静默地不丢弃"的 bug——比静默丢弃更难发现，因为结果看起来"正常"。
- **暗示的方向**：这类"配置项无效果"的 bug 只能靠**单元测试**抓（构造 3 个名字 + 1 个 drop，断言输出 2 个）。基准仓库普遍没有测试目录（四个仓库全部无 `tests/`），这是可复现性研究的低垂果实。

#### M3｜异常循环用邻居循环的数据整体复制回填
- **文件/行**：`batteryml/preprocess/preprocess_SNL.py:146-195`
- **原文**：
`@python
def find_forward_imputation_cycle(cycle, to_exclude):
    # First look back, then look forward
    while cycle > 0 and cycle in to_exclude:
        cycle -= 1
    while cycle == 0 or cycle in to_exclude:
        cycle += 1
    return cycle
...
    tdf = timeseries_df[timeseries_df.Cycle_Index == imp_cycle].copy()
    cdf = cycle_data_df[cycle_data_df.Cycle_Index == imp_cycle].copy()
    tdf['Cycle_Index'] = cycle      # L185  改个号，冒充原循环
`@
- **为什么是问题**：被 3σ/跳变检测判为异常的循环**不删除**，而是把**相邻循环的整条电压-电流-容量轨迹复制过来**，只改 `Cycle_Index`。于是第 k 圈的容量曲线就是第 k−1 圈的复制品。对以"容量衰减轨迹"为标签的任务（EOL@80%），这直接抹平了一个退化台阶。函数名里的 "forward imputation" 有误导性——它不是插值，是**复制**。全程无日志、无计数。
- **暗示的方向**：异常检测之后应当**降权**或**标记**，而不是复制。更一般地：**任何"清洗"都必须留下 provenance**，否则下游无法区分"真实退化"与"清洗伪影"。这与我们 P1（拟合窗边界伪影）是同一种病：伪影被平滑进特征，然后被当成物理。

#### M4｜额定容量按文件名字符串硬编码
- **文件/行**：`batteryml/preprocess/preprocess_SNL.py:82-93`、`:23-49`、`:110-127`
- **原文**：
`@python
def get_capacity(cell_name):
    if 'NMC' in cell_name:
        if '15C' in cell_name:
            return 3 * 0.9
        return 3
    if 'NCA' in cell_name:
        if '20-80' in cell_name:  # Only use 60% of the capacity
            return 1.92  # 3.2 * 0.6
`@
- **为什么是问题**：额定容量（SOH 的分母、C-rate 的分母、EOL 判据的分母）**由文件名字符串决定**。`'20-80'` 的电芯分母取 1.92 Ah，于是它的"SOH=1.0"对应真实容量的 60%，"EOL@0.8"对应真实容量的 **48%**。**同一批数据里，不同 SOC 窗口的电芯，EOL 定义在物理上不是同一个点。** 跨电芯汇总时，RUL 标签不可比。另外 `:110` `rates = name.split('_')[-2][:-1].split('-')` 用文件名解析倍率，命名规范一变就 IndexError 或静默错值。
- **暗示的方向**：这正是"标签口径随数据源漂移"的机制。我们 P2 讨论的是"体检次数 vs 循环数"，这里是"SOC 窗 vs SOC 窗"。**统一口径**（例如一律以每电芯 BOL 实测容量为分母，并把 SOC 窗口作为协变量）是一个可以立刻做、且能解释跨源性能差异的实验。

#### M5｜NaN 标签在 task 层被静默剔除，测试集也一起被剔
- **文件/行**：`batteryml/task.py:62-68`
- **原文**：
`@python
# Omit NaN label cells
train_mask = ~torch.isnan(train_labels)
test_mask = ~torch.isnan(test_labels)
`@
- **为什么是问题**：这是 M1 里 `min_rul_limit` 与 `pad_eol=False` 的实际执行点。**测试集被同样过滤**——于是"测试集"不是"留出的电芯"，而是"留出且寿命>100 圈的电芯"。报告 RMSE 时，分母里没有短寿命电芯。没有任何计数或警告。
- **暗示的方向**：测试集的过滤必须显式报告（N_test_before / N_test_after）。这也是我们 v2 该做而没做的事：所有"剔除"都应在结果文件里留痕。

#### M6｜SOH 标签的 nominal 退化路径与 TODO
- **文件/行**：`batteryml/label/soh.py:47-61`（TODO 在 `:55`）
- **原文**：
`@python
if len(cell_data.cycle_data) >= self.cycle_index:
    Qd = max(cell_data.cycle_data[self.cycle_index-1].discharge_capacity_in_Ah)
    ...
    # calcute nominal_capacity_in_Ah using first cycle TODO:maybe we need to use mean of first 5 cycles to enhance stable?
    nominal_capacity_in_Ah = max(cell_data.cycle_data[0].discharge_capacity_in_Ah)
`@
- **为什么是问题**：SOH 分母取**第 1 圈的单次放电容量**。第 1 圈通常还在化成/浸润后的不稳定期，单点噪声直接进入所有后续 SOH。作者自己在 TODO 里承认了。此外 `len(cycle_data) < cycle_index` 时返回 NaN → 被 M5 剔除，**短寿命电芯在 SOH 任务里也被丢掉**。
- **暗示的方向**：BOL 容量估计（用前 k 圈中位数/拟合截距）本身就是一个可发表的小问题，且直接影响所有 SOH/RUL 标签。四个仓库里三个都有这个毛病（R2 用数据集级常数，R4 用数据集级常数，R3 用首圈单点）。

### 3.2 对 R3 五问的直接回答

| 问题 | 回答 |
|---|---|
| ① 静默丢弃/填充/插值 | 丢弃：`task.py:62-68`（NaN 标签）、`label/soh.py:60-61`（不足 100 圈）、`preprocess_SNL.py:23-49`（26 个电芯按名丢弃，无计数）。填充：`preprocess_SNL.py:178-194`（**复制邻居循环**，不是插值）。插值：未在预处理主路径发现。 |
| ② 划分与指标 vs 论文 | 划分器有 `random_split` / `MATR_split` / `MIX100_split` / `CRUSH_split` / `CRUH_split` / `HUST_split` / `SNL_split` 七种，**但默认的 `RandomTrainTestSplitter` 是纯随机 60/40**（`random_split.py:43-44`），不按工况。`DataBundle` 的变换只在训练集上 fit（`databundle.py:54-61`），**这一点是对的，没有泄漏**。指标 `_evaluate_score`（`databundle.py:100-106`）只有 RMSE/MAE/MAPE，**没有按电芯/工况分组的置信区间**。 |
| ③ 硬编码假设 | 额定容量按文件名（M4）；`eol_soh=0.8`、`min_rul_limit=100`、`cycle_index=100`（`rul.py:15-17`、`soh.py:17`）；`test_size=0.4`（`random_split.py:18` 的 0.6 比例）；SNL 的 `se = ... < 1.5`（`preprocess_SNL.py:66`，单个电芯的魔法阈值）。 |
| ④ TODO/FIXME/未完成路径 | 5 处 TODO（`pipeline.py:44`、`label/soh.py:55`、`preprocess_CALCE.py:99`、`models/nn_model.py:56`）。**`random_split.py` 的 `cell_to_drop` 是失效配置（M2）**，属于"看起来完成、实际无效"的路径。 |
| ⑤ 用到 UConn 第一个崩的地方 | 需要先把 UConn 转成 `BatteryData`/`CycleData` 的 pkl（含 `voltage_in_V` / `current_in_A` / `time_in_s` 逐点序列）。UConn 是**表格型 RPT 记录**（本项目 2,813 行），没有逐秒曲线 → 无法构造 `CycleData`。退一步，若只做 SOH 任务，`label/rul.py:27` 的 `Qd <= cell_data.nominal_capacity_in_Ah * self.eol_soh` 在 `nominal_capacity_in_Ah` 缺失时是 **TypeError: unsupported operand type(s) for *: 'NoneType' and 'float'**（`rul.py` 没有 `soh.py:51` 那样的 `hasattr` 保护）。**即：R3 假设你有一份逐点时序 + 额定容量，UConn 两样都得现造。** |

---

## 4. R4 PINN4SOH（Nat Commun 2024，物理信息 SOH）

### 4.1 逐条发现

#### P1｜循环序号被当作输入特征喂进网络
- **文件/行**：`dataloader/dataloader.py:50`、`:76-77`、`:58-64`
- **原文**：
`@python
df.insert(df.shape[1]-1,'cycle index',np.arange(df.shape[0]))   # L50  插在倒数第二列
...
x = df.iloc[:,:-1].values                                        # L76  除最后一列全是特征
y = df.iloc[:,-1].values                                         # L77  最后一列是 capacity
`@
`@python
f_df = df.iloc[:,:-1]                                            # L58  含 'cycle index'
f_df = 2*(f_df - f_df.min())/(f_df.max() - f_df.min()) - 1       # L60
`@
- **为什么是问题**：CSV 的列是 16 个统计特征 + `capacity`（我读了 `data/HUST data/1-1.csv` 的表头确认）。`insert` 把 `cycle index` 放在 capacity 之前，于是它落在 `iloc[:,:-1]` 里，**成为第 17 个输入特征**，并被 min-max 归一化。也就是说：模型在预测第 k 圈的 SOH 时，**知道 k**。SOH(k) 是 k 的单调光滑函数，这条特征单独就能解释大部分方差。论文的卖点是"物理信息神经网络学习退化律"，但**时间坐标是直接给的**，F 网络要学的 `x_{k+1}=F(x_k)` 退化了一步差分的最难部分。这不是说结果无效（SOH 估计任务里给圈号是常见做法），而是说：**"物理信息"的增益里，有多少来自 PDE 约束、有多少来自这条圈号特征，代码里没有做消融**（我没找到去掉 cycle index 的开关）。
- **暗示的方向**：**必须做"去时间坐标"消融**。如果去掉圈号后 PINN 的优势消失，那这个方向的真实贡献就被高估了。这对我们是直接警示：我们的 C_ecm 特征里，RPT 序号是否也隐含地充当了时间坐标？（我们的 `num_cycles` 就是序号轴。）

#### P2｜训练/验证是行级随机 8:2，同一电芯的相邻循环跨集
- **文件/行**：`dataloader/dataloader.py:157-158`（Condition 2，实际被 `main_*.py` 使用的 `train_2`/`valid_2`）
- **原文**：
`@python
train_X1, valid_X1, train_X2, valid_X2, train_Y1, valid_Y1, train_Y2, valid_Y2 = \
    train_test_split(tensor_X1, tensor_X2, tensor_Y1, tensor_Y2, test_size=0.2, random_state=420)
`@
- **为什么是问题**：`tensor_X1` 是把所有电芯的所有循环**按文件顺序拼接**后的矩阵。随机 8:2 切分意味着：同一电芯的第 57 圈在训练集、第 58 圈在验证集。由于相邻循环的 16 维统计特征高度自相关，验证集几乎是训练集的复制。**早停（`early_stop=20`）在这个泄漏的验证集上做**，选出的 epoch 不代表泛化。测试集（`test_3`，独立电芯）本身是干净的，但**模型选择被污染了**——这是比测试集泄漏更隐蔽的一类。
- **暗示的方向**：模型选择必须用**电芯级/工况级**的验证划分。我们 v2 的 LOGO 是电芯级留出，但超参选择是否也按电芯分组？这一条值得自查。

#### P3｜额定容量是数据集级常数
- **文件/行**：`dataloader/dataloader.py:191`（XJTU）、`:234`（HUST）、`:268`（MIT）、`:316`（TJU）
- **原文**：
`@python
self.nominal_capacity = 2.0        # L191 XJTU
self.nominal_capacity = 1.1        # L234 HUST
self.nominal_capacity = 1.1        # L268 MIT
self.nominal_capacities = [3.5,3.5,2.5]   # L316 TJU
`@
- **为什么是问题**：SOH = capacity / 常数。**同一数据集内所有电芯共用一个分母**。XJTU 的 55 个电芯标称 2 Ah，实际 BOL 容量在 1.9–2.1 之间波动；用 2.0 作分母，SOH 的起点就不是 1.0，而是 0.95–1.05。跨数据集比较时（论文的核心卖点是"跨数据集稳定"），**每个数据集的 SOH 起点偏移不同**，这会直接制造"跨数据集性能差异"，而它其实是分母造成的。
- **暗示的方向**：这是四个仓库里**最干净的一个可量化实验**：把数据集级常数换成每电芯 BOL 估计，看跨数据集指标变化多少。如果变化大，说明"跨源稳定性"有一部分是标签构造的假象。**这条可以直接搬到我们的 UConn/Bayreuth 上做。**

#### P4｜3σ 逐列删行，删完不重编号、不计数
- **文件/行**：`dataloader/dataloader.py:17-41`、`:50-52`
- **原文**：
`@python
rule = (Ser1.mean() - 3 * Ser1.std() > Ser1) | (Ser1.mean() + 3 * Ser1.std() < Ser1)
...
out_index.extend(index)
out_index = list(set(out_index))
df = df.drop(out_index, axis=0)
`@
- **为什么是问题**：三条。(a) 3σ 是**逐列**判的，任一列越界就删整行——一个容量离群点会连带删掉那圈的电压/电流特征。(b) `mean/std` 在**单个电芯内部**算，于是"离群"是相对于该电芯自己的分布，**跨电芯不可比**：退化剧烈的电芯会被删掉更多晚期循环，正好是最有信息的那段。(c) `cycle index` 在 L50 就插好了，删行之后**保留原编号但留下空洞**，模型看到的时间轴是断的。全程无计数。
- **暗示的方向**：离群处理应在**特征空间**而非行空间，且必须报告"每电芯删了多少圈、删在寿命的哪个阶段"。删在早期和删在晚期，对 RUL 的影响完全相反。

#### P5｜测试集按"文件名里含 4 或 8"划分
- **文件/行**：`main_XJTU.py:15-19`
- **原文**：
`@python
if args.batch in file:
    if '4' in file or '8' in file:
        test_list.append(os.path.join(root, file))
    else:
        train_list.append(os.path.join(root, file))
`@
- **为什么是问题**：`'4' in file` 是**子串匹配**。XJTU 的文件名形如 `2C_battery-4.csv`、`3C_battery-14.csv`（我列过目录：`2C_battery-1..8`、`3C_battery-1..15`、`R2.5_*`、`R3_*`、`RW_*`、`Sim_satellite_*`）。于是 `3C` 批次的测试集是 {4, 8, 14}（14 里含 '4'），训练集 12 个；`2C` 批次测试集 {4,8}，训练 6 个。**批次之间的 train/test 比例不一致（25% vs 33%），而且这是字符串巧合，不是设计。** 更要命的是：换一个数据集（文件名不同），这条规则会给出任意结果——比如文件名里含 '4' 的批次可能一个都没有。
- **暗示的方向**：划分规则必须显式、可审计、可迁移。这跟 G9（BatteryLife 的手写名单）是同一问题的两个极端：一个写死名单，一个靠子串。**两者都不可迁移到 UConn。**

#### P6｜MIT 测试集按 `id % 5 == 0`
- **文件/行**：`main_MIT.py:44-52`
- **原文**：
`@python
for batch in ['2017-05-12','2017-06-30','2018-04-12']:
    ...
    id = int(f.split('-')[-1].split('.')[0])
    if id % 5 == 0:
        test_list.append(os.path.join(batch_root,f))
`@
- **为什么是问题**：每 5 个电芯取 1 个做测试，**且三个批次混在一起取**。这既不是留一批次（跨批次泛化），也不是留一工况。论文若声称"跨批次稳定"，代码里的测试集却包含来自**所有三个批次**的电芯，且训练集也包含这三个批次 —— **批次效应无法被检验**。
- **暗示的方向**：跨批次/跨工况的声明必须配"留一批次"的实验。我们 Bayreuth 的 23 工况正是这种设计，但结论是"仅 a1、c 过 Bonferroni"，说明留一工况比留一电芯难得多。R4 的代码**回避**了这个难点。

#### P7｜作者自认代码有 bug，且与 Supplementary 的 α/β 不一致
- **文件/行**：`fix.md:4`
- **原文**：`由于初始版本的代码存在部分bug，我们对其进行了修复，导致 $\alpha$ 和 $\beta$ 的值和 Supplementary File中的值不一致，请见谅。`
- **为什么是问题**：这是仓库里**唯一一处**承认"代码与论文数值不一致"的文字，日期是 2026 年 9 月（论文 2024 年发表）。它说明：**公开代码在两年内与论文的对应关系是断的**，而修复只改了 α/β，没说改了哪里、影响哪些表。任何人按 Supplementary 复现都会得到不同数字，且无法判断是"随机性"还是"bug 修复"。
- **暗示的方向**：**版本化的复现契约**（每次修复都记录：改了哪个函数、影响哪些图表、重跑后的数字）应当成为标配。这条对我们尤其相关：我们 v1→v2 的修复正是同一类事件，只是我们做了文档（`docs/e1_v2_fixed_results.md`），R4 没有。

#### P8｜全仓库无随机种子
- **文件/行**：全仓库 grep `manual_seed|np.random.seed|random.seed` **零命中**（`dataloader.py:144` 的 `random_state=420` 只固定了划分，不固定初始化/打乱）
- **为什么是问题**：`main_*.py` 全部用 `for e in range(10)` 跑 10 次然后（推测）取平均。没有种子意味着：这 10 次的方差里混着初始化、数据打乱、dropout。**"10 次实验"无法区分"方法稳定"与"运气好"。** 而且 `DataLoader(shuffle=True)` 用的是全局 RNG，与任何种子无关。
- **暗示的方向**：多种子 + 报均值±标准差 + 固定种子清单。我们 v2 的"电芯级 CI / 工况簇 CI"正是这个问题的更严格版本。

### 4.2 对 R4 五问的直接回答

| 问题 | 回答 |
|---|---|
| ① 静默丢弃/填充/插值 | 丢弃：`dataloader.py:31-40`（3σ 逐列删行，无计数）；`:144` 行级切分把 20% 行挪进 valid（不是丢弃但同类）。填充：未发现显式填充。插值：未发现。**但有更隐蔽的一种**：`cycle index` 的插入（P1）等价于给每个样本附加了一个"人造时间轴"，而这条轴在删行后带空洞（P4）。 |
| ② 划分与指标 vs 论文 | 划分：XJTU 靠**子串** `'4' in file or '8' in file`（P5），MIT 靠 **`id % 5 == 0`**（P6），train/valid 靠**行级随机 8:2**（P2）。论文（据 README 与 fix.md）强调跨数据集稳定与"6 batches"的逐批结果（Table 2），但**代码里没有任何"留一批次"的开关**——`main_XJTU.py:32-34` 是逐批次各自训练+测试，批次内再按文件名分。指标：代码里我只看到训练/验证损失与测试损失，**没有找到按电芯/工况的置信区间**。 |
| ③ 硬编码假设 | 额定容量 2.0/1.1/1.1/[3.5,3.5,2.5]（P3）；`random_state=420`（`:144`）；3σ（`:22`）；`test_size=0.2`；`batch_size` 256/512；`early_stop=20`、`warmup_epochs=30`、`epochs=200`；`alpha=0.5`、`beta=0.01`（`main_MIT.py:30-31`）与 `beta=10`（`main_XJTU.py:57` 的 small_sample 分支）**互相矛盾**。 |
| ④ TODO/FIXME/未完成路径 | 无 TODO/FIXME（grep 零命中）。但有 **`fix.md` 自认的未完成修复**（P7），以及 `main_comparision.py` 与 `main_*.py` 之间**重复的模型选择 if/elif 链**（`evaluate_model.py` 在 R2 里也有一份几乎相同的），说明代码是从别处拷贝改的，拷贝处没同步。 |
| ⑤ 用到 UConn 第一个崩的地方 | 输入要求是**每电芯一个 CSV，17 列（16 统计特征 + capacity），每行一个循环**。UConn 是 RPT 表格（2,813 行 / 64 电芯 / 11 工况组），没有这 16 维特征。第一步 `pd.read_csv` 能过，但 `df.insert(df.shape[1]-1, 'cycle index', ...)` 后 `y = df.iloc[:,-1]` 取的"最后一列"若不含 `capacity` 命名，`:56` 的 `df['capacity']` 直接 **KeyError: 'capacity'**。即便补上，`nominal_capacity=2.0` 对 UConn 的混编电芯也是错的（P3）。**最根本的：这套管线假设"每个循环都有完整充放电曲线"，而 UConn 的 RPT 是稀疏体检点。** |

---

## 5. 汇总：代码层面的未解决问题（按"可迁移性"排序）

### 第一梯队：直接改变结论方向（5 条）

| # | 仓库 | 位置 | 一句话 | 迁移到我们项目的含义 |
|---|---|---|---|---|
| **A1** | R1 | `utils/exp_util.py:213-215` | 任一通道缺失即丢整行 → **通道消融没有做到样本隔离** | 我们的"加 C_ecm"对比，若 EIS/弛豫通道的可用样本与 A_curve 不同，−5.3% 里混着样本选择效应。**必须先报共同可用掩码下的重算结果。** |
| **A2** | R3 | `batteryml/label/rul.py:31-35` | 删失电芯被赋 `label=观测圈数+2`；短寿命被 `min_rul_limit=100` 丢弃 | 两端截断会系统性压低长寿命预测。我们的 `num_cycles` 若也有截断（只保留有完整 RPT 的电芯），同理。 |
| **A3** | R2 | `data_provider/data_loader.py:501-523` | 所有样本共享同一条前 100 圈曲线，只改 mask；标签恒为 `eol` 而非 `eol-i` | "RUL vs total life"的口径差，在 i=100 时是 100 圈。**我们的标签是"剩余体检次数"，与真实循环数的缩放比 1.98——同构。** |
| **A4** | R1 | `utils/models.py:142-158` | 点级 bootstrap 当作不确定度 → **推断单位错** | 与 P3（ICC=0.414, 等效 n=21.4）完全同构。**按电芯/工况 cluster bootstrap 是必须做的。** |
| **A5** | R4 | `dataloader/dataloader.py:50,76-77` | 循环序号被当特征喂入 → 时间坐标泄漏 | 我们的 C_ecm 里是否也隐含 RPT 序号？**"去时间坐标"消融是必须的对照。** |

### 第二梯队：让复现不可能（5 条）

| # | 仓库 | 位置 | 一句话 |
|---|---|---|---|
| **B1** | R2 | `evaluate_model.py:184-185` + `:397` | `args.alpha` 未定义（只有 `--alpha1`）→ AttributeError；调用处 `dataset` 未定义 → NameError。**公开的评估入口跑不起来，逐圈精度曲线的产线不可执行。** |
| **B2** | R3 | `batteryml/train_test_split/random_split.py:29-38` | `cell_to_drop` 的 `continue` 在内层循环 → **配置项完全无效**，一个电芯都没删。 |
| **B3** | R1 | `experiments/data-efficiency.py:22-23` | `np.random.permutation(24)` 无种子 + 硬编码 24 → 数据效率曲线不可复现。 |
| **B4** | R4 | `fix.md:4` | 作者自认 bug 修复后 α/β 与 Supplementary 不一致；**代码与论文的对应关系在两年内是断的**。 |
| **B5** | R2 | `monotonicity_check_results.pkl`（5 字节） | 是 pickle 的**空列表**（`80 04 5D 94 2E`）。"容量单调性校验"留下空结果文件却进了主分支。 |

### 第三梯队：标签口径随数据源漂移（6 条）

| # | 仓库 | 位置 | 一句话 |
|---|---|---|---|
| **C1** | R3 | `preprocess/preprocess_SNL.py:82-93` | 额定容量按文件名给（`'20-80'`→1.92 Ah），**EOL@0.8 对不同 SOC 窗对应不同物理点**。 |
| **C2** | R2 | `data_provider/data_loader.py:446-451` | 额定容量硬编码（RWTH 1.85、SNL 3.2），SOH/C-rate 分母错则全错。 |
| **C3** | R4 | `dataloader/dataloader.py:191,234,268,316` | 数据集级常数分母（2.0/1.1/1.1/[3.5,3.5,2.5]），**跨数据集的"稳定"可能是分母造成的**。 |
| **C4** | R3 | `label/soh.py:55-56` | SOH 分母取第 1 圈单点容量（作者 TODO 自认应改前 5 圈均值）。 |
| **C5** | R1 | `utils/exp_util.py:178` | `true_cycle = 1+(cycle-2)*n_steps+step` 假设每块恰好 4 段 → **自造时间轴**。 |
| **C6** | R2 | `data_provider/data_loader.py:629-644` | 按采样点序号线性重采样 → **采样率差异被当成形状差异**。 |

### 第四梯队：清洗即造数（4 条）

| # | 仓库 | 位置 | 一句话 |
|---|---|---|---|
| **D1** | R2 | `data_provider/data_loader.py:462-464` | 整行置 NaN + `bfill` → 时间倒退、循环号被改写。 |
| **D2** | R3 | `preprocess/preprocess_SNL.py:178-194` | 异常循环用邻居循环**整条复制**，只改 `Cycle_Index`。 |
| **D3** | R4 | `dataloader/dataloader.py:17-41` | 3σ 逐列删行，删完不计数、时间轴留洞，且删除量随电芯退化剧烈程度变化。 |
| **D4** | R2 | `data_provider/data_loader.py:620-622` | 缺循环补全零曲线，`np.isnan` 检查查不出零。 |

### 第五梯队：工程上的"加不了新数据"（4 条）

| # | 仓库 | 位置 | 一句话 |
|---|---|---|---|
| **E1** | R2 | `data_loader.py:379-431` | if/elif 前缀链**无 else** → 新数据集 UnboundLocalError。 |
| **E2** | R2 | `data_split_recorder.py:1-106` | 划分是 200+ 个写死文件名；seen/unseen 是第二份手写 JSON。 |
| **E3** | R4 | `main_XJTU.py:15-19` / `main_MIT.py:44-52` | 测试集靠**子串** `'4' in file or '8' in file` / `id % 5 == 0`。 |
| **E4** | R1 | `utils/exp_util.py:352-355` | 列数≠7 时 `time.sleep(120)` 无限重试 → **不是崩溃，是挂起**。 |

**合计 24 条，覆盖 4 个仓库。** 其中 15 条带明确的"会改变数字"的机制，9 条是"让复现不可能"的工程缺陷。

---

## 6. 如果把这些方法用到 UConn 数据上，第一个崩的地方（逐仓库）

前提（二手转述，未直接读原始数据）：UConn = 64 电芯 / 11 工况组 / 2,813 行 RPT 记录；非循环测量通道是**脉冲/静置弛豫**（2-RC 拟合），**没有 EIS 频谱**。

| 仓库 | 第一处崩溃 | 机制 |
|---|---|---|
| R1 | `utils/exp_util.py:352-355` | 找不到 GCPL/GEIS 的 7 列 tab 文件 → 要么 FileNotFoundError 被裸 except 吞成 None、最终空数据集在 `np.vstack` 炸；要么列数≠7 → **进入 120 秒睡眠的无限重试，静默挂死**。 |
| R2 | `data_provider/data_loader.py:336` | `datasetName2ids['UConn']` → **KeyError**；即使绕过，`:379-431` 无 else → **UnboundLocalError**。 |
| R3 | `batteryml/label/rul.py:27` | UConn 无逐点 `CycleData`，无法构造 `BatteryData`；若只做 SOH，`nominal_capacity_in_Ah` 缺失 → **TypeError: NoneType * float**（`soh.py` 有 hasattr 保护，`rul.py` 没有）。 |
| R4 | `dataloader/dataloader.py:56` | 需要 17 列（16 统计特征 + `capacity`）的每电芯 CSV；UConn 是稀疏 RPT → **KeyError: 'capacity'**；即便补上，`nominal_capacity=2.0` 对混编电芯是错的。 |

**共同点：四个仓库没有一个能"读入一个新数据集"而不改源码。** 这不是巧合——它们都是"为一个（或一组）已发表数据集写的实验脚本"，不是"为数据设计的管线"。**这正是下一个方向可以占据的位置。**

---

## 7. 我没能验证的东西（必须标注）

1. **没有跑通任何一个仓库。** 四个仓库的原始数据都不在仓库里（R1 完全没有 `data/`；R2/R3 需从 HuggingFace/Zenodo 下载；R4 带预处理 CSV 但缺原始曲线）。本文所有结论都是**静态代码审计**，不是运行结果。
2. **没有读论文正文。** R1 仅摘要，R2 仅 README，R3 仅 README，R4 仅 README + fix.md。因此凡是"论文声称 X"的表述，都只到"摘要/README 声称 X"这一层。**我没有能力判断代码与论文 Methods 的具体数字是否一致。**
3. **没有逐个核对 R2 的 18 个模型 forward 是否严格遵守 attention mask。** G3 里"(a) 若未严格遵守 mask 则看到未来"是**条件句**，不是断言。要确认需要读 `models/CPGRU.py`、`CPMLP.py` 等的 forward。
4. **没有核对 R2 论文表格里的 MAPE 是小数还是百分数**（G7 里提到的 100 倍量纲问题）。这需要论文 PDF。
5. **没有读 UConn 原始数据。** 第 6 节的"没有 EIS"来自 `RESEARCH_STATE.md` 的转述。
6. **没有读 R1 的 `utils/exp_util_new.py` / `exp_util_new_reduced.py`**（51 KB / 36 KB）。它们是 `exp_util.py` 的变体，可能修了部分问题。我只审计了被 `experiments/*.py` 实际 import 的 `exp_util.py`（见 `next-cycle-capacity.py:6`）。
7. **没有验证 R2 的 seen/unseen 划分在其它数据集上是否同样自洽。** 我只逐条核对了 `cal_for_test_CALB42.json` 的 5 个电芯与 `CALB_42_train_files` 的温度条件，结论是**自洽的**（25 ℃ 未出现在训练集，标注为 unseen）。MATR/HUST 等因文件名不含可解析的温度/倍率字段，我**无法**从文件名判断，故未计入。
8. **R1 的 24 vs 88 电芯问题未解。** `identify_cells`（`exp_util.py:720-763`）只覆盖 24+16=40 个电芯，而摘要说 88 个。差异原因（数据未公开？分批发布？）我无法确定，故未作为发现列出。

---

## 8. 这些发现指向什么方向（供下一步决策）

### 方向 1｜"删失感知的电池寿命预测"（锚定 A2 / G1 / M5）
四个仓库里，**三个**对右删失样本做了某种静默处理：R2 整条丢弃（`data_loader.py:342-344`）、R3 编造标签（`rul.py:31-32`）、R3 在测试集上再丢一次（`task.py:62-68`）。**没有一个用生存似然。** 这是一个有明确代码证据、有现成统计工具（censored regression / survival NLL）、且直接影响长寿命端预测的空白。我们 UConn 的 64 电芯里若也有未到 EOL 的，同样适用。

### 方向 2｜"标签口径的元数据化"（锚定 C1–C6 / A3 / F5）
六条发现指向同一件事：**SOH/RUL 的分子分母、时间轴、聚合单位，全都是由代码里的常数或算术式决定的**，而论文只报最终指标。可以做一个通用工具 + 一篇方法学论文：把标签定义写成显式元数据（分母来源、时间轴类型、删失标记、推断单位），然后量化"口径变化对排序的影响"。我们自己的 P2（体检次数 vs 循环数，缩放 1.98）就是这个工具的第一个案例。

### 方向 3｜"通道可用性掩码下的多模态融合"（锚定 A1 / F1–F4 / G4）
R1 的通道消融没有做样本隔离，R2 用零填充缺失循环。两者都说明：**"缺哪个通道"这个信息本身没有被建模**。正确做法是 missing-modality 训练（mask token + 可用性嵌入），并报告"共同可用子集"上的对照。我们研究的正是"非循环测量通道"，这是最贴合我们数据形态的方向。

### 方向 4｜"可迁移的评估协议 DSL"（锚定 E1–E4 / B1 / B2）
四个仓库的划分规则分别是：手写名单（R2）、子串匹配（R4）、`id % 5`（R4）、纯随机（R3）。**没有一个能表达"留一工况"而不改源码。** 我们已经有 11 个工况组的 LOGO 需求，做一个声明式划分 DSL（按元数据过滤 + 自动生成 seen/unseen + 自动 cluster bootstrap）既是工程需要，也可以作为基准论文的贡献点。

### 方向 5（谨慎）｜"物理信息模型的增益归因"（锚定 A5 / P1 / P8）
R4 把循环序号当特征喂进去，且全仓库无种子。如果去掉圈号特征后 PINN 的优势大幅缩水，那"物理信息"的贡献需要重新归因。**这条对我们最有警示意义**：我们的 C_ecm 是在 RPT 序号轴上拟合的，若 RPT 序号本身强烈预测标签，那 C_ecm 的边际贡献会被高估。**建议在下一轮实验里加一个"仅 RPT 序号"的基线**——`INNOVATIONS_AND_RESULTS.md:30` 已有"仅体检序号 13.501"，说明这个对照**已经做过**，且 C_ecm 6.238 远好于它。所以这条方向的风险较低，但仍应显式报告。

---

## 9. 一句话结论

**这四个仓库里，没有一个是"方法不行"，全部是"标签、划分、清洗、单位"这四件事在代码里被悄悄决定了，而论文只呈现结果。** 我们项目自己的 v1→v2（拟合窗 bug + 单位失配）不是意外，是这一类工作的**结构性风险**。下一个方向如果继续做"更好的模型"，会重复它们的命运；如果做"让这四件事显式化、可审计、可迁移"，则同时踩中了 24 条代码级空白里的 15 条。
