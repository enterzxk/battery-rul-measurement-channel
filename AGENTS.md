# AGENTS.md · 项目级科研 Agent 契约

> **定位**：本文件只管四件事——**科研目标、决策权、质量标准、持续执行规则**。
> 科研工作流本身由 **ARIS skills** 负责，本文件不复制、不覆盖、不改写任何 SKILL.md。
>
> **阅读顺序**：本文件 → `.research/STATE.md`（唯一运行期真相）→ `.research/CAPABILITIES.md`（实测能力）→ 相关 ARIS SKILL.md。
>
> 最后更新：2026-11-08

---

## 1. 研究任务

**方向**：锂离子电池剩余寿命（RUL）与健康状态（SOH）预测。
**目标**：形成一项方法上有真实创新、证据可复现、可投 Q1 期刊（IEEE TIM / TII / TTE、Applied Energy、eTransportation 等，按贡献定）的成果。

**当前主线（2026-11-08 起）**：**标签预算**——跨工况零标签（LOGO）不可行；给目标工况少量**其他电芯**的标签即可大幅降低误差。

| k（目标工况标签数） | cell-macro MAE | Δ | 检验 |
|---:|---:|---:|---|
| 0 | 6.516 | — | — |
| 8 | 5.185 | −1.331 | p=0.196，5/11（不显著）|
| **16** | **4.505** | **−2.010** | **Wilcoxon p=0.0049，9/11** |
| 32 | 4.248 | −2.268 | p=0.0010，11/11 |

**备选**：论文级统计实践审计（单位=论文，需先过全文可达性与编码可靠性两道闸门）。

**已证伪、不得重试**：见 `.research/FALSIFIED.md`（F-001 通道增量 / F-002 参数化优于描述量 / F-003 四条方法路线 / F-004 可辨识性定律 / F-005 保序重建 / F-006 leaky 口径的 49%）。

---

## 2. 三层科研决策权限

> 目的：把「停下来问用户」从默认行为改成**例外**。非授权性质的科研问题一律自决或交 Codex。

### L1 · DSH 自主决定（不问用户，也不必调 Codex）

- 常规代码实现、重构、修复
- 实验参数、运行计划、随机种子
- GPU 任务调度（campus-h3 / lab-server）
- 文献筛选、整理、精读
- 可恢复的实验失败（报错、依赖缺失、显存不足）
- 基线复现、数据分析、画图
- 实验报告与科研记录

### L2 · Codex 决定，DSH 执行（**不再问用户**）

以下问题**必须**先交 Codex，拿到决定后立即执行：

1. 多个科研 Idea 如何取舍
2. 是否放弃当前技术路线
3. 新方法是否真正具有创新性
4. 重要的数学建模与架构设计选择
5. 是否需要额外消融或实验
6. 出现相互矛盾的实验结果
7. 重要的论文方法学争议
8. 是否进入下一个科研阶段

**调用要求**：给足上下文（候选方案、文献证据、实验结果、判断标准），要求输出**决定 / 理由 / 反对证据 / 风险 / 下一步**。

**辩论上限**：证据不足时允许 Codex 与 DSH 最多**三轮**针对性辩论；仍有争议则按预定义证据标准选**可验证**的那条，不得无限辩论。

**路由**：

| 场景 | 用哪个 |
|---|---|
| 需要多轮往返、要 threadId 续接 | `mcp__codex__codex` + `mcp__codex__codex-reply` |
| 一次性独立决策/代码审查，异步即可 | ~~`subagent_codex`~~ **实测不可用**（`product-error`），改用 `mcp__codex__codex` |

两者都走 ARIS codex-exec 桥，模型 **gpt-6.1-sol**，强度 **xhigh**（见 §8）。

### L3 · 必须人工授权（Codex 不得代授）

1. 不可逆删除已有重要数据
2. 访问未经授权的外部资源
3. 产生新的付费义务
4. 修改安全与访问权限
5. 对外投稿、发布成果、不可逆外部操作

**Codex 不能替用户授予本来没有的权限。** 这三类之外，一律不停下来问。

### 执行纪律

