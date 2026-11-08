# CD-013 · L2 决策：机制结果如何写

model: gpt-6.1-sol / xhigh
threadId: 01a1bacd-c86e-7711-bf76-b7f819a8d04a

**Decision: continue with one locked validation package. Reject “mechanism confirmed”; the current manuscript is not ready for TIM submission.**

1. **The probe is legitimate; the proposed interpretation overreaches.** For query prediction \(x\) and the same nearest calibration point \(j\), your [implementation](E:/桌面/rul/rul_v4_20261107/.research/results/mechanism.py:44) gives
   \[
   \hat y_L=y_j,\qquad \hat y_R=x+y_j-x_j.
   \]
   Residual borrowing removes **neighbor prediction displacement \(x_j-x\)**. It retains donor residual bias \(y_j-x_j\). At \(x=x_j\), both estimators are identical—even with donor heterogeneity. It also changes the local slope from zero to one. Therefore write: **“Donor-count effects depend on calibration geometry; displacement and donor heterogeneity are candidate explanations.”** Coverage and heterogeneity remain unmeasured. Falsifiers: coverage-matched allocations retain the gains; independently changing donor offsets at fixed prediction coordinates fails to produce the predicted harm. Isotonic is shape-constrained fitting, not simply slope fitting.

2. **Poor absolute performance does not invalidate a diagnostic probe.** It does prevent claiming an improved method. More seriously, \(p=.953\) establishes neither equivalence nor cancellation: test the paired interaction \(\Delta_{\mathrm{resid}}-\Delta_{\mathrm{level}}\), and assess residual-effect equivalence against a prespecified practical margin.

3. **Title:** *When More Donor Cells Help or Harm: Fixed-Budget Calibration of Battery Remaining Useful Life.*

   The three figures:
   - **Design and geometry:** cell-disjoint calibration, fixed \(k\), donor-colored prediction–label plots, and the exact estimator identity.
   - **Empirical effects:** both datasets, four calibrators, condition-level paired donor effects with confidence intervals, direct interactions, and absolute MAE.
   - **Mechanism discrimination:** independently varied coverage and donor offsets, measured nearest-neighbor distances, boundary frequency, and predicted versus observed effects.

4. **TIM still needs a defensible measurement contribution and stronger identification.** Position the contribution against existing local-gradient correction work such as [DNNR](https://proceedings.mlr.press/v162/nader22a.html); the estimator contrast alone does not establish novelty. Required evidence includes physical-cycle results—the code currently uses RPT-count RUL—realistic label availability, uncalibrated and intercept-only controls, another frozen base predictor, and uncertainty that respects condition-level dependence. Correct the Holm implementation’s missing cumulative maximum. TIM’s [author guidance](https://ieee-ims.org/publication/ieee-tim/information-authors) explicitly flags existing-dataset-only studies lacking adequate measurement discussion and justification for absent original experimental validation.

5. **Yes: run UConn once under a frozen protocol.** It tests transfer of the probe beyond its discovery dataset and is not redundant. UConn is already explored, so call this a **locked follow-up**, not untouched external confirmation. With 11 conditions, prioritize effect intervals and interaction estimates; failure to reach significance alone cannot decide replication.
