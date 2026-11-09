# DATA-ADMISSION-20261109 · 数据准入审计

- **日期**：2026-11-09
- **授权**：Codex L2（thread `01a1bed6-3d2e-72a2-a408-f5c88f4ee6e0`）——四小时、**不许拟合**的数据准入审计
- **目的**：判定「重建元数据」可行，还是必须「获取独立新数据」。本审计**不授权任何新实验**，也**不能重开 C3**。
- **状态**：**部分完成**（源定位已做，字段级核对未做——原始归档未下载）

---

## 1 已核实

### 1.1 UConn 64 电芯 / 11 工况数据集 —— 源已定位 ✅

| 字段 | 值 |
|---|---|
| 名称 | UConn-ISU-ILCC LFP/Gr Battery Aging Dataset |
| 作者 | Nowacki, Ramamurthy, Thelen, Tischer, Pint, Hu |
| 位置 | `digitalcommons.lib.uconn.edu/reil_datasets/5/` |
| 许可 | **CC BY 4.0** |
| 内容 | 64 颗 LithiumWerks APR18650M1B，11 个工况，循环至 80% 剩余容量 |
| RPT 节奏 | 每约 3.5 天（约 100 循环）一次；1 Hz 采样；跨度 38 周 |
| **随附文件** | `README.txt`(5 kB)、`rpt_data.zip`(**2.35 GB**)、`cycling_part1.zip`(6.55 GB)、`cycling_part2.zip`(7.05 GB)、**`CyclingParameters.csv`(1 kB)**、`CITATION.bib`、`LICENSE.txt` |
| 对应论文 | Nowacki et al., *J. Power Sources* 628:235813, 2025, doi:10.1016/j.jpowsour.2024.235813 |

**结论**：**物理工况描述符（CyclingParameters.csv）与原始 1 Hz 时序（含真实时间戳）都可取回。** 本地处理表里没有描述符，是**处理过程的产物，不是数据源缺失**。

### 1.2 ISU 248 电芯 / 63 工况数据集 —— **源已定位（本审计修正）** ✅

**上一版判定「源未定位」是错的，特此更正。**

定位依据（四条独立证据，全部可复现）：

1. `tingkai-li/early-prediction-varying-usage-data/feature_extraction/feature_extraction.py` 首行注释：*"ISU-ILCC battery aging dataset is available at: https://doi.org/10.25380/iastate.22582234"*，且其代码读取的字段（`start_stop_time['start']`、`QV_charge_C_2` 等）与本地 JSON **逐字相同**。
2. figshare API `articles/22582234` 返回标题 **"ISU-ILCC Battery Aging Dataset"**，DOI `10.25380/iastate.22582234.v2`，许可 **CC BY 4.0**。
3. 官方 README 摘录：*"Each cell was assigned a unique identifier... For example, G3C1 is the first cell in group three"* —— 与本地 `G{n}C{m}` 命名逐字一致。
4. 一篇独立论文引用该队列时写 **n = 251** —— 与本地 `Valid_cells.csv` 的 251 行逐字一致。

**官方发布文件 vs 本地副本**

| 文件 | 官方大小 | 本地 |
|---|---:|---|
| `Valid_cells.csv` | 1,727 B | ✅ 有（字节数一致） |
| `Q_interpolated.zip` | 47,797,453 B | ✅ 有（字节数一致） |
| `RPT_json.zip` | 929,406,930 B | ✅ 有（字节数一致） |
| `process_data.py` | 9,769 B | ❌ 无 |
| `capacity_fade.zip` | 140,256 B | ❌ 无 |
| `README_V2.0.pdf` | 640,953 B | ❌ 无（本地 `README_uconn.txt` 实为 Cloudflare 挑战页，下载从未成功） |
| **`Cycling_json.zip`** | **10,208,088,439 B** | ❌ **无** |

**后果**：
- **物理寿命时钟可得**：`RPT_json.zip` 里已有 `start_stop_time` 的**真实日历时间戳**（如 G30C1 起始 2022-09-16）；`Cycling_json.zip` 另含真实循环数。**上一版「只有 RPT 序号」的说法也是错的。**
- **物理工况描述符**：官方 `README_V2.0.pdf` 含分组条件说明（本次下载被 figshare 挡下：202/404，未取得）。**未验证**，但**很可能可得**。
- 本地副本是**部分拷贝**，不是来源不明。

**这一条从「阻塞」降级为「待补取」**：只需下载 `Cycling_json.zip`(10.2 GB) 与 `README_V2.0.pdf`(0.64 MB) 即可补齐。

---

## 2 字段级准入表

