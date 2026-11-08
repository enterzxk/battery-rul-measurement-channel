# 中断源诊断（2026-11-08）

| 源 | 实测状态 | 处理 |
|---|---|---|
| **A 模型主动提问** | 本会话确实多次以「要我现在开 M0 吗？」收尾 | **已修**：AGENTS.md §2 三层权限，L1/L2 不停，只有 L3 停 |
| **B ARIS 阶段检查点** | skill 常量 `AUTO_PROCEED=true` / `HUMAN_CHECKPOINT=false` 默认已是非阻塞；本会话的 Stage 1 五个阶段全部连续跑完，未因检查点暂停 | **无需改**；调用时显式传参即可 |
| **E 官方 `subagent_codex`** | ❌ **不可用**：bundle 已装（`@deepseek-ai/dsh-subagent-codex@0.2.2-rc.1`）且工具已注册，但实测 dispatch 后失败 `Product subagent failure (product: Codex; stage: turn; category: product-error)` | **降级**：L2 决策一律走 `mcp__codex__codex`（ARIS 桥），不用 `subagent_codex` |
| **C DSH 工具权限审批** | 会话策略：`danger-full-access`，且「Approval prompts are disabled — actions requiring approval are rejected automatically」 | **不是暂停源，是硬失败源**。任何需要审批的操作会直接失败而非等待。故工作流必须留在 full-access 内，不触发审批 |
| **D 上下文压缩** | 本会话已压缩过一次 | **已修**：`.research/STATE.md`（唯一真相）+ `LEDGER.jsonl` + `CODEX_DECISIONS.md` + `.aris/runs/*.json`（done vs accepted，可 resume）|

## 关键区分

- `AUTO_PROCEED` 是**决策开关**，不是**工具授权开关**。打开它不会获得任何原本没有的权限。
- 本会话没有「自动审批」可配：审批被禁用且自动拒绝。因此 C 类中断不会发生，但也意味着**不能依赖审批提示来兜底**——权限判断必须写在 AGENTS.md 里。

## ARIS 参数的真实支持情况

| 参数 | 是否真实存在 | 依据 |
|---|---|---|
| `AUTO_PROCEED` | ✅ | research-pipeline / idea-discovery / auto-review-loop 的 Constants 段 |
| `HUMAN_CHECKPOINT` | ✅ | 同上 |
| `REVIEWER_DIFFICULTY` | ✅ | research-pipeline Constants |
| `CODE_REVIEW` | ✅ | research-pipeline Constants |
| `effort` | ⚠️ **不是 skill 参数** | skill 无此参数；这是 Codex 侧 `model_reasoning_effort`，已设为 `xhigh` |
| `reviewer: codex` | ⚠️ **不是 skill 参数** | skill 用 `REVIEWER_MODEL`（硬编码 gpt-6-astra，不改）；实际路由由 §8 覆盖为 gpt-6.1-sol |
| `beast` | ❌ **不存在** | 无此档位；Codex 支持 low/medium/high/xhigh/max/ultra |