- 不得为了「避免提问」而随手选一个方案——自决的前提是有证据。
- **不得把 Codex 的主观评分当创新性证据**；它只能裁决「走哪条」，不能证明「够新」。
- 重要结论必须能追溯到论文、代码或真实实验。
- 不要让每个低价值问题都触发 Codex（L1 的事自己做完）。
- 汇报 ≠ 提问：除非属于 L3，汇报里写「已自动选择 X 并继续」。

```yaml
AUTO_PROCEED: true
HUMAN_CHECKPOINT: false
```

---
## 3. 子代理编制（真实创建，不是角色扮演）

重要假设必须由**独立上下文**裁决，不得自己评估自己。

| 时机 | 必须启动 | 交付 |
|---|---|---|
| 任何新假设进入实验前 | **文献/查重代理** | 最接近的已发表工作 + 是否已被占据 |
| 任何新假设进入实验前 | **创新性审查代理** | 四轴查重结论：GO / NO-GO / 降级 |
| 方法定型前 | **方法设计代理** | 机制、数学定义、可证伪预测 |
| 实验跑完后、写论文前 | **实验审计代理** | 泄漏、口径、统计单位、功效复核 |
| 方向决策 | **独立决策代理** | 排序 + 理由 + 风险，主代理执行 |

规则：

- 子代理任务必须**自包含**（它看不到本会话上下文）。
- 推理档位用当前环境支持的最高档（实测：`low / high / max`）。
- **禁止**把「我自己又看了一遍」写成「已由独立代理审阅」。审不了就标 `REVIEW-UNAVAILABLE` 并降级。

---

## 4. 质量标准

### 4.1 每个 Idea 必须写全

研究问题 / 文献证据 / **可证伪假设** / 差异化机制（不是模块命名）/ 数学或算法规格 / 强基线 / 可复现评测协议 / 失效条件。

### 4.2 新颖性不能自证

LLM 自评的 novelty 分数不算证据。必须走 ARIS `novelty-check` 或 `research-review` 的四轴查重。
本机 `rules/contracts/NOVELTY.md` 不存在 → 用 ARIS skill 替代，并标注替代来源。

### 4.3 功效先于方法（本项目用血换来的）

**任何以聚类为单位的推断，选题前先算**：

```
有效 n = 可用单位数 / design effect
design effect = 1 + (组均大小 − 1) × ICC
```

本项目实测：ICC = 0.414 → deff 2.99 → 64 电芯等效 **n = 21.4**；n=11 工况的 MDE = 基线 MAE 的 **17.1%**，检出 d=0.28 需 **120 个工况**。
**功效上界在选数据那一刻就被封顶，事后无法用方法补救。**

### 4.4 三条硬约束（违反即结论作废）

1. **单位不变性**：若标签是部署单位的电芯特异缩放（如"体检次数"vs"循环数"，缩放比 1.98），该单位下的 MAE 不是尺度不变的，必须换单位复算。
2. **校准必须电芯不相交**：少样本校准的标签不得来自被评估的电芯。leaky 与 strict 在本项目差 49% vs 31%。
3. **预注册必须可检验**：自变量取值 < 5 个时禁止做单调性检验。一个无法检验的预注册比没有预注册更伤信誉。

### 4.5 报告纪律

- 数字必须有锚点（文件路径 + 行号/表号），算不出来的写「未知」。
- 失败必须登记进 `.research/FALSIFIED.md`，写清机制，不得用换种子/加轮次掩盖。
- 负结果与正结果同等对待；不得为了叙事删掉 8.6% 那段历史。

---

## 5. 算力政策

**实测能力（2026-11-08）**：

| 资源 | 状态 |
|---|---|
| 本机 GPU | RTX 3060 12 GB 存在，但 torch 为 CPU-only 构建（`2.4.1+cpu`）→ 需装 CUDA 版 torch 才可用 |
| 本机 CPU | i5-13400F，10 物理核 / 16 线程，16 GB |
| **lab-server** | ✅ **NVIDIA A40 48 GB**（SSH `lab-server`，key `id_ed25519_lab_server`）；32 核 / 62 GB RAM |
| **campus-h3** | ✅ **2 × RTX 3090 24 GB**（SSH `campus-h3`，key `id_ed25519_campus_h3`）；64 核 / 125 GB RAM |

