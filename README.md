# 非循环测量通道对电池 RUL 预测的增量价值

> 实证研究草稿。全部数字可追溯到 `docs/` 下的结果文件。

## 一句话

在 64 个 LFP 电芯、11 个工况组上，把脉冲弛豫的两节 RC 拟合参数加入放电曲线基线，电芯宏平均误差从 **6.587 降到 6.020（−8.6%）**，95% CI **[−0.999, −0.133]**，留一电芯下同向，62.5% 电芯改善。

## 核心结论

| 项 | 结果 |
|---|---|
| 通道增量（LOGO） | 6.587 → 6.020，−8.6%，CI [−0.999, −0.133] |
| 通道增量（LOCO） | 5.069 → 4.591 |
| 维度匹配后的参数化优势 | 从 0.135 缩到 0.089（约 1/3–1/2 是维度效应）|
| 方法层（轨迹编码 + 测试时适配） | 7.825，劣于基线 |
| 方法层（因果物理正则） | 6.274，劣于基线 |
| 跨工况稳健性（Bayreuth 23 工况） | 6 个参数中仅 a1、c 过 Bonferroni 校正 |

## 这个结果为什么可信

1. **模型完全固定**，只更换输入特征集——增益只能归因到通道
2. **用一组更强的方法排除"拟合能力"解释**——四种更强的表征方案全部劣于固定模型
3. **转导结果被明确排除**——唯一更好的 5.724 使用整批查询，标注为不可部署
4. **跨工况判据预注册**——统计单位锁定为工况（n=23），避免芯级 p-hacking
5. **数字单一来源**——`scripts/e1_final.py` 一次跑出，4 个种子结果完全相同（HGB 在此规模确定性）

## 仓库结构

```
docs/
  idea_report.md            Part 1–3：动机、RQ、相关工作、方法、实验设计
  e1_final_results.md       E1/E2 唯一权威数字
  tier2_results.md          方法层负结果
  bayreuth_D_results.md     跨工况判定与符号翻转表
  nasa_results.md           NASA 为何不可用
  second_dataset_check.md   CALCE 为何不可用
  data_inventory.md         本地数据盘点
  manuscripts/v1.0-draft.md 手稿初稿
scripts/
  e1_final.py               主实验（特征集对照 + bootstrap）
  tier2_pass.py             轨迹编码器 + 测试时自监督
  bayreuth_parse_all.py     48 电芯解析
  bayreuth_D.py             跨工况一致性检验
```

## 复现

```bash
# 主实验（约 32 分钟，单核 CPU）
python scripts/e1_final.py

# Bayreuth 解析（约 30 秒）
python scripts/bayreuth_parse_all.py

# 跨工况检验（约 3 分钟）
python scripts/bayreuth_D.py
```

依赖：numpy、scipy、scikit-learn、openpyxl（Bayreuth 部分）。

## 数据

| 数据集 | 获取方式 |
|---|---|
| UConn-ISU-ILCC | 本地 `data/external/uconn/`；公开数据集，见 UConn REIL |
| Bayreuth 2025 | Zenodo [10.5281/zenodo.15755725](https://zenodo.org/records/15755725)，CC-BY-4.0，875 MB |
| NASA PCoE | 经核查仅 4 个电芯有完整寿命轨迹，本项目**未使用** |
| CALCE | 无随寿命阻抗，本项目**未使用** |

数据不随仓库分发。

## 状态

草稿，未投稿。未完成项见 `docs/manuscripts/v1.0-draft.md` 末尾的 Pending 列表：
E3 分层分析未跑、图未画、参考文献作者待补。
