---
id: EXP-023
phase: 6
status: done
gate: 补 UConn 循环单位的 median 聚合臂值
started: 2026-11-08T23:15
ended:   2026-11-08T23:30
---

# EXP-023 · UConn 循环单位的 median 聚合（补主表缺口）

## 为什么做

诚信审计指出：主表只有 mean 聚合，而 §3.3 声明 median 是 mandatory sensitivity。

## 结果（UConn，真实循环数，k=8，200 次 MC）

| 校准器 | m=1 | m=2 | Δ | p | 改善 | Holm |
|---|---:|---:|---:|---:|---:|---:|
| affine | 510.13 | 495.80 | +14.32 | 0.0005 | 10/11 | 0.0016 |
| isotonic | 456.76 | 449.83 | +6.94 | 0.1157 | 8/11 | 0.1157 |
| 1-NN | 528.62 | 539.68 | −11.06 | 0.0012 | 0/11 | 0.0023 |

## 判定

与 mean 聚合同构：affine 显著、isotonic 不显著、1-NN 反向且显著。

**median 与 mean 在符号与「哪些校准器过校正」上完全一致。**

## 复算

脚本 .research/results/uconn_median.py
