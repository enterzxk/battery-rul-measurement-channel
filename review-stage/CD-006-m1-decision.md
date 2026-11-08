# CD-006 · L2 决策：M1 两项未过线后怎么办

model: gpt-6.1-sol / xhigh
threadId: 01a1baa7-45ac-7e51-a6b6-ce069f7d84e4

**Decision: D — withdraw the floor title, mark the current M1 as unaccepted, and correct P2’s implementation under the original protocol before deciding whether to continue.** Source inspection found a material mismatch that changes the interpretation of your results. An independent reviewer concurs.

1. **The reported P2 did not implement the preregistered test.** In [m1_run.py](E:/桌面/rul/rul_v4_20261107/.research/results/m1_run.py:67), each target cell receives **one donor permutation**; there is no repeated donor-draw loop in `e1_2`. At line 74, `mean` versus `median` aggregates **across evaluated target cells**, whereas the [plan specifies MC-draw aggregation](E:/桌面/rul/rul_v4_20261107/refine-logs/EXPERIMENT_PLAN.md:41) and **1,000 nested draws** for P2. Consequently, 0.408/10-of-11 and 0.420/8-of-11 describe two different summaries of one sampled donor allocation. The 8-of-11 result is **not the preregistered MC-median sensitivity test**. P2 therefore remains untested under its specified procedure; calling it either confirmed or definitively failed is premature. M0’s 0.018 does not validate this different implementation.

2. **Do one corrective P2 run; do not choose A.** Keep the original target population, strict donor exclusion, full-trajectory arms, and condition-level inference. Use 1,000 draws, nesting donor sets within each draw. Preserve M0’s aggregation order: calculate cell MAEs, take the cell-macro mean within each condition and draw, then apply mean/median across MC draws. Retain the original joint gate: **Δ≥0.15 and ≥10/11 conditions improving under both aggregations**. Preserve the old outputs with an implementation-deviation notice. Changing P1’s eligibility or endpoint now would answer a different question; it cannot repair the original floor claim. P1 remains unestablished, and P3’s interval supports neither a confirmed interaction nor an identified mechanism.

3. **The strongest title currently supportable is descriptive:**  
   *“One versus Two Full-Trajectory Donors in Cross-Condition Battery RUL Calibration: An Exploratory Study.”*  
   The surviving statement is: **“For the sampled donor allocation, using two complete donor trajectories reduced mean calibration error relative to one.”** Remove *Labels Cannot Buy Diversity*, *Identity Floor*, and saturation language. Full-trajectory donor count also increases total label rows, so this comparison cannot isolate an independent benefit of donor identity. The positive reported estimates justify preserving the observation; they do not justify a publication GO.

4. **The single most likely current artifact is a favorable one-off donor allocation being presented as MC-robust evidence.** The misplaced median calculation makes that same allocation appear to have undergone the registered robustness check. The condition bootstrap quantifies variation conditional on that allocation; it does not turn one allocation into the intended MC-averaged result.

5. **One result would reverse this decision:** a correctly implemented, preregistration-faithful P2 run passing the **unchanged joint gate** would move me from D to **B, restricted to a descriptive donor-count result**. It would reopen the empirical direction. It would not restore the floor title, establish complementarity, or demonstrate identity benefits at equal label budget.
