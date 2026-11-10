# 模型新颖性审计

> 程序 `dual-rate-transformer-rul-20261110` · 独立文献代理（Crossref/OpenAlex/出版社核实）

## 判定

**DROCT 作为 IEEE TIM 方法贡献：不通过。** 代理原文：
> "the contribution is an application composition"
> "a conjunction of four occupied parts with no new identifiable object is not novelty."

## 逐模块

| 模块 | 最接近已发表工作 | 判定 |
|---|---|---|
| **M5 观测校正**（`z⁺ = z⁻ + K(r − H(z⁻))`） | KalmanNet, IEEE TSP 2022, `10.1109/TSP.2022.3158588`；KalmanFormer, Front. Neurorobot. 2025, `10.3389/fnbot.2024.1460255`；**电池 SOH 版**：Sayed & Mahmoud, IEEE ECCE 2025, `10.1109/ECCE58356.2025.11259867`；多观测 EKF 电池 RUL：Chen et al., CJEE 2026, `10.23919/CJEE.2025.000151` | **OCCUPIED** |
| M1/M2 逐循环 patch Transformer | IIP-Mixer, Energies 2024, `10.3390/en17143553`；CyclePatch/BatteryLife, KDD 2025, arXiv:2502.18807 | **OCCUPIED** |
| M2 真实时间位置编码 | ConvTrans+tAPE, **IEEE TIM 2025**, `10.1109/TIM.2025.3564016`；SambaMixer, IEEE Access 2025 | **PARTIALLY OCCUPIED** |
| 潜退化状态 + Transformer + RUL | DSST, RESS 2026, `10.1016/j.ress.2026.113686` | **OCCUPIED** |
| M4 跨注意力双流融合 | BatteryCDE, IEEE TTE 2025, `10.1109/TTE.2025.3547740`；CJEE 2026 多观测融合 | **OCCUPIED** |

## 联合偏置 b(Δt, ΔN, ΔQ)

未检索到完全相同的三元联合偏置，但**每一项都是已知技术**，且其联合是已知相对位置偏置的
重新参数化。更要命的是**在本数据上不可识别**：同一工况内 C-rate 与 DoD 固定，
故 ΔQ ≈ c·ΔN、Δt ≈ s·ΔN；三者近似共线，**联合偏置只在跨工况时才有区分度**——
而留一工况恰好移除了训练侧的跨工况信号。**应作为不可识别项删除，而不是作为创新保留。**

## 必须撤回的主张

1. 不得声称「观测校正」是新颖机制。
2. 不得声称「多尺度 Transformer」是新颖结构。
3. 不得声称「不规则 RPT 到达」——ISU 的 RPT 是**协议排定**（每周一次，工况 20–64 另有 3.5 天加测）。
4. 不得从注意力权重推断日历老化与循环老化的物理因果贡献。