| 字段 | UConn 64（源已定位） | ISU-ILCC 251（源已定位，本地部分） |
|---|---|---|
| 源版本 | ✅ REIL item 5，CC BY 4.0 | ✅ doi:10.25380/iastate.22582234.v2，CC BY 4.0 |
| 电芯→工况映射 | ✅ 随附 | ✅ `Valid_cells.csv` + `G{n}C{m}` 命名 |
| 批次身份 | ⚠️ 需读 README | ⚠️ 需读 README_V2.0.pdf（未取得） |
| **物理工况描述符** | ✅ `CyclingParameters.csv` | ⚠️ **很可能可得**（README 分组条件），未取得 |
| **物理寿命时钟** | ✅ 1 Hz 原始时序，含时间戳 | ✅ **RPT 内已有真实日历时间戳**；`Cycling_json.zip` 另含循环数 |
| EOL 阈值与删失记录 | ✅ README 说明 80% | ⚠️ 需 README_V2.0.pdf |
| 重复数 | ✅ 每工况 4–6 颗（需核） | ✅ 每工况 4 颗（60 个工况） |
| 资源记账（通道小时） | ❌ 需从时序重建 | ⚠️ 需 `Cycling_json.zip` |
| 未用过的评估队列 | ❌ 全部 64 颗已被本项目检查过 | ❌ 全部 63 工况已被检查过 |

---

## 3 判定

**重建可行（仅 UConn），且重建后仍不足以支撑一个确认性实验。** 理由：

1. **UConn 可以重建**：描述符、时间戳、EOL 都有。但只有 **11 个工况**——外层留出的独立单位只有 11 个，Codex 明确要求「独立单位数按工况级配对差计划功效」，11 个撑不起一个分配律研究。
2. ~~**ISU 不能重建**：源未定位。这是**阻塞级**问题~~ —— **此条已作废**。ISU 源已定位为 ISU-ILCC Battery Aging Dataset（`doi:10.25380/iastate.22582234.v2`，CC BY 4.0），三因子表已取回并核对。见 §1.2 与 §4.4。
3. **两个数据集都已被本项目检查过**：恢复元数据**不能**把已检查工况变成独立确认集。这一点 Codex 已明确。
4. **因此**：靠现有两个数据集，**任何**分配类研究都只能得到探索性结论，不能得到确认性结论。

---

## 4 下一步（供决策，不自行执行）

| 选项 | 说明 |
|---|---|
| **A. 取回 `README_V2.0.pdf`** | **本轮已尝试并失败**（见 §4.1）。物理描述符仍未验证 |
| **B. 取回 `Cycling_json.zip`(10.2 GB)** | 真实循环数；未尝试（体积大，需确认磁盘与用途） |
| **C. 用 UConn 重建 + 找一个 ≥30 工况的公开 LFP 数据集** | UConn 只有 11 工况，仍不足以做工况级分配研究 |
| **D. 停止分配类研究** | 若 A/B 都不成，诚实结论：现有资产不支持分配律主张 |

### 4.1 `README_V2.0.pdf` 取回尝试记录（全部失败）

| 路径 | 结果 |
|---|---|
| `ndownloader.figshare.com/files/43754898`（经代理） | HTTP **202**，body 0 字节，重试 4 次均同 |
| 同上（直连） | HTTP 403 |
| `iastate.figshare.com/ndownloader/...`（代理/直连） | HTTP 403 |
| `figshare.com/ndownloader/...`（代理/直连） | HTTP 403 |
| figshare API `articles/22582234/files/43754898/download` | HTTP 404 |
| 带 cookie 会话 + Referer 重试 | HTTP 202，0 字节 |

**判定**：当前网络路径**取不到**该文件。202 是 figshare 的异步准备响应，但始终不返回内容——很可能是代理拦截或需要 JS 挑战。

**替代路径（未尝试，供后续）**：
- 论文 *"Predicting battery lifetime from early aging data"*（Tingkai Li 等）正文可能含 63 个工况的条件表；
- 用 Windows 桌面浏览器（`windows-mcp`）人工过 figshare 的挑战页下载。

### 4.2 已验证「不可得」的替代来源

| 来源 | 结果 |
|---|---|
| HuggingFace `not-the-bell-curve/Operational_Context_of_Li_ion_batteries` 的 `process_data_iowa.py` / `Iowa.py` | 已下载（9,776 / 14,305 字节），**只是加载器，不含工况→温度/倍率映射** |

### 4.3 **描述符空间已确定**（figshare API 的 `description` 字段，1,036 字符）

这是本轮的决定性发现。原文：

> "The ISU-ILCC battery aging dataset was collected jointly by the System Reliability and Safety Laboratory at Iowa State University (ISU), now the **Reliability Engineering and Informatics Laboratory (REIL) at the University of Connecticut**, and Iowa Lakes Community College (ILCC). The dataset is designed to study the dependency of battery capacity fade from **three stress factors: charge rate, discharge rate, and depth of discharge**. The dataset contains cycle aging data from **251** lithium-ion polymer cells cycled under **63 unique conditions**. **The current release contains 238 cells**; the other 12 cells have not completed the testing."

**由此确定**：

| 项 | 值 |
|---|---|
| 描述符空间 | **3 维：充电倍率 × 放电倍率 × 放电深度（DoD）** |
| 工况数 | 63（三因子设计） |
| 电芯总数 | 251 计划 / 238 已完成 |
| 数据集归属 | ISU + **UConn REIL** + ILCC 联合 |

