# CD-011 · L2 决策：外部复现推翻 CD-010 之后

model: gpt-6.1-sol / xhigh
threadId: 01a1bac5-3535-7731-953f-d3875faf1a28

**L2 decision: keep the donor-method direction frozen pending one corrected replication. Withdraw the “affine-only artifact” conclusion.** The code reveals a material protocol difference that prevents accepting the reported external result as confirmation.

1. **Does this unfreeze the direction? No, not yet.** ISU’s script allows two donors with four rows each, while one donor needs eight; unsuccessful draws silently remove evaluated cells. UConn required every candidate donor to have at least eight rows. Thus donor count changes donor eligibility and potentially the evaluated population. Exact matching of the total row budget does not resolve this confounding. See [ISU sampling](/E:/桌面/rul/rul_v4_20261107/.research/results/isu_repl.py:74) versus [UConn eligibility](/E:/桌面/rul/rul_v4_20261107/.research/results/m2c3.py:61). **I authorize one corrected confirmation, with a fixed decision rule.**

2. **What claim becomes defensible if it passes?** “At an eight-label budget, distributing labels across two donor cells modestly improves affine and isotonic calibration on ISU; affine benefit and 1-NN harm recur across datasets.” That supports a reproducible allocation finding. Donor-identity causality, universal diversity benefit, and an original method remain unestablished. A paired donor-count × calibrator contrast should quantify estimator dependence. UConn’s isotonic null is compatible with low power; its cause remains unknown. Compare native units and within-dataset relative effects.

3. **Single most important control: common-support replication.** Use the same donor pool with **≥8 rows per donor**, the same evaluable cells and conditions, exactly eight labels per arm, and shared calibration samples across calibrators. Save draw-level results; derive MAEs, paired deltas, intervals and Holm-adjusted tests from that identical support. Currently, the displayed MAEs and paired deltas use different condition sets—explaining why the displayed 1-NN means improve while its paired delta indicates harm. See [aggregation](/E:/桌面/rul/rul_v4_20261107/.research/results/isu_repl.py:99).

4. **Is “the effect is an affine-family artifact” dead? As an established explanation, yes. I withdraw it.** An isotonic nonsignificant result never demonstrated affine specificity. The external signal strengthens the challenge, but clean empirical falsification requires repairing the population mismatch.

5. **What would stop the reopening?** Failure of the corrected isotonic benefit under the fixed multiplicity family, disappearance of gains on common support, or practically negligible benefit against a criterion fixed before rerunning. If confirmation passes, reopen the empirical allocation/sensitivity programme. **The 1-NN reversal belongs in its central result; a reproducible 4–6% gain alone is not a reason to stop.**
