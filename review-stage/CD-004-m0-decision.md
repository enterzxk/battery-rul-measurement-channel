# CD-004 · L2 决策：M0 是否先跑

model: gpt-6.1-sol / xhigh
threadId: 01a1ba79-064d-7092-8f93-b803830f1822

**1. Decision: D — complete the full M0, then run a corrected M1 with the estimator controls before proceeding to M2–M6.**

M0 remains a hard blocker. Resolving 60% of the 0.27 drift leaves roughly **0.10 MAE unexplained**, larger than the reported 0.062 row-budget gain and several later donor increments. B and C would generate results whose interpretation could change when the remaining choices are resolved.

I reject A **as specified** because the downstream plan contains inferential errors: the floor analysis treats 45 target–donor pairs from only **three conditions** as independent, and the complementarity contrast has its sign reversed relative to its prediction. These require correction before execution. See [floor analysis](E:/桌面/rul/rul_v4_20261107/refine-logs/EXPERIMENT_PLAN.md:115) and [interaction definition](E:/桌面/rul/rul_v4_20261107/refine-logs/EXPERIMENT_PLAN.md:154).

**2. Strongest counter-evidence against my choice**

Every reported trajectory improves from m=1 to m=2, including the median analysis. The entire programme costs only about eight CPU-hours, so running A could be operationally simpler. Also, **p=0.065 versus p=0.00098 does not itself establish contradictory effects**: both estimates favor additional donors. My objection concerns identification and valid uncertainty, not crossing 0.05.

**3. Single highest-risk assumption**

**The single-donor plateau represents a transferable donor-identity floor, rather than a finite-budget plateau or instability of the affine estimator.** Reproducing the same curve cannot establish that mechanism. Neither a nonsignificant +0.018 nor a small significant 0.062 establishes equivalence; the latter also exceeds the proposed ±0.05 equivalence margin.

**4. Next three concrete actions, in order**

1. **Freeze all five DoFs in M0:** affine scope, strict donor eligibility, weighting order, aggregation, and nested sampling. Use identical eligibility keys and donor draws across implementations. Separate implementation agreement from variability across the three fixed MC seeds; retain the <0.03 convergence gate **within each aggregation rule**.

2. **Correct and timestamp the analysis plan before M1.** Use mean MAE over donor draws as primary because the decision target is expected error; retain median as mandatory sensitivity. Record this as an amendment after inspecting results. Fix the interaction sign, use condition-level dependence for uncertainty, and remove the option to rescue a failed robustness gate by reporting mean alone.

3. **Run the decisive M1 contrasts plus clipped-affine/isotonic controls.** Compare donor counts at matched total label budgets and common evaluation keys. Test the row plateau separately. With only three eligible conditions, restrict the floor claim accordingly. Proceed to the remaining programme only when these results support the claimed mechanism; otherwise deliver the bounded negative result.

**5. One reversal trigger**

If the donor advantage disappears under **matched label budgets and stable alternative calibrators**, I would terminate the donor-identity-floor direction and redirect the work to a protocol-sensitivity report. That would directly undermine the mechanism carrying the title.
