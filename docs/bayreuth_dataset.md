# Bayreuth 2025 数据集落地（2026-11-07）

## 下载

Zenodo record 15755725，CC-BY-4.0，49 个文件 / **875.7 MB**，零失败。
位置：`data/external/bayreuth/`

> 注：本机此前对 Zenodo 返回 403，是请求头过于简陋（缺 Accept / Sec-Fetch-*）。补全浏览器头后恢复正常。Node 的 fetch 仍报 DNS 失败，PowerShell 的 Invoke-WebRequest 可用。

## 结构

每个电芯一个 zip，内含 9 个文件：

| 文件 | 大小 | 内容 |
|---|---|---|
| `M0001_checkup.txt` | ~14 MB | 首次全面体检：充/放/静置 |
| `M0002_aging.txt` | ~43 MB | 连续老化循环，**含周期性长静置** |
| `M0003_checkup.txt` | ~14 MB | 第二次全面体检 |
| `fXXXX_bol.txt` / `_eol.txt` | 10 KB | BOL / EOL 的 EIS |
| `fXXXX_bol_nfra.txt` / `_eol_nfra.txt` | 19 KB | BOL / EOL 的 N-FRA |

实测 F0001 的 `M0002_aging.txt`：209 万行数据，命令分布 Discharge 58k / Charge 68k / **Pause 81k** / Set-Temp 890。

**静置段是测量通道**：长静置可达 1081 个采样点、约 3 小时，电压从 3.00 V 恢复到 3.17 V——完整的弛豫曲线。

## 汇总表

`extracted_degradation_metrics.xlsx`，48 行 × 11 列：

`cell_name, temperature, c-rate, CF, dR_dch, dR_ch, LLI, LAMpe, LAMne, RMSE`

- **条件变量**：温度 {10, 25, 30, 55} × 倍率 {0.5, 1, 1.5} → 最多 12 个工况组，每组约 4 个电芯
- 这正好提供 LOGO 所需的工况结构，是 UConn（11 组）之外第二个可做留一工况的数据集

## 与 UConn 的互补性

| | UConn | Bayreuth |
|---|---|---|
| 电芯 | 64 | 48 |
| 测量通道 | 时域脉冲（101 点 × 3 SOC × 2 向）| 时域弛豫（3 小时静置）+ EIS + N-FRA |
| 工况结构 | 11 组 | 温度 × 倍率，最多 12 组 |
| 化学体系 | LFP | 未标注（需查原文）|

## 解析难点

1. `M0002_aging.txt` 每电芯 43 MB，48 个合计约 2 GB，需分块读取。
2. `Cyc-Count` 列在样本中恒为 1，不能直接当老化循环序号；需按 Charge/Discharge 段自行切分循环。
3. 长静置段需与循环对齐，才能得到"第 k 次循环时的弛豫曲线"。

## 待办

- [ ] 写分块解析器：按命令段切分循环，提取每次放电容量与每次长静置的弛豫曲线
- [ ] 用 xlsx 的 temperature / c-rate 构造工况分组
- [ ] 复跑 UConn 的同一套流程（ECM 拟合 → 特征集 → LOGO）
- [ ] 若 48 电芯上也成立，Part 1 的"两个数据集"才真正兑现