**政策**：

- 允许为一个有前景的想法跑**数小时到一天**的实验，不因"贵"而放弃。
- **拒绝没有研究价值的反复小测试**：改一个超参跑一次、换个种子看波动、无假设的网格扫描——这类一律不做。
- 每个实验跑之前先回答：**如果失败，我得到什么信息？** 答不出来就不跑。
- 神经网络实验要多 seed；但本项目已实测 HGB 在此规模**确定性**（std=0），不要浪费算力跑多 seed，改用 bootstrap 承载方差。
- 上服务器跑之前先探测 GPU（`nvidia-smi`），没探测不许声明"已部署到 GPU"。
- **优先 campus-h3**（2×3090，64 核，125 GB）；A40 在 lab-server，单卡 48 GB 适合大显存单任务。
- 远程跑一律 `nohup`/`tmux` + 日志落盘，结果拉回本地 `results/` 后才算数。

---

## 6. 持久化与恢复

**唯一运行期真相**：`.research/STATE.md`。任何新会话/新子代理接手，先读它。

| 文件 | 作用 |
|---|---|
| `.research/STATE.md` | 当前位置、已确定/未确定/已证伪、下一步 |
| `.research/CAPABILITIES.md` | 实测能力与降级点 |
| `.research/LEDGER.jsonl` | 机器账本，只追加不改写 |
| `.research/FALSIFIED.md` | 已证伪清单，防重试 |
| `.research/reports/PHASE-N-*.md` | 每阶段报告 |
| `.research/exp/EXP-*.md` | 实验记录（配置/种子/结果路径）|
| `research-wiki/` | ARIS 知识库（论文/想法/实验/论断图谱）|
| `.research/CODEX_DECISIONS.md` | **L2 决策记录**——新会话先读，不重复讨论已决问题 |
| `.aris/runs/<run_id>.json` | ARIS 流水线阶段状态（done vs accepted），可 resume |
| `refine-logs/FINAL_PROPOSAL.md` | 当前方案定稿 |
| `refine-logs/EXPERIMENT_PLAN.md` | 当前实验计划（M0–M6）|
| `docs/` | 论文证据与历史结果（只读，不覆盖）|

**规则**：

- `done` ≠ `accepted`：文件写完只算 done；报告写完 + STATE.md 更新才算 accepted。
- 上下文压缩前必须先把状态 flush 进 STATE.md，宁可写短不能丢。
- 历史结果只读：新结论写新文件，旧文件加作废横幅，不覆盖。

---

## 7. 与 ARIS 的关系

**ARIS 负责工作流，本文件负责目标/决策/质量/持久化。**

| 阶段 | 用什么 ARIS skill |
|---|---|
| 仓库与历史审计 | `research-lit` + 本文件 §1 |
| 文献检索与精读 | `arxiv` / `semantic-scholar` / `openalex` / `research-lit` / `deepxiv` |
| 知识沉淀 | `research-wiki` / `wiki-enrich` |
| 找 gap 与想法 | `idea-discovery` / `idea-creator` |
| 方案细化 | `research-refine` / `research-refine-pipeline` |
| 查重与对抗审稿 | `novelty-check` / `research-review` / `kill-argument` |
| 实验计划 | `experiment-plan` / `ablation-planner` |
| 跑实验 | `run-experiment` / `experiment-queue` / `monitor-experiment` |
| 结果裁决 | `result-to-claim` / `analyze-results` |
| 实验审计 | `experiment-audit` / `paper-claim-audit` |
| 写论文 | `paper-plan` / `paper-write` / `paper-writing` |
| 图 | `paper-figure` / `nature-figure` / `figure-spec` |
| 引用与诚信 | `citation-audit` / `integrity-forensics` |

### 实际支持的参数（不要虚构）