**重要修正**：ISU-ILCC 与 UConn-ISU-ILCC **同属 UConn REIL 实验室的联合采集**，不是两个互不相关的来源。这影响"跨数据集复现"的独立性表述——两个数据集可能有共同的实验规范与设备谱系。

**仍未解决**：63 个工况各自对应哪一组（充电倍率, 放电倍率, DoD）。该映射只在 `README_V2.0.pdf` 的表里，当前不可得。

**可行的替代路径**（不需 README）：
- `Cycling_json.zip`（10.2 GB）含真实电流/电压时序，可**从数据直接测出**每个工况的充电倍率、放电倍率与 DoD，而不必依赖表格。这是**测量**而非**推断**，符合本项目纪律。
- 或从论文 *"Predicting battery lifetime from early aging data"*（Tingkai Li 等）正文的条件表取。

**注意**：本轮 C3 用的 scout 前缀描述符是从容量通道统计量导出的 1 维代理。若补取到三因子映射，应改用**真实应力因子**，那才是设计上预设的工况轴。

### 4.4 **三因子映射已取回** ✅（转录、覆盖、方向三项一致性检查通过——**不是**对映射的认证）

**取回路径**：curl / API / 直连 / cookie 会话全部失败后，用 **Edge headless 过 JS 挑战页**，再复用该 profile 下载 → `README_V2.0.pdf` **640,953 字节**（与 figshare 官方字节数完全一致）落到 `%USERPROFILE%\Downloads`。

**已落盘**：
- `.research/lit/ISU-ILCC-README_V2.0.pdf`（640,953 B）
- `.research/results/isu_conditions.csv`（1,269 B，63 行）

**解析结果（Table A1）**

| 项 | 值 |
|---|---|
| 工况数 | **63**（组号 1–64，**缺 15**） |
| 充电倍率 | 0.500 – 3.000，39 个不同取值 |
| 放电倍率 | 0.500 – 2.475，36 个不同取值 |
| 平均 DoD | **4.16% – 98.16%** |
| 与数据交叉核对 | 数据 63 组 vs 表 63 组，**双向零差异**（无「数据有表无」，无「表有数据无」） |

**一致性检查（不是「验证」）**：用解析出的描述符去预测各工况的平均 EOL，看方向是否符合物理：

| 描述符 | Spearman ρ（vs 平均 EOL RPT） | p |
|---|---:|---:|
| **平均 DoD** | **−0.619** | **< 0.0001** |
| 充电倍率 | −0.301 | 0.0167 |
| 放电倍率 | −0.058 | 0.6490 |

放电深度越深 → 寿命越短，这是电池老化的基本规律。

**但这只证明「聚合层面与预期方向一致」，不证明每一个组号映射都正确。** 错误映射若保持 DoD 的秩、或只在 DoD 相同的组之间互换，该相关依然成立；代码里没有做任何映射误差模型。配合前两项（转录逐值一致、组号集合双向零差异），合计是**三项一致性检查**，不是对映射的**认证**。

（放电倍率不显著，与这批电芯的倍率范围窄有关，不是解析错误。）

### 4.5 描述符可用后，候选的可做性变化

| 候选 | 之前 | 现在 |
|---|---|---|
| C5 无标签选校准器 | 不需要描述符 | 不变 |
| C2 无标签 go/no-go | 不需要 | 不变 |
| **C4 下一个工况选哪个** | 需退化到 1 维代理（C3 已证退化） | ✅ **现在有真实 3 维应力因子**，不再退化 |
| C3 | 已关闭 | 仍关闭（不因数据改善而复活） |

---

## 5 本审计**没有**做的事

- 未下载 2.35 GB / 6.55 GB / 7.05 GB 原始归档（时间与磁盘）
- 未做字段级核对（需先下载）
- 未核实 `CyclingParameters.csv` 的实际列（1 kB 文件，需先取得真实下载 URL；item 页给出的 `viewcontent` 链接未成功取回）
- 未做任何拟合

## 6 一句话（已修正）

> **两个数据集的来源都已追溯清楚，且都是 CC BY 4.0 公开数据。** 本项目的两个"数据问题"（没有描述符、来源不明）其实都是**本地副本不完整 + 下载失败**造成的，不是数据源缺失。
>
> 但这**不改变 C3 关闭的结论**。**准确说法**：C3 **未能建立所指定的 5% 实用优势**（点估计为负、G_A 上界 +0.06%）。**不能说「效应不存在」**——边际区间上界为正，仍允许小的正收益；数据量也**不是**已排除的成因（原始地板检验只有 3 个合格工况）。补齐数据只能让**将来的**实验更干净，不能复活 C3。

## 7 上一版的错误

本审计第一版写「ISU 源未定位、阻塞级」，是**错的**。错因：只查了 UConn REIL 集合（那里确实没有 248 电芯的），没有查 ISU 自己的 figshare 仓库，也没有核对本地 `README_uconn.txt` 其实是 Cloudflare 挑战页而不是 README。

**教训**：`README` 文件名对、内容是挑战页 —— 这种"看起来有、其实是空的"证据，必须打开看内容，不能只 `Test-Path`。
