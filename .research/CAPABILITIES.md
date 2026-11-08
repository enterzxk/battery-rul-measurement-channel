# CAPABILITIES · 能力探测（2026-11-07 首次进入）

| 能力 | 状态 | 实测依据 |
|---|---|---|
| Python | ✅ 3.8.7 | python --version |
| numpy/scipy/sklearn | ✅ 1.24.4 / 1.10.1 / 1.3.2 | code/rulkit/env.py |
| torch | ✅ 2.4.1+cpu | torch.cuda.is_available() == False |
| GPU（硬件） | ✅ **NVIDIA RTX 3060 12 GB 存在** | nvidia-smi --query-gpu |
| GPU（可用） | ❌ 当前不可用 | torch 2.4.1+cpu，cuda.is_available()==False；须装 CUDA 版 torch |
| CPU | ✅ i5-13400F 10 核 16 线程 16 GB | A4 实测 |
| git 网络 | ✅ 需代理 http://127.0.0.1:7897 | 已写入 rul_v4_20261107/.git/config |
| GitHub API | ✅ 经代理可用 | 仓库创建/推送/校验均成功 |
| raw.githubusercontent | ⚠️ 直连失败，需完整浏览器头 | 本轮多次失败 |
| arXiv 直连 | ✅ | A1 下载 9 篇 |
| Zenodo | ⚠️ 需完整浏览器头（非防火墙） | 前期记录 |
| MDPI / ScienceDirect | ❌ 403 | A1 记录，未绕过 |
| pdflatex / latexmk | ❌ 未安装 | Get-Command 为空 |
| **lab-server** | ✅ **NVIDIA A40 48 GB**，32 核，62 GB RAM | `ssh lab-server nvidia-smi` 实测 2026-11-08 |
| **campus-h3** | ✅ **2× RTX 3090 24 GB**，64 核，125 GB RAM | `ssh campus-h3 nvidia-smi` 实测 2026-11-08 |
| dsh-aris 插件 | ✅ 0.1.1（= npm latest），desktop profile | npm view + package.json |
| ARIS skills | ✅ 87 个目录，7 个重点全部 SKILL.md 就位 | 目录清点 |
| Codex 审稿桥 | ✅ 可用；**模型 gpt-6.1-sol / effort xhigh**（会话元数据实测）| 实调用 2026-11-08 13:45 |
| Codex 额度 | ⚠️ 有上限，2026-11-08 早间曾耗尽（11-11 恢复），现已重置 | 报错原文记录在 REVIEW_STATUS.md |
| ARIS skills | ✅ 已装于 dsh-aris 包（28 个在 ~/.dsh/skills，全套在 node_modules/dsh-aris/skills） | 目录清点 |
| research-wiki 助手 | ✅ .aris/tools/research_wiki.py | init 成功 |
| subagent（独立上下文） | ✅ | 本会话已用 8 次 |
| subagent_codex | ❌ **实测失败** | dispatch 后返回 `Product subagent failure (product: Codex; stage: turn; category: product-error)`；L2 决策改走 `mcp__codex__codex` |
| rules/scripts/gate.py | ❌ 不存在 | 只有 rules/phases/1,2 手册 |
| rules/phases/3..7 | ❌ 不存在 | 仅 1-literature-scout.md、2-deep-reader.md |

## 降级声明（按 R5）

- **阶段出口 gate 无法执行**（gate.py 缺失）→ 阶段 1–7 一律标注 degraded: ["gate:missing"]，出口检查由人工清单替代。
- **阶段 5 独立审稿可用**（subagent 已实测）→ 不降级。
- **LaTeX 缺失** → 论文只交 Markdown，PDF 编译延后。