| 参数 | 支持 | 说明 |
|---|---|---|
| `AUTO_PROCEED` | ✅ | research-pipeline / idea-discovery / auto-review-loop |
| `HUMAN_CHECKPOINT` | ✅ | 同上 |
| `REVIEWER_DIFFICULTY` | ✅ | research-pipeline（medium / hard / nightmare）|
| `CODE_REVIEW` | ✅ | research-pipeline |
| `effort` | ❌ 不是 skill 参数 | 属 Codex 的 `model_reasoning_effort`，见 §8 |
| `reviewer: codex` | ❌ 不是 skill 参数 | skill 用硬编码 `REVIEWER_MODEL`；由 §8 覆盖 |

**禁令**：

- 不修改 ARIS 原始 SKILL.md，不复制其内容到本文件。
- 执行任一工作流前先读对应 SKILL.md。
- 若 skill 与实测能力冲突（如 GPU 不可用），按实测降级并写明降级点，**不得假装调用成功**。

---

## 8. 模型配置

**不改动现有 DeepSeek V4.1 Flash 配置。** 子代理沿用当前 provider/model；推理档位按任务需要选 `low/high/max`，但不新增、不替换、不重配任何模型路由。

### 跨模型 Reviewer（Codex）

| 项 | 值 | 依据 |
|---|---|---|
| 模型 | **gpt-6.1-sol** | `~/.codex/config.toml` + 会话元数据实测 |
| 推理强度 | **xhigh** | 同上（`"effort":"xhigh"`）|
| 桥 | ARIS `codex-exec` MCP（**不是**已废弃的 `codex mcp-server`）| `mcp__codex__codex` 实测可用 |
| 配置位置 | `~/.codex/config.toml`（备份 `config.toml.before-xhigh-20261108`）| — |

**调用约定**：所有审稿调用都显式传 `model: "gpt-6.1-sol"` 与 `config: {model_reasoning_effort: "xhigh"}`。
ARIS 的 41 个 skill 里硬编码的是 `gpt-6-astra`——**不改 skill 文件**，由本文件覆盖。

**可用性**：Codex 有额度上限。额度耗尽时审稿降级为 same-family `provisional`，必须写进 `.research/REVIEW_STATUS.md`，不得当 `accepted`。

---

## 9. 禁止事项

- 编造文献、DOI、作者、数据集、实验结果。
- 用测试集反复挑选方法/超参。
- 把负结果包装成正结果，或删掉不利的历史记录。
- 未探测就声明"已部署 / 已审阅 / 已复现"。
- 破坏性覆盖：删历史结果、重写 git 历史、覆盖他人文件。
- 未经授权的外部发布与付费资源。

---

## 10. 汇报格式（每阶段结束必须）

先写 `.research/reports/PHASE-N-YYYYMMDD-HHMM.md`，再在对话里给 ≤25 行摘要：

```
━━━ 阶段 N · <名称> ━━━ ✅完成 | ⚠️带保留 | ⛔阻塞
结论：<一句话，说人话>

能确定：
 · <结论> ← <证据路径>
 · <结论> ← <证据路径>

还不能确定：
 · <问题>（缺 <什么证据>）

本轮否决：
 · <对象> — 原因：<一句>；处置：<FALSIFIED 编号>

下一步：<阶段 M> — 因为 <一句>
需要你决定：<具体问题 + 选项> | 无需你操作
```

「能确定」最多 4 条，「还不能确定」最多 3 条。「本轮否决」必须写，哪怕是"无"——没有否决记录通常意味着没做审稿。

---

## 11. 完成标准

不要因为出了 idea 列表、读完文献、跑完一次实验就宣布完成。

**达到以下全部才算可投稿**：

1. 文献证据体系可信（含最接近工作的正面对比）。
2. 研究问题有明确未解决部分，且有证据说明别人没解决。
3. 方法有原创机制 + 数学定义 + 可证伪预测。
4. 与强基线相比有可信、可复现、有实际意义的结果——或足以支撑严谨负向结论的其他证据。
5. 核心结果经过泛化、统计与独立审查。
6. 论文的主张、方法、实验、局限都有可写依据。
7. 代码、数据协议、结果可复现。

**若所有合理路线都被证伪**：由决策代理否决并切换，不得无限微调；最终必须给出可审计的负向结论，不得制造成功。
