# CD-015 · L2 决策：范围与最终主张

model: gpt-6.1-sol / xhigh
threadId: 01a1baff-23c0-7ca1-a1a5-5eaa45d5dbf5

**1. Decision: begin writing; do not declare the work TIM-ready.** The single missing piece is **validated, original guidance for allocating a calibration budget relative to a strong competing strategy**. You have credible estimator-dependent findings; “averaging helps” alone does not establish that contribution. TIM requires a clear advance in instrumentation and measurement, with explicit justification for dataset-only validation. [TIM author guidance](https://ieee-ims.org/publication/ieee-tim/information-authors)

Two interpretations must narrow: null interactions do not establish constraint invariance; consistent quartile signs do not establish RUL invariance. The selected-query reversal remains real. Aggregation is a supported explanation, not an identified causal mechanism.

**2. Small effects and ranking reversals are honest boundaries, not disqualifiers.** However, practical value requires comparing absolute errors. HGB affine with two donors scores **500.21**, worse than isotonic with one donor at **459.95**. Improving an inferior strategy does not establish useful allocation guidance. Also distinguish significance rankings from performance rankings: your table’s lowest-error calibrator is isotonic for HGB and affine for Ridge. [EXP-017](E:/桌面/rul/rul_v4_20261107/.research/exp/EXP-017-controls.md:16)

**3. Authorize one final experiment: a frozen practical-utility comparison.** At identical eight-label budgets, compare a joint calibrator/donor-count rule selected exclusively on training conditions against the strongest fixed calibration strategy. Keep evaluation cells disjoint, donor eligibility identical, and donor acquisition costs explicit. Report condition-level paired confidence intervals and cell-level harm; separately report the selected-query boundary.

Move Ridge normalization inside training folds: [controls.py](E:/桌面/rul/rul_v4_20261107/.research/results/controls.py) currently standardizes before LOGO splitting. Call this a locked internal evaluation, not untouched confirmation. **If allocation adds no useful benefit, stop pursuing method superiority and finish the empirical boundary paper.**

**4. Final title:**  
*Donor Allocation at a Fixed Label Budget: Estimator Dependence and Population Boundaries in Battery RUL Calibration*

The paper may make exactly these three claims:

- At eight labels from other target-condition cells, increasing donors from one to two produced modest average improvements for affine and isotonic calibration across two datasets, with unequal statistical support.
- Donor-count effects depend on the estimator: raw-label 1-NN showed the opposite direction; residual borrowing attenuated that harm. These controls constrain possible mechanisms without proving aggregation alone causes the difference.
- Full-population benefits have population boundaries: quartile estimates retain their signs, while the selected-query subset reverses affine/isotonic effects under both donor pools. No universal donor-count or calibrator recommendation follows.
