# F · 数据恢复

> 程序 `online-mechanisms-20261110` · 分支 `research/online-mechanisms-20261110`
> 授权：用户 2026-11-10 授权获取公开数据 `Cycling_json.zip`（仅数据获取、解析、
> 建立物理时钟、对齐、审计；不含付费服务、不含删除旧数据、不含解封测试集）。

---

## 1 官方版本核对（先于任何下载）

来源：DOI `10.25380/iastate.22582234.v2`，经 figshare API 直接核对（article 22582234）。

| 项 | 值 |
|---|---|
| 标题 | ISU-ILCC Battery Aging Dataset |
| DOI | 10.25380/iastate.22582234.v2 |
| 版本 | **2** |
| 发布日期 | **2023-12-21T14:03:15Z** |
| 归档总大小 | 11,186,085,527 字节 |

官方清单（名称 / 大小 / md5）：

| 文件 | 大小 | md5 |
|---|---:|---|
| Valid_cells.csv | 1,727 | 88e4a2a884c436831b6b5f1274409bad |
| process_data.py | 9,769 | ccb61a35ffb6f2e17b2d55b336f170c8 |
| README_V2.0.pdf | 640,953 | c03da9a1a3499989d2cdb655b41d4d0b |
| capacity_fade.zip | 140,256 | a25a6f717d51992f30abbb3d9046909f |
| Q_interpolated.zip | 47,797,453 | e4402a8a8537956880c2349f2531b358 |
| RPT_json.zip | 929,406,930 | 36331bf80f21d00e19a9a45095f542e8 |
| **Cycling_json.zip** | **10,208,084,439** | **27ac156b31f7c35d4f27a78267c0dd56** |

## 2 避免重复下载的检查（任务 §3.2）

| 检查 | 结果 |
|---|---|
| 本地是否已有 cycling 数据 | `data/external/isu_raw/one/G30C1.json`（12.6 MB）实为**RPT 记录**（双重编码字符串），**不是** cycling 数据 |
| 本地 `RPT_json.zip` | md5 **36331bf80f21d00e19a9a45095f542e8**，与官方清单**逐字节一致** → RPT 侧已核验 |
| 本地 `Q_interpolated.zip` / `README_V2.0.pdf` / `Valid_cells.csv` | 大小与官方一致 |
| `capacity_fade.zip` | 官方为 **RPT 派生的 time-on-test 曲线**（每电芯一个两列 CSV），**不含逐循环信息** |
| 结论 | **逐循环数据确实缺失**，必须下载 |

## 3 下载与完整性（任务 §3.3–3.4）

- 主机：**campus-h3**（`/home/user/dline/data/`），`nohup setsid` 断点续传。
- figshare 对**单连接限速**：实测单连接 63 KB/s、8 连接 496 KB/s、32 连接约 550 KB/s 起步，
  随后升至 10 MB/s 量级。故改用**分块并行**（64 MB/块，153 块，32 并发，逐块续传）。
- **校验结果**：

```
size 10208088439   (expect 10208088439)   ✓
md5  27ac156b31f7c35d4f27a78267c0dd56 (expect same)  ✓
entries: 253
```

**未把任何归档文件上传至 Git 仓库。** 归档仅存在于 campus-h3，仓库只保存代码与派生表。

## 4 解析（任务 §3.5–3.7）

`code/F1_parse_cycling.py`，按官方 `process_data.py` 的 schema 解析（双重编码 JSON）：

- 每个电芯的 `capacity_charge` / `capacity_discharge` 为**逐循环**列表（Ah）
- `time_series_charge/discharge` 为**逐循环**起止时间
- `start_stop_time` 为**逐周**起止时间

**解析结果：251 电芯 / 0 解析错误。**

| 量 | min | median | max |
|---|---:|---:|---:|
| 逐循环条目数 | 62 | 3,122 | 172,318 |
| 周数 | 1 | 18 | 79 |
| cycling 跨度（天） | 6.9 | 144.9 | 673.1 |
| 累计充电通量（Ah） | 14.5 | 245.7 | 697.2 |
| 累计放电通量（Ah） | 14.7 | 242.0 | 686.1 |

**版本交叉核对（重要）**：解析出的两个发布子目录为 `Release 1.0`（238 电芯）与
`Release 2.0`（**13 电芯**），**与官方 `process_data.py` 中硬编码的 `batch2` 列表
（G57C1-4, G58C1, G26C3, G49C1-4, G50C1/C3/C4，共 13 个）完全一致**。
这是版本一致性的独立证据。

## 5 对齐（任务 §3.7）

`code/F2_align_clock.py`：**用绝对时间戳对齐**（不用相对天轴，因为 RPT 与 cycling
两套记录不共享 t0）。对每个 (电芯, RPT) 记录该 RPT **之前**已累积的实测暴露量。

- 配对成功：**208 电芯 / 4,712 条 RPT 记录**
- 无前置循环的 RPT：208 条（4.41%），即每个电芯的第 0 次 RPT —— 符合预期

## 6 交付物

| 文件 | 内容 |
|---|---|
| `protocol/F1_cycling_cells.csv` | 逐电芯解析摘要 |
| `protocol/F1_cycling_arrays.pkl` | 逐电芯紧凑数组（时间戳 int64、累计通量） |
| `protocol/F2_cell_audit.csv` | 逐电芯质量指标 |
| `protocol/F2_rpt_alignment.csv` | 逐 (电芯, RPT) 三时钟对齐 |
| `protocol/F4_clock_table.csv` | **最终时钟表**（含准入标记） |
| `protocol/F4_admission.csv/.json` | 准入决定 |
| `code/F1_parse_cycling.py`、`F2_align_clock.py`、`F3_quality.py`、`F4_admission.py` | 原始文件→物理时间轴的全部转换代码 |
| `code/remote/fetch_cycling_parallel.sh` | 分块并行下载与校验 |

Git commit：见仓库 `research/online-mechanisms-20261110` 分支最新提交。
