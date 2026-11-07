# 论文下载清单

下载后请放到本目录：**`E:\桌面\rul\rul_v4_20261107\docs\papers\`**

文件名**不必严格一致**，我按标题模糊匹配；但用下面的名字最省事（已去掉 Windows 非法字符 `: / \ * ? " < > |`）。
下载到的文件请不要改名成中文，也不要用 `(1)`、`(2)` 这类浏览器后缀。

---

## 必下（9 篇）— Part 1 已引用但正文未读

| # | 开放获取 | 标题 | 刊名 / 年 | DOI | 建议文件名 |
|---|---|---|---|---|---|
| 1 | ✅ 免费 | Toward Trustworthy and Transferable SOH/RUL Estimation for Lithium-Ion Batteries: A Critical Review and Multi-Fidelity Validation | Batteries 12(7):255, 2026 | — | `Toward Trustworthy and Transferable SOH-RUL Estimation for Lithium-Ion Batteries - A Critical Review and Multi-Fidelity Validation.pdf` |
| 2 | ✅ 免费 | Incremental capacity feature selection for lithium-ion battery state of health estimation considering estimation capability and efficiency | Cell Rep. Phys. Sci., 2026 | 10.1016/j.xcrp.2025.103083 | `Incremental Capacity Feature Selection for Lithium-Ion Battery State of Health Estimation Considering Estimation Capability and Efficiency.pdf` |
| 3 | ✅ 免费 | A Review of Methods of Generating Incremental Capacity–Differential Voltage Curves for Battery Health Determination | Energies 17(17):4309, 2024 | 10.3390/en17174309 | `A Review of Methods of Generating Incremental Capacity-Differential Voltage Curves for Battery Health Determination.pdf` |
| 4 | ✅ 免费 | Battery Health Monitoring and Remaining Useful Life Prediction Techniques: A Review of Technologies | Batteries 11(1):31, 2025 | 10.3390/batteries11010031 | `Battery Health Monitoring and Remaining Useful Life Prediction Techniques - A Review of Technologies.pdf` |
| 5 | ❌ 需权限 | Incremental capacity analysis (dQ/dV) as a tool for analysing the effect of ambient temperature and mechanical clamping on degradation | J. Electroanal. Chem., 2023 | 10.1016/j.jelechem.2023.117627 | `Incremental Capacity Analysis dQ-dV as a Tool for Analysing the Effect of Ambient Temperature and Mechanical Clamping on Degradation.pdf` |
| 6 | ❌ 需权限 | Early Prediction of Knee Point and Knee Capacity for Fast-Charging Lithium-Ion Battery With Uncertainty Quantification and Calibration | IEEE TTE, 2024 | 10.1109/tte.2023.3304670 | `Early Prediction of Knee Point and Knee Capacity for Fast-Charging Lithium-Ion Battery With Uncertainty Quantification and Calibration.pdf` |
| 7 | ❌ 需权限 | Nonlinear aging knee-point prediction for lithium-ion batteries faced with different application scenarios | eTransportation, 2023 | 10.1016/j.etran.2023.100270 | `Nonlinear Aging Knee-Point Prediction for Lithium-Ion Batteries Faced with Different Application Scenarios.pdf` |
| 8 | ❌ 需权限 | Battery lifetime prediction across diverse ageing conditions with inter-cell deep learning | Nature Mach. Intell., 2025 | 10.1038/s42256-024-00972-x | `Battery Lifetime Prediction across Diverse Ageing Conditions with Inter-Cell Deep Learning.pdf` |
| 9 | ⚠️ ACM 付费 | BatteryLife: A Comprehensive Dataset and Benchmark for Battery Life Prediction | KDD 2025 | 10.1145/3711896.3737372 | `BatteryLife - A Comprehensive Dataset and Benchmark for Battery Life Prediction.pdf` |

> 第 1/2/3/4 篇是开放获取，Google Scholar 点进去直接有 PDF 按钮，不用权限。
> 第 9 篇如果 ACM 页面下不动，搜 arXiv 版（BatteryLife 有预印本）。

---

## 建议补充（4 篇）— 写 Related Works 会用到

| # | 标题 | 刊名 / 年 | 用途 |
|---|---|---|---|
| 10 | Life-decomposition-based battery remaining useful life estimation: From a probabilistic view | Applied Energy, 2026 | RUL 的概率视角对照 |
| 11 | Physics-constrained deep learning with conformal prediction for early knee-point prediction in lithium-ion batteries | J. Energy Storage, 2026 | 膝点 + conformal，与 RQ3 相关 |
| 12 | Machine learning is rewiring Li-ion battery RUL prediction: A systematic review and outlook | ScienceDirect, 2026 | 最新综述，用于定位 gap |
| 13 | A comprehensive review of machine learning-based state of health estimation for lithium-ion batteries: data, features, algorithms | Renew. Sustain. Energy Rev., 2025 | 特征侧综述 |

---

## 已经在目录里的（不用下）

| 文件 | 说明 |
|---|---|
| `BatteryTTT - physics-guided test-time training (arXiv 2402.00068).pdf` | 拟借鉴的模型组件 |
| `RUL-QMoE - non-crossing quantile mixture-of-experts (arXiv 2512.23725).pdf` | SOTA 对照 |
| `battery-dataset-catalog.yaml` | 28 条电池数据集目录（BSEBench） |

---

## 下载后我会做什么

1. 逐篇读正文，把 Part 1 里标 `[PDF 不可用]` 的条目替换成实读结论
2. 补齐 References 的作者、卷期、页码
3. 清空"待核实清单"里能清掉的条目
4. 用实读内容重写 Related Works（阶段 B）

> 若某篇实在拿不到，告诉我，我按摘要级信息处理并在文中标注，不会假装读过。
