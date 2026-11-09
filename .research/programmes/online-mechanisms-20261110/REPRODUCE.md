# REPRODUCE · online-mechanisms-20261110

环境：Windows，`python` 3.8（numpy / scipy / sklearn / pandas / PyMuPDF 已装）。
所有路径相对于仓库根 `E:\桌面\rul\rul_v4_20261107`。
必须设 `$env:PYTHONIOENCODING='utf-8'`（否则中文输出 GBK 报错）。

---

## 0 前置数据（不入库，需本地存在）

| 文件 | 大小 | 用途 |
|---|---:|---|
| `data/external/uconn/data_cc_1.pkl` | 70 MB | UConn RPT 级表（64 电芯 / 11 工况） |
| `data/external/uconn/data_slowpulse_1.pkl` | 16 MB | UConn 脉冲数据（本程序未用） |
| `data/external/isu_raw/RPT_json.zip` | 929 MB | ISU 原始发布（251 电芯） |
| `.research/results/isu_table.npz` | 418 KB | 旧处理表（248 电芯） |
| `.research/results/isu_conditions.csv` | 1.3 KB | 三因子工况表（63 行，本程序恢复） |

SHA256（本程序冻结）：

```
isu_table.npz         41D2C15AD22C6070A56B071E8C9A57DCAE7EC123CDBA22314B4F9A9993963805
isu_conditions.csv    262DC2C34392CF02FFF7719CC35943C78FDCC0CFAD988DE8D034AE1FC769B2EC
data_cc_1.pkl         7159BADAD08B68EDA55093B1FA8B0A9E435A6F56BA6407CC02E5F27E6809E3A5
data_slowpulse_1.pkl  0E7215513959D73FF797977C333B6F032C007348C73CD400E6017B93655F1C37
```

## 1 问题 A

```bash
cd .research/programmes/online-mechanisms-20261110/code
python build_uconn_online.py     # -> protocol/uconn_online_tidy.csv (2855 行), uconn_eol_intervals.csv (64), uconn_data_contract.json
python harness.py                # -> protocol/queries_S0/S1/S2.csv (各 192 查询)
python arms.py --sub S0 --out ../protocol/results_S0.csv
python arms.py --sub S1 --out ../protocol/results_S1.csv
python arms.py --sub S2 --out ../protocol/results_S2.csv
```

关键中间量：`protocol/uconn_data_contract.json` 里 `cadence_cycles.cv = 0.2292`（**跨电芯池化**）；
**电芯内** CV 0.091 与 `cum_cycles~rpt` R²=0.999 由 `RESULTS_A.md §2` 记录，复算见 `protocol/_probe/uconn_c_cadence.py`。

## 2 问题 B

```bash
python rebuild_isu_lifetime.py   # -> protocol/isu_lifetime_raw.csv (250), isu_lifetime_interval.csv (250)
python B_corrected.py            # -> protocol/B_corrected.json, B_corrected_loco.csv
```

**作废脚本（保留但不得引用结果）**：`B_mechanism.py`、`B_damage_law.py`、`B_loco.py`（见 CORRECTIONS.md C4–C8）。

## 3 问题 C

```bash
python C_thinning_uconn.py       # -> protocol/C_thinning_uconn.csv（固定 64 电芯 / 11 工况）
python C_landmark_fraction.py    # -> protocol/C_landmark_fraction.csv（f = 0.25/0.5/0.75，两队列）
```

**作废脚本**：`C_thinning.py`（v1）、`C_stress_budget.py`、`C_landmark_both.py`。

## 4 一键复核

```powershell
$env:PYTHONIOENCODING='utf-8'
cd .research\programmes\online-mechanisms-20261110\code
python build_uconn_online.py; python harness.py
foreach ($s in "S0","S1","S2") { python arms.py --sub $s --out "..\protocol\results_$s.csv" }
python rebuild_isu_lifetime.py
python B_corrected.py
python C_thinning_uconn.py
python C_landmark_fraction.py
```

预计总时长：ISU 原始 JSON 读取约 3–5 分钟（929 MB zip），其余各 1–3 分钟。

## 5 已知不可复现项

| 项 | 原因 |
|---|---|
| UConn 日历时间轴 | 需 `rpt_data.zip`（2.35 GB），未下载 |
| UConn / ISU 实测 Ah-throughput | 需 cycling 原始时序（13.6 GB / 10.2 GB），未下载 |
| ISU 右删失分析 | 重建后**零删失**，无对象 |
| 应力是否影响所需检查预算 | `C_stress_budget.py` 作废，未重做 |
