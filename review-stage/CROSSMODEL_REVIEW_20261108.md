# Cross-model review · gpt-6.1-sol / xhigh · 2026-11-08

threadId: 01a1b9b3-c2b1-74a1-bf71-a2362bf1d4a1

**The evidence supports a benefit from target-condition supervision, but it does not establish that label placement is unimportant.** I could not independently retrieve Zhao’s cited paper, so the Zhao-specific assessment below is conditional on your description.

1. **Publishability after Zhao: insufficient as a standalone budget curve.**

   My assessment for TIM/TII/Applied Energy is **below the contribution threshold in its current form**. More k values, stricter cell separation, and better statistics improve credibility, but mainly refine an existing empirical question.

   The surrounding literature is also broader than Zhao: Su et al. studied transferable battery **SOH data sufficiency** across 310 batteries, seven datasets and six chemistries. SOH differs from RUL, but “limited data can suffice for transfer” is already occupied territory. [Su et al., 2025](https://doi.org/10.1016/j.xcrp.2025.102901).

   What must be new is a **decision-changing result**: a mechanism predicting when calibration succeeds or fails, a defensible acquisition-cost rule, or a replicated evaluation finding that overturns existing deployment recommendations. A detailed learning curve alone does not deliver that.

2. **Below MDE yet significant: no contradiction; neither number alone governs the claim.**

   An 80%-power MDE is the effect size giving an 80% rejection probability under specified assumptions. It is **not a minimum effect capable of producing significance**. Smaller effects can yield \(p=0.0098\).

   Furthermore, power for a mean MAE difference and a Wilcoxon signed-rank test concern different quantities. Wilcoxon uses signed ranks; interpreting it as a location-shift test requires appropriate assumptions. Its p-value does not directly establish a 29–32% population mean reduction.

   Report the condition-level paired effects, uncertainty for the stated estimand, the exact MDE calculation, and multiplicity across searched budgets and calibrators. The MDE informs design sensitivity; valid inference and uncertainty govern the resulting claim. Do not use retrospective power as a second acceptance test. [Hoenig and Heisey, 2001](https://doi.org/10.1198/000313001300339897).

   Also, deleting each condition produces correlated sensitivity analyses, not 11 independent replications.

3. **A framing beyond refining Zhao: none is established by the supplied evidence.**

   A potentially distinct question is: **“What does deployable target supervision actually cost?”** Your k counts labeled rows; Zhao reportedly counts cells. Several retrospective RUL labels from one completed donor trajectory do not represent several independently acquired lifetimes. Multiplying cells by average rows per cell cannot establish equivalent information or cost. The contribution would have to show how donor diversity and label availability change an actual acquisition decision.

   The current placement claim also faces three concrete objections:

   - At k=16, endpoint MAE is **1.081 higher than random—24.9% worse**. Placement can therefore matter materially within your tested designs.
   - Quantile–random nonsignificance does not establish equivalence. Specify a practically justified margin and show a suitable paired interval lies entirely within it. [Lakens, 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906/).
   - “y-oracle” is a true-label-based heuristic, not an optimal acquisition oracle. Its failure does not bound what better placement could achieve.

   **There is also a provenance problem:** your local calibrator script tests quantile versus **mean-random**, while the quoted leave-one-condition-out analysis concerns placement at **k=4**. Those results cannot establish robustness of the new median-random budget claim. [Calibrator script](<E:/桌面/rul/rul_v4_20261107/review-stage/_diag6.py>), [leave-one-condition-out analysis](<E:/桌面/rul/rul_v4_20261107/review-stage/NOVELTY_REVIEW.md:272>).

4. **Highest-value single experiment: a frozen, cost-aware replication on a second dataset.**

   Use a multi-condition dataset with replicated cells and reserve evaluation cells entirely. Freeze the predictor, calibrator, selection rules and primary contrast before inspecting results.

   Run one crossed acquisition study: vary **labeled rows k and distinct donor cells m**, comparing random, quantile and endpoint selection within each eligible \((k,m)\) setting. Include k=0. Admit RUL labels only from donor lifetimes completed before the simulated deployment date; report completed donor lifetimes and aging time alongside row count.

   Predefine a placement-equivalence margin from practical prediction requirements—not the 41.6% MDE—and assess whether budget gains exceed placement effects with uncertainty. Preserve the random-arm distribution and its tail risks; 1,000 draws improve Monte Carlo precision without increasing the number of independent conditions.

   This tests generalization, distinguishes rows from independent supervision, and exposes retrospective availability advantages. It can largely use CPU calibration, giving high information value per GPU-hour. If placement remains material or the gain disappears under eligible labels, the headline must change.

5. **Verdict: DOWNGRADE—retain a dataset-specific supervision benefit, withdraw “placement is not a main lever,” and defer a Q1 submission claim until cost-aware external replication establishes a distinct contribution.**
