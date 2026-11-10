# Current research task — turn-the-programme-s-only-robust-positive-result

- Stage: **S2 Research Gap Discovery** (visit 1)
- Status: active
- Goal: Turn the programme's only robust positive result (ISU: observed health trajectory improves EOL prediction by 19.4% over age+stress, CI [-27.4,-11.2]) into a genuine method contribution — a schedule/inspection-aware monitoring decision rule with an explicit decision loss, a sparsity or information metric, and a falsifiable threshold — or prove that it cannot be done and close the line with an auditable negative result.

## Active task

- **Stage E closed: timing policy NO-GO; both pivots fail their gates**
- Pre-registered 18-cell temporal policy replay, nested LOCO, non-anticipating acquisition, R=max(T,exp(q_tau)). Result: 14 NEGATIVE / 4 INCONCLUSIVE / 0 SUPPORT. Primary setting (T=63,N=2,c_f/c_w=5): VoI delta_CF +0.23 d [-1.65,+2.28] vs margin 4.25 d; Candidate -3.69 d. Oracle hindsight gap 12.67 d (29.8% of total J) but the best online policy captures 3.0%. All six identifiability gates passed (I1-I6), so this is a negative result from an identified design, not an invalid experiment. Pivots: B (clock discrimination) structurally unidentifiable - ISU records have no cycle-count and no measured-throughput field, only a nominal throughput that is a per-condition rescaling of calendar days; A (design sets the error) downgraded to a diagnostic by Codex. Registered F-020 and F-021.

## Next actions

1. Do not reopen the timing-policy direction without a new online policy class that reduces subset-selection variance without foreknowledge, tested under the same frozen contract
2. To reopen pivot B, obtain the ISU Cycling_json.zip (10.2 GB, previously blocked) or a cohort whose cycles-per-day varies at fixed throughput; then build the Codex-required condition-level exposure map before any model comparison
3. If pivot A is retained, first correct the target quantity (expected absolute error, not prediction sd), define held-out leverage excluding the test condition, pre-register the response surface and a training-only scale estimate, and include a constant-scale rival plus a median-lifetime rival
4. Preserve the reusable asset: the six-gate identifiability audit (oracle ceiling, within-cell loss CV, policy Jaccard, feature-locality destruction test, subset enumerability) plus the nested non-anticipating replay harness
5. All future experiments on campus-h3 or lab-server; local runs are void under the workspace compute rule
6. Archive the timing programme; no further policy fits. Register F-020 and F-021
7. To reopen pivot B, obtain the ISU Cycling_json.zip (10.2 GB, previously blocked) or a cohort whose cycles-per-day varies at fixed throughput; then build the condition-level exposure map before any model comparison
8. If pivot A is retained, correct the target quantity to expected absolute error, define held-out leverage excluding the test condition, and add a constant-scale rival plus a median-lifetime rival
9. Preserve the six-gate identifiability audit and the nested non-anticipating replay harness as the reusable assets
10. Do not rescue the closed direction via budget points, seeds, favourable subsets or stacked modules

## Selected idea

_none selected yet_

## Resume

Read NEXT_48H_PLAN.md, REVIEW_RESPONSE.md, CLAIM_EVIDENCE_MAP.md, RESULTS_C.md, CORRECTIONS.md, TEN_HOUR_FINAL_REPORT.md in .research/programmes/online-mechanisms-20261110/, then research_status and continue from next_actions[0]. Hard discipline: (1) fix the evaluation population; (2) never build query times from the eventual answer; (3) one statistical unit (condition for cluster inference); (4) always run the age baseline; (5) save per-cell predictions; (6) no fabrication. Every new contrast must first be checked for whether the 'change' is produced automatically by schedule or population structure.

