# CD-014 · L2 决策：部署约束导致效应反转

model: gpt-6.1-sol / xhigh
threadId: 01a1bae7-e715-7972-9b3d-6e4695a6e6df

**Decision: authorize one matched-population experiment. Treat the constraint as a candidate central finding; hold the manuscript pivot until attribution is resolved.**

1. **Fatal or central?** Fatal to an unconditional “more donors help” claim. Potentially central to a study of label availability and calibration. But your deployment premise needs qualification: `donor_eol_cum ≤ target_cycle` compares **cycle ages**, not calendar availability. A historical donor can outlive the target and still have finished before deployment. Your rule represents a synchronized cohort with comparable cycling schedules; otherwise call it **lifetime-truncated donor eligibility**.

2. **Could population change explain it? Yes—and you also changed weighting.** EXP-017 averages queries within each cell before averaging cells; EXP-018 pools eligible queries within each condition. Cells with more eligible queries therefore receive more weight. See [controls.py](E:/桌面/rul/rul_v4_20261107/.research/results/controls.py:70) and [asof.py](E:/桌面/rul/rul_v4_20261107/.research/results/asof.py:73). You changed donor eligibility, evaluation population, and aggregation simultaneously. Also, “early RPTs have small RUL” is backwards within a cell: earlier queries have larger remaining life. The explanation for lower absolute MAE is **unestablished**.

3. **The defensible claim now:** “Under the implemented restricted-donor protocol, at eight labels, two donors increased error for affine, isotonic, and 1-NN calibration, while intercept calibration improved.” Only affine and isotonic **reversed**; 1-NN was already harmful. Your clustering/dilution hypothesis remains untested. Selecting short-lived donors does not establish that their calibration information clusters, and intercept’s improvement contradicts a general dilution explanation.

4. **The single decisive experiment:** run a **donor-pool × donor-count factorial comparison on identical queries**.

   - Freeze the 199 `(cell, RPT)` keys, base predictions, and calibrators.
   - Compare unrestricted versus restricted pools, each with one versus two donors.
   - Keep exactly eight labels, identical donor-length eligibility, and equal Monte Carlo budgets.
   - Aggregate queries → cells → conditions, using identical weights throughout.
   - For each condition and calibrator, calculate  
     \[
     \Delta_P=MAE_{P,1}-MAE_{P,2},\qquad I=\Delta_R-\Delta_U.
     \]
     Report paired interaction uncertainty; Holm-correct four interaction tests. Independent \(n=11\), not 199.

   Positive \(\Delta_U\), negative \(\Delta_R\), and a supported negative interaction establish reversal attributable to the eligibility policy **on that population**. If unrestricted calibration already reverses there, population/weighting contributed. Both explanations can coexist. Rescore unrestricted full versus common populations with identical aggregation to quantify the population component.

5. **TIM direction:** conditionally yes—center **availability-aware calibration evaluation**, retaining donor count as an experimental factor. A credible measurement-protocol contribution fits [TIM’s stated scope](https://ieee-ims.org/publication/ieee-tim), but one confounded reversal establishes neither novelty nor submission readiness. After the matched experiment passes, require literature differentiation and external replication before committing the manuscript.

Independent-context review agreed. Formal ARIS review remains **provisional** because its required reviewer bridge is unavailable; this read-only session did not persist the decision.
