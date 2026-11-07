# -*- coding: utf-8 -*-
"""rulkit —— 本项目统一实验框架（特征构造 / 划分 / 指标 / 落盘 / 登记）。

设计约束
--------
1. 只读原始数据，不修改 docs/ 下任何历史结果。
2. 所有随机性必须显式记录在配置里（seed 列表），不允许隐式随机。
3. 每次运行都落盘 JSON 摘要 + 预测矩阵，并追加到 EXPERIMENT_REGISTRY.md。

模块
----
env        环境快照（python / 包版本 / CPU）
data_uconn UConn-ISU-ILCC 原始 pickle 读取
features   统一特征构造（A_curve / C_desc20 / C_desc30 / C_ecm）
splits     统一 LOGO / LOCO 折生成
metrics    电芯宏平均 MAE、配对 bootstrap、分电芯误差
models     模型工厂（固定超参，跨实验共用）
runner     统一执行 + 落盘
registry   追加写入 EXPERIMENT_REGISTRY.md
"""
__version__ = "0.1.0"
