# 本地数据盘点（2026-11-07 实测）

来源：直接解析 `E:\桌面\rul\data\external\`，非文档转述。

## UConn（LFP，64 电芯 / 11 工况组 / 77 次 RPT）

**`data_slowpulse_1.pkl`** — 17,130 行

| 字段 | 形状 | 含义 |
|---|---|---|
| cell_id / group_id / rpt | (17130,) | 电芯 / 工况组 / RPT 序号（0–77）|
| num_cycles | (17130,) | 0–197 |
| soc | (17130,) | {20, 50, 90} |
| pulse_type | (17130,) | {chg, dchg} |
| **voltage** | **(17130, 101)** | **完整弛豫波形，101 点** |
| q_dchg / soh | (17130,) | 容量 / SOH（72.34–100）|
| dcir_chg_20/50/90, dcir_dchg_20/50/90 | (17130,) ×6 | 六个 DCIR 标量 |

**`data_cc_1.pkl`** — 14,373 行：同上字段，但 `voltage` 为 (14373, 600) 的恒流放电曲线。

**关键观察**：现有工作只用了 6 个 DCIR 标量，101 点弛豫波形（每次脉冲 × 3 SOC × 2 方向）从未进入特征。

## ISU-ILCC（NMC，188 电芯）

**`RPT_json.zip`** — 250 个电芯 JSON（25–70 MB/个），实测字段仅 9 个：

`capacity_discharge_C_5` / `C_2`、`capacity_charge_C_5` / `C_2`、
`QV_discharge_C_5` / `QV_charge_C_5` / `QV_discharge_C_2` / `QV_charge_C_2`（Q,V,t,E,I）、`start_stop_time`

**结论：ISU 没有脉冲，也没有 EIS**，只有容量与 QV 曲线。任何"测量通道"研究在 ISU 上无法验证。

## Severson（LFP，124 电芯）

`data/external/severson`，31.5 MB。仅快充循环，无脉冲 / EIS。

## NASA PCoE（LCO，2026-11-07 已下载并验证）

位置：`data/external/nasa_pcoe/NASA_5_Battery_Data_Set.zip`（200 MB，107 s 下完），
内含 6 个子包：FY08Q4（B0005/6/7/18）与 B0025–B0056 分四组。

已实测 B0005.mat：

| 项 | 值 |
|---|---|
| 操作总数 | 616（charge 170 / discharge 168 / **impedance 278**）|
| EIS 频点 | 48 点复阻抗 `Battery_impedance` |
| 标量摘要 | `Re`（欧姆内阻）、`Rct`（电荷转移电阻）|
| 频段 | 0.1 Hz – 5 kHz（README）|
| EOL 判据 | 额定容量衰减 30%（2.0 → 1.4 Ah）|

结论：NASA 是第二个具备**非循环测量通道**的数据集，且频点完整、跨全寿命。

## 结论

- 有非循环测量通道的**只有 UConn**（64 电芯 / 11 组）。
- 该通道的原始波形已在本地，不需要下载。
- 第二数据集已落地：NASA PCoE（EIS）。Zenodo（Bayreuth）在本机返回 403，不可达；CALCE 可达但暂未下载。
- 两个数据集的测量通道不同（UConn = 时域脉冲弛豫；NASA = 频域 EIS），这本身构成跨模态可比性检验。
