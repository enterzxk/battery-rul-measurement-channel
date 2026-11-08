# 交接文档 · battery-RUL donor allocation 项目

> 写于 2026-11-09 01:20。给**新开的对话**用。读完这份就能接手，不需要读历史。
> 项目根：`E:\桌面\rul\rul_v4_20261107`

---

## 0 一句话现状

**28 个实验做完了，3,866 词稿件写好了，两轮独立审计过了，目标已按"未达成"标记并冻结。**
剩下的全是**收尾与投稿准备**，不需要再跑实验。

---

## 1 这份稿子到底是什么

**标题**（暂定）：

> Donor Allocation at a Fixed Label Budget: Estimator Dependence and Population Boundaries in Battery RUL Calibration

**主贡献**（2026-11-09 改过一次定位，现在以这个为准）：

> 校准后处理层里，几个**从未被声明**的实现选择会大幅改变报告的效应量。
> 五个选择里，**拟合作用域**与**评估总体**始终是最大的两个（比其他三个大 3.3–17 倍），
> 其中**评估总体在两个数据集上都翻转结论符号**。

**供体效应**（多加一个供体细胞有没有用）**降级为这个框架的实例**，不再是标题主张。

---

## 2 关键文件在哪

| 用途 | 路径 |
|---|---|
| **稿件（唯一现行版）** | `docs/manuscripts/v4.0-tim.md` |
| 实验记录 28 份 | `.research/exp/EXP-001..028*.md` |
| 复算脚本 32 个 | `.research/results/*.py` |
| 单一事实源 | `.research/STATE.md` |
| 已证伪清单 | `.research/FALSIFIED.md` |
| Codex 决策 CD-001..016 | `.research/CODEX_DECISIONS.md` + `review-stage/CD-*.md` |
| 数字审计 | `.research/AUDIT_v4.0.md` |
| 引用审计 | `.research/AUDIT_CITATIONS.md` |
| **诚信审计（1 FAIL + 9 WARN）** | `review-stage/INTEGRITY_AUDIT.md` |
| 诚信修复记录 | `.research/AUDIT_INTEGRITY_REMEDIATION.md` |
| 文献查重 | `review-stage/LIT_SENSITIVITY.md` |
| 文献判定 | `.research/LIT_VERDICT.md` |
| 主张→实验映射 | `.research/CLAIM_MAP.md` |
| 图 | `docs/figures/sensitivity_budget.png` |
| **交接文档（本文）** | `HANDOFF.md` |
| GitHub | `https://github.com/enterzxk/battery-rul-measurement-channel` |

---

## 3 稿件结构（3,866 词，摘要 249 词）

```
## Abstract
## 1 Introduction
## 2 Related work
## 3 Protocol
  3.1 Data / 3.2 Predictor and calibration / 3.3 Statistics / 3.4 Protocol lock
## 4 Results
  4.1 Donor count, two datasets
  4.2 Estimator dependence
  4.3 Population boundaries
  4.4 Controls
  4.5 Practical utility
## 5 A sensitivity budget for calibration post-processing   ← 主贡献
## 6 Limitations
## 7 Conclusion
## References（5 条，全部核实）
```

---

## 4 核心数字（都已核实可追溯）

**供体数效应**（k=8，1 vs 2 供体，cell-macro，mean 聚合）

| 数据 | 校准器 | m=1 | m=2 | Δ | 改善 | Holm |
|---|---|---:|---:|---:|---:|---:|
| UConn 循环 | affine | 516.88 | 500.21 | +16.67 | 11/11 | 0.0002 |
| UConn 循环 | isotonic | 459.95 | 453.33 | +6.63 | 8/11 | 0.34 ns |
| UConn 循环 | 1-NN | 535.51 | 543.33 | −7.82 | 2/11 | 0.036 |
| ISU RPT | affine | 2.827 | 2.670 | +0.156 | 44/57 | 0.0003 |
| ISU RPT | isotonic | 2.551 | 2.466 | +0.085 | 39/57 | 0.0005 |
| ISU RPT | 1-NN | 2.756 | 2.819 | −0.063 | 7/57 | 0.0000 |

**敏感度预算**（相对各自基线）

| 决定 | UConn | ISU |
|---|---:|---:|
| 拟合作用域 | **+274%** | **+140%** |
| 评估总体 | **−208%** | **−332%** |
| 抽样聚合 | −6% | −43% |
| 聚合顺序 | +12% | −26% |
| 行分配 | −10% | +28% |

分离度：UConn **17.3×**，ISU **3.3×**。

**2×2 联合空间（UConn）**：+17.11 / −16.27 / +74.22 / +1.13，极差 90.49（基线 5.3 倍），交互 −39.70。
**2×2 联合空间（ISU）**：+0.095 / −0.193 / +0.080 / −0.245，交互仅 −0.037。

→ **交互项只在 UConn 出现，不复现。作用域主导也不复现。只有"评估总体翻转符号"在两个数据集上都成立。**

---

## 5 还没做完的事（按优先级）

### P0 · 必须做，否则不能投

1. **自己核对 Peng 2026 原文**（`doi:10.3390/en19204805`）。
   现在稿子里引的具体数字（108%、−5.3%→+4.5%、−16.8%→+4.3%）**全部来自子代理转述，我没读过原文**。
   MDPI 直连 403，需要换路子（学校图书馆 / windows-mcp 走浏览器 / 找 PDF 镜像）。
   **这是目前最大的风险点。**

