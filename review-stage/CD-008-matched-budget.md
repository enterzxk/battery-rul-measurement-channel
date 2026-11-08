# CD-008 · L2 决策：匹配行预算结果

model: gpt-6.1-sol / xhigh
threadId: 01a1bab0-93a0-73b3-9ee7-0693f1babfa5

**L2 decision: continue with a corrected EXP-009; do not promote the current result to a paper-carrying identity claim. Independent source review concurs.**

1. **Enough to carry the paper? No.** The m1→m2 results at k=8/16 support an exploratory **donor-allocation effect under the evaluated calibrator**, not an isolated identity mechanism. Matching row count does not separate identity from temporal coverage or estimator conditioning. Moreover, even Holm correction across just these two budgets gives adjusted p≈.078 for both; 200 draws leave **11 independent conditions**. The report also overstates robustness: k=8 median p=.072, with 8/11 improving—not dual significance. See [EXP-009, line 36](E:/桌面/rul/rul_v4_20261107/.research/exp/EXP-009-matched-budget.md:36); [Holm reference](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html).

2. **k=32: re-scope; retain the original as a documented confounded result.** Restrict every arm to the **same eligible donor pool, evaluated cells, and conditions**, requiring candidate donors to have ≥32 rows. Report exclusions and actual condition/cell counts; call this a long-trajectory subset analysis. Do not pool it with k≤16. The displayed means imply a .883 improvement, versus the paired .267, because the code averages each arm over its available conditions but computes paired differences over their intersection. Both summaries must use identical populations.

3. **The reversal currently falsifies nothing about fixed-budget donor count.** I found a decisive implementation error: [`per_donor = k // m`](E:/桌面/rul/rul_v4_20261107/.research/results/matched_budget.py:55). At k=8, m=3 receives **six rows**, whereas m=2 receives eight; the other m=3 arms receive 15/30 rows. Thus “spreading labels too thin hurts” is also unestablished. Preserve the result as a protocol error. **If deterioration survives exact budgets and common support**, it would falsify universal monotonic benefit and strengthen a conditional allocation paper while weakening a “more donors always helps” story. Neither outcome alone identifies a mechanism.

4. **Strongest defensible title now:** *One versus Two Donor Cells at Equal Label Counts for Cross-Condition Battery RUL Calibration: An Exploratory Study.* The working claim is limited: two-donor allocation showed small average gains at 8–16 labels under this protocol. **No identity floor, saturation, optimal donor count, or general diversity benefit.**

5. **Next: correct EXP-009 with exact-k randomized remainder allocation, common donor/evaluation support, and a frozen testing family; then prioritize M2’s estimator/coverage controls before M3.**

Project records remain unchanged because this session is read-only.