2. **重跑诚信审计复检**。上一次判 SERIOUS-ISSUES（1 FAIL + 9 WARN），已全部修复，但**修完没复检**。
   可用 `integrity-forensics` 或 `paper-claim-audit` 或 `citation-audit` skill。

### P1 · 投稿形态

3. **转 LaTeX**。现在只有 Markdown。TIM 用 IEEEtran 双栏。
4. **Figure 1 图注**（图已生成，图注还没写）。
5. **作者信息 / 单位 / 基金**（我不知道，需要用户提供）。

### P2 · 可选增强

6. ISU 上补 median 聚合的臂值（UConn 已有，ISU 没有）。
7. 第二个基模型（Ridge）在 ISU 上的完整对照（现在只有 UConn 有）。

---

## 6 千万不要重做的事（已证伪，重做纯浪费时间）

| 编号 | 已证伪的内容 |
|---|---|
| F-001 | 非循环测量通道能加 RUL 信息（两个 artifact：ECM 拟合窗口 bug、标签单位误读）|
| F-002 | 参数化优于描述符 |
| F-003 | 四条方法路线 |
| F-004 | 可辨识性定律 |
| F-005 | isotonic 重建 |
| F-006 | 泄漏 49% |
| F-007 | 分位数放置 |
| F-008 | D-optimal / S_k 机制 |
| F-009 | 「k 不是主要杠杆」 |

**还有三个方向性误判，别重走**：
- **「部署约束（as-of）导致效应反转」** → EXP-019 因子设计证明是**评估总体**造成的，不是约束。交互项全零。
- **「效应随 RUL 翻转」** → EXP-020 分层，16 个格子符号零例外，不翻转。
- **「两个后处理决定都主导」** → EXP-027 在 ISU 上只有总体主导，作用域不重要。

---

## 7 环境与坑

**Python**：系统 `python` 可用，有 numpy/scipy/sklearn/matplotlib/fitz。

**必须设**：`$env:PYTHONIOENCODING='utf-8'`（否则中文输出 GBK 报错）。

**数据（已固化进仓库，不再依赖临时目录）**：
- `.research/results/v2_main.py` — 含 `build()`，UConn 全流程，会 refit ECM（约 30–90 秒）
- `.research/results/isu_table.npz` — ISU 特征表（418 KB）

30 个脚本已改成从**脚本所在目录**读这两个文件，可以整个仓库搬到别处跑。
已验证：`python uconn_median.py` 从仓库内数据复现出 510.13 / 495.80 / +14.32 / Holm 0.0016，与记录一致。

**代理**：`http://127.0.0.1:7897`（git push、外网请求都要走它）
- `web_fetch` 工具**坏了**，别用
- MDPI / ScienceDirect 直连 403
- arxiv.org 直连可用
- Crossref API 可用（`api.crossref.org/works/{doi}`）
- OpenAlex 返回空，别用

**git**：每个 repo 需要单独设 proxy
```
git config http.proxy http://127.0.0.1:7897
```
push 容易超时，用 `run_in_background: true` 跑。

**Codex 审稿桥**：`mcp__codex__codex`（model `gpt-6.1-sol`，`model_reasoning_effort: "xhigh"`）。
`subagent_codex` 工具**坏的**，别用。

---

## 8 三条纪律（用户明确要求过）

1. **不要问用户做决定**。决策交给 Codex（L2）或子代理。只有 L3（不可逆删除、未授权外部访问、付费义务、安全权限、对外发布）才需要人。
2. **每次结束必须给「实验结果 + 创新点」**，不能只叙述过程。
3. **负结果照实报**。用户说过「一般论文不会写自己不好的地方」，但**负结果不是"不好的地方"**——那是论文内容。可以删的是"我们犯了六个错"这类过程自曝，不能删的是"1-NN 反向""选择规则不超越最优固定策略"。

---

## 9 目标的当前状态

目标 `goal-69c022d3-...` 已标记 **blocked**，理由：

> FIXED GOAL UNMET; CURRENT EXPERIMENTAL LINE EXHAUSTED.
> M1 没建立预注册的行轴饱和判据（k=16→64 仍变 0.03–0.15，超 0.05 等价界，且只有 3 个配对单元）。
> 后续实验支持的是「估计器依赖的分配效应」，不是原定的「供体身份地板」。

**要继续必须由用户明确改写目标范围**，否则按 CD-016 应保持冻结。

---

## 10 新对话的第一句话建议

把这段直接贴给新会话：

> 读 `E:\桌面\rul\rul_v4_20261107\HANDOFF.md`，然后按里面 §5 的 P0 开始做。
> 不要问我，决策交给 Codex。


---

## 11 数据可复现性（2026-11-09 01:30 补）

原来 32 个脚本都从 `C:\Users\Administrator\AppData\Local\Temp\` 读数据和构建函数。
**临时目录一清，全部失效。**

已修：
- `v2_main.py`（11 KB，含 `build()`）与 `isu_table.npz`（418 KB）已复制进 `.research/results/`
- 30 个脚本改成用 `os.path.dirname(os.path.abspath(__file__))` 定位
- 冒烟测试通过：`uconn_median.py` 复现出与 EXP-023 完全一致的数值

**现在整个仓库是自包含的**，clone 下来就能重跑。
